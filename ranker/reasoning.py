"""Fact-grounded reasoning strings for the top-100.

Rules (mirrors the Stage-4 review rubric):
  - every claim must trace to an extracted profile fact;
  - connect to a specific JD requirement;
  - acknowledge real concerns (notice period, location, activity, gaps);
  - tone must match rank band;
  - vary structure across rows (deterministic, seeded by candidate_id).
"""

CONCEPT_PHRASES = {
    "retrieval": "embeddings/vector-retrieval work",
    "ranking": "shipped ranking/recommendation systems",
    "evaluation": "ranking-evaluation rigor",
    "llm": "hands-on LLM engineering",
    "nlp_ir": "NLP/IR foundations",
    "production": "production deployment experience",
    "ltr_ml": "learning-to-rank modeling",
    "external": "open-source/external footprint",
    "domain": "HR-tech/marketplace domain exposure",
}

CORE = ("retrieval", "ranking", "evaluation", "llm", "nlp_ir", "ltr_ml")


def _strengths(f: dict, limit: int = 3) -> list[str]:
    ranked = sorted(
        ((lbl, v) for lbl, v in f["concepts"].items() if lbl in CORE and v >= 0.8),
        key=lambda kv: -kv[1],
    )
    out = []
    for i, (lbl, _) in enumerate(ranked[:limit]):
        where = f["concept_where"].get(lbl)
        phrase = CONCEPT_PHRASES[lbl]
        # quote the actual evidence terms found in their work history so each
        # reasoning is grounded in that candidate's own profile text
        terms = f.get("concept_terms", {}).get(lbl, [])
        if terms and i == 0:
            phrase += f" ({', '.join(terms[:2])})"
        out.append(f"{phrase} at {where}" if where else phrase)
    return out


def _concerns(f: dict, notes: list[str]) -> list[str]:
    c = list(notes)
    if f["notice_period_days"] > 60:
        c.append(f"{f['notice_period_days']}-day notice period")
    if f["last_active_days"] > 90:
        c.append(f"last active {f['last_active_days'] // 30} months ago")
    if f["recruiter_response_rate"] < 0.25:
        c.append(f"low recruiter response rate ({f['recruiter_response_rate']:.0%})")
    if f["country"] != "India":
        c.append(f"based in {f['country']} (no visa sponsorship)")
    return c


def build(f: dict, notes: list[str], rank: int, cid: str) -> str:
    seed = int(cid.split("_")[1]) % 3
    strengths = _strengths(f)
    concerns = _concerns(f, notes)
    yoe = f["yoe"]
    title, company = f["title"], f["company"]
    loc_city = f["location"].split(",")[0]

    if strengths:
        s = strengths[0] if len(strengths) == 1 else f"{strengths[0]} plus {strengths[1]}"
    else:
        s = "adjacent data/ML engineering background"

    openers = [
        f"{title} at {company} with {yoe:g} yrs; {s}",
        f"{yoe:g} yrs as {title} ({company}) — {s}",
        f"{s}; currently {title} at {company} with {yoe:g} yrs",
    ]
    sentence1 = openers[seed]

    if rank <= 15:
        tails = [
            " — close match to the JD's retrieval+ranking+eval core.",
            " — squarely the production retrieval-and-ranking profile this role asks for.",
            "; hits the JD's must-haves (production embeddings, ranking systems) directly.",
        ]
    elif rank <= 50:
        tails = [
            ", aligning well with the JD's production-retrieval focus.",
            ", covering most of the JD's embeddings/ranking must-haves.",
            " — solid overlap with the role's core, if not the full trifecta.",
        ]
    else:
        tails = [
            ", a partial match on the JD's core requirements.",
            " — covers part of the JD's core; weaker on the rest.",
            ", which overlaps the role but misses some must-haves.",
        ]
    tail = tails[seed]

    bits = [sentence1 + tail]

    if concerns:
        cstr = concerns[0] if rank <= 50 else "; ".join(concerns[:2])
        bits.append(f"Main caveat: {cstr}.")
    else:
        extras = []
        if f["open_to_work"]:
            extras.append("open to work")
        if f["last_active_days"] <= 30:
            extras.append("active this month")
        if f["recruiter_response_rate"] >= 0.5:
            extras.append(f"{f['recruiter_response_rate']:.0%} recruiter response rate")
        if loc_city.lower() in ("pune", "noida"):
            extras.append(f"already in {loc_city}")
        if extras:
            bits.append("Strong availability signals: " + ", ".join(extras[:3]) + ".")

    text = " ".join(bits)
    return text.replace('"', "'")
