"""Score blending: evidence fit x structural fit x availability.

Final score = clamp(fit) * availability_multiplier, where fit combines:
  - core evidence (retrieval, ranking, evaluation — the JD's three must-haves)
  - supporting evidence (LLM, NLP/IR, production, LTR, external validation)
  - experience-band fit (trapezoid over the JD's 5-9y band, peak 6-8)
  - product-company exposure
  - explicit JD penalties (research-only, services-only, CV-primary,
    shallow-LLM, hopper, non-coding, stuffing)
"""


def experience_band(yoe: float) -> float:
    """Trapezoid: 0 below 3y, ramps 3-5, plateau 5-9 (peak 6-8), soft decay after."""
    if yoe < 3.0:
        return max(0.0, (yoe - 1.5) / 1.5 * 0.4)
    if yoe < 5.0:
        return 0.4 + 0.5 * (yoe - 3.0) / 2.0
    if yoe <= 9.0:
        return 1.0 if 6.0 <= yoe <= 8.0 else 0.93
    return max(0.45, 0.93 - 0.07 * (yoe - 9.0))


def fit_score(f: dict) -> tuple[float, list[str]]:
    """Return (fit, penalty_notes). fit is unnormalised; caller rescales."""
    c = f["concepts"]
    notes = []

    core = (
        c.get("retrieval", 0.0) * 1.0
        + c.get("ranking", 0.0) * 1.0
        + c.get("evaluation", 0.0) * 0.8
    )
    support = (
        c.get("llm", 0.0) * 0.5
        + c.get("nlp_ir", 0.0) * 0.4
        + c.get("production", 0.0) * 0.5
        + c.get("ltr_ml", 0.0) * 0.4
        + c.get("external", 0.0) * 0.3
        + c.get("domain", 0.0) * 0.3
    )

    # Both retrieval AND ranking evidence => the actual target profile;
    # reward the conjunction, not just the sum.
    if c.get("retrieval", 0) >= 1.0 and c.get("ranking", 0) >= 1.0:
        core *= 1.25

    fit = core + support

    # corroborated skill claims add confirmation, capped
    fit += min(f["corroborated"], 6) * 0.15

    # experience band multiplies (a 2y candidate with great text is still junior)
    fit *= 0.35 + 0.65 * experience_band(f["yoe"])

    # product-company exposure (JD: applied ML at product companies)
    if f["product_company_count"] == 0:
        fit *= 0.30
        notes.append("services/consulting-only career")
    elif f["product_company_count"] >= 2:
        fit *= 1.05

    if f["research_only"]:
        fit *= 0.15
        notes.append("research-only background, no production deployment")
    if f["cv_primary"]:
        fit *= 0.35
        notes.append("CV/speech-primary without NLP/IR depth")
    if f["shallow_llm"]:
        fit *= 0.55
        notes.append("LLM experience looks recent/framework-level")
    if f["hopper"]:
        fit *= 0.75
        notes.append("pattern of short stints")
    if f["non_coding"]:
        fit *= 0.60
        notes.append("recent roles look non-hands-on")
    if f["stuffing"]:
        fit *= 0.10
        notes.append(
            f"{f['ai_claims']} AI skills listed but career history shows none of them in use"
        )
    if not f["is_engineering"] and f["concepts"].get("retrieval", 0) + f["concepts"].get("ranking", 0) < 2.0:
        fit *= 0.15
        notes.append(f"current title '{f['title']}' is not an engineering role")

    # small grace signals
    if f["github"] >= 60:
        fit *= 1.04
    if f["edu_tier"] == "tier_1":
        fit *= 1.03

    return fit, notes


def final_score(f: dict, semantic_sim: float = 0.0) -> tuple[float, list[str]]:
    """Blend rubric fit with the semantic-similarity refinement (shortlist only).

    semantic_sim is the TF-IDF cosine between the candidate's career text and
    the JD, used as a tie-breaking refinement (15%), never as the driver —
    keyword similarity is exactly the signal the traps exploit.
    """
    fit, notes = fit_score(f)
    blended = fit * (1.0 + 0.15 * semantic_sim)
    return blended * f["availability"], notes
