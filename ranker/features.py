"""Feature extraction: evidence-based fit + structured fit + availability.

Design principle (from the JD itself): the gap between what a profile *says*
and what the career history *shows* is the whole game. So:

  - Evidence comes from career_history descriptions and titles — text someone
    had to write about actual work — never from the self-reported skill list
    alone.
  - The skills list is used only two ways: (a) corroborated skills add a small
    confirmation bonus; (b) a large AI skill list with zero corroboration in
    the work history is treated as keyword stuffing and penalised.
  - Behavioral signals gate *availability*, not competence, so they enter as a
    multiplier rather than additive terms.
"""

import datetime as dt

from . import jd_profile

LEXICONS = jd_profile.compile_lexicons()

# Skill-list names that count as "AI claims" for the stuffing check
AI_SKILL_NAMES = {
    "rag", "pinecone", "weaviate", "qdrant", "milvus", "faiss", "embeddings",
    "vector search", "semantic search", "llm", "llms", "langchain",
    "fine-tuning llms", "sentence-transformers", "huggingface", "transformers",
    "bert", "gpt", "openai api", "lora", "qlora", "peft", "nlp", "mlops",
    "pytorch", "tensorflow", "deep learning", "machine learning",
}


def _job_weight(job: dict) -> float:
    """Recency- and context-weighted contribution of one career entry."""
    w = 1.0 if job["is_current"] else 0.75
    end = job["end_date"]
    if end:  # decay evidence that ended long ago
        years_ago = max(0.0, (dt.date(*jd_profile.TODAY) - dt.date.fromisoformat(end)).days / 365)
        w *= max(0.45, 1.0 - 0.09 * years_ago)
    # evidence earned at a product company is worth more than at services firms
    if _is_services(job.get("company", ""), job.get("industry", "")):
        w *= 0.55
    return w


def _is_services(company: str, industry: str) -> bool:
    return (
        company.strip().lower() in jd_profile.SERVICES_COMPANIES
        or industry.strip().lower() in jd_profile.SERVICES_INDUSTRIES
    )


