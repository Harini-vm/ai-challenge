"""Streamlit sandbox for the Redrob ranker.

Runs the *identical* pipeline modules as rank.py on an uploaded candidate
sample (<=100 records) and returns the ranked CSV. Exists to satisfy the
hackathon's sandbox requirement: small-sample reproducibility on CPU.

    streamlit run app.py
"""

import io
import json

import streamlit as st

from rank import JD_SUMMARY, prescreen
from ranker import features, gates, reasoning, scoring

st.set_page_config(page_title="Redrob Ranker Sandbox", layout="wide")
st.title("Redrob Ranker — sandbox")
st.caption(
    "Upload a JSONL sample of candidates (one JSON object per line, "
    "schema per candidate_schema.json). The same gates → evidence → "
    "availability → refinement pipeline as the full run executes here."
)

uploaded = st.file_uploader("candidates sample (.jsonl)", type=["jsonl", "json", "txt"])
top_n = st.slider("Rows to rank", 5, 100, 25)

if uploaded:
    lines = uploaded.read().decode("utf-8").splitlines()
    pool, skipped, honeypots = [], 0, []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not prescreen(line):
            skipped += 1
            continue
        cand = json.loads(line)
        flags = gates.honeypot_flags(cand)
        if flags:
            honeypots.append((cand["candidate_id"], flags))
            continue
        f = features.extract(cand)
        fit, notes = scoring.fit_score(f)
        pool.append((fit * f["availability"], cand["candidate_id"], f, notes))

    pool.sort(key=lambda r: (-r[0], r[1]))

    # TF-IDF refinement (same 15% blend as the full pipeline)
    sims = [0.0] * len(pool)
    if len(pool) >= 5:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        mat = vec.fit_transform([r[2]["full_text"] for r in pool] + [JD_SUMMARY])
        sims = cosine_similarity(mat[:-1], mat[-1]).ravel().tolist()

    refined = sorted(
        (
            (scoring.final_score(f, sim)[0], cid, f, notes)
            for (_, cid, f, notes), sim in zip(pool, sims)
        ),
        key=lambda r: (-r[0], r[1]),
    )[:top_n]

    max_score = refined[0][0] if refined and refined[0][0] > 0 else 1.0
    rows = [
        {
            "candidate_id": cid,
            "rank": i,
            "score": round(score / max_score, 6),
            "reasoning": reasoning.build(f, notes, i, cid),
        }
        for i, (score, cid, f, notes) in enumerate(refined, start=1)
    ]

    st.success(
        f"Scored {len(pool)} candidates "
        f"(skipped {skipped} non-engineering titles, "
        f"excluded {len(honeypots)} honeypot-flagged)."
    )
    if honeypots:
        with st.expander("Honeypot-flagged profiles"):
            for cid, flags in honeypots:
                st.write(f"`{cid}` — {'; '.join(flags)}")

    st.dataframe(rows, use_container_width=True)

    buf = io.StringIO()
    import csv as _csv

    w = _csv.DictWriter(buf, fieldnames=["candidate_id", "rank", "score", "reasoning"])
    w.writeheader()
    w.writerows(rows)
    st.download_button("Download ranked CSV", buf.getvalue(), "ranked_sample.csv", "text/csv")
else:
    st.info("Waiting for a candidate sample. Tip: `head -100 candidates.jsonl > sample.jsonl`")
