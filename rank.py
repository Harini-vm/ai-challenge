#!/usr/bin/env python
"""Redrob Intelligent Candidate Discovery & Ranking Challenge — ranking entry point.

Produces the top-100 submission CSV from candidates.jsonl in a single pass plus
a shortlist refinement, CPU-only, no network, well under the 5-minute budget.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Pipeline:
  1. Stream-parse all candidates (~100K).
  2. Hard gates: honeypot impossibility checks; integrity flags exclude.
  3. Feature extraction: evidence from career-history text (never the raw
     skill list), structural fit vs the JD's explicit rubric, behavioral
     availability multiplier.
  4. Coarse score -> shortlist top SHORTLIST_N.
  5. TF-IDF cosine vs the JD text refines the shortlist (15% blend).
  6. Top 100 with fact-grounded reasoning -> CSV.
"""

import argparse
import csv
import gzip
import json
import sys
import time

from ranker import features, gates, reasoning, scoring

SHORTLIST_N = 1500

# Raw-line prescreen on the exact current_title field. The JD is explicit
# that a non-engineering title is disqualifying no matter how good the skill
# list looks ("A candidate who has all the AI keywords listed as skills but
# whose title is 'Marketing Manager' is not a fit"), and these 12 generator
# titles cover ~68% of the pool. Skipping them before json.loads keeps the
# full pass well inside the 5-minute budget. Keyword stuffers with technical
# titles still flow through and are handled by the corroboration gate.
NON_TECHNICAL_TITLES = frozenset(
    {
        "Business Analyst", "HR Manager", "Mechanical Engineer", "Accountant",
        "Project Manager", "Customer Support", "Operations Manager",
        "Content Writer", "Sales Executive", "Civil Engineer",
        "Graphic Designer", "Marketing Manager",
    }
)
_TITLE_KEY = '"current_title": "'


def prescreen(line: str) -> bool:
    """True if the candidate should be fully parsed and scored."""
    i = line.find(_TITLE_KEY)
    if i == -1:
        return True  # unexpected shape: parse it rather than guess
    i += len(_TITLE_KEY)
    title = line[i : line.index('"', i)]
    return title not in NON_TECHNICAL_TITLES

JD_SUMMARY = """
Senior AI Engineer founding team Series A talent intelligence platform.
Own the intelligence layer: ranking retrieval matching systems recruiters
candidates search. Production experience embeddings based retrieval systems
sentence-transformers OpenAI embeddings BGE E5 embedding drift index refresh
retrieval quality regression production. Vector databases hybrid search
Pinecone Weaviate Qdrant Milvus OpenSearch Elasticsearch FAISS. Strong Python
code quality. Evaluation frameworks ranking systems NDCG MRR MAP offline
online correlation A/B test interpretation. LLM fine-tuning LoRA QLoRA PEFT.
Learning-to-rank XGBoost neural. HR-tech recruiting marketplace. Distributed
systems inference optimization. Open-source contributions. Shipped end-to-end
ranking search recommendation system real users meaningful scale. Hybrid
dense retrieval evaluation offline online fine-tune prompt. Applied ML AI
product companies. BM25 rule-based scoring embeddings hybrid retrieval LLM
re-ranking recruiter engagement. Offline benchmarks online A/B testing
recruiter feedback loops. NLP information retrieval.
"""


def iter_candidates(path: str):
    """Yield (parsed_candidate | None) per line; None = prescreened out."""
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if not prescreen(line):
                yield None
            else:
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", required=True, help="candidates.jsonl[.gz]")
    ap.add_argument("--out", required=True, help="output submission CSV path")
    ap.add_argument("--top", type=int, default=100)
    args = ap.parse_args()

    t0 = time.time()
    pool = []  # (coarse_score, cid, feats, notes)
    n_total = n_honeypot = 0

    for cand in iter_candidates(args.candidates):
        n_total += 1
        if cand is None:
            continue
        if gates.honeypot_flags(cand):
            n_honeypot += 1
            continue
        f = features.extract(cand)
        # cheap pre-filter: skip profiles with zero core evidence AND
        # non-engineering titles — they cannot reach the top 100
        core = sum(f["concepts"].get(k, 0.0) for k in ("retrieval", "ranking", "evaluation", "nlp_ir", "llm"))
        if core < 0.5 and not f["is_engineering"]:
            continue
        fit, notes = scoring.fit_score(f)
        coarse = fit * f["availability"]
        if coarse > 0:
            pool.append((coarse, cand["candidate_id"], f, notes))

    pool.sort(key=lambda r: (-r[0], r[1]))
    shortlist = pool[:SHORTLIST_N]
    t_parse = time.time() - t0
    print(
        f"[rank] parsed {n_total} candidates in {t_parse:.1f}s | "
        f"honeypots excluded: {n_honeypot} | scored pool: {len(pool)}",
        file=sys.stderr,
    )

    # ---- shortlist refinement: TF-IDF cosine vs the JD ----
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    docs = [r[2]["full_text"] for r in shortlist]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2, max_features=60000)
    mat = vec.fit_transform(docs + [JD_SUMMARY])
    sims = cosine_similarity(mat[:-1], mat[-1]).ravel()

    refined = []
    for (coarse, cid, f, notes), sim in zip(shortlist, sims):
        score, notes2 = scoring.final_score(f, float(sim))
        refined.append((score, cid, f, notes2))
    refined.sort(key=lambda r: (-r[0], r[1]))

    top = refined[: args.top]
    max_score = top[0][0] if top else 1.0

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (score, cid, f, notes) in enumerate(top, start=1):
            w.writerow(
                [cid, rank, f"{score / max_score:.6f}", reasoning.build(f, notes, rank, cid)]
            )

    print(
        f"[rank] wrote top-{len(top)} to {args.out} | total {time.time() - t0:.1f}s",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
