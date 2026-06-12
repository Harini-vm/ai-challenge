// Standalone architecture funnel image for the idea-submission template (slide 7).
const pptxgen = require("pptxgenjs");
const NAVY = "1E1B2E";
const PURPLE = "7D45E0";
const MIDP = "9B6BE8";
const GREY = "5A6072";
const ACCENT = "4A2ECC";

const p = new pptxgen();
p.layout = "LAYOUT_16x9";
const s = p.addSlide();
s.background = { color: "FFFFFF" };

const steps = [
  ["100,000", "raw pool", "streamed JSONL, one pass — no precomputation", NAVY],
  ["~32,000", "title prescreen", "the JD's own rule: 12 non-engineering titles are out, checked on the raw line", PURPLE],
  ["~21,000", "gates + evidence", "honeypot consistency gates · 9 concept lexicons over career prose · structural fit · availability multiplier", NAVY],
  ["1,500", "shortlist refine", "TF-IDF cosine vs JD, 15% blend — tie-breaker, never driver", MIDP],
  ["100", "ranked output", "fact-grounded reasoning quoting each candidate's own evidence", ACCENT],
];
let y = 0.55;
steps.forEach((st, i) => {
  const w = 6.3 - i * 0.95;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w, h: 0.74, fill: { color: st[3] }, rectRadius: 0.06 });
  s.addText(st[0], { x: 0.68, y: y + 0.06, w: 1.25, h: 0.62, fontSize: 16, bold: true, color: "FFFFFF", fontFace: "Verdana", valign: "middle", margin: 0 });
  s.addText(st[1], { x: 2.0, y: y + 0.06, w: w - 1.6, h: 0.62, fontSize: 12.5, bold: true, color: "DCCDFA", fontFace: "Verdana", valign: "middle", margin: 0 });
  s.addText(st[2], { x: 7.0, y: y + 0.02, w: 2.5, h: 0.7, fontSize: 10, color: GREY, fontFace: "Verdana", valign: "middle", margin: 0 });
  if (i < 4) s.addShape(p.shapes.LINE, { x: 1.05, y: y + 0.74, w: 0, h: 0.21, line: { color: "B9A3EE", width: 2.5, endArrowType: "triangle" } });
  y += 0.95;
});
s.addText("score = (core evidence × conjunction bonus + support) × experience band × JD penalties × availability   —   94 s end-to-end, CPU-only, no network",
  { x: 0.5, y: 5.18, w: 9.0, h: 0.32, fontSize: 10.5, italic: true, color: GREY, fontFace: "Verdana", margin: 0 });
p.writeFile({ fileName: "arch_slide.pptx" }).then(() => console.log("ok"));
