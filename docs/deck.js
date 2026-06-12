const pptxgen = require("pptxgenjs");

const NAVY = "1E2761";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const MID = "4A5899";
const ACCENT = "F96167";
const GREY = "5A6072";
const LIGHT = "F4F7FE";

const p = new pptxgen();
p.layout = "LAYOUT_16x9";
p.title = "Redrob Ranker — Approach";

const H = { fontFace: "Georgia", color: NAVY };
const B = { fontFace: "Calibri", color: "333333" };

function title(slide, text, sub) {
  slide.addText(text, { ...H, x: 0.5, y: 0.3, w: 9.0, h: 0.55, fontSize: 25, bold: true });
  if (sub) slide.addText(sub, { ...B, x: 0.5, y: 0.92, w: 9.0, h: 0.32, fontSize: 13, italic: true, color: GREY });
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(p.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: fill }, rectRadius: 0.06,
    line: { color: "E3E8F5", width: 1 },
  });
}

function chip(slide, x, y, num, color) {
  slide.addShape(p.shapes.OVAL, { x, y, w: 0.34, h: 0.34, fill: { color } });
  slide.addText(num, { x, y: y - 0.012, w: 0.34, h: 0.36, fontSize: 14, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Calibri", margin: 0 });
}

/* ---------------- Slide 1 — title ---------------- */
let s = p.addSlide();
s.background = { color: NAVY };
s.addText("Reading between the lines", { x: 0.7, y: 1.55, w: 7.5, h: 0.9, fontSize: 40, bold: true, color: WHITE, fontFace: "Georgia" });
s.addText("An evidence-first candidate ranker for the Redrob Intelligent Candidate\nDiscovery & Ranking Challenge", { x: 0.7, y: 2.55, w: 8.2, h: 0.85, fontSize: 18, color: ICE, fontFace: "Calibri" });
s.addText("100,000 candidates  ·  one Senior AI Engineer JD  ·  94 seconds  ·  zero LLM calls at rank time", { x: 0.7, y: 4.6, w: 8.8, h: 0.4, fontSize: 14, italic: true, color: "8FA3D8", fontFace: "Calibri" });
s.addShape(p.shapes.OVAL, { x: 8.65, y: 0.45, w: 0.9, h: 0.9, fill: { color: ACCENT } });
s.addShape(p.shapes.OVAL, { x: 9.15, y: 1.15, w: 0.5, h: 0.5, fill: { color: MID } });

/* ---------------- Slide 2 — the problem ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "The pool is designed to fool keyword systems", "What 30 minutes of data exploration told us before any code was written");
const stats = [
  ["68%", "of the pool has non-engineering titles (HR, accounting, civil...) — bulk noise", NAVY],
  ["~5,100", "keyword stuffers: non-technical profiles listing RAG, Pinecone, FAISS as skills", ACCENT],
  ["~80", "honeypots with subtly impossible profiles — >10% of them in a top-100 disqualifies", ACCENT],
  ["≤ 5 min", "CPU-only, 16 GB, no network: no LLM-per-candidate architectures allowed", NAVY],
];
stats.forEach((st, i) => {
  const x = 0.5 + (i % 2) * 4.62, y = 1.5 + Math.floor(i / 2) * 1.78;
  card(s, x, y, 4.38, 1.58, LIGHT);
  s.addText(st[0], { x: x + 0.25, y: y + 0.16, w: 2.0, h: 0.66, fontSize: 34, bold: true, color: st[2], fontFace: "Georgia", margin: 0 });
  s.addText(st[1], { ...B, x: x + 0.25, y: y + 0.82, w: 3.9, h: 0.68, fontSize: 12.5, color: GREY, margin: 0 });
});
s.addText("Plus: behavioral twins (identical on paper, different availability) and “plain-language Tier 5s” who never use a single buzzword.", { ...B, x: 0.5, y: 5.12, w: 9.0, h: 0.38, fontSize: 13, italic: true, color: NAVY });

/* ---------------- Slide 3 — key insight ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "Key insight: the traps live close to the JD in embedding space");
card(s, 0.5, 1.45, 4.38, 3.55, LIGHT);
s.addText("The usual hybrid", { x: 0.78, y: 1.68, w: 3.8, h: 0.4, fontSize: 17, bold: true, color: GREY, fontFace: "Georgia" });
s.addText([
  { text: "Embed JD + profiles, rank by similarity, sprinkle rules on top.", options: { breakLine: true } },
  { text: "", options: { breakLine: true } },
  { text: "A stuffer's skill list is engineered to sit next to the JD in vector space. Similarity-driven ranking maximizes exactly the failure mode this dataset punishes.", options: {} },
], { ...B, x: 0.78, y: 2.12, w: 3.85, h: 2.7, fontSize: 13.5, color: GREY });
card(s, 5.12, 1.45, 4.38, 3.55, NAVY);
s.addText("Our inversion", { x: 5.4, y: 1.68, w: 3.8, h: 0.4, fontSize: 17, bold: true, color: WHITE, fontFace: "Georgia" });
s.addText([
  { text: "Explicit, JD-derived evidence reasoning drives the score.", options: { breakLine: true } },
  { text: "", options: { breakLine: true } },
  { text: "Evidence is read from career-history prose — text someone had to write about real work — never from the self-reported skills list. Semantic similarity (TF-IDF) enters only as a 15% refinement on an already-vetted shortlist.", options: {} },
], { x: 5.4, y: 2.12, w: 3.85, h: 2.9, fontSize: 13.5, color: ICE, fontFace: "Calibri" });

/* ---------------- Slide 4 — architecture ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "Architecture: a funnel that earns trust at every stage");
const steps = [
  ["100,000", "raw pool", "streamed JSONL, one pass", GREY],
  ["~32,000", "title prescreen", "the JD's own rule: non-engineering titles are out", MID],
  ["~21,000", "gates + evidence", "honeypot gates · evidence from career prose · availability multiplier", NAVY],
  ["1,500", "shortlist refine", "TF-IDF cosine vs JD, 15% blend — tie-breaker, never driver", MID],
  ["100", "ranked output", "fact-grounded reasoning per candidate", ACCENT],
];
let y = 1.42;
steps.forEach((st, i) => {
  const w = 6.5 - i * 1.0;
  const x = 0.5;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.68, fill: { color: i === 4 ? ACCENT : i % 2 ? MID : NAVY }, rectRadius: 0.05 });
  s.addText(st[0], { x: x + 0.18, y: y + 0.05, w: 1.15, h: 0.58, fontSize: 15, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0 });
  s.addText(st[1], { x: x + 1.35, y: y + 0.05, w: w - 1.5, h: 0.58, fontSize: 12, bold: true, color: ICE, fontFace: "Calibri", valign: "middle", margin: 0 });
  s.addText(st[2], { x: 7.15, y: y + 0.02, w: 2.35, h: 0.66, fontSize: 10.5, color: GREY, fontFace: "Calibri", valign: "middle", margin: 0 });
  y += 0.79;
});

/* ---------------- Slide 5 — evidence extraction ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "Evidence comes from what they did, not what they claim", "Nine concept lexicons applied to career-history descriptions and titles only");
const rows = [
  ["Retrieval (w 3.0)", "embeddings, FAISS, vector DBs, semantic search, HNSW, dense retrieval"],
  ["Ranking (w 3.0)", "ranking models, recommenders, LTR, BM25, discovery feeds, search relevance"],
  ["Evaluation (w 2.5)", "NDCG, MRR, A/B tests, offline-online correlation, relevance judgments"],
  ["Supporting (w 0.8–1.5)", "LLM engineering · NLP/IR · production scale · XGBoost-LTR · open source · HR-tech"],
];
rows.forEach((r, i) => {
  const ry = 1.62 + i * 0.78;
  card(s, 0.5, ry, 5.6, 0.66, i < 3 ? LIGHT : WHITE);
  s.addText(r[0], { x: 0.72, y: ry + 0.06, w: 1.95, h: 0.54, fontSize: 13, bold: true, color: NAVY, fontFace: "Calibri", valign: "middle", margin: 0 });
  s.addText(r[1], { x: 2.72, y: ry + 0.06, w: 3.3, h: 0.54, fontSize: 10.5, color: GREY, fontFace: "Calibri", valign: "middle", margin: 0 });
});
card(s, 6.35, 1.62, 3.15, 3.0, NAVY);
s.addText("Context-weighted", { x: 6.6, y: 1.8, w: 2.7, h: 0.38, fontSize: 15, bold: true, color: WHITE, fontFace: "Georgia" });
s.addText([
  { text: "× recency decay on past roles", options: { bullet: true, breakLine: true } },
  { text: "× 0.55 if earned at a services firm", options: { bullet: true, breakLine: true } },
  { text: "× 1.25 conjunction bonus when retrieval AND ranking co-occur — the JD's ideal is the intersection, not the sum", options: { bullet: true } },
], { x: 6.6, y: 2.22, w: 2.72, h: 2.3, fontSize: 12, color: ICE, fontFace: "Calibri" });
s.addText("Skills list used only for corroboration: a skill counts when the prose backs it.", { ...B, x: 0.5, y: 4.85, w: 5.6, h: 0.55, fontSize: 12, italic: true, color: NAVY });

/* ---------------- Slide 6 — traps ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "How each trap dies");
const traps = [
  ["Keyword stuffers", "≥5 AI skill claims with ≤1 corroborated in work history and no core evidence → ×0.10. Non-engineering titles never enter scoring at all (the JD's explicit rule)."],
  ["Honeypots", "Internal-consistency gates: job duration contradicting its own dates (>12 mo), claimed YoE exceeding the dated career span, “expert” skills with zero months of use. 65 profiles flagged; 0 honeypots in our top-100 even under tightened thresholds."],
  ["Behavioral twins", "Availability is a multiplier on fit, not a feature: last-active decay, recruiter response rate, interview completion, notice period, location/visa. Identical resumes separate cleanly."],
  ["Plain-language Tier 5s", "Lexicons include prose phrases (“built a recommendation system”, “discovery feed”, “collaborative filtering”) — candidates who never say RAG or Pinecone still surface."],
];
traps.forEach((t, i) => {
  const x = 0.5 + (i % 2) * 4.62, ty = 1.4 + Math.floor(i / 2) * 1.92;
  card(s, x, ty, 4.38, 1.78, i % 3 === 0 ? LIGHT : WHITE);
  chip(s, x + 0.22, ty + 0.2, String(i + 1), i < 2 ? ACCENT : NAVY);
  s.addText(t[0], { x: x + 0.68, y: ty + 0.16, w: 3.5, h: 0.4, fontSize: 15, bold: true, color: NAVY, fontFace: "Georgia", margin: 0 });
  s.addText(t[1], { x: x + 0.24, y: ty + 0.62, w: 3.95, h: 1.1, fontSize: 10.3, color: GREY, fontFace: "Calibri", margin: 0 });
});

/* ---------------- Slide 7 — JD fidelity ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "Every weight traces to a JD sentence", "docs/JD_MAPPING.md in the repo carries the full table — a sample:");
const map = [
  ["“research-only careers — we will not move forward”", "research_only → ×0.15"],
  ["“under 12 months of LangChain calling OpenAI”", "shallow_llm → ×0.55"],
  ["“only worked at consulting firms in their entire career”", "services-only → ×0.30 (prior product experience passes, as the JD allows)"],
  ["“CV/speech/robotics without significant NLP/IR exposure”", "cv_primary → ×0.35"],
  ["“title-chasers switching every 1.5 years”", "hopper → ×0.75"],
  ["“hasn't written production code in 18 months”", "non-coding title → ×0.60"],
  ["“5–9 years... ideal 6–8”", "experience trapezoid, plateau 5–9, peak 6–8"],
];
map.forEach((m, i) => {
  const ry = 1.58 + i * 0.52;
  s.addText(m[0], { x: 0.5, y: ry, w: 4.7, h: 0.46, fontSize: 11.5, italic: true, color: GREY, fontFace: "Georgia", valign: "middle", margin: 0 });
  s.addText("→", { x: 5.22, y: ry, w: 0.3, h: 0.46, fontSize: 13, color: ACCENT, bold: true, valign: "middle", margin: 0, fontFace: "Calibri" });
  s.addText(m[1], { x: 5.58, y: ry, w: 3.95, h: 0.46, fontSize: 11.5, color: NAVY, fontFace: "Consolas", valign: "middle", margin: 0 });
});

/* ---------------- Slide 8 — results ---------------- */
s = p.addSlide();
s.background = { color: WHITE };
title(s, "Results on the full 100K pool");
const res = [
  ["94 s", "full run, laptop CPU\n(budget: 300 s)"],
  ["~1.5 GB", "peak RAM\n(budget: 16 GB)"],
  ["0", "honeypot flags in top-100,\neven with tightened checks"],
  ["6.3 yrs", "mean experience of top-100\n(JD ideal: 6–8)"],
];
res.forEach((r, i) => {
  const x = 0.5 + i * 2.32;
  card(s, x, 1.45, 2.12, 1.7, LIGHT);
  s.addText(r[0], { x: x + 0.14, y: 1.62, w: 1.84, h: 0.6, fontSize: 28, bold: true, color: i === 2 ? ACCENT : NAVY, fontFace: "Georgia", align: "center", margin: 0 });
  s.addText(r[1], { x: x + 0.1, y: 2.28, w: 1.92, h: 0.8, fontSize: 10.5, color: GREY, align: "center", fontFace: "Calibri", margin: 0 });
});
card(s, 0.5, 3.4, 9.0, 1.7, NAVY);
s.addText("Sample reasoning (rank 42)", { x: 0.78, y: 3.56, w: 8.4, h: 0.36, fontSize: 13, bold: true, color: ICE, fontFace: "Georgia" });
s.addText("“Senior AI Engineer at Apple with 5.9 yrs; shipped ranking/recommendation systems (collaborative filtering, recommendation system) at Apple plus embeddings/vector-retrieval work, aligning well with the JD's production-retrieval focus. Strong availability signals: open to work, active this month, 80% recruiter response rate.”", { x: 0.78, y: 3.94, w: 8.5, h: 1.05, fontSize: 12, italic: true, color: WHITE, fontFace: "Calibri" });
s.addText("92% of the top-100 are India-based · official validator: “Submission is valid.”", { ...B, x: 0.5, y: 5.18, w: 9.0, h: 0.34, fontSize: 12, italic: true, color: GREY });

/* ---------------- Slide 9 — production path ---------------- */
s = p.addSlide();
s.background = { color: NAVY };
s.addText("From hackathon to production", { x: 0.7, y: 0.5, w: 8.6, h: 0.6, fontSize: 30, bold: true, color: WHITE, fontFace: "Georgia" });
const next = [
  ["Learn the weights", "The rubric is hand-tuned today; with recruiter-engagement labels it becomes a learning-to-rank model over the same interpretable features."],
  ["Precompute embeddings", "Offline sentence-transformer index (allowed outside the 5-min window) upgrades the 15% lexical refinement to true semantic recall — gates still veto."],
  ["Close the loop", "NDCG/MRR offline benchmarks + A/B hooks are the JD's weeks 9–12 mandate; the evidence features double as explanation strings recruiters can audit."],
];
next.forEach((n, i) => {
  const ny = 1.45 + i * 1.28;
  chip(s, 0.7, ny + 0.06, String(i + 1), ACCENT);
  s.addText(n[0], { x: 1.22, y: ny, w: 7.9, h: 0.4, fontSize: 17, bold: true, color: ICE, fontFace: "Georgia", margin: 0 });
  s.addText(n[1], { x: 1.22, y: ny + 0.42, w: 8.0, h: 0.62, fontSize: 12.5, color: "B9C6E8", fontFace: "Calibri", margin: 0 });
});
s.addText("Repo: rank.py · ranker/ (5 modules) · tests · Streamlit sandbox · docs/JD_MAPPING.md", { x: 0.7, y: 5.18, w: 8.8, h: 0.34, fontSize: 12, italic: true, color: "8FA3D8", fontFace: "Calibri" });

p.writeFile({ fileName: "redrob_ranker_deck.pptx" }).then(() => console.log("written"));
