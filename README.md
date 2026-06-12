# Redrob Ranker — Intelligent Candidate Discovery & Ranking Challenge

Ranks the 100,000-candidate Redrob pool against the **Senior AI Engineer (Founding Team)**
job description and produces a recruiter-trustworthy top-100 shortlist with
per-candidate reasoning.

**No LLM calls, no GPU, no network at rank time.** Full run on the 100K pool:
**~95 seconds** on a laptop CPU (budget: 5 minutes), ~1.5 GB peak RAM (budget: 16 GB).

## Reproduce the submission

```bash
pip install -r requirements.txt
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

That is the entire pipeline — there is no pre-computation step, no cached
artifacts, and no hidden state. `candidates.jsonl` (or `.jsonl.gz`) is the
file from the hackathon bundle. The output passes `validate_submission.py`.

## Why not embeddings / an LLM?

We tried to answer the question the JD actually poses: *what separates a real
fit from a profile that merely sounds like one?* In this dataset (and in real
recruiting) that separation is **not semantic distance** — the traps
(keyword stuffers, honeypots, behavioral twins) are specifically constructed
to be close to the JD in embedding space. A pure vector ranker maximizes its
own failure mode here. So the architecture inverts the usual hybrid: explicit,
JD-derived evidence reasoning is the driver, and lexical semantic similarity
(TF-IDF cosine) is only a 15% refinement applied to an already-vetted shortlist.

## Architecture

```
candidates.jsonl (100K)
   │  1. raw-line title prescreen           — the 12 non-engineering generator titles
   │                                          (68% of pool) are out per the JD's own rule
   │  2. hard gates (gates.py)              — honeypot impossibility checks:
   │       · stated job duration vs its own dates (>12mo contradiction)
   │       · claimed YoE vs dated career span
   │       · "expert" skills with zero months of use
   │  3. evidence extraction (features.py)  — concept lexicons over CAREER-HISTORY TEXT,
   │       never the raw skills list: retrieval, ranking, evaluation, LLM, NLP/IR,
   │       production, LTR, open-source, HR-tech. Weighted by recency and by
   │       product-company vs services context.
   │  4. structural fit (scoring.py)        — YoE trapezoid (5–9, peak 6–8); explicit JD
   │       penalties: research-only, services-only, CV/speech-primary, shallow-LLM,
   │       title-chasing hoppers, non-coding titles, uncorroborated skill lists
   │  5. availability multiplier            — behavioral signals gate availability, not
   │       competence: last-active recency, recruiter response rate, interview
   │       completion, notice period, location/relocation (no visa sponsorship)
   ▼
shortlist (top 1,500 by rubric score)
   │  6. TF-IDF cosine vs JD text           — 15% blend, tie-breaking refinement only
   ▼
top 100 + fact-grounded reasoning (reasoning.py) → submission.csv
```

### Design decisions, briefly defended

- **Career text over skill lists.** The skills array is self-reported and is the
  stuffers' attack surface. A skill counts only when the work-history prose
  corroborates it; ≥5 AI skill claims with ≤1 corroboration and no core
  evidence is treated as stuffing (×0.10).
- **Honeypots via internal consistency, not special-casing.** The three checks
  are calibrated on the pool so generator noise doesn't trip them. Result: 0
  flagged profiles in our top 100 even under tightened thresholds.
- **Behavioral signals are a multiplier, not features.** A 10/10 engineer who
  hasn't logged in for 6 months and ignores recruiters is not hireable; a 6/10
  who replies within hours doesn't become an 8/10. Multiplicative composition
  encodes exactly that.
- **Conjunction bonus.** The JD's ideal profile has retrieval AND ranking AND
  eval experience together; candidates showing both core concepts get a ×1.25
  on the core, rewarding the intersection rather than the sum.
- **Plain-language Tier 5s.** Because evidence comes from prose
  ("built a recommendation system for the discovery feed") rather than buzzword
  presence, candidates who never say "RAG" or "Pinecone" still surface.

## Repo layout

| Path | What it is |
|---|---|
| `rank.py` | CLI entry point; streaming pipeline + shortlist refinement |
| `ranker/jd_profile.py` | The JD reading: lexicons, weights, disqualifier patterns (see `docs/JD_MAPPING.md`) |
| `ranker/gates.py` | Honeypot / profile-integrity hard gates |
| `ranker/features.py` | Evidence extraction + availability multiplier |
| `ranker/scoring.py` | Score blending and penalty logic |
| `ranker/reasoning.py` | Fact-grounded, rank-consistent reasoning strings |
| `app.py` | Streamlit sandbox: upload a small candidate sample, get a ranked CSV |
| `tests/` | Unit tests for gates and scoring edge cases |
| `output/submission.csv` | The submitted top-100 |

## Sandbox

```bash
streamlit run app.py
```

Upload any JSONL sample (≤100 candidates) and the app runs the identical
pipeline (same modules, no divergence) and offers the ranked CSV for download.

## Tests

```bash
python -m pytest tests/ -q
```
