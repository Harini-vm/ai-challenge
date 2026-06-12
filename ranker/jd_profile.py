"""JD-derived scoring profile for the Redrob Senior AI Engineer role.

This module is the "understanding" of the job description, hand-derived from a
close reading of the JD rather than from keyword extraction. Every lexicon and
weight here maps to an explicit sentence in the JD (see docs/JD_MAPPING.md).

The JD is unusually explicit about three things:
  1. Must-haves: production embeddings/retrieval, vector/hybrid search infra,
     ranking evaluation rigor (NDCG/MRR/A-B), strong Python.
  2. Explicit anti-patterns: research-only careers, consulting-only careers,
     LangChain-only recency, non-coding architects, CV/speech-only profiles,
     title-chasing job hoppers.
  3. Availability matters: behavioral signals modify on-paper fit.
"""

import re

# Reference "today" for recency math. The dataset's last_active dates top out
# at 2026-05-xx, so 2026-06-01 is the effective snapshot date of the pool.
TODAY = (2026, 6, 1)

# ---------------------------------------------------------------------------
# Evidence lexicons, applied to career_history descriptions + titles ONLY.
# The self-reported skills list is never trusted directly: a skill counts only
# when corroborated by work-history text (anti keyword-stuffing).
# Each pattern maps to (concept_label, weight).
# ---------------------------------------------------------------------------

EVIDENCE = {
    # Core must-have 1: embeddings-based retrieval in production
    "retrieval": (
        r"embedding|vector (search|database|db|index)|semantic search|faiss|"
        r"pinecone|weaviate|qdrant|milvus|sentence.transformers|"
        r"\bbge\b|\be5\b|minilm|nearest.neighbou?r|\bann index|hnsw|"
        r"dense retrieval|retrieval.augmented|\brag pipeline|hybrid (search|retrieval)",
        3.0,
    ),
    # Core must-have 2: ranking / recommendation / search systems shipped
    "ranking": (
        r"ranking (model|system|service|pipeline)|re.rank|learning.to.rank|"
        r"\bltr\b|recommendation (system|engine|model|feature)|recommender|"
        r"search relevance|relevance (model|tuning|judgments)|discovery feed|"
        r"personali[sz]ation|collaborative filtering|matrix factori[sz]ation|"
        r"two.tower|\bbm25\b|elasticsearch|opensearch|query (expansion|understanding)",
        3.0,
    ),
    # Core must-have 3: evaluation rigor for ranking systems
    "evaluation": (
        r"\bndcg\b|\bmrr\b|mean average precision|\bmap@|a/b test|ab test|"
        r"offline.online correlation|offline (metric|eval)|online metric|"
        r"interleaving|relevance judgments|eval(uation)? (framework|harness|suite|infra)|"
        r"recall@|precision@|golden (set|dataset)",
        2.5,
    ),
    # Nice-to-have: LLM engineering with substance
    "llm": (
        r"fine.tun|lora\b|qlora|peft\b|instruction.tun|llm (inference|serving|eval)|"
        r"prompt (engineering|pipeline)|quantiz|distill|\bvllm\b|token (latency|throughput)|"
        r"hallucination|grounding|guardrail",
        1.5,
    ),
    # NLP/IR foundation (JD: "understood retrieval and ranking before it was fashionable")
    "nlp_ir": (
        r"\bnlp\b|natural language|text classification|named entity|\bner\b|"
        r"information retrieval|\bir system|topic model|word2vec|glove|"
        r"\bbert\b|transformer|tf.idf|tokeni[sz]|language model",
        1.5,
    ),
    # Production engineering muscle (deployed to real users, scale, latency)
    "production": (
        r"production|deployed|shipped|serving|real users|latency|p99|p95|"
        r"\bqps\b|throughput|millions? of (users|queries|requests)|10m\+|"
        r"on.call|monitoring|drift|index refresh|regression",
        1.5,
    ),
    # Nice-to-have: learning-to-rank / classic ML on tabular ranking
    "ltr_ml": (
        r"xgboost|lightgbm|gradient.boost|feature (engineering|store|pipeline)|"
        r"catboost|logistic regression",
        0.8,
    ),
    # JD nice-to-have: external validation (open source, papers, talks)
    "external": (
        r"open.source|github|kaggle|published|paper|conference|talk|blog|"
        r"contribut(ed|or|ion)|maintainer|pypi|meetup",
        0.8,
    ),
    # Domain bonus: HR-tech / marketplace exposure
    "domain": (
        r"recruit|hiring|talent|candidate|job (board|matching|search)|hr.tech|"
        r"marketplace|two.sided",
        0.8,
    ),
}

# Negative evidence: profiles whose ML identity is CV/speech/robotics without IR
CV_SPEECH = (
    r"computer vision|image (classification|segmentation|detection)|object detection|"
    r"\byolo\b|opencv|speech (recognition|synthesis)|\btts\b|\basr\b|audio|"
    r"robotic|autonomous (vehicle|driving)|lidar|slam\b|3d (vision|point cloud)"
)

# Research-only careers (JD: explicit "will not move forward")
RESEARCH_TITLE = r"research (scientist|fellow|assistant|intern)|postdoc|professor|phd researcher"
RESEARCH_INDUSTRY = {"academia", "research", "education"}

# LangChain-tutorial-recency pattern (JD: "under 12 months of LangChain calling OpenAI")
SHALLOW_LLM = r"langchain|llamaindex|openai api|gpt.4 api|chatgpt|prompt"

