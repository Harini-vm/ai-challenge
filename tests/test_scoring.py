"""Scoring behavior tests: the JD's explicit rules must hold end-to-end."""

import copy

from ranker import features, scoring

SIGNALS = {
    "profile_completeness_score": 90,
    "signup_date": "2024-01-01",
    "last_active_date": "2026-05-20",
    "open_to_work_flag": True,
    "profile_views_received_30d": 40,
    "applications_submitted_30d": 3,
    "recruiter_response_rate": 0.7,
    "avg_response_time_hours": 5,
    "skill_assessment_scores": {},
    "connection_count": 300,
    "endorsements_received": 50,
    "notice_period_days": 30,
    "expected_salary_range_inr_lpa": {"min": 30, "max": 45},
    "preferred_work_mode": "hybrid",
    "willing_to_relocate": True,
    "github_activity_score": 70,
    "search_appearance_30d": 50,
    "saved_by_recruiters_30d": 5,
    "interview_completion_rate": 0.9,
    "verified_email": True,
    "verified_phone": True,
    "linkedin_connected": True,
    "offer_acceptance_rate": 0.5,
}


def make(title, company, industry, description, yoe=6.5, skills=(), location="Pune, Maharashtra"):
    return {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "T", "headline": "", "summary": "",
            "location": location, "country": "India",
            "years_of_experience": yoe, "current_title": title,
            "current_company": company, "current_company_size": "201-500",
            "current_industry": industry,
        },
        "career_history": [
            {
                "company": company, "title": title, "start_date": "2020-01-01",
                "end_date": None, "duration_months": 77, "is_current": True,
                "industry": industry, "company_size": "201-500",
                "description": description,
            }
        ],
        "education": [],
        "skills": [
            {"name": s, "proficiency": "advanced", "endorsements": 5, "duration_months": 24}
            for s in skills
        ],
        "redrob_signals": copy.deepcopy(SIGNALS),
    }


def score_of(cand):
    f = features.extract(cand)
    fit, _ = scoring.fit_score(f)
    return fit * f["availability"]


STRONG_TEXT = (
    "Built and shipped a semantic search and ranking system in production using "
    "sentence-transformers embeddings with FAISS retrieval and a re-ranking model. "
    "Owned NDCG/MRR offline evaluation and A/B testing for search relevance."
)


def test_evidence_beats_keyword_stuffing():
    """The JD's canonical trap: perfect skill list, wrong career."""
    real = make("ML Engineer", "ProductCo", "E-commerce", STRONG_TEXT)
    stuffer = make(
        "Marketing Manager", "AgencyCo", "Marketing",
        "Ran social media campaigns and managed brand partnerships.",
        skills=("RAG", "Pinecone", "FAISS", "Embeddings", "LLM", "LangChain"),
    )
    assert score_of(real) > 10 * score_of(stuffer)


def test_plain_language_builder_outranks_buzzword_lister():
    """Tier-5 candidates may never say RAG or Pinecone."""
    plain = make(
        "Software Engineer", "ShopCo", "E-commerce",
        "Built the product recommendation system for the storefront; trained "
        "ranking models on engagement data, ran A/B tests, deployed to production "
        "serving millions of users.",
    )
    lister = make(
        "Software Engineer", "GenericCo", "Software",
        "Worked on internal tools and bug fixes.",
        skills=("RAG", "Pinecone", "FAISS", "Embeddings", "LLM"),
    )
    assert score_of(plain) > 3 * score_of(lister)


def test_services_only_career_penalised():
    product = make("ML Engineer", "ProductCo", "E-commerce", STRONG_TEXT)
    services = make("ML Engineer", "Infosys", "IT Services", STRONG_TEXT)
    assert score_of(product) > 2 * score_of(services)


def test_experience_band():
    assert scoring.experience_band(7.0) == 1.0
    assert scoring.experience_band(2.0) < 0.2
    assert scoring.experience_band(15.0) < 0.6


def test_stale_candidate_downweighted():
    fresh = make("ML Engineer", "ProductCo", "E-commerce", STRONG_TEXT)
    stale = make("ML Engineer", "ProductCo", "E-commerce", STRONG_TEXT)
    stale["redrob_signals"]["last_active_date"] = "2025-10-01"
    stale["redrob_signals"]["recruiter_response_rate"] = 0.05
    stale["redrob_signals"]["open_to_work_flag"] = False
    assert score_of(fresh) > 1.25 * score_of(stale)