def extract(cand: dict) -> dict:
    """Compute all scoring features for one candidate."""
    profile = cand["profile"]
    history = cand.get("career_history", [])
    signals = cand["redrob_signals"]

    # ---------------- evidence over career text ----------------
    concept_scores: dict[str, float] = {}
    concept_where: dict[str, str] = {}  # concept -> company where best shown
    concept_terms: dict[str, list] = {}  # concept -> actual matched phrases
    full_text_parts = [profile.get("headline", ""), profile.get("summary", "")]

    job_texts = []
    for job in history:
        text = f"{job['title']} {job['description']}"
        full_text_parts.append(text)
        job_texts.append((job, text, _job_weight(job)))
    career_text = " \n ".join(t for _, t, _ in job_texts)
    career_lower = career_text.lower()

    for label, (rx, weight) in LEXICONS.items():
        # fast fail: literal trigger pre-test, then authoritative regex;
        # scan per-job only when the concept appears in the career text at all
        triggers = jd_profile.TRIGGERS[label]
        if not any(t in career_lower for t in triggers):
            continue
        if not rx.search(career_text):
            continue
        for job, text, jw in job_texts:
            matched = set(m.group(0).lower() for m in rx.finditer(text))
            hits = len(matched)
            if hits:
                contrib = weight * jw * min(hits, 4) / 4 * (1 + 0.15 * min(hits, 4))
                if contrib > concept_scores.get(label, 0.0):
                    concept_where[label] = job["company"]
                    concept_terms[label] = sorted(matched, key=len, reverse=True)[:3]
                concept_scores[label] = concept_scores.get(label, 0.0) + contrib

    # summary/headline corroborate at half weight (self-description, but still prose)
    head = " ".join(full_text_parts[:2])
    for label, (rx, weight) in LEXICONS.items():
        hits = len(set(m.group(0).lower() for m in rx.finditer(head)))
        if hits:
            concept_scores[label] = concept_scores.get(label, 0.0) + 0.5 * weight * min(hits, 3) / 3

    full_text = " ".join(full_text_parts)

    # ---------------- skill-list corroboration ----------------
    skills = cand.get("skills", [])
    ai_claims = [s for s in skills if s["name"].lower() in AI_SKILL_NAMES]
    lower_text = full_text.lower()
    corroborated = sum(1 for s in ai_claims if s["name"].lower() in lower_text)
    core_evidence = (
        concept_scores.get("retrieval", 0)
        + concept_scores.get("ranking", 0)
        + concept_scores.get("nlp_ir", 0)
        + concept_scores.get("llm", 0)
    )
    # Stuffing: many AI claims, nothing in the actual work history backs them
    stuffing = len(ai_claims) >= 5 and corroborated <= 1 and core_evidence < 1.0

    # ---------------- structured career shape ----------------
    yoe = profile["years_of_experience"]
    title = profile["current_title"]

    is_engineering = bool(jd_profile.COMPILED_ENG.search(title))
    non_coding = bool(jd_profile.COMPILED_NONCODING.search(title))

    product_companies = [
        j for j in history if not _is_services(j["company"], j["industry"])
        and j.get("industry", "").lower() not in jd_profile.RESEARCH_INDUSTRY
    ]
    services_only = bool(history) and not product_companies

    research_jobs = [
        j for j in history
        if jd_profile.COMPILED_RESEARCH.search(j["title"])
        or j.get("industry", "").lower() in jd_profile.RESEARCH_INDUSTRY
    ]
    research_only = bool(history) and len(research_jobs) == len(history)

    # CV/speech-primary without IR exposure
    full_lower = lower_text
    cv_hits = (
        len(jd_profile.COMPILED_CV.findall(full_text))
        if any(t in full_lower for t in jd_profile.CV_TRIGGERS)
        else 0
    )
    ir_core = concept_scores.get("retrieval", 0) + concept_scores.get("ranking", 0)
    nlp_core = concept_scores.get("nlp_ir", 0)
    cv_primary = cv_hits >= 3 and ir_core < 1.0 and nlp_core < 1.0

    # Shallow-LLM recency: AI signal exists only as recent framework usage
    shallow_llm = (
        any(t in full_lower for t in jd_profile.SHALLOW_TRIGGERS)
        and bool(jd_profile.COMPILED_SHALLOW.search(full_text))
        and core_evidence < 1.2
        and concept_scores.get("production", 0) < 0.8
    )

    # Job hopping with title escalation (JD: title-chasers)
    short_stints = sum(
        1 for j in history if not j["is_current"] and j["duration_months"] < 20
    )
    hopper = len(history) >= 3 and short_stints >= max(2, len(history) - 1)

    # ---------------- availability multiplier ----------------
    today = dt.date(*jd_profile.TODAY)
    last_active_days = (today - dt.date.fromisoformat(signals["last_active_date"])).days
    activity = 1.0 if last_active_days <= 45 else max(0.70, 1.0 - 0.0022 * (last_active_days - 45))

    rrr = signals["recruiter_response_rate"]
    responsiveness = 0.78 + 0.22 * min(rrr / 0.55, 1.0)

    engagement = 1.0
    if signals["open_to_work_flag"]:
        engagement += 0.04
    if signals["applications_submitted_30d"] > 0 or signals["profile_views_received_30d"] > 10:
        engagement += 0.02
    icr = signals["interview_completion_rate"]
    if icr < 0.5:
        engagement -= 0.08
    elif icr >= 0.85:
        engagement += 0.02

    notice = signals["notice_period_days"]
    notice_mult = 1.0 if notice <= 30 else (0.96 if notice <= 60 else 0.90)

    loc = profile.get("location", "").lower()
    country = profile.get("country", "")
    if country != "India":
        location_mult = 0.72  # no visa sponsorship; case-by-case only
    elif any(c in loc for c in jd_profile.PREFERRED_CITIES):
        location_mult = 1.0
    elif any(c in loc for c in jd_profile.WELCOME_CITIES):
        location_mult = 0.97
    else:
        location_mult = 0.97 if signals["willing_to_relocate"] else 0.88

    availability = activity * responsiveness * engagement * notice_mult * location_mult

    return {
        "concepts": concept_scores,
        "concept_where": concept_where,
        "concept_terms": concept_terms,
        "full_text": full_text,
        "yoe": yoe,
        "title": title,
        "company": profile["current_company"],
        "location": profile.get("location", ""),
        "country": country,
        "is_engineering": is_engineering,
        "non_coding": non_coding,
        "services_only": services_only,
        "research_only": research_only,
        "cv_primary": cv_primary,
        "shallow_llm": shallow_llm,
        "hopper": hopper,
        "stuffing": stuffing,
        "ai_claims": len(ai_claims),
        "corroborated": corroborated,
        "product_company_count": len(product_companies),
        "availability": availability,
        "last_active_days": last_active_days,
        "recruiter_response_rate": rrr,
        "notice_period_days": notice,
        "open_to_work": signals["open_to_work_flag"],
        "github": signals["github_activity_score"],
        "edu_tier": min(
            (e.get("tier", "unknown") for e in cand.get("education", [])),
            default="unknown",
        ),
    }