# Consulting / pure-services employers (JD: consulting-only careers are out;
# current services employer is OK if there is prior product experience).
SERVICES_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "mindtree", "ltimindtree", "mphasis", "hcl",
    "hcl technologies", "tech mahindra", "lti", "ibm consulting", "deloitte",
    "ey", "kpmg", "pwc", "genpact", "dxc technology", "virtusa", "hexaware",
    "zensar", "birlasoft", "cyient", "l&t infotech", "persistent systems",
    "mastek", "coforge", "niit technologies", "sonata software",
}
SERVICES_INDUSTRIES = {"it services", "consulting", "bpo", "outsourcing"}

# Engineering-track current titles. Everything else needs strong text evidence
# to survive (a Marketing Manager with a perfect AI skill list is the JD's
# canonical trap).
ENGINEERING_TITLE = (
    r"engineer|developer|scientist|architect|sde\b|swe\b|programmer|"
    r"ml |ai |data |devops|sre\b|tech lead|technical lead|cto\b|vp eng|"
    r"head of (ai|ml|data|engineering)|principal|staff"
)

# Titles that signal "moved away from hands-on code" (JD: this role writes code)
NON_CODING_TITLE = (
    r"\b(director|vp|vice president|head of|general manager|delivery manager|"
    r"program manager|engagement manager|portfolio)\b"
)

# Title-seniority ladder for hopping detection
SENIORITY = [
    (r"\b(principal|staff|distinguished|head|director|vp|lead)\b", 3),
    (r"\bsenior\b|\bsr\.?\b", 2),
    (r"\bjunior\b|\bjr\.?\b|intern|trainee|associate", 0),
]

# Location handling (JD: Pune/Noida preferred; Hyd/Pune/Mumbai/Delhi-NCR
# welcome; outside India case-by-case, no visa sponsorship).
PREFERRED_CITIES = ("pune", "noida")
WELCOME_CITIES = ("hyderabad", "mumbai", "delhi", "gurgaon", "gurugram", "ghaziabad", "faridabad", "bangalore", "bengaluru")

JD_TEXT_PATH = "job_description"  # resolved by rank.py relative to data dir


# Literal substring triggers per concept: a cheap superset pre-test run on
# lowercased text before the (slow, authoritative) regex. Python's `str in`
# runs in C; the alternation regexes do not. A concept's regex is only
# evaluated when at least one trigger appears, which is rare for most
# candidates and makes the full pass ~5x faster.
TRIGGERS = {
    "retrieval": (
        "embedding", "vector", "semantic search", "faiss", "pinecone",
        "weaviate", "qdrant", "milvus", "sentence-transformer", "bge", "e5",
        "minilm", "neighbor", "neighbour", "ann index", "hnsw", "retrieval",
        "rag", "hybrid search",
    ),
    "ranking": (
        "rank", "recommend", "relevance", "discovery feed", "personali",
        "collaborative filtering", "matrix factor", "two-tower", "two tower",
        "bm25", "elasticsearch", "opensearch", "query expansion",
        "query understanding",
    ),
    "evaluation": (
        "ndcg", "mrr", "average precision", "map@", "a/b", "ab test",
        "offline", "online metric", "interleaving", "relevance judgment",
        "eval", "recall@", "precision@", "golden",
    ),
    "llm": (
        "fine-tun", "finetun", "lora", "qlora", "peft", "instruction", "llm",
        "prompt", "quantiz", "distill", "vllm", "token", "hallucination",
        "grounding", "guardrail",
    ),
    "nlp_ir": (
        "nlp", "natural language", "text classification", "named entity",
        "ner", "information retrieval", "ir system", "topic model",
        "word2vec", "glove", "bert", "transformer", "tf-idf", "tf.idf",
        "tokeni", "language model",
    ),
    "production": (
        "production", "deploy", "shipped", "serving", "real users", "latency",
        "p99", "p95", "qps", "throughput", "million", "10m+", "on-call",
        "on call", "monitoring", "drift", "index refresh", "regression",
    ),
    "ltr_ml": (
        "xgboost", "lightgbm", "gradient", "feature", "catboost",
        "logistic regression",
    ),
    "external": (
        "open-source", "open source", "github", "kaggle", "publish", "paper",
        "conference", "talk", "blog", "contribut", "maintainer", "pypi",
        "meetup",
    ),
    "domain": (
        "recruit", "hiring", "talent", "candidate", "job board",
        "job matching", "job search", "hr-tech", "hr tech", "marketplace",
        "two-sided", "two sided",
    ),
}

CV_TRIGGERS = (
    "vision", "image", "object detection", "yolo", "opencv", "speech", "tts",
    "asr", "audio", "robot", "autonomous", "lidar", "slam", "3d",
)
SHALLOW_TRIGGERS = ("langchain", "llamaindex", "openai", "gpt", "chatgpt", "prompt")


def compile_lexicons():
    """Pre-compile all regexes once; returns dict[label] -> (compiled, weight)."""
    return {k: (re.compile(p, re.I), w) for k, (p, w) in EVIDENCE.items()}


COMPILED_CV = re.compile(CV_SPEECH, re.I)
COMPILED_RESEARCH = re.compile(RESEARCH_TITLE, re.I)
COMPILED_SHALLOW = re.compile(SHALLOW_LLM, re.I)
COMPILED_ENG = re.compile(ENGINEERING_TITLE, re.I)
COMPILED_NONCODING = re.compile(NON_CODING_TITLE, re.I)
COMPILED_SENIORITY = [(re.compile(p, re.I), lvl) for p, lvl in SENIORITY]
