"""Honeypot gate tests: impossible profiles flag, plausible ones don't."""

from ranker import gates


def _base_candidate():
    return {
        "candidate_id": "CAND_0000001",
        "profile": {"years_of_experience": 6.0},
        "career_history": [
            {
                "company": "Acme",
                "title": "ML Engineer",
                "start_date": "2020-06-01",
                "end_date": None,
                "duration_months": 72,
                "is_current": True,
            }
        ],
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 70},
        ],
    }


def test_clean_profile_passes():
    assert gates.honeypot_flags(_base_candidate()) == []


def test_duration_contradiction_flags():
    c = _base_candidate()
    # claims 8 years at a job whose own dates span ~2 years
    c["career_history"][0]["start_date"] = "2024-06-01"
    c["career_history"][0]["duration_months"] = 96
    flags = gates.honeypot_flags(c)
    assert any("duration_contradiction" in f for f in flags)


def test_yoe_beyond_dated_career_flags():
    c = _base_candidate()
    c["profile"]["years_of_experience"] = 14.0  # dated span is ~6 years
    flags = gates.honeypot_flags(c)
    assert any("yoe_exceeds_span" in f for f in flags)


def test_expert_skills_never_used_flags():
    c = _base_candidate()
    c["skills"] = [
        {"name": s, "proficiency": "expert", "duration_months": 0}
        for s in ("RAG", "Pinecone", "FAISS")
    ]
    flags = gates.honeypot_flags(c)
    assert any("expert_skills_never_used" in f for f in flags)


def test_small_generator_noise_does_not_flag():
    c = _base_candidate()
    # 6 months of date/duration disagreement is generator noise, not a trap
    c["career_history"][0]["duration_months"] = 66
    assert gates.honeypot_flags(c) == []
