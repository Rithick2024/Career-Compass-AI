"""
Service layer for Placement Readiness and Skill Gap Intelligence.
"""

from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.shared.enums import ProficiencyLevel
from app.modules.intelligence.repository import IntelligenceRepository
from app.modules.intelligence.schemas import (
    ReadinessResponse,
    ReadinessComponent,
    MarketSkillGapResponse,
    SkillGapItem,
    JobMatchResponse,
    JobMatchSkillItem,
)


def prof_to_num(prof: Optional[ProficiencyLevel | str]) -> int:
    """Helper to convert ProficiencyLevel to ordinal numeric scale 1..3."""
    if prof is None:
        return 1
    val = prof.value if hasattr(prof, "value") else str(prof)
    val = val.lower()
    if val == "intermediate":
        return 2
    if val == "advanced":
        return 3
    return 1  # beginner default


def prof_to_str(prof: Optional[ProficiencyLevel | str]) -> str:
    """Helper to standardize proficiency enum/str to lowercase string."""
    if prof is None:
        return "beginner"
    val = prof.value if hasattr(prof, "value") else str(prof)
    return val.lower()


class IntelligenceService:
    def __init__(self, db: AsyncSession) -> None:
        self.repository = IntelligenceRepository(db)

    async def calculate_readiness(self, user_id: int) -> ReadinessResponse:
        """Calculate overall 100-point transparent placement readiness score."""
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        student_skills = await self.repository.get_student_skills(student.id)
        active_student_skills = [ss for ss in student_skills if ss.skill and ss.skill.is_active]

        resumes = await self.repository.get_student_resumes(student.id)
        has_default_resume = any(r.is_default for r in resumes)

        is_placed = await self.repository.has_accepted_placement(student.id)
        active_jobs = await self.repository.get_active_visible_jobs()

        # --- 1. Academic Readiness Pillar (25 pts max) ---
        if student.cgpa is not None:
            cgpa_val = float(student.cgpa)
            cgpa_score = max(0.0, min(20.0, (cgpa_val / 10.0) * 20.0))
        else:
            cgpa_score = 0.0

        dept_score = 5.0 if student.department_id is not None else 0.0
        academic_total = round(cgpa_score + dept_score, 1)

        if student.cgpa is not None and student.department_id is not None:
            academic_expl = f"CGPA is {float(student.cgpa):.2f}/10.00 ({cgpa_score:.1f} pts) and Department is assigned (5.0 pts)."
        elif student.cgpa is not None:
            academic_expl = f"CGPA is {float(student.cgpa):.2f}/10.00 ({cgpa_score:.1f} pts). Select a department for +5.0 pts."
        elif student.department_id is not None:
            academic_expl = "Department is assigned (5.0 pts). Add your CGPA to evaluate academic eligibility (up to +20.0 pts)."
        else:
            academic_expl = "Add your CGPA and select your department to earn academic readiness points."

        # --- 2. Skill Profile Pillar (35 pts max) ---
        active_count = len(active_student_skills)
        quantity_score = min(active_count / 5.0, 1.0) * 15.0

        if active_count == 0:
            quality_score = 0.0
            skill_expl = "No active skills added yet. Add skills to improve your technical profile."
        else:
            prof_factors = []
            for ss in active_student_skills:
                num_val = prof_to_num(ss.proficiency)
                if num_val == 3:
                    prof_factors.append(1.0)
                elif num_val == 2:
                    prof_factors.append(0.7)
                else:
                    prof_factors.append(0.4)
            avg_factor = sum(prof_factors) / active_count
            quality_score = avg_factor * 20.0
            skill_expl = f"You have {active_count} active skill{'s' if active_count > 1 else ''} ({quantity_score:.1f}/15.0 pts) with proficiency factor ({quality_score:.1f}/20.0 pts)."

        skill_total = round(quantity_score + quality_score, 1)

        # --- 3. Profile & Resume Pillar (20 pts max) ---
        opt_fields = [
            bool(student.phone and student.phone.strip()),
            student.date_of_birth is not None,
            bool(student.address and student.address.strip()),
            bool(student.linkedin_url and student.linkedin_url.strip()),
            bool(student.github_url and student.github_url.strip()),
            student.graduation_year is not None,
        ]
        populated_count = sum(opt_fields)
        profile_score = (populated_count / 6.0) * 10.0
        resume_score = 10.0 if has_default_resume else 0.0
        profile_resume_total = round(profile_score + resume_score, 1)

        compl_pct = int(round((populated_count / 6.0) * 100))
        res_status = "uploaded" if has_default_resume else "missing"
        profile_expl = f"Profile is {compl_pct}% complete ({profile_score:.1f}/10.0 pts) and Default Resume is {res_status} ({resume_score:.1f}/10.0 pts)."

        # --- 4. Market Eligibility Pillar (20 pts max) ---
        total_active_jobs = len(active_jobs)
        if total_active_jobs == 0:
            market_score = 0.0
            market_expl = "No active jobs are currently available to evaluate market eligibility."
        else:
            eligible_jobs = 0
            for job in active_jobs:
                cgpa_ok = job.min_cgpa is None or (student.cgpa is not None and student.cgpa >= job.min_cgpa)
                dept_ids = [ed.department_id for ed in job.eligible_departments]
                dept_ok = len(dept_ids) == 0 or (student.department_id is not None and student.department_id in dept_ids)
                if cgpa_ok and dept_ok:
                    eligible_jobs += 1
            ratio = eligible_jobs / total_active_jobs
            market_score = round(ratio * 20.0, 1)
            pct_val = int(round(ratio * 100))
            market_expl = f"You are eligible for {eligible_jobs} out of {total_active_jobs} active job postings ({pct_val}% alignment)."

        # --- Total Score & Status Category ---
        raw_total = academic_total + skill_total + profile_resume_total + market_score
        readiness_score = round(max(0.0, min(100.0, raw_total)), 1)

        if readiness_score < 40.0:
            status_category = "Needs Improvement"
        elif readiness_score < 60.0:
            status_category = "Developing"
        elif readiness_score < 80.0:
            status_category = "Good"
        else:
            status_category = "Strong"

        # --- Actionable Recommendations ---
        recs = []
        if not has_default_resume:
            recs.append("Upload a default resume.")
        if active_count < 5:
            rem = 5 - active_count
            recs.append(f"Add {rem} more active skill{'s' if rem > 1 else ''} to reach the platform readiness baseline of 5 skills.")
        if student.cgpa is None:
            recs.append("Add your CGPA to evaluate academic eligibility.")
        if student.department_id is None:
            recs.append("Select your department to evaluate job eligibility.")
        if populated_count < 6:
            recs.append("Complete missing profile details (such as LinkedIn URL or GitHub URL).")
        if total_active_jobs > 0 and (market_score / 20.0) < 0.5:
            recs.append("Improve your eligibility for more active jobs by reviewing their CGPA and department requirements.")

        # Deduplicate and limit to top 3
        dedup_recs = []
        for r in recs:
            if r not in dedup_recs:
                dedup_recs.append(r)
            if len(dedup_recs) == 3:
                break

        components = [
            ReadinessComponent(
                name="Academic Readiness",
                score=academic_total,
                max_score=25.0,
                weight_percentage=25,
                explanation=academic_expl,
            ),
            ReadinessComponent(
                name="Skill Profile",
                score=skill_total,
                max_score=35.0,
                weight_percentage=35,
                explanation=skill_expl,
            ),
            ReadinessComponent(
                name="Profile & Resume",
                score=profile_resume_total,
                max_score=20.0,
                weight_percentage=20,
                explanation=profile_expl,
            ),
            ReadinessComponent(
                name="Market Eligibility",
                score=market_score,
                max_score=20.0,
                weight_percentage=20,
                explanation=market_expl,
            ),
        ]

        return ReadinessResponse(
            readiness_score=readiness_score,
            status_category=status_category,
            is_placed=is_placed,
            components=components,
            actionable_recommendations=dedup_recs,
        )

    async def calculate_market_skill_gaps(self, user_id: int) -> MarketSkillGapResponse:
        """Calculate top market skill gaps for the authenticated student across active visible jobs."""
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        student_skills = await self.repository.get_student_skills(student.id)
        student_skill_map = {ss.skill_id: ss for ss in student_skills if ss.skill and ss.skill.is_active}

        active_jobs = await self.repository.get_active_visible_jobs()
        if not active_jobs:
            return MarketSkillGapResponse(
                total_active_jobs_evaluated=0,
                gaps=[],
                explanation="No active jobs available to evaluate market skill gaps.",
            )

        # Filter relevant jobs if profile has academic criteria
        relevant_jobs = []
        for job in active_jobs:
            cgpa_ok = job.min_cgpa is None or (student.cgpa is not None and student.cgpa >= job.min_cgpa)
            dept_ids = [ed.department_id for ed in job.eligible_departments]
            dept_ok = len(dept_ids) == 0 or (student.department_id is not None and student.department_id in dept_ids)
            if cgpa_ok and dept_ok:
                relevant_jobs.append(job)

        # If no relevant jobs match student's specific filters, evaluate across all active jobs
        eval_jobs = relevant_jobs if relevant_jobs else active_jobs

        gap_map: Dict[int, Dict] = {}

        for job in eval_jobs:
            for jrs in job.required_skills:
                if not jrs.skill or not jrs.skill.is_active:
                    continue
                sk_id = jrs.skill_id
                req_prof = jrs.min_proficiency or ProficiencyLevel.BEGINNER
                req_num = prof_to_num(req_prof)

                if sk_id not in student_skill_map:
                    g_type = "MISSING"
                    stu_prof_str = None
                else:
                    stu_ss = student_skill_map[sk_id]
                    stu_num = prof_to_num(stu_ss.proficiency)
                    stu_prof_str = prof_to_str(stu_ss.proficiency)
                    if stu_num < req_num:
                        g_type = "INSUFFICIENT_PROFICIENCY"
                    else:
                        continue  # Student satisfies requirement for this job

                if sk_id not in gap_map:
                    gap_map[sk_id] = {
                        "skill_id": sk_id,
                        "skill_name": jrs.skill.name,
                        "category": jrs.skill.category,
                        "jobs_requiring_skill": 0,
                        "max_req_num": req_num,
                        "required_prof_str": prof_to_str(req_prof),
                        "student_proficiency": stu_prof_str,
                        "gap_type": g_type,
                    }

                gap_map[sk_id]["jobs_requiring_skill"] += 1
                if req_num > gap_map[sk_id]["max_req_num"]:
                    gap_map[sk_id]["max_req_num"] = req_num
                    gap_map[sk_id]["required_prof_str"] = prof_to_str(req_prof)

                # Prioritize MISSING if mixed
                if g_type == "MISSING":
                    gap_map[sk_id]["gap_type"] = "MISSING"
                    gap_map[sk_id]["student_proficiency"] = None

        gaps_list = list(gap_map.values())
        # Sort by jobs_requiring_skill DESC, then skill_name ASC
        gaps_list.sort(key=lambda x: (-x["jobs_requiring_skill"], x["skill_name"]))
        top_gaps = gaps_list[:10]

        items = [
            SkillGapItem(
                skill_id=g["skill_id"],
                skill_name=g["skill_name"],
                category=g["category"],
                jobs_requiring_skill=g["jobs_requiring_skill"],
                required_proficiency=g["required_prof_str"],
                student_proficiency=g["student_proficiency"],
                gap_type=g["gap_type"],
            )
            for g in top_gaps
        ]

        expl = f"Evaluated {len(eval_jobs)} active visible job postings and identified top market skill gaps."

        return MarketSkillGapResponse(
            total_active_jobs_evaluated=len(eval_jobs),
            gaps=items,
            explanation=expl,
        )

    async def calculate_job_match(self, user_id: int, job_id: int) -> JobMatchResponse:
        """Calculate job-specific academic eligibility and skill match breakdown."""
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        job = await self.repository.get_active_visible_job_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found or is not currently active.")

        student_skills = await self.repository.get_student_skills(student.id)
        student_skill_map = {ss.skill_id: ss for ss in student_skills if ss.skill and ss.skill.is_active}

        # --- Academic Eligibility Check ---
        cgpa_ok = job.min_cgpa is None or (student.cgpa is not None and student.cgpa >= job.min_cgpa)
        dept_ids = [ed.department_id for ed in job.eligible_departments]
        dept_ok = len(dept_ids) == 0 or (student.department_id is not None and student.department_id in dept_ids)
        is_eligible = cgpa_ok and dept_ok

        if is_eligible:
            elig_expl = "You meet all academic CGPA and department eligibility criteria for this job."
        else:
            reasons = []
            if not cgpa_ok:
                if student.cgpa is None:
                    reasons.append(f"CGPA is not set (minimum required: {float(job.min_cgpa):.2f}).")
                else:
                    reasons.append(f"Your CGPA ({float(student.cgpa):.2f}) is below minimum required ({float(job.min_cgpa):.2f}).")
            if not dept_ok:
                if student.department_id is None:
                    reasons.append("Your department is not selected.")
                else:
                    reasons.append("Your department is not among the eligible departments for this position.")
            elig_expl = "Ineligible: " + " ".join(reasons)

        # --- Skill Match Check ---
        req_skills = [jrs for jrs in job.required_skills if jrs.skill and jrs.skill.is_active]
        total_req = len(req_skills)

        if total_req == 0:
            return JobMatchResponse(
                job_id=job.id,
                job_title=job.title,
                company_name=job.company.name if job.company else "",
                is_eligible=is_eligible,
                cgpa_eligible=cgpa_ok,
                department_eligible=dept_ok,
                eligibility_explanation=elig_expl,
                skill_match_percentage=100.0,
                total_required_skills=0,
                matched_skills=[],
                strong_matches=[],
                insufficient_proficiency=[],
                missing_skills=[],
                skill_match_explanation="No specific skills are currently defined for this job.",
            )

        matched_skills: List[JobMatchSkillItem] = []
        strong_matches: List[JobMatchSkillItem] = []
        insufficient_prof: List[JobMatchSkillItem] = []
        missing_skills: List[JobMatchSkillItem] = []

        for jrs in req_skills:
            req_prof = jrs.min_proficiency or ProficiencyLevel.BEGINNER
            req_num = prof_to_num(req_prof)
            req_str = prof_to_str(req_prof)
            sk_name = jrs.skill.name

            if jrs.skill_id in student_skill_map:
                stu_ss = student_skill_map[jrs.skill_id]
                stu_num = prof_to_num(stu_ss.proficiency)
                stu_str = prof_to_str(stu_ss.proficiency)

                if stu_num == req_num:
                    matched_skills.append(
                        JobMatchSkillItem(
                            skill_id=jrs.skill_id,
                            skill_name=sk_name,
                            min_proficiency=req_str,
                            student_proficiency=stu_str,
                            status="MATCHED",
                        )
                    )
                elif stu_num > req_num:
                    strong_matches.append(
                        JobMatchSkillItem(
                            skill_id=jrs.skill_id,
                            skill_name=sk_name,
                            min_proficiency=req_str,
                            student_proficiency=stu_str,
                            status="STRONG_MATCH",
                        )
                    )
                else:
                    insufficient_prof.append(
                        JobMatchSkillItem(
                            skill_id=jrs.skill_id,
                            skill_name=sk_name,
                            min_proficiency=req_str,
                            student_proficiency=stu_str,
                            status="INSUFFICIENT_PROFICIENCY",
                        )
                    )
            else:
                missing_skills.append(
                    JobMatchSkillItem(
                        skill_id=jrs.skill_id,
                        skill_name=sk_name,
                        min_proficiency=req_str,
                        student_proficiency=None,
                        status="MISSING",
                    )
                )

        satisfied_count = len(matched_skills) + len(strong_matches)
        match_pct = round((satisfied_count / total_req) * 100.0, 1)
        skill_expl = f"You match {satisfied_count} out of {total_req} required skills ({match_pct}%)."

        return JobMatchResponse(
            job_id=job.id,
            job_title=job.title,
            company_name=job.company.name if job.company else "",
            is_eligible=is_eligible,
            cgpa_eligible=cgpa_ok,
            department_eligible=dept_ok,
            eligibility_explanation=elig_expl,
            skill_match_percentage=match_pct,
            total_required_skills=total_req,
            matched_skills=matched_skills,
            strong_matches=strong_matches,
            insufficient_proficiency=insufficient_prof,
            missing_skills=missing_skills,
            skill_match_explanation=skill_expl,
        )
