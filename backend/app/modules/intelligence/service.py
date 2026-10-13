"""
Service layer for Placement Readiness and Skill Gap Intelligence.
"""

from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
from app.shared.enums import ProficiencyLevel
from app.modules.intelligence.gemini_provider import GeminiProvider
from app.modules.intelligence.models import ImprovementPlan, ImprovementPlanAction
from app.modules.intelligence.repository import IntelligenceRepository
from app.modules.jobs.models import Job
from app.modules.intelligence.schemas import (
    ReadinessResponse,
    ReadinessComponent,
    MarketSkillGapResponse,
    SkillGapItem,
    JobMatchResponse,
    JobMatchSkillItem,
    MentorChatRequest,
    MentorChatResponse,
    MentorContextSummary,
    MentorMessageResponse,
    MentorSessionSummaryResponse,
    MentorSessionDetailResponse,
    JobReadinessAssessmentResponse,
    SkillEvidenceItem,
    HistoricalRoundSignal,
    ImprovementPlanResponse,
    ImprovementPlanActionResponse,
    JobMentorAdviceRequest,
    JobMentorAdviceResponse,
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
    def __init__(
        self,
        db: AsyncSession,
        gemini_provider: Optional[GeminiProvider] = None,
    ) -> None:
        self.repository = IntelligenceRepository(db)
        self.gemini_provider = gemini_provider or GeminiProvider()

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

    async def ask_career_mentor(
        self, user_id: int, request: MentorChatRequest
    ) -> MentorChatResponse:
        """
        Grounded AI Career Mentor answering placement, skill, application, and interview preparation questions.

        Strict Privacy & Security:
        - Retrieves only sanitized educational standing, verified skills, and placement metrics for the authenticated student.
        - Zero personal identifiers (no names, emails, phones, or addresses) sent to provider.
        - Grounded in active campus hiring drives and student application status.
        """
        student = await self.repository.get_student_by_user_id(user_id)
        student_skills = await self.repository.get_student_skills(student.id)
        active_student_skills = [
            ss for ss in student_skills if ss.skill and ss.skill.is_active
        ]
        active_jobs = await self.repository.get_active_visible_jobs()
        applications = await self.repository.get_student_applications_with_details(student.id)
        resumes = await self.repository.get_student_resumes(student.id)
        is_placed = await self.repository.has_accepted_placement(student.id)

        dept_name = student.department.name if student.department else None
        grad_year = student.graduation_year
        has_cgpa = student.cgpa is not None
        cgpa_str = f"{float(student.cgpa):.2f}/10.0" if has_cgpa else "Not provided"

        top_skill_names = [ss.skill.name for ss in active_student_skills][:8]
        skills_summary = ", ".join(
            f"{ss.skill.name} ({prof_to_str(ss.proficiency).capitalize()})"
            for ss in active_student_skills[:12]
        ) or "None recorded yet"

        skills_detail_lines = []
        for ss in active_student_skills:
            cat = f" (Category: {ss.skill.category})" if ss.skill.category else ""
            skills_detail_lines.append(f"- {ss.skill.name}: {prof_to_str(ss.proficiency).capitalize()}{cat}")
        skills_detailed_str = "\n".join(skills_detail_lines) if skills_detail_lines else "No skills registered on profile yet."

        app_lines = []
        for a in applications:
            c_name = a.job.company.name if a.job and a.job.company else "Campus Drive"
            j_title = a.job.title if a.job else "Role"
            ctc_val = f" [₹{float(a.job.ctc_lpa):.1f} LPA]" if a.job and a.job.ctc_lpa else ""
            round_info = ""
            if a.rounds:
                sorted_r = sorted(a.rounds, key=lambda r: r.id)
                last_r = sorted_r[-1]
                r_type = last_r.round_type.value if hasattr(last_r.round_type, "value") else str(last_r.round_type)
                r_res = last_r.result.value if last_r.result and hasattr(last_r.result, "value") else "In Progress"
                round_info = f" | Current Round: {r_type} ({r_res})"
            app_lines.append(f"- {j_title} at {c_name}{ctc_val} -> Application Status: {a.status.value}{round_info}")
        applications_detailed_str = "\n".join(app_lines) if app_lines else "No job applications submitted yet."

        active_jobs_lines = []
        for j in active_jobs[:10]:
            c_name = j.company.name if j.company else "Campus Drive"
            ctc_str = f"₹{float(j.ctc_lpa):.1f} LPA" if j.ctc_lpa else "Disclosed during drive"
            cgpa_req = f"Min CGPA: {float(j.min_cgpa):.1f}" if j.min_cgpa else "No min CGPA"
            is_cgpa_ok = (student.cgpa is not None and float(student.cgpa) >= float(j.min_cgpa)) if j.min_cgpa else True
            dept_ok = True
            if j.eligible_departments:
                dept_ids = {ed.department_id for ed in j.eligible_departments}
                dept_ok = (student.department_id in dept_ids) if student.department_id else False
            elig_str = "Eligible" if (is_cgpa_ok and dept_ok) else "Check criteria"
            active_jobs_lines.append(f"- {j.title} at {c_name} (Package: {ctc_str}, {cgpa_req}, Eligibility: {elig_str})")
        active_jobs_detailed_str = "\n".join(active_jobs_lines) if active_jobs_lines else "No active campus placement drives currently open."

        active_roles = list(dict.fromkeys(job.title for job in active_jobs))[:5]
        active_roles_str = (
            ", ".join(active_roles) if active_roles else "General technical & engineering roles"
        )

        applied_count = len(applications)
        active_apps_count = len([a for a in applications if a.status.value not in ("Rejected", "Withdrawn")])

        context_summary = MentorContextSummary(
            department=dept_name,
            graduation_year=grad_year,
            cgpa_available=has_cgpa,
            skills_count=len(active_student_skills),
            top_skills=top_skill_names,
            active_campus_jobs_count=len(active_jobs),
            applied_jobs_count=applied_count,
            active_applications_count=active_apps_count,
            is_placed=is_placed,
            resumes_count=len(resumes),
        )

        # Session & conversation history management
        session = None
        history_payload: List[Dict[str, str]] = []

        if request.session_id is not None:
            session = await self.repository.get_mentor_session_by_id(student.id, request.session_id)
            if session and session.messages:
                for msg in session.messages[-8:]:
                    history_payload.append({"role": msg.role, "content": msg.content})
        elif request.history:
            for msg in request.history[-6:]:
                history_payload.append({"role": msg.role, "content": msg.content})
            session = await self.repository.get_or_create_mentor_session(
                student.id, initial_title=request.message[:45]
            )
        else:
            session = await self.repository.get_or_create_mentor_session(
                student.id, initial_title=request.message[:45]
            )
            if session and session.messages:
                for msg in session.messages[-8:]:
                    history_payload.append({"role": msg.role, "content": msg.content})

        system_instruction = (
            "You are Career Compass AI Mentor, an expert campus placement coach and technical career mentor. "
            "Your goal is to help undergraduate and postgraduate students prepare for campus placements, technical interviews, and software careers.\n\n"
            "STUDENT PROFILE CONTEXT (Verified platform data for the logged-in student):\n"
            f"- Academic Department: {dept_name or 'Not specified'}\n"
            f"- Target Graduation Year: {grad_year or 'Not specified'}\n"
            f"- Academic CGPA Standing: {cgpa_str}\n"
            f"- Placement Status: {'Offer Accepted / Placed 🎉' if is_placed else 'Seeking Campus Placement'}\n"
            f"- Uploaded Resumes Count: {len(resumes)}\n"
            f"- Student's Registered Skills & Proficiencies:\n{skills_detailed_str}\n"
            f"- Student's Job Applications (Total Applied: {applied_count}, Active: {active_apps_count}):\n{applications_detailed_str}\n"
            f"- Current Active Campus Placement Drives ({len(active_jobs)} total):\n{active_jobs_detailed_str}\n\n"
            "CAREER COMPASS AI PLATFORM FEATURES (Guide students to these tabs/routes if they ask about app actions):\n"
            "- 'Skills Profile' (/student/skills): Add/update technical skills and proficiency tiers.\n"
            "- 'Campus Jobs' (/student/jobs): View active campus drives, check match percentage, and submit applications.\n"
            "- 'My Applications' (/student/applications): Track application status, recruitment round progression, and interview outcomes.\n"
            "- 'Placement Readiness' (/student/readiness): View composite readiness score, skill gap breakdown, and personalized improvement plans.\n"
            "- 'Resume Manager' (/student/resumes): Upload and manage multiple PDF/DOCX resumes.\n\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Ground your advice in the student's actual department and registered skills when answering role-specific questions.\n"
            "2. When the student asks about their profile, skills, applied jobs, application count/status, or available campus jobs, answer accurately and directly using their verified profile data provided above.\n"
            "3. Clearly distinguish between what the student currently possesses in their profile versus your recommendations or suggested next steps.\n"
            "4. If recommending skill development, suggest concrete, realistic projects with modern tech stacks and technical interview topics.\n"
            "5. For interview preparation questions, structure advice into practical phases: Core Data Structures/Algorithms, System/Architecture Concepts, and Behavioral/HR communication.\n"
            "6. If student profile context is sparse (e.g. no skills registered), answer general placement questions cleanly without pretending to know their profile.\n"
            "7. Keep responses well-formatted with markdown headings, concise bullet points, and actionable next steps.\n"
            "8. Never claim or guarantee placement offers or invent fictitious institution policies."
        )

        ai_response_text = await self.gemini_provider.generate_response(
            system_instruction=system_instruction,
            user_prompt=request.message,
            history=history_payload,
        )

        model_used = getattr(self.gemini_provider, "last_used_model", self.gemini_provider.model)

        if session is not None:
            await self.repository.add_mentor_messages(
                session=session,
                user_text=request.message,
                model_text=ai_response_text,
                model_used=model_used,
            )

        return MentorChatResponse(
            response=ai_response_text,
            grounded_context=context_summary,
            model_used=model_used,
            session_id=session.id if session else None,
        )

    async def list_mentor_sessions(self, user_id: int) -> List[MentorSessionSummaryResponse]:
        student = await self.repository.get_student_by_user_id(user_id)
        sessions = await self.repository.get_student_mentor_sessions(student.id)
        res: List[MentorSessionSummaryResponse] = []
        for s in sessions:
            last_msg = s.messages[-1].content if s.messages else None
            preview = (last_msg[:60] + "...") if last_msg and len(last_msg) > 60 else last_msg
            res.append(
                MentorSessionSummaryResponse(
                    id=s.id,
                    title=s.title,
                    message_count=len(s.messages),
                    last_message_preview=preview,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )
        return res

    async def create_new_mentor_session(
        self, user_id: int, title: str = "New Conversation"
    ) -> MentorSessionDetailResponse:
        student = await self.repository.get_student_by_user_id(user_id)
        session = await self.repository.create_mentor_session(student.id, title=title)
        return MentorSessionDetailResponse(
            id=session.id,
            title=session.title,
            messages=[],
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def get_mentor_session_detail(
        self, user_id: int, session_id: int
    ) -> MentorSessionDetailResponse:
        student = await self.repository.get_student_by_user_id(user_id)
        session = await self.repository.get_mentor_session_by_id(student.id, session_id)
        if not session:
            raise NotFoundError("Chat session not found.")
        msg_responses = [
            MentorMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                model_used=m.model_used,
                created_at=m.created_at,
            )
            for m in session.messages
        ]
        return MentorSessionDetailResponse(
            id=session.id,
            title=session.title,
            messages=msg_responses,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def delete_mentor_session(self, user_id: int, session_id: int) -> dict:
        student = await self.repository.get_student_by_user_id(user_id)
        deleted = await self.repository.delete_mentor_session(student.id, session_id)
        if not deleted:
            raise NotFoundError("Chat session not found.")
        return {"success": True, "deleted_id": session_id}


    def _plan_to_response(self, plan: ImprovementPlan, job: Job) -> ImprovementPlanResponse:
        total = len(plan.actions)
        completed = sum(1 for a in plan.actions if a.status == "COMPLETED")
        progress = round((completed / total) * 100.0, 1) if total > 0 else 0.0

        action_responses = [
            ImprovementPlanActionResponse(
                id=a.id,
                plan_id=a.plan_id,
                skill_id=a.skill_id,
                skill_name=a.skill_name,
                current_proficiency=a.current_proficiency,
                target_proficiency=a.target_proficiency,
                priority=a.priority,
                status=a.status,
                reason=a.reason,
                suggested_activity=a.suggested_activity,
                completion_criteria=a.completion_criteria,
                evidence_source=a.evidence_source,
                evidence_reference=a.evidence_reference,
                completed_at=a.completed_at,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in plan.actions
        ]

        return ImprovementPlanResponse(
            id=plan.id,
            student_id=plan.student_id,
            job_id=plan.job_id,
            job_title=job.title,
            company_name=job.company.name if job.company else "",
            total_actions=total,
            completed_actions=completed,
            progress_percentage=progress,
            actions=action_responses,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    async def assess_job_readiness(
        self, user_id: int, job_id: int
    ) -> JobReadinessAssessmentResponse:
        """
        Explainable, deterministic job readiness assessment.
        Evaluates actual academic criteria, required skills vs student evidence,
        document preparation, and past interview/assessment signals.
        """
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        job = await self.repository.get_active_visible_job_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found or is not currently active.")

        student_skills = await self.repository.get_student_skills(student.id)
        student_skill_map = {
            ss.skill_id: ss for ss in student_skills if ss.skill and ss.skill.is_active
        }

        resumes = await self.repository.get_student_resumes(student.id)
        has_default_resume = any(r.is_default for r in resumes)

        # 1. Academic Eligibility Check (30 pts max)
        cgpa_ok = job.min_cgpa is None or (student.cgpa is not None and student.cgpa >= job.min_cgpa)
        eligible_dept_ids = [ed.department_id for ed in job.eligible_departments]
        eligible_dept_names = [
            ed.department.name for ed in job.eligible_departments if ed.department
        ]
        dept_ok = len(eligible_dept_ids) == 0 or (
            student.department_id is not None and student.department_id in eligible_dept_ids
        )
        is_eligible = cgpa_ok and dept_ok

        eligibility_reasons: List[str] = []
        if not cgpa_ok:
            if student.cgpa is None:
                eligibility_reasons.append(
                    f"CGPA is unrecorded in profile (job requires minimum {float(job.min_cgpa):.2f})."
                )
            else:
                eligibility_reasons.append(
                    f"CGPA ({float(student.cgpa):.2f}) is below employer cutoff ({float(job.min_cgpa):.2f})."
                )
        if not dept_ok:
            if student.department_id is None:
                eligibility_reasons.append("Academic department is not assigned in profile.")
            else:
                dept_name = student.department.name if student.department else "Your Department"
                eligibility_reasons.append(
                    f"Department ({dept_name}) is not among the eligible departments specified for this role."
                )
        if is_eligible:
            eligibility_reasons.append(
                "All academic criteria met: CGPA cutoff and eligible department criteria satisfied."
            )

        academic_score = (15.0 if cgpa_ok else 0.0) + (15.0 if dept_ok else 0.0)

        # 2. Skill Competency & Evidence Check (50 pts max)
        req_skills = [jrs for jrs in job.required_skills if jrs.skill and jrs.skill.is_active]
        total_req = len(req_skills)

        # Retrieve actual assessment and technical interview round signals
        assessed_skills_map = await self.repository.get_student_assessed_skills(student.id)
        existing_plan = await self.repository.get_improvement_plan(student.id, job.id)
        completed_actions = (
            {a.skill_id: a for a in existing_plan.actions if a.status == "COMPLETED" and a.skill_id}
            if existing_plan
            else {}
        )

        skills_breakdown: List[SkillEvidenceItem] = []
        demonstrated_count = 0
        partial_count = 0
        missing_evidence_count = 0

        for jrs in req_skills:
            req_prof = jrs.min_proficiency or ProficiencyLevel.BEGINNER
            req_num = prof_to_num(req_prof)
            req_str = prof_to_str(req_prof).capitalize()
            sk_name = jrs.skill.name
            sk_id = jrs.skill_id

            has_profile = sk_id in student_skill_map
            has_assessment = sk_id in assessed_skills_map
            action_completed = completed_actions.get(sk_id)

            stu_ss = student_skill_map.get(sk_id)
            stu_num = prof_to_num(stu_ss.proficiency) if stu_ss else 0
            stu_str = prof_to_str(stu_ss.proficiency).capitalize() if stu_ss else None

            # Case 1: Verified via formal recruitment assessment or technical round
            if has_assessment:
                ass_info = assessed_skills_map[sk_id]
                ass_prof = ass_info.get("min_proficiency") or ProficiencyLevel.BEGINNER
                ass_num = prof_to_num(ass_prof)
                # Supported proficiency is verified by the passed assessment
                effective_num = max(stu_num, ass_num)
                effective_str = stu_str if (stu_str and stu_num >= ass_num) else prof_to_str(ass_prof).capitalize()

                if effective_num >= req_num:
                    demonstrated_count += 1
                    status = "DEMONSTRATED"
                else:
                    partial_count += 1
                    status = "PARTIAL_EVIDENCE"

                evidence_summary = (
                    f"Assessed & Verified: Passed {ass_info['round_type']} ({ass_info['result']}) for "
                    f"{ass_info['job_title']} at {ass_info['company_name']}."
                )
                evidence_ref = f"{ass_info['round_type']} ({ass_info['result']}) - {ass_info['company_name']}"

                skills_breakdown.append(
                    SkillEvidenceItem(
                        skill_id=sk_id,
                        skill_name=sk_name,
                        required_proficiency=req_str,
                        student_proficiency=effective_str,
                        status=status,
                        is_verified=True,
                        evidence_source="ASSESSMENT_VERIFIED",
                        evidence_reference=evidence_ref,
                        practice_completed=bool(action_completed),
                        evidence_summary=evidence_summary,
                    )
                )

            # Case 2: Self-reported on student profile (no passed recruitment assessment yet)
            elif has_profile:
                if stu_num >= req_num:
                    demonstrated_count += 1
                    status = "DEMONSTRATED"
                    status_desc = f"Meets required cutoff at {stu_str} level (self-reported)"
                else:
                    partial_count += 1
                    status = "PARTIAL_EVIDENCE"
                    status_desc = f"Partially supported: profile has {stu_str}; target requirement is {req_str}"

                if action_completed:
                    act_ref = action_completed.evidence_reference or "Practice activity completed"
                    evidence_summary = (
                        f"{status_desc}. Formative practice completed ({act_ref}); "
                        f"formal technical assessment verification pending."
                    )
                    evidence_src = "PRACTICE_COMPLETED"
                    evidence_ref = act_ref
                else:
                    evidence_summary = (
                        f"{status_desc}. Self-reported on profile; no formal recruitment assessment on record."
                    )
                    evidence_src = "SELF_REPORTED"
                    evidence_ref = "Student profile inventory"

                skills_breakdown.append(
                    SkillEvidenceItem(
                        skill_id=sk_id,
                        skill_name=sk_name,
                        required_proficiency=req_str,
                        student_proficiency=stu_str,
                        status=status,
                        is_verified=False,
                        evidence_source=evidence_src,
                        evidence_reference=evidence_ref,
                        practice_completed=bool(action_completed),
                        evidence_summary=evidence_summary,
                    )
                )

            # Case 3: Missing from profile
            else:
                missing_evidence_count += 1
                if action_completed:
                    act_ref = action_completed.evidence_reference or "Practice activity completed"
                    evidence_summary = (
                        f"Practice task completed ({act_ref}), but {sk_name} is not recorded in "
                        f"your profile skills inventory or verified by formal assessment."
                    )
                    evidence_src = "PRACTICE_COMPLETED"
                    evidence_ref = act_ref
                else:
                    evidence_summary = (
                        f"Unverified on platform: {sk_name} is not recorded in your profile skills inventory."
                    )
                    evidence_src = "NONE"
                    evidence_ref = None

                skills_breakdown.append(
                    SkillEvidenceItem(
                        skill_id=sk_id,
                        skill_name=sk_name,
                        required_proficiency=req_str,
                        student_proficiency=None,
                        status="UNVERIFIED_OR_MISSING",
                        is_verified=False,
                        evidence_source=evidence_src,
                        evidence_reference=evidence_ref,
                        practice_completed=bool(action_completed),
                        evidence_summary=evidence_summary,
                    )
                )


        if total_req == 0:
            skill_score = 50.0
        else:
            skill_score = round(
                ((demonstrated_count * 1.0 + partial_count * 0.5) / total_req) * 50.0, 1
            )

        # 3. Preparation & Document Readiness (20 pts max)
        resume_score = 10.0 if has_default_resume else 0.0
        profile_completeness_pts = (
            10.0
            if (student.cgpa is not None and student.department_id is not None and len(student_skills) >= 3)
            else 5.0
        )
        prep_score = resume_score + profile_completeness_pts

        # 4. Total Deterministic Score
        raw_score = academic_score + skill_score + prep_score
        final_readiness_score = round(max(0.0, min(100.0, raw_score)), 1)

        if final_readiness_score >= 80.0:
            tier = "High Match"
        elif final_readiness_score >= 60.0:
            tier = "Moderate Match"
        elif final_readiness_score >= 40.0:
            tier = "Developing"
        else:
            tier = "Action Required"

        # 5. Historical Round Signals
        past_rounds = await self.repository.get_student_past_round_signals(student.id)
        signals: List[HistoricalRoundSignal] = []
        for r in past_rounds[:4]:
            res_str = r.result.value if hasattr(r.result, "value") else str(r.result)
            sig_type = "POSITIVE" if res_str == "Passed" else ("ATTENTION_NEEDED" if res_str == "Failed" else "NEUTRAL")
            r_type = r.round_type.value if hasattr(r.round_type, "value") else str(r.round_type)
            signals.append(
                HistoricalRoundSignal(
                    round_type=r_type,
                    result=res_str,
                    notes=r.notes,
                    signal_type=sig_type,
                )
            )

        explanation = (
            f"Readiness score of {final_readiness_score}/100.0 based on 3 deterministic pillars: "
            f"Academic Eligibility ({academic_score:.1f}/30.0 pts), "
            f"Skill Evidence Match ({skill_score:.1f}/50.0 pts), and "
            f"Platform Document Preparation ({prep_score:.1f}/20.0 pts)."
        )

        limitations = (
            "This assessment represents a deterministic matching indicator derived strictly from recorded platform "
            "evidence and employer criteria. It reflects profile alignment and does not constitute a guarantee of selection."
        )

        return JobReadinessAssessmentResponse(
            job_id=job.id,
            job_title=job.title,
            company_name=job.company.name if job.company else "",
            ctc_lpa=float(job.ctc_lpa) if job.ctc_lpa else None,
            readiness_score=final_readiness_score,
            readiness_tier=tier,
            is_eligible=is_eligible,
            cgpa_eligible=cgpa_ok,
            student_cgpa=float(student.cgpa) if student.cgpa is not None else None,
            min_cgpa=float(job.min_cgpa) if job.min_cgpa is not None else None,
            department_eligible=dept_ok,
            student_department=student.department.name if student.department else None,
            eligible_departments=eligible_dept_names,
            eligibility_reasons=eligibility_reasons,
            total_required_skills=total_req,
            demonstrated_count=demonstrated_count,
            partial_count=partial_count,
            missing_evidence_count=missing_evidence_count,
            skills_breakdown=skills_breakdown,
            historical_signals=signals,
            score_breakdown={
                "academic_points": academic_score,
                "skill_points": skill_score,
                "preparation_points": prep_score,
            },
            scoring_explanation=explanation,
            limitations_notice=limitations,
        )

    async def get_or_create_improvement_plan(
        self, user_id: int, job_id: int
    ) -> ImprovementPlanResponse:
        """
        Generate or refresh an explainable Personalized Improvement Plan for a specific job.
        Prioritizes missing mandatory skills and insufficient proficiencies into structured actions.
        """
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        job = await self.repository.get_active_visible_job_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found or is not currently active.")

        assessment = await self.assess_job_readiness(user_id, job_id)
        company_name = job.company.name if job.company else "the recruiting company"

        actions_data: List[dict] = []

        # 1. Address Missing or Unverified Skills (HIGH priority)
        for sk in assessment.skills_breakdown:
            if sk.status == "UNVERIFIED_OR_MISSING":
                activity = get_suggested_activity_for_skill(sk.skill_name, sk.required_proficiency)
                actions_data.append(
                    {
                        "skill_id": sk.skill_id,
                        "skill_name": sk.skill_name,
                        "current_proficiency": None,
                        "target_proficiency": sk.required_proficiency,
                        "priority": "HIGH" if assessment.is_eligible else "MEDIUM",
                        "status": "PENDING",
                        "reason": f"Required prerequisite for {job.title} at {company_name}. Currently unverified in your profile.",
                        "suggested_activity": activity,
                        "completion_criteria": f"Demonstrate practical proficiency in {sk.skill_name} at {sk.required_proficiency} tier and add it to your student profile skills inventory.",
                    }
                )

        # 2. Address Partially Supported Skills (MEDIUM priority)
        for sk in assessment.skills_breakdown:
            if sk.status == "PARTIAL_EVIDENCE":
                activity = get_suggested_activity_for_skill(sk.skill_name, sk.required_proficiency)
                actions_data.append(
                    {
                        "skill_id": sk.skill_id,
                        "skill_name": sk.skill_name,
                        "current_proficiency": sk.student_proficiency,
                        "target_proficiency": sk.required_proficiency,
                        "priority": "MEDIUM",
                        "status": "PENDING",
                        "reason": f"You have recorded {sk.student_proficiency} in {sk.skill_name}, but {job.title} specifically requires {sk.required_proficiency} proficiency.",
                        "suggested_activity": activity,
                        "completion_criteria": f"Upgrade recorded proficiency in {sk.skill_name} from {sk.student_proficiency} to {sk.required_proficiency} with demonstrated project milestones.",
                    }
                )

        # 3. Document Preparation Action if default resume missing
        resumes = await self.repository.get_student_resumes(student.id)
        if not any(r.is_default for r in resumes):
            actions_data.append(
                {
                    "skill_id": None,
                    "skill_name": "Default Resume Document",
                    "current_proficiency": None,
                    "target_proficiency": "Active",
                    "priority": "HIGH",
                    "status": "PENDING",
                    "reason": f"Applying for {job.title} requires a designated default resume document for recruiter review.",
                    "suggested_activity": "Upload a polished, ATS-compliant PDF resume in Resume Management and mark it as default.",
                    "completion_criteria": "Active default resume document designated in platform.",
                }
            )

        # If zero gaps exist (100% match)
        if not actions_data:
            actions_data.append(
                {
                    "skill_id": None,
                    "skill_name": "Technical Interview Practice",
                    "current_proficiency": "Advanced",
                    "target_proficiency": "Interview Ready",
                    "priority": "LOW",
                    "status": "PENDING",
                    "reason": f"You already meet all stated skill requirements for {job.title}! Maintain competitive edge with mock interview practice.",
                    "suggested_activity": f"Conduct timed system design and algorithmic problem solving targeted for {company_name} technical rounds.",
                    "completion_criteria": "Review core architectural patterns and complete 3 mock interview questions.",
                }
            )

        plan = await self.repository.create_or_update_improvement_plan(
            student.id, job.id, actions_data
        )
        return self._plan_to_response(plan, job)

    async def get_improvement_plan(
        self, user_id: int, job_id: int
    ) -> Optional[ImprovementPlanResponse]:
        """Fetch existing improvement plan for student and job if one has been generated."""
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        job = await self.repository.get_active_visible_job_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found or is not currently active.")

        plan = await self.repository.get_improvement_plan(student.id, job.id)
        if not plan:
            return None
        return self._plan_to_response(plan, job)

    async def update_plan_action_status(
        self,
        user_id: int,
        action_id: int,
        new_status: str,
        evidence_source: Optional[str] = None,
        evidence_reference: Optional[str] = None,
    ) -> ImprovementPlanActionResponse:
        """Update an action's progress status (PENDING -> IN_PROGRESS -> COMPLETED) with ownership validation."""
        student = await self.repository.get_student_by_user_id(user_id)
        if not student:
            raise NotFoundError("Student profile not found.")

        action = await self.repository.get_action_by_id_and_student(action_id, student.id)
        if not action:
            raise NotFoundError("Improvement plan action not found or access denied.")

        updated_action = await self.repository.update_action_status(
            action, new_status, evidence_source=evidence_source, evidence_reference=evidence_reference
        )
        return ImprovementPlanActionResponse(
            id=updated_action.id,
            plan_id=updated_action.plan_id,
            skill_id=updated_action.skill_id,
            skill_name=updated_action.skill_name,
            current_proficiency=updated_action.current_proficiency,
            target_proficiency=updated_action.target_proficiency,
            priority=updated_action.priority,
            status=updated_action.status,
            reason=updated_action.reason,
            suggested_activity=updated_action.suggested_activity,
            completion_criteria=updated_action.completion_criteria,
            evidence_source=updated_action.evidence_source,
            evidence_reference=updated_action.evidence_reference,
            completed_at=updated_action.completed_at,
            created_at=updated_action.created_at,
            updated_at=updated_action.updated_at,
        )

    async def ask_job_mentor_advice(
        self, user_id: int, job_id: int, request: JobMentorAdviceRequest
    ) -> JobMentorAdviceResponse:
        """
        Connects AI Career Mentor directly to the student's job readiness assessment and improvement plan.
        Provides resilient fallback if provider encounters quota or connectivity issues.
        """
        assessment = await self.assess_job_readiness(user_id, job_id)
        plan = await self.get_or_create_improvement_plan(user_id, job_id)

        job_title = assessment.job_title
        company = assessment.company_name
        score = assessment.readiness_score

        demonstrated = [sk.skill_name for sk in assessment.skills_breakdown if sk.status == "DEMONSTRATED"]
        partial = [
            f"{sk.skill_name} ({sk.student_proficiency} -> {sk.required_proficiency})"
            for sk in assessment.skills_breakdown
            if sk.status == "PARTIAL_EVIDENCE"
        ]
        missing = [sk.skill_name for sk in assessment.skills_breakdown if sk.status == "UNVERIFIED_OR_MISSING"]
        actions = [f"- [{act.priority}] {act.skill_name}: {act.suggested_activity}" for act in plan.actions[:3]]

        system_instruction = (
            "You are Career Compass AI Mentor, a campus placement coach specializing in company-specific technical preparation. "
            "Help the student understand their job-specific readiness assessment and execute their personalized improvement plan.\n\n"
            f"TARGET JOB: {job_title} at {company}\n"
            f"READINESS SCORE: {score}/100 ({assessment.readiness_tier})\n"
            f"ELIGIBILITY STATUS: {'Eligible' if assessment.is_eligible else 'Ineligible'}\n"
            f"DEMONSTRATED SKILLS: {', '.join(demonstrated) or 'None recorded'}\n"
            f"PARTIALLY SUPPORTED: {', '.join(partial) or 'None'}\n"
            f"UNVERIFIED / GAPS: {', '.join(missing) or 'None'}\n"
            f"TOP PLANNED ACTIONS:\n{chr(10).join(actions)}\n\n"
            "INSTRUCTIONS:\n"
            "1. Give direct, actionable technical advice on how to execute the top planned actions before campus recruitment drives.\n"
            "2. Explain how to discuss partially supported skills with technical interviewers (e.g., highlighting growth velocity and foundational knowledge).\n"
            "3. Format cleanly with clear bullet points, practical interview tips, and motivating tone.\n"
            "4. Do not invent salary guarantees or unverified facts."
        )

        user_prompt = (
            request.question
            if request.question and request.question.strip()
            else f"How should I prioritize my preparation and execute my improvement plan for {job_title} at {company}?"
        )

        try:
            advice = await self.gemini_provider.generate_response(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
            )
            model_used = self.gemini_provider.model
        except Exception:
            # Deterministic, helpful fallback so student experience NEVER crashes if Gemini is rate limited
            model_used = "Deterministic Guidance Engine (Fallback)"
            advice = (
                f"### Strategic Preparation for {job_title} at {company}\n\n"
                f"**Current Match Tier:** {assessment.readiness_tier} ({score}/100.0)\n\n"
                "**1. High-Priority Action Items:**\n"
                + "\n".join(f"- **{act.skill_name}**: {act.suggested_activity}" for act in plan.actions if act.priority == "HIGH")
                + "\n\n**2. Interview Strategy:**\n"
                "- Review core data structures and ensure you can explain your demonstrated skills with metrics.\n"
                "- Be prepared to discuss ongoing projects bridging your unverified skills during technical rounds."
            )

        return JobMentorAdviceResponse(
            advice=advice,
            grounded_job_title=job_title,
            grounded_company=company,
            readiness_score=score,
            model_used=model_used,
        )


PRACTICE_TEMPLATES = {
    "python": "Build a modular async backend service using FastAPI/PostgreSQL with JWT authentication and comprehensive pytest unit tests.",
    "sql": "Design a relational schema with normalization, write complex joins, aggregated window functions, and optimize query execution plans.",
    "react": "Develop a responsive single-page web application featuring TypeScript, centralized state management, and real-time UI updates.",
    "fastapi": "Implement asynchronous REST endpoints with Pydantic request validation, dependency injection, and Dockerized deployment.",
    "docker": "Containerize a multi-tier web application using Docker and Docker Compose, configuring network bridges and persistent volumes.",
    "git": "Practice team Git workflows: branch protection, feature branching, resolving merge conflicts, and interactive rebase.",
    "java": "Build an object-oriented backend service using Spring Boot, JPA/Hibernate, and implement unit tests with JUnit and Mockito.",
    "c++": "Solve 20+ algorithmic challenges focusing on memory management, STL containers, dynamic programming, and time/space complexity.",
    "aws": "Deploy a containerized application to AWS ECS/Fargate, configuring IAM roles, S3 storage buckets, and CloudWatch metrics.",
    "machine learning": "Train and evaluate a supervised model on a real dataset using scikit-learn, implementing feature engineering and cross-validation.",
}


def get_suggested_activity_for_skill(skill_name: str, target_proficiency: str) -> str:
    key = skill_name.lower().strip()
    for t_key, t_act in PRACTICE_TEMPLATES.items():
        if t_key in key:
            return t_act
    return (
        f"Complete a portfolio-grade project implementing core {skill_name} capabilities "
        f"at {target_proficiency} level, focusing on robust error handling, tests, and documentation."
    )
