"""Hard gates: honeypot detection and profile-integrity checks.

The dataset contains ~80 honeypots with subtly impossible profiles. We detect
them through internal-consistency checks rather than special-casing, exactly
as a careful human screener would: the numbers in the profile must agree with
each other.
"""

import datetime as dt

from . import jd_profile


def _months_between(start: str, end: str | None) -> int:
    a = dt.date.fromisoformat(start)
    b = dt.date.fromisoformat(end) if end else dt.date(*jd_profile.TODAY)
    return (b.year - a.year) * 12 + (b.month - a.month)


def honeypot_flags(cand: dict) -> list[str]:
    """Return a list of impossibility flags. Non-empty => exclude from ranking.

    Three checks, each calibrated on the pool so that legitimate generator
    noise (e.g. skill durations slightly beyond career span) does NOT trip:

    1. stated job duration contradicts its own start/end dates by > 12 months
       (catches "8 years at a company founded 3 years ago" style traps);
    2. claimed years_of_experience exceeds the entire dated career span by
       > 2.5 years;
    3. three or more "expert" proficiency skills with zero months of use.
    """
    flags = []
    history = cand.get("career_history", [])

    for job in history:
        dated = _months_between(job["start_date"], job["end_date"])
        if abs(dated - job["duration_months"]) > 12:
            flags.append(
                f"duration_contradiction:{job['company']}"
                f"({job['duration_months']}mo stated vs {dated}mo dated)"
            )
            break

    if history:
        span = _months_between(min(j["start_date"] for j in history), None)
        yoe = cand["profile"]["years_of_experience"]
        if yoe * 12 > span + 30:
            flags.append(f"yoe_exceeds_span({yoe}y claimed vs {span / 12:.1f}y dated)")

    expert_zero = sum(
        1
        for s in cand.get("skills", [])
        if s.get("proficiency") == "expert" and s.get("duration_months", 1) == 0
    )
    if expert_zero >= 3:
        flags.append(f"expert_skills_never_used({expert_zero})")

    return flags
