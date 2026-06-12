# JD → scoring rubric mapping

Every lexicon, weight, and penalty in `ranker/jd_profile.py` and
`ranker/scoring.py` traces to an explicit statement in the job description.
This file is that trace.

| JD statement | Implementation |
|---|---|
| "Production experience with embeddings-based retrieval systems ... deployed to real users" | `EVIDENCE["retrieval"]` (w=3.0) + `EVIDENCE["production"]`; evidence extracted only from career-history prose |
| "Production experience with vector databases or hybrid search infrastructure" | vector-DB names inside `EVIDENCE["retrieval"]`; Elasticsearch/OpenSearch/BM25 inside `EVIDENCE["ranking"]` |
| "Hands-on experience designing evaluation frameworks ... NDCG, MRR, MAP, offline-to-online correlation, A/B test interpretation" | `EVIDENCE["evaluation"]` (w=2.5) |
| "Shipped at least one end-to-end ranking, search, or recommendation system to real users" | `EVIDENCE["ranking"]` (w=3.0); conjunction bonus ×1.25 when retrieval AND ranking evidence co-occur |
| "LLM fine-tuning experience (LoRA, QLoRA, PEFT)" — nice-to-have | `EVIDENCE["llm"]` at half-class weight (1.5) |
| "Experience with learning-to-rank models (XGBoost-based or neural)" | `EVIDENCE["ltr_ml"]` (0.8) |
| "Prior exposure to HR-tech, recruiting tech, or marketplace products" | `EVIDENCE["domain"]` (0.8) |
| "Open-source contributions in the AI/ML space" / "external validation (papers, talks, open-source)" | `EVIDENCE["external"]` (0.8) + GitHub-activity bonus ×1.04 |
| "5–9 years ... ideal 6-8 years" | `experience_band()` trapezoid: plateau 5–9, peak 6–8, soft outside |
| "pure research environments without any production deployment — we will not move forward" | `research_only` ×0.15 |
| "'AI experience' ... under 12 months using LangChain to call OpenAI — we will probably not move forward" | `shallow_llm` ×0.55 (LLM-framework terms without core evidence or production signal) |
| "hasn't written production code in the last 18 months ... 'architecture' or 'tech lead' roles" | `NON_CODING_TITLE` ×0.60 |
| "Title-chasers ... switching companies every 1.5 years" | `hopper` ×0.75 (≥3 jobs, nearly all stints <20 months) |
| "only worked at consulting firms (TCS, Infosys, Wipro, ...) in their entire career" | `SERVICES_COMPANIES`/`SERVICES_INDUSTRIES`; services-only ×0.30; current-services-with-prior-product passes (JD allows it) |
| "primary expertise is computer vision, speech, or robotics without significant NLP/IR exposure" | `cv_primary` ×0.35 |
| "A candidate who has all the AI keywords listed as skills but whose title is 'Marketing Manager' is not a fit" | title prescreen (12 generator non-engineering titles) + `stuffing` ×0.10 (≥5 uncorroborated AI skill claims) |
| "A Tier 5 candidate may not use the words 'RAG' or 'Pinecone' ... if their career history shows they built a recommendation system at a product company, they're a fit" | evidence lexicons include plain-language phrases (recommendation system, discovery feed, collaborative filtering, personalization, search relevance...) applied to prose; skill list never required |
| "perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is not actually available. Down-weight them." | multiplicative availability: last-active decay, response-rate map (0→0.78), interview-completion, open-to-work |
| "Pune/Noida-preferred ... Hyderabad, Pune, Mumbai, Delhi NCR welcome ... we don't sponsor work visas" | location multiplier 1.0 / 0.97 / 0.93–0.97 (other India, relocation-dependent) / 0.72 (outside India) |
| "We'd love sub-30-day notice. We can buy out up to 30 days. 30+ day candidates ... bar gets higher" | notice multiplier 1.0 / 0.96 (≤60) / 0.90 (>60) |
| "the dataset contains traps ... ~80 honeypots with subtly impossible profiles" | `gates.honeypot_flags`: duration-vs-dates contradiction, YoE vs dated span, expert skills never used — internal-consistency checks, no ID lists |
