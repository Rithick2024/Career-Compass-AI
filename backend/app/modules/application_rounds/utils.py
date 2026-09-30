"""
Helper utilities for derived Application Round timing & state calculations.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.modules.application_rounds.models import (
    ApplicationRound,
    RoundResult,
    RoundStatus,
    ScheduleType,
    StaffVerification,
    StudentAttendance,
)


def get_now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_round_derived_state(round_obj: ApplicationRound, now: datetime | None = None) -> str:
    """
    Calculate derived UI / timing state for an ApplicationRound.
    """
    if now is None:
        now = get_now_utc()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # 1. CANCELLED
    if round_obj.status == RoundStatus.CANCELLED:
        return "CANCELLED"

    # 2. PASSED
    if round_obj.result == RoundResult.PASSED:
        return "PASSED"

    # 3. FAILED
    if round_obj.result == RoundResult.FAILED:
        return "FAILED"

    # 4. NOT_ATTENDED
    if round_obj.result == RoundResult.NOT_ATTENDED:
        return "NOT_ATTENDED"

    # 5. COMPLETED / RESULT PENDING
    if (
        round_obj.student_attendance == StudentAttendance.ATTENDED
        and round_obj.staff_verification == StaffVerification.VERIFIED
        and (round_obj.result is None or round_obj.result == RoundResult.PENDING)
    ):
        return "COMPLETED"

    # 6. AWAITING VERIFICATION
    if (
        round_obj.student_attendance in (StudentAttendance.ATTENDED, StudentAttendance.ABSENT)
        and round_obj.staff_verification == StaffVerification.PENDING
    ):
        return "AWAITING_VERIFICATION"

    # Timing calculations
    available_from = round_obj.available_from
    if available_from is None:
        return "UPCOMING"

    if available_from.tzinfo is None:
        available_from = available_from.replace(tzinfo=timezone.utc)

    duration_mins = round_obj.duration_minutes or 60

    if round_obj.schedule_type == ScheduleType.AVAILABILITY_WINDOW:
        available_until = round_obj.available_until
        if available_until is not None and available_until.tzinfo is None:
            available_until = available_until.replace(tzinfo=timezone.utc)

        # 7. UPCOMING
        if now < available_from:
            return "UPCOMING"

        # 8 & 9. Window open / closed -> AWAITING_ATTENDANCE
        return "AWAITING_ATTENDANCE"
    else:
        # FIXED_TIME
        session_end = available_from + timedelta(minutes=duration_mins)

        # 7. UPCOMING
        if now < available_from:
            return "UPCOMING"

        # 8. IN PROGRESS / DUE TODAY
        if available_from <= now <= session_end:
            return "IN_PROGRESS"

        # 9. AWAITING ATTENDANCE
        if now > session_end and round_obj.student_attendance == StudentAttendance.NOT_REPORTED:
            return "AWAITING_ATTENDANCE"

    return "UPCOMING"


def get_round_derived_metadata(round_obj: ApplicationRound, now: datetime | None = None) -> Dict[str, Any]:
    if now is None:
        now = get_now_utc()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    derived_state = get_round_derived_state(round_obj, now)

    available_from = round_obj.available_from
    if available_from is not None and available_from.tzinfo is None:
        available_from = available_from.replace(tzinfo=timezone.utc)

    available_until = round_obj.available_until
    if available_until is not None and available_until.tzinfo is None:
        available_until = available_until.replace(tzinfo=timezone.utc)

    duration_mins = round_obj.duration_minutes or 60
    session_end = (available_from + timedelta(minutes=duration_mins)) if (available_from and round_obj.schedule_type == ScheduleType.FIXED_TIME) else None

    is_cancelled = round_obj.status == RoundStatus.CANCELLED

    if round_obj.schedule_type == ScheduleType.AVAILABILITY_WINDOW:
        can_student_respond = (
            not is_cancelled
            and available_from is not None
            and available_until is not None
            and available_from <= now <= available_until
            and round_obj.student_attendance == StudentAttendance.NOT_REPORTED
            and round_obj.staff_verification == StaffVerification.PENDING
        )
        is_upcoming = (not is_cancelled) and (available_from is not None) and (now < available_from)
        is_due = (
            (not is_cancelled)
            and (available_from is not None)
            and (available_until is not None)
            and (available_from <= now <= available_until)
        )
        is_overdue = (
            (not is_cancelled)
            and (available_until is not None)
            and (now > available_until)
            and (round_obj.student_attendance == StudentAttendance.NOT_REPORTED)
        )
    else:
        can_student_respond = (
            not is_cancelled
            and available_from is not None
            and now >= available_from
            and round_obj.student_attendance == StudentAttendance.NOT_REPORTED
            and round_obj.staff_verification == StaffVerification.PENDING
        )
        is_upcoming = (not is_cancelled) and (available_from is not None) and (now < available_from)
        is_due = (
            (not is_cancelled)
            and (available_from is not None)
            and (session_end is not None)
            and (available_from <= now <= session_end)
        )
        is_overdue = (
            (not is_cancelled)
            and (session_end is not None)
            and (now > session_end)
            and (round_obj.student_attendance == StudentAttendance.NOT_REPORTED)
        )

    can_staff_verify = (
        not is_cancelled
        and round_obj.student_attendance in (StudentAttendance.ATTENDED, StudentAttendance.ABSENT)
        and round_obj.staff_verification == StaffVerification.PENDING
    )

    can_staff_set_result = (
        not is_cancelled
        and round_obj.staff_verification == StaffVerification.VERIFIED
    )

    return {
        "derived_state": derived_state,
        "session_end_at": session_end,
        "can_student_respond": can_student_respond,
        "can_staff_verify": can_staff_verify,
        "can_staff_set_result": can_staff_set_result,
        "is_upcoming": is_upcoming,
        "is_due": is_due,
        "is_overdue": is_overdue,
    }
