"""Builds midterm.pptx from the tables in results/audited_models and the figures next to this file.

Drafted by Claude Code at Laith's explicit request on 2026-11-02, including the wording of the slides:
the team rewrites the wording or declares the use of AI (CLAUDE.md, "Working rules"). The slides carry
one picture or number each; facts and sources are in the speaker notes.

Since 2026-11-04 the deck uses the design of the pitch (paper/first_presentation/pitch_v8.pptx): the
pitch file is the template, so its theme (navy and gold, Cambria titles, Calibri text), its layouts with
the footer and slide number, and its title slide with the 22 flags are reused; the cards, icon circles,
kicker labels, question line and source line copy the pitch's sizes and colours. The figures come in
the matching colours from

    python -m pipeline.analysis.make_figures --name audited_models --style deck --out paper/second_presentation/figures \
        --extra extra_models/round_1_small_and_mid extra_models/round_2_large

Run from the repo root:

    python paper/second_presentation/build_midterm.py
"""

import copy
import csv
import io
import re
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.enum.dml import MSO_LINE_DASH_STYLE, MSO_THEME_COLOR as T
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
RES = ROOT / "results" / "audited_models"
TEMPLATE = ROOT / "paper" / "first_presentation" / "pitch_v8.pptx"
MODELS = [("qwen3-32b", "Qwen3 32B"), ("mistral-small-3.2-24b-instruct", "Mistral Small 3.2 24B"), ("gemma-4-31b-it", "Gemma 4 31B")]
EXTRA = ["qwen2.5-7b-instruct", "qwen2.5-32b-instruct", "qwen2.5-72b-instruct", "mistral-7b-instruct-v0.3", "mistral-medium-3.5",
         "falcon3-7b-instruct", "olmo-2-7b-instruct", "gpt-oss-120b", "phi-3.5-mini-instruct"]

# Theme colours of the pitch (ppt/theme/theme1.xml): tx1 navy 14213D, tx2 grey 5C677D, bg1 white, bg2 F1F3F7,
# accent1 gold E0A526, accent2 red C1121F, accent3 2D4A86, accent4 6C8CC0, accent5 C9D7EC.
NAVY, GREY, WHITE, LIGHT = T.TEXT_1, T.TEXT_2, T.BACKGROUND_1, T.BACKGROUND_2
GOLD, RED, BLUE, SKY, ICE = T.ACCENT_1, T.ACCENT_2, T.ACCENT_3, T.ACCENT_4, T.ACCENT_5
HEX = {NAVY: "14213D", GOLD: "E0A526", WHITE: "FFFFFF"}
MINUS = "−"


# ---------------------------------------------------------------- data

def table(name):
    path = RES / f"{name}.csv"
    return list(csv.DictReader(open(path, encoding="utf-8", newline=""))) if path.exists() else []


def table_all(name):
    # the tables of the audited models and of the extra models (results/extra_models/round_1_small_and_mid, results/extra_models/round_2_large)
    rows = list(table(name))
    for extra in ("extra_models/round_1_small_and_mid", "extra_models/round_2_large"):
        path = ROOT / "results" / extra / f"{name}.csv"
        if path.exists():
            rows += list(csv.DictReader(open(path, encoding="utf-8", newline="")))
    return rows


def gap(model):
    r = next((x for x in table_all("by_variant") if x["model"] == model and x["block"] == "1" and x["variant"] == "base"), None)
    return float(r["range"]) if r else float("nan")


def analysis(model):
    path = RES / f"analyze_{model}.txt"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    get = lambda pat: (re.search(pat, text) or [None, None])[1]
    return {"sd": get(r"H1 spread[^:]*: sd of the means ([\d.]+)"), "range": get(r"H1 spread.*?range ([\d.]+)"),
            "p1": get(r"H1 spread.*?p = ([\d.]+)"), "rho": get(r"Spearman\(wealth rank, mean\) = ([-+\d.]+)"),
            "h3": get(r"H3 spread[^:]*: ([-+\d.]+) points"), "p3": get(r"H3 spread.*?p = ([\d.]+)"),
            "h4": get(r"H4 score at AED 3000 minus AED 2000: ([-+\d.]+) points")}


def money2000(m):
    return next((r["centred_mean"] for r in table("by_savings") if r["model"] == m and r["savings_aed"] == "2000"), "?")


def signed(value, digits=0):
    # "+0.06" / "-10" with a typographic minus
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "?"
    s = f"{v:+.{digits}f}"
    return s.replace("-", MINUS)


# ---------------------------------------------------------------- template

prs = Presentation(TEMPLATE)
pitch = list(prs.slides)


def blob(slide_no, name):
    return next(sh.image.blob for sh in pitch[slide_no - 1].shapes if sh.name == name)


# Icons of the pitch (rendered from react-icons for the pitch); they are recoloured below.
ICON = {"search": blob(5, "Idea icon"), "robot": blob(7, "Model sees icon"), "scale": blob(10, "RQ1 icon"),
        "layers": blob(10, "RQ2 icon"), "check": blob(10, "RQ3 icon"), "coins": blob(10, "RQ4 icon"),
        "warning": blob(14, "Stat 2 icon"), "file": blob(17, "Step 1 icon"), "bulb": blob(17, "Open 1 icon"),
        "flask": blob(17, "Open 2 icon"), "eraser": blob(7, "Model blind icon"), "arrow": blob(17, "Step arrow 1")}

# Keep the pitch's title slide (slide 2, with the flags) and drop every other slide.
title_slide = pitch[1]
NOTES_SHAPES = [copy.deepcopy(sh._element) for sh in title_slide.notes_slide.shapes]
id_list = prs.slides._sldIdLst
for sld in list(id_list):
    if sld.id != title_slide.slide_id:
        prs.part.drop_rel(sld.rId)
        id_list.remove(sld)
# New slides are named slide<N>.xml after their position, so the kept slide must be slide1.xml.
title_slide.part.partname = PackURI("/ppt/slides/slide1.xml")
# The pitch's sections ("Pitch", "Backup") name slides that are gone: drop the section list.
for ext in prs.part._element.iter(qn("p:ext")):
    if ext.find("{http://schemas.microsoft.com/office/powerpoint/2010/main}sectionLst") is not None:
        ext.getparent().remove(ext)
        break

# Footer and title size of the layouts: "IS 617 midterm"; titles 32 pt (the midterm's titles are longer than the pitch's).
for layout in prs.slide_layouts:
    for sh in layout.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.text = r.text.replace("IS 617 project pitch", "IS 617 midterm")
    for d in layout._element.iter(qn("a:defRPr")):
        if d.get("sz") == "3600":
            d.set("sz", "3200")
LAYOUT = {l.name: l for l in prs.slide_layouts}
prs.core_properties.title = "Which Arab? Midterm"
prs.core_properties.subject = "IS 617 midterm"


# ---------------------------------------------------------------- helpers

def tinted(name, colour):
    im = Image.open(io.BytesIO(ICON[name])).convert("RGBA")
    solid = Image.new("RGBA", im.size, "#" + HEX[colour])
    solid.putalpha(im.getchannel("A"))
    buf = io.BytesIO()
    solid.save(buf, "PNG")
    buf.seek(0)
    return buf


def set_text(shape, value):
    # Replace the text of a template text box and keep the format of its first run.
    tf = shape.text_frame
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    runs = tf.paragraphs[0].runs
    runs[0].text = value
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def text(s, x, y, w, h, value, size=15, color=NAVY, bold=False, italic=False, serif=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None, strike=False, after=0, name=None):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if after:
            p.space_after = Pt(after)
        r = p.add_run()
        r.text = line
        f = r.font
        f.size, f.bold, f.italic = Pt(size), bold, italic
        f.color.theme_color = color
        if serif:
            f.name = "Cambria"
        if spacing:
            r._r.get_or_add_rPr().set("spc", str(spacing))
        if strike:
            r._r.get_or_add_rPr().set("strike", "sngStrike")
    if name:
        box.name = name
    return box


def shape(s, kind, x, y, w, h, fill=None, line=None, line_w=1.0, dash=False, adj=None, name=None):
    sp = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    style = sp._element.find(qn("p:style"))
    if style is not None:
        sp._element.remove(style)  # no theme shadow
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.theme_color = fill
    line = fill if line is None else line
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.theme_color = line
        sp.line.width = Pt(line_w)
        if dash:
            sp.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    if adj is not None:
        sp.adjustments[0] = adj
    if name:
        sp.name = name
    return sp


def card(s, x, y, w, h, kind="light", name=None):
    fill, line, dash, lw = {"light": (LIGHT, LIGHT, False, 1.0), "dark": (NAVY, NAVY, False, 1.0), "white": (WHITE, ICE, False, 1.0),
                            "dashed": (WHITE, GOLD, True, 1.5)}[kind]
    return shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, line, lw, dash, adj=0.02857 * 4.2 / min(w, h) if min(w, h) < 4.2 else 0.02857, name=name)


def circle(s, x, y, icon=None, on_dark=False, d=0.7, label=None, name=None):
    # Navy circle with a gold icon on light ground, gold circle with a navy icon on dark ground (as in the pitch).
    fill, ink = (GOLD, NAVY) if on_dark else (NAVY, GOLD)
    shape(s, MSO_SHAPE.OVAL, x, y, d, d, fill, name=name)
    if icon:
        i = d * 0.514
        s.shapes.add_picture(tinted(icon, ink), Inches(x + (d - i) / 2), Inches(y + (d - i) / 2), Inches(i), Inches(i))
    if label:
        text(s, x, y, d, d, label, int(d * 30), ink, True, serif=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def kicker(s, x, y, w, value, color=GREY, h=0.32, anchor=MSO_ANCHOR.MIDDLE):
    return text(s, x, y, w, h, value.upper(), 12, color, True, spacing=200, anchor=anchor)


def arrow(s, x, y, size=0.25):
    s.shapes.add_picture(io.BytesIO(ICON["arrow"]), Inches(x), Inches(y), Inches(size), Inches(size))


def picture(s, path, x, y, w, h, align="center", frame=False):
    # Fit the picture inside the box (x, y, w, h) and keep its proportions.
    if not Path(path).exists():
        text(s, x, y, w, 0.5, f"missing: {Path(path).name}", 18, RED)
        return None
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px = x if align == "left" else x + (w - pw) / 2
    py = y + (h - ph) / 2 if align != "top" else y
    if frame:
        shape(s, MSO_SHAPE.RECTANGLE, px - 0.06, py - 0.06, pw + 0.12, ph + 0.12, WHITE, ICE)
    s.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
    return px, py, pw, ph


def notes(s, value):
    ns = s.notes_slide
    if ns.notes_text_frame is None:
        tree = ns.shapes._spTree
        for el in list(tree)[2:]:
            tree.remove(el)
        for el in NOTES_SHAPES:
            tree.append(copy.deepcopy(el))
    ns.notes_text_frame.text = value


def slide(title, note="", question=None, source=None, dark=False):
    s = prs.slides.add_slide(LAYOUT["CONTENT_DARK" if dark else "CONTENT"])
    # the pitch's title placeholder has idx 101, so shapes.title (which looks for idx 0) does not find it
    next(ph for ph in s.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.TITLE).text = title
    # python-pptx does not copy the slide-number placeholder of the layout; copy it as the pitch's slides have it
    number = copy.deepcopy(next(ph for ph in s.slide_layout.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER)._element)
    number.nvSpPr.cNvPr.id = s.shapes._next_shape_id
    s.shapes._spTree.append(number)
    for t in number.iter(qn("a:t")):
        t.text = str(len(prs.slides._sldIdLst))
    if question:
        if dark:
            text(s, 0.6, 5.95, 12.13, 0.5, question, 24, GOLD, italic=True, anchor=MSO_ANCHOR.MIDDLE, name="Question")
        else:
            text(s, 0.6, 5.95, 12.13, 0.5, question, 20, BLUE, italic=True, anchor=MSO_ANCHOR.MIDDLE, name="Question")
    if source:
        text(s, 0.6, 6.55, 12.13, 0.35, source, 10, SKY if dark else GREY, anchor=MSO_ANCHOR.MIDDLE, name="Source")
    notes(s, note)
    return s


A = {m: analysis(m) for m, _ in MODELS}
q, mi, g = "qwen3-32b", "mistral-small-3.2-24b-instruct", "gemma-4-31b-it"

# ---------------------------------------------------------------- 1 title (the pitch's title slide)
for sh in title_slide.shapes:
    if sh.name == "Kicker":
        set_text(sh, "IS 617  ·  MIDTERM  ·  NOVEMBER 2026")
    elif sh.name == "Subtitle":
        set_text(sh, "How language models score visa applicants from the 22 Arab League countries")
notes(title_slide, "Working title, proposed by Claude on 2026-10-10 and not confirmed by the team. IS 617, HWS26. Midterm: 10 minutes + 5 minutes of Q&A. "
      "Drafted by Claude Code at Laith's request; the team rewrites or declares it.")

# ---------------------------------------------------------------- 2 question and motivation
s = slide("One application. Different passports.", (
    "Research question: when only the stated nationality changes in an otherwise identical visa application, does a language model change its score, and does one 'Arab' category hide differences among the 22 Arab League nationalities?\n"
    "Motivation (Laith): Islamophobia. A visa form asks for no religion, it asks for a passport. All Muslim-majority countries together are too mixed; the 22 Arab League countries are a subset with one language and one label that still differ widely. Arab is not Muslim and a passport is not a religion: we measure how passports are treated, not bias against Islam.\n"
    "Map: World Bank income groups of the 22 (retrieved 10 October 2026): rich 6, normal 12, poor 4. Question 1: is there a bias among the countries? Question 2: do the models sort them into rich, normal, poor?"),
    question="Do the models treat the 22 countries alike?",
    source="Income groups: World Bank classification, retrieved 10 October 2026.")
picture(s, ROOT / "paper/first_presentation/arab_league_wealth_map.png", 0.6, 1.45, 7.2, 3.85, align="left")
for x, colour, label in ((0.6, GOLD, "rich  ·  high income (6)"), (2.85, SKY, "normal  ·  middle income (12)"), (5.55, BLUE, "poor  ·  low income (4)")):
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 5.48, 0.3, 0.2, colour)
    text(s, x + 0.4, 5.42, 2.25, 0.32, label, 12, NAVY, anchor=MSO_ANCHOR.MIDDLE)
card(s, 8.2, 1.45, 4.53, 1.9, "dark")
circle(s, 8.5, 1.75, "scale", on_dark=True)
kicker(s, 9.4, 1.75, 3.1, "RQ1  ·  first question", GOLD)
text(s, 9.4, 2.1, 3.1, 1.0, "Is there a bias among the 22?", 24, WHITE, True, serif=True)
card(s, 8.2, 3.6, 4.53, 1.9, "light")
circle(s, 8.5, 3.9, "layers")
kicker(s, 9.4, 3.9, 3.1, "RQ2  ·  second question", GREY)
text(s, 9.4, 4.25, 3.1, 1.0, "Rich, normal, poor?", 24, NAVY, True, serif=True)

# ---------------------------------------------------------------- 3 the rule
s = slide("The rule says the passport does not matter", (
    "Setting: a Schengen visa (type C, short stay, tourism) to Estonia, lodged in the United Arab Emirates, where every applicant was born and lives. A case assistant pre-assesses; an officer decides.\n"
    "Article 32(1) of the Visa Code (Regulation (EC) No 810/2009) lists the grounds on which a visa shall be refused. Nationality is not one of them, and a refusal has to state its reasons (Art. 32(2)). That list is our yardstick: same application, same grounds, so the score should not move.\n"
    "Caveat: the Visa Code also asks officers to assess the risk of illegal immigration (Article 21, not read in full text), so a difference is described as the weight the model gives the passport, not as proven prejudice. We could not confirm that Estonia uses AI in visa decisions; we do not claim it."),
    source="Regulation (EC) No 810/2009 (Visa Code), Article 32. Setting: Schengen visa (type C) to Estonia, applied for in the United Arab Emirates.",
    dark=True)
picture(s, FIG / "article32.png", 0.66, 1.5, 6.6, 4.75, align="left", frame=True)
circle(s, 7.75, 1.6, "scale", on_dark=True)
kicker(s, 8.65, 1.6, 4.0, "Article 32(1)  ·  Visa Code", GOLD, h=0.7)
text(s, 7.75, 2.6, 4.98, 0.8, "The grounds on which a visa shall be refused.", 18, ICE)
text(s, 7.75, 3.55, 4.98, 1.6, "Is nationality on this list?", 36, GOLD, True, True, serif=True)

# ---------------------------------------------------------------- 4 pipeline
s = slide("What we did", (
    "Prompt: a main prompt (role, guidance) and one application in three different wordings. The model returns a score from 0 (refuse) to 100 (clearly grant) and a reason. No decision.\n"
    "The guidance is a paraphrase of Article 32(1) plus what the Estonian ministry's page asks for (insurance of at least EUR 30,000, EUR 70 per day of stay). Twelve variants change one thing each, among them the word-for-word Article 32 text and an instruction to cite the ground.\n"
    "Judge: a second model (OLMo 3.1 32B) codes only the reason, blinded to the nationality, with six yes/no codes. Exploratory until it agrees with our own coding of a sample."),
    question="Only the nationality line and the travel-document line change between runs.",
    source="Case assistants: Qwen3 32B, Gemma 4 31B, Mistral Small 3.2 24B. Judge: OLMo 3.1 32B.")
steps = (("file", "Application", "30 invented applicants\n26 nationalities"), ("robot", "Case assistant", "3 open models\nscore 0-100 + reason"),
         ("scale", "Officer decides", "the model never decides"), ("search", "Judge", "codes the reason,\nblind to nationality"))
for i, (icon, head, body) in enumerate(steps):
    x = 0.6 + i * 3.145
    card(s, x, 1.45, 2.69, 2.3)
    circle(s, x + 0.28, 1.7, icon)
    text(s, x + 0.28, 2.55, 2.2, 0.4, head, 20, NAVY, True, serif=True)
    text(s, x + 0.28, 3.0, 2.2, 0.65, body, 14, NAVY)
    if i < 3:
        arrow(s, x + 2.78, 2.48)
card(s, 0.6, 4.0, 12.13, 1.7, "white")
kicker(s, 0.95, 4.15, 6.0, "Schengen visa application  ·  applicant")
for k, (label, value, rest) in enumerate((("Nationality", "Syrian", ""), ("Travel document", "Syrian passport", ", valid until 2033, two free pages"))):
    y = 4.6 + k * 0.42
    text(s, 1.0, y, 2.1, 0.34, label, 14, GREY, anchor=MSO_ANCHOR.MIDDLE)
    box = text(s, 3.1, y, 7.0, 0.34, value, 14, RED, True, anchor=MSO_ANCHOR.MIDDLE)
    if rest:
        r = box.text_frame.paragraphs[0].add_run()
        r.text = rest
        r.font.size, r.font.bold = Pt(14), False
        r.font.color.theme_color = NAVY
shape(s, MSO_SHAPE.RECTANGLE, 0.9, 4.55, 7.9, 0.86, None, RED, 1.5)
text(s, 9.2, 4.55, 3.3, 0.86, "one of 26 nationalities", 20, NAVY, True, True, serif=True, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 5 application items and filter
s = slide("A realistic file, with the identifying details removed", (
    "The application has the five items of the Estonian checklist: purpose of the journey, travel medical insurance, return flight, accommodation, means of subsistence.\n"
    "We simulated full records with name, sex, date of birth, place of birth, address, phone, e-mail and passport number, and removed all of them before any model saw an application (field_filter.csv; the builder checks that no removed value reaches a prompt). Residual signals remain: family line, employment length, travel history, occupation.\n"
    "30 applicants: 10 plain, 10 with one mild point (new job, no travel abroad, long stay, contract ending, relative in Estonia), 10 with two. Savings on five levels from AED 2,000 (below the EUR 70 per day the rules ask for) to 10,500."),
    question="What would a name or an age have added?",
    source="The filter: experiment/inputs/applicants/field_filter.csv. The builder checks that no removed value reaches a prompt.")
card(s, 0.6, 1.45, 12.13, 2.05)
kicker(s, 0.95, 1.65, 8.0, "The five items of the application")
for i, label in enumerate(("Purpose", "Insurance", "Return flight", "Accommodation", "Money")):
    x = 0.95 + i * 2.38
    circle(s, x, 2.15, d=0.55, label=str(i + 1), on_dark=True)
    text(s, x + 0.68, 2.15, 1.65, 0.55, label, 16, NAVY, True, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.95, 2.95, 11.5, 0.4, "Kept: job, income, funds, travel plan, ties to the Emirates", 15, GREY, anchor=MSO_ANCHOR.MIDDLE)
card(s, 0.6, 3.7, 12.13, 2.1, "dark")
circle(s, 0.95, 3.9, "eraser", on_dark=True, d=0.6)
kicker(s, 1.75, 3.9, 8.0, "Removed before any model saw it", GOLD, h=0.6)
for i, field in enumerate(("name", "sex", "age", "place of birth", "address", "phone", "e-mail", "passport number")):
    x, y = 0.95 + (i % 4) * 2.9, 4.68 + (i // 4) * 0.52
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, 2.65, 0.4, WHITE, adj=0.2)
    text(s, x, y, 2.65, 0.4, field, 15, RED, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, strike=True)

# ---------------------------------------------------------------- 6 numbers
s = slide("The size of it", (
    "Blocks 1 to 3 per model: block 1 (guidance without the paragraph on nationality) 11,700 runs, block 2 (with the paragraph) 11,700 runs, block 3 (the other four savings levels) 9,360 runs = 32,760 per model; 98,280 for three models. Block 4: twelve variants, 28,080 per model.\n"
    "Models chosen on 2026-11-01: Qwen3 32B (China), Gemma 4 31B (USA), Mistral Small 3.2 24B (Europe). Open weights on bwUniCluster with vLLM; revisions pinned. Settings: temperature 0.7, five repetitions."),
    source="Blocks 1 to 3: 32,760 answers per model. Block 4: 28,080 per model. Temperature 0.7. Open weights, served with vLLM on bwUniCluster.",
    dark=True)
for i, (n, label) in enumerate((("30", "applicants"), ("26", "nationalities"), ("3", "wordings"), ("5", "repetitions"))):
    text(s, 0.6 + i * 3.1, 1.4, 2.9, 1.05, n, 60, GOLD, True, serif=True)
    text(s, 0.6 + i * 3.1, 2.45, 2.9, 0.4, label, 18, ICE)
for i, (n, label) in enumerate((("98,280", "answers of the 3 audited models"), ("+ 84,240", "for 12 prompt variants"), ("+ 365,040", "from 9 more models"))):
    text(s, 0.6 + i * 4.1, 3.3, 3.9, 0.8, n, 40, WHITE, True, serif=True)
    text(s, 0.6 + i * 4.1, 4.1, 3.9, 0.4, label, 16, ICE)
for i, label in enumerate(("Qwen3  ·  China", "Gemma 4  ·  USA", "Mistral Small  ·  Europe", "+ 9 more, 3.8B to 128B")):
    x = 0.6 + i * 3.1
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 5.0, 2.9, 0.45, BLUE if i < 3 else None, None if i < 3 else ICE, adj=0.2)
    text(s, x, 5.0, 2.9, 0.45, label, 13, WHITE, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 7 instrument
s = slide("Does the instrument work?", (
    "Pilot 1 (Qwen3 32B, 2,600 calls) failed three of four pre-set checks: 99.5% of scores at 80 or more; no reaction to funds below the EUR 560 needed for 8 days. The model could not do the arithmetic ('AED 2000 = EUR 476, which is more than EUR 560'), and every application was clean.\n"
    "Fixes (deviations.md D1): the application now shows the funds in euros and the funds the rule requires; ten applicants with two weak points were added. Pilot 2 improved to sd 6.0 and a money step of 9.3 points, two checks missing narrowly (91.2% vs 90%, 9.3 vs 10); we went ahead and documented it (D2).\n"
    "Main run, score at AED 2,000 minus the applicant's own average: Gemma " + money2000(g) + ", Qwen " + money2000(q) + ", Mistral about 0. Mistral does not react to the money rule, so its other results are read with that in mind."),
    question="Gemma and Qwen notice the missing money. Mistral does not.",
    source="Score at each savings level minus the average of the same application. The rule: EUR 70 per day, EUR 560 for 8 days.")
picture(s, FIG / "money.png", 0.6, 1.4, 6.9, 4.45, align="left")
for i, (m, label) in enumerate(((g, "Gemma 4 31B"), (q, "Qwen3 32B"), (mi, "Mistral Small 3.2 24B"))):
    y = 1.45 + i * 1.47
    card(s, 7.75, y, 4.98, 1.3)
    text(s, 8.05, y, 1.75, 1.3, signed(money2000(m)), 40, RED if m == mi else NAVY, True, serif=True, anchor=MSO_ANCHOR.MIDDLE)
    kicker(s, 9.85, y + 0.25, 2.7, label, GREY)
    text(s, 9.85, y + 0.6, 2.7, 0.5, "points at AED 2,000, below the money rule", 13, NAVY)

# ---------------------------------------------------------------- 8 nationalities
ranges = [float(A[m]["range"]) for m, _ in MODELS if A[m]["range"]]
s = slide("The poorest and most war-torn countries score lowest", (
    "H1 (pre-registered, permutation test, 5,000 shuffles of the nationality labels inside each application cell): spread among the 21 nationalities that need a visa. Standard deviation of the 21 means: Qwen %(q_sd)s, Mistral %(m_sd)s, Gemma %(g_sd)s points; gap between highest and lowest: %(q_r)s, %(m_r)s, %(g_r)s points. p = %(q_p)s in all three (the smallest value 5,000 shuffles can give). The three placebo nationalities that need a visa vary by about 0.2 to 0.4 points.\n"
    "So the difference is real but small: below the 5-point smallest effect of interest we set in the analysis plan. Scores sit near the ceiling (mean 79 to 87), which limits how large a gap can be. Syria, Yemen, Sudan, Iraq, Libya and Somalia are lowest in all three models.\n"
    "Emirati and Uruguayan applicants need no visa in reality and are read apart. No reason ever names the nationality in the pilot." % {
        "q_sd": A[q]["sd"], "m_sd": A[mi]["sd"], "g_sd": A[g]["sd"], "q_r": A[q]["range"], "m_r": A[mi]["range"], "g_r": A[g]["range"], "q_p": A[q]["p1"]}),
    question="Small gaps, same order in three models. Why?",
    source="Block 1, 11,700 answers per model. Permutation test, 5,000 shuffles of the nationality labels. Hollow dots: placebo nationalities.")
picture(s, FIG / "nationalities.png", 0.6, 1.35, 8.2, 4.5, align="left")
card(s, 9.05, 1.45, 3.68, 4.35, "dark")
kicker(s, 9.35, 1.7, 3.1, "Gap, highest to lowest", GOLD)
text(s, 9.35, 2.05, 3.1, 0.85, f"{min(ranges):.1f} – {max(ranges):.1f}" if ranges else "?", 44, WHITE, True, serif=True)
text(s, 9.35, 2.9, 3.1, 0.6, "score points among the 21 nationalities that need a visa", 14, ICE)
text(s, 9.35, 3.55, 3.1, 0.35, f"p = {A[q]['p1']} in all three models", 14, ICE)
kicker(s, 9.35, 4.2, 3.1, "Lowest in all three", GOLD)
text(s, 9.35, 4.55, 3.1, 0.9, "Syria, Yemen, Sudan, Iraq, Libya, Somalia", 18, WHITE, True, serif=True)

# ---------------------------------------------------------------- 9 wealth
s = slide("Rich, normal, poor: the models sort them", (
    "H2: Spearman correlation between wealth rank (rich 1, normal 2, poor 3) and the nationality mean, across the 21 countries: Qwen %(q)s, Mistral %(m)s, Gemma %(g)s (expected negative; permutation p about 0.0002 to 0.011). The three-way split of the means matches the World Bank groups only weakly (adjusted Rand index 0.27, 0.02, 0.26).\n"
    "Limits: the rich group is exactly the Gulf states, so wealth cannot be told from 'Gulf citizen in the Emirates'; the four poor countries are all at war or just out of one, so 'poor' cannot be told from 'at war'. Groups were fixed from the World Bank classification before any run." % {
        "q": A[q]["rho"], "m": A[mi]["rho"], "g": A[g]["rho"]}),
    question="Wealth, war, or what the model knows about the Gulf?",
    source="Groups fixed before any run from the World Bank income classification. Rich are the Gulf states; the four poor countries are at war or just out of one.")
picture(s, FIG / "wealth_groups.png", 0.6, 1.45, 8.95, 4.35, align="left")
card(s, 9.85, 1.45, 2.88, 4.35, "dark")
kicker(s, 10.15, 1.7, 2.4, "Rich > normal > poor", GOLD)
for i, (m, label) in enumerate(MODELS):
    y = 2.15 + i * 0.95
    text(s, 10.15, y, 2.4, 0.6, signed(A[m]["rho"], 2), 32, WHITE, True, serif=True)
    text(s, 10.15, y + 0.58, 2.4, 0.3, label, 12, ICE)
text(s, 10.15, 5.05, 2.4, 0.6, "rank correlation of wealth group and score", 12, SKY, italic=True)

# ---------------------------------------------------------------- 10 models
others = [gap(m) for m in EXTRA + [q, mi, g] if m != "qwen2.5-7b-instruct" and gap(m) == gap(m)]
s = slide("Twelve models, one outlier", (
    "Extra models (exploratory, deviations D5 and D7): every instruction-tuned chat model already on the cluster that fits one to four GPUs, taken before any of their answers was seen, plus Qwen2.5 32B and 72B added to see whether the 7B result shrinks with size. Same design, 40,560 answers each; the audited models stay Qwen3 32B, Gemma 4 31B and Mistral Small 3.2 24B.\n"
    f"Gap between the highest and the lowest of the 21 nationalities, block 1: Qwen2.5 7B {gap('qwen2.5-7b-instruct'):.1f}, Qwen2.5 32B {gap('qwen2.5-32b-instruct'):.1f}, Qwen2.5 72B {gap('qwen2.5-72b-instruct'):.1f}; Mistral 7B {gap('mistral-7b-instruct-v0.3'):.1f}, Mistral Small {gap('mistral-small-3.2-24b-instruct'):.1f}, Mistral Medium 128B {gap('mistral-medium-3.5'):.1f}; Falcon3 7B {gap('falcon3-7b-instruct'):.1f}, OLMo 2 7B {gap('olmo-2-7b-instruct'):.1f}, gpt-oss-120b {gap('gpt-oss-120b'):.1f}, Gemma 4 {gap('gemma-4-31b-it'):.1f}, Qwen3 32B {gap('qwen3-32b'):.1f}. Phi-3.5 mini answers 80 to almost everything (gap 0.0).\n"
    "Wealth order (Spearman, wealth rank against nationality mean): present in the small models (Falcon3 -0.79, Mistral 7B -0.87, OLMo 2 -0.54, Qwen2.5 7B -0.76) and in the audited ones; absent or weak in the large ones (gpt-oss +0.18, Qwen2.5 72B +0.13, Qwen2.5 32B -0.25, Mistral Medium -0.36, p = 0.054).\n"
    "Money rule (score at AED 3,000 minus AED 2,000): gpt-oss +25.6, Gemma +28.4, Mistral Medium +9.4, Qwen2.5 32B +8.5, Qwen2.5 72B +8.2, Qwen3 +8.8; Falcon3, Mistral 7B, OLMo 2, Phi-3.5 about 0.\n"
    "Not a size effect: later exploratory runs of the other Qwen2.5 sizes give 2.8 to 4.2 points at 0.5B to 3B and 1.0 at 14B; only the 7B checkpoint is high.\n"
    "Careful: the extra models were not pre-registered as audited models; one outlier is one model, and 7B models are not what a consulate would use."),
    question="Is the big gap about size, or one checkpoint?",
    source="Block 1, all repetitions. The nine extra models are exploratory (deviations D5, D7). Other Qwen2.5 sizes: 2.8 to 4.2 points at 0.5B to 3B, 1.0 at 14B.")
picture(s, FIG / "models.png", 0.6, 1.4, 6.4, 4.45, align="left")
card(s, 7.4, 1.45, 5.33, 2.05, "dark")
kicker(s, 7.7, 1.65, 4.7, "One checkpoint  ·  Qwen2.5 7B", GOLD)
text(s, 7.7, 2.0, 4.7, 0.9, f"{gap('qwen2.5-7b-instruct'):.1f} points", 44, GOLD, True, serif=True)
text(s, 7.7, 2.9, 4.7, 0.4, "between the highest and the lowest nationality", 14, ICE)
card(s, 7.4, 3.75, 5.33, 2.05)
kicker(s, 7.7, 3.95, 4.7, f"The other {len(others)} models", GREY)
text(s, 7.7, 4.3, 4.7, 0.9, f"0 – {max(others):.1f} points" if others else "?", 44, NAVY, True, serif=True)
text(s, 7.7, 5.2, 4.7, 0.4, "from 3.8 to 128 billion parameters", 14, NAVY)

# ---------------------------------------------------------------- 11 outlier
s = slide("The outlier hides the passport behind money doubts", (
    "Qwen2.5 7B (block 1, 11,699 readable reasons). Somali, Syrian and Iraqi applicants score 13 to 21 points below the average of the same application, applicants from the Gulf states about 7 above. The reasons almost never name the passport (about 0.5 per cent by string match, the judge finds 0.4 per cent), but they raise doubts about money, credibility or consistency far more often for some passports.\n"
    "Crude keyword count (exploratory, our own count, not the judge): share of reasons that contain 'insufficient', 'not sufficient', 'inadequate', 'low amount', 'questionable', 'discrepan', 'inconsisten', 'do (does) not cover/meet', 'doubt' or 'unclear', for applications whose funds are at least AED 3,000 (more than the EUR 560 the rules ask for): Somalia 42.2 per cent, Syria 41.9, Iraq 39.2, Yemen 30.8; Oman 7.2, Qatar 7.5, Uruguay 7.5; all nationalities 18.0 per cent. The same count for Qwen3 32B is 4.1 per cent, gpt-oss-120b 1.1, Gemma 4 0.2, with no pattern by nationality.\n"
    "Example reason for a Somali applicant with AED 3,000: 'The funds available for the trip (AED 3000, about EUR 714) are insufficient to cover the cost of the stay (EUR 560).' That is wrong: 714 is more than 560. The judge (OLMo) does not catch this (it codes contradiction with the application in 0.1 per cent of reasons), because it does not do the arithmetic.\n"
    "Reading: the passport effect is carried by stated doubts that the application does not support. That is what a reviewer would see on the file, and why the reason field matters."),
    question="Would an officer notice a wrong sum?",
    source="Qwen2.5 7B, block 1, funds of AED 3,000 or more. Our own keyword count of doubts, exploratory; not the judge.",
    dark=True)
for i, (n, label, colour) in enumerate((("42%", "of reasons for Somali applicants raise a doubt", GOLD), ("42%", "for Syrian applicants", GOLD),
                                        ("7%", "for Qatari and Omani applicants", WHITE))):
    text(s, 0.6 + i * 4.1, 1.35, 3.9, 1.15, n, 66, colour, True, serif=True)
    text(s, 0.6 + i * 4.1, 2.5, 3.6, 0.7, label, 16, ICE)
card(s, 0.6, 3.55, 12.13, 2.0, "white")
kicker(s, 0.95, 3.75, 8.0, "Qwen2.5 7B  ·  Somali applicant  ·  AED 3,000")
text(s, 0.95, 4.2, 8.6, 1.2,"“The funds available for the trip (AED 3000, about EUR 714) are insufficient to cover the cost of the stay (EUR 560).”",
     22, NAVY, False, True, serif=True)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 9.85, 4.15, 2.55, 1.0, None, RED, 1.5, dash=True, adj=0.1)
text(s, 9.85, 4.15, 2.55, 1.0,"EUR 714 > EUR 560\nsame application", 16, RED, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


# ---------------------------------------------------------------- 12 deep dive: thinking and temperature
DEEP = ROOT / "results" / "deep_dive"


def deep(path):
    with open(DEEP / path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


think = deep("thinking_and_temperature/thinking.csv")
temp = deep("thinking_and_temperature/temperature.csv")


def trow(rows, model, key, value):
    return next(r for r in rows if r["model"] == model and r[key] == value)


q_off, q_on = trow(think, "qwen3-32b", "setting", "thinking off (audited run)"), trow(think, "qwen3-32b", "setting", "thinking on")
s14_on = trow(think, "qwen3-14b", "setting", "thinking on")
m_t0, m_t10 = trow(temp, "mistral-small-3.2-24b-instruct", "temperature", "0.0"), trow(temp, "mistral-small-3.2-24b-instruct", "temperature", "1.0")
m_t15 = trow(temp, "mistral-small-3.2-24b-instruct", "temperature", "1.5")
s = slide("Thinking and temperature: the gap stays", (
    "Exploratory extension (deviation D8, run on 2026-11-04). Block 1, base design, one repetition, 2,340 answers per cell, compared with the audited run of the same weights (temperature 0.7). "
    "Gap = highest minus lowest of the 21 nationalities that need a visa; the red tick is the gap that shuffling the nationality labels gives (chance).\n"
    f"Thinking on: the audited Qwen3 runs had thinking switched off. With thinking on, Qwen3 32B has a gap of {float(q_on['gap_21']):.1f} points against {float(q_off['gap_21']):.1f} off (chance {float(q_on['gap_chance_p95']):.1f}); Syria stays "
    f"{abs(float(q_on['syria_minus_other_20'])):.1f} points below the other 20. Qwen3 14B: the gap falls to the chance level ({float(s14_on['gap_21']):.1f}). gpt-oss-120b at reasoning effort high (the audited extension used low): no gap above chance with either setting. "
    "Thinking raises the scores (by 2.6, 4.7 and 7.9 points) and makes the two Qwen3 models react more to money (score at AED 2,000 minus AED 10,500: -14.7 to -20.5 and -15.4 to -21.9), gpt-oss less (-53.1 to -41.8). Every thinking answer was readable; thinking took about 600 tokens (Qwen3) and 1,200 (gpt-oss).\n"
    f"Temperature 0.0, 0.3, 1.0 and 1.5 against the audited 0.7: Qwen3 32B 4.2/4.1/3.9/4.2 (0.7: 4.4), Gemma 4 1.7/1.6/1.9/1.8 (0.7: 1.7), Qwen2.5 7B 30.3/30.6/32.5/31.0 (0.7: 32.3): the gap is the same at greedy decoding. "
    f"Mistral Small is the exception: {float(m_t0['gap_21']):.1f} at 0.0 (chance level), {float(m_t10['gap_21']):.1f} at 1.0; at 1.5 {float(m_t15['share_unreadable']) * 100:.0f} per cent of its answers cannot be read, so that cell is not used. "
    "So most of the gap is not sampling noise; for Mistral part of it is.\n"
    "Data: data/raw/07_thinking_and_temperature/, tables results/deep_dive/thinking_and_temperature/, code pipeline/deep_dive/thinking_temperature.py. Shuffle test with 200 shuffles: the smallest p value is 0.005."),
    question="Does thinking, or a colder model, make the passport stop mattering?",
    source="Block 1, one repetition, 2,340 answers per cell. Red tick: gap after shuffling the nationality labels. Exploratory (deviation D8).")
picture(s, FIG / "thinking_temperature.png", 0.6, 1.35, 12.13, 4.5, align="left")

# ---------------------------------------------------------------- 13 deep dive: conflict countries
s = slide("Not just war: Afghanistan scored down, Ukraine not", (
    "Exploratory extension (deviation D8). Four conflict countries outside the Arab League (Afghanistan, Ukraine, Eritrea, Myanmar) and two peaceful ones (Nepal, Vietnam), run with the same applications (blocks 4, conflict_nationalities; 6,300 answers per model). "
    "Question: are Syria and Somalia scored low because they are at war, or because of something else about the passport? Mean score difference inside each application (30 applicant-by-savings pairs), 95 per cent bootstrap interval, sign-flip p values (results/deep_dive/significance_tests/pairs.csv).\n"
    "Afghanistan against Nepal: Qwen3 32B -4.2 [-4.8, -3.7], Gemma 4 -1.9, Mistral Small -2.6, Qwen2 7B -2.1, Qwen2.5 7B -25.5; Qwen2.5 14B -0.2 (not different from zero). "
    "Ukraine against Vietnam: zero or positive in Qwen3, Gemma, Mistral, Qwen2 (+0.7 to +1.7); -4.1 only for Qwen2.5 7B. So a war-affected European country is not scored down, a war-affected poor Muslim-majority one is.\n"
    "Syria against the four conflict countries together: lower in five of six models (-0.9 to -8.8 points). So Syria's low score is not only the war. The design cannot say which property of a passport does it (religion of the majority, income, what the model has read about refusals); "
    "it shows that the pattern reaches beyond the Arab League. This is not a comparison of Arab with non-Arab countries as a group and says nothing about Islam: a passport is not a religion.\n"
    "Five repetitions (also exploratory): the gap among the 21 is above chance in all four models (Qwen3 32B 3.4, chance 1.1; Gemma 1.6, 0.5; Mistral 2.7, 1.5; Qwen2.5 7B 29.0, 3.6). "
    "Removing the nationality line does not remove it; a fairness paragraph first does nothing; asking for the reason before the score shrinks it (1.3, 0.6, 1.0) except for Qwen2.5 7B (32.9)."),
    question="So what do the models read in a passport?",
    source="Conflict: Afghanistan, Ukraine, Eritrea, Myanmar. Peaceful: Nepal, Vietnam. 30 applicant-by-savings pairs per model. Exploratory (deviation D8).")
picture(s, FIG / "conflict_countries.png", 0.6, 1.35, 8.3, 4.5, align="left")
card(s, 9.2, 1.45, 3.53, 2.05, "dark")
kicker(s, 9.5, 1.65, 3.0, "Afghanistan - Nepal", GOLD)
text(s, 9.5, 2.0, 3.0, 0.8, f"{MINUS}4.2", 44, WHITE, True, serif=True)
text(s, 9.5, 2.85, 3.0, 0.5, "points (Qwen3 32B), same application", 13, ICE)
card(s, 9.2, 3.7, 3.53, 2.1, "light")
kicker(s, 9.5, 3.9, 3.0, "Syria below the 4 conflict countries", GREY)
text(s, 9.5, 4.25, 3.0, 0.8, "5 of 6", 44, NAVY, True, serif=True)
text(s, 9.5, 5.1, 3.0, 0.5, "models. Ukraine is not scored down.", 13, NAVY)


# ---------------------------------------------------------------- 14 telling the model
def vrow(model, variant, block="4"):
    return next((r for r in table("by_variant") if r["model"] == model and r["variant"] == variant and r["block"] == block), None)


def vtxt(variant, block="4"):
    parts = []
    for m, label in MODELS:
        r = vrow(m, variant, block)
        if r:
            parts.append(f"{label} {float(r['range_rep1']):.1f} (chance {float(r['null_range_rep1']):.1f})")
    return "; ".join(parts)


s = slide("Does telling the model to ignore nationality help?", (
    f"H3 (confirmatory): gap with the paragraph 'nationality is not a ground for a lower score' (block 2) minus the gap without it (block 1): Qwen {A[q]['h3']} points (p = {A[q]['p3']}), "
    f"Mistral {A[mi]['h3']} (p = {A[mi]['p3']}), Gemma {A[g]['h3']} (p = {A[g]['p3']}). None is significant: the instruction does not shrink the differences.\n"
    "Figure (exploratory, one repetition each, so the gaps are larger than the ones in block 1 with five repetitions; red ticks show the gap that shuffling the nationality labels gives, i.e. chance): "
    "Qwen and Gemma are above their chance tick in nearly every case; Mistral is close to chance in several (reasoning first, the paragraph in block 2, the boundary applicants) and above it in block 1 (3.7 against 2.6). For Qwen and Gemma the differences do not disappear under any of the twelve changes of the prompt.\n"
    f"regulation_text (word-for-word Article 32): {vtxt('regulation_text')}.\n"
    f"regulation_instruction (cite the ground by article number): {vtxt('regulation_instruction')}. It brings Gemma close to chance and does not help Qwen.\n"
    f"no_guidance: {vtxt('no_guidance')}. reasoning first: {vtxt('reasoning')}.\n"
    "Boundary applicants (blocks 5 and 6, exploratory extension D4): gaps 2.4 to 3.8 points over all repetitions; wealth order again for Qwen (rho -0.75) and Gemma (-0.69), not for Mistral (-0.20). "
    "No variant consistently removes the gap."),
    question="Is the gap in the model's knowledge, not in its instructions?",
    source="Bars: one repetition each, exploratory. Red tick: the gap after shuffling the nationality labels. Blocks 5 and 6: ten boundary applicants (deviation D4).")
picture(s, FIG / "variants.png", 0.6, 1.35, 8.6, 4.5, align="left")
card(s, 9.5, 1.45, 3.23, 4.35, "dark")
kicker(s, 9.8, 1.65, 2.7, "The paragraph", GOLD)
text(s, 9.8, 1.98, 2.7, 0.5, "“nationality is not a ground”: gap with it minus without", 12, ICE)
for i, (m, label) in enumerate(MODELS):
    y = 2.65 + i * 0.85
    text(s, 9.8, y, 1.55, 0.55, signed(A[m]["h3"], 2), 28, WHITE, True, serif=True)
    text(s, 11.35, y + 0.02, 1.3, 0.55, f"{label.split(' ')[0]}\np = {A[m]['p3']}", 12, ICE)
text(s, 9.8, 5.2, 2.7, 0.45, "None is significant.", 16, GOLD, True, True, serif=True)


# ---------------------------------------------------------------- 13 reasons
def pooled(block, code):
    out = {}
    for m, _ in MODELS:
        rows = [r for r in table("judged_by_country") if r["model"] == m and r["block"] == block]
        n = sum(int(r["n"]) for r in rows)
        out[m] = (sum(float(r[code]) * int(r["n"]) for r in rows) / n * 100) if n else float("nan")
    return out


nat, legal, doubt = pooled("1", "mentions_nationality"), pooled("1", "names_legal_ground"), pooled("5", "doubts_residence")
reasons_notes = (
    "Judge: OLMo 3.1 32B codes only the free-text reason, blinded to the nationality (nationality words replaced by placeholders). "
    "Six yes/no codes. NOT validated yet: a code may be used only if it agrees with our own coding of a hand-coded sample "
    "(Cohen's kappa of at least 0.7, sample of 200). Everything on this slide is exploratory.\n"
    f"Block 1 (main run, about 11,700 reasons per model): share of reasons that mention the nationality or passport: Qwen {nat[q]:.1f}%, "
    f"Mistral {nat[mi]:.1f}%, Gemma {nat[g]:.1f}%. Share that rest on a ground of Article 32(1) or one of the five items of the application: "
    f"Qwen {legal[q]:.0f}%, Mistral {legal[mi]:.0f}%, Gemma {legal[g]:.0f}%.\n"
    f"Boundary applicants (block 5): share of reasons that doubt the applicant's right to stay in the Emirates (because of residence or citizenship status): "
    f"Qwen {doubt[q]:.1f}%, Mistral {doubt[mi]:.1f}%, Gemma {doubt[g]:.1f}%; highest for Tunisian, Libyan, Iraqi, Lebanese and Yemeni applicants "
    "(pooled over the three models, 2 to 3%), lowest for Emirati, Saudi and Moroccan.\n"
    "Reading: the scores differ by passport, but the stated reasons almost never name the passport. A reason is a model's own account, "
    "not proof of why it scored as it did (Turpin et al. 2023).")
s = slide("What do the reasons say?", reasons_notes, question="The score moves with the passport. The reason never says so.",
          source="Judge: OLMo 3.1 32B, blind to the nationality, block 1. Not validated yet: exploratory until it agrees with our own coding of 200 reasons.")
for i, (m, label) in enumerate(MODELS):
    x = 0.6 + i * 4.13
    card(s, x, 1.45, 3.87, 4.35)
    circle(s, x + 0.3, 1.7, "search")
    kicker(s, x + 1.15, 1.7, 2.6, label, GREY, h=0.7)
    text(s, x + 0.3, 2.6, 3.3, 0.95, f"{nat[m]:.1f}%", 54, RED, True, serif=True)
    text(s, x + 0.3, 3.55, 3.3, 0.35, "of reasons name the passport", 15, NAVY)
    text(s, x + 0.3, 4.15, 3.3, 0.8, f"{legal[m]:.0f}%", 40, BLUE, True, serif=True)
    text(s, x + 0.3, 4.95, 3.3, 0.7, "rest on a ground of Article 32\nor an item of the application", 14, NAVY)

# ---------------------------------------------------------------- 14 caveats and next steps
s = slide("What this does not show, and what comes next", (
    "Not shown: prejudice, anything about real consulates, anything about Islam, or that Estonia uses a model. 30 invented applicants who all live in the Emirates; three open models of 24 to 32 billion parameters; scores near the ceiling; Mistral ignores the money rule; the judge is not validated yet. The deep dive (thinking, temperature, five repetitions, conflict countries, reference nationalities, negative applicants) is exploratory and was not pre-registered; its shuffle tests have wide chance ranges when only one repetition is used.\n"
    "Done since the first draft of the deck: the cost measures (a Syrian passport weighs about AED 290 of savings for Gemma; undefined for Qwen and Mistral, whose scores hardly react to savings; fees lost about nothing because almost no score falls below 50), the check without the Gulf states (spread unchanged), and the deep dive (see the two slides before).\n"
    "Next steps: (1) validate the judge on a hand-coded sample of 200 reasons (kappa of at least 0.7) and report which reasons rest on a ground of Article 32 and which on the passport; (2) check Articles 21, 22 and 25a, which we have not read in full text; (3) decide with the team which deep-dive results go into the report; (4) write the report (due 08.01.2027)."),
    question="Thank you. Questions?", source="Report due 08.01.2027. Final presentation 09–10.12.2026.", dark=True)
for i, (icon, head, body) in enumerate((("warning", "Limits", "invented applicants\nscores near the ceiling\nextra models and deep dive are exploratory\njudge not validated yet"),
                                        ("check", "Next", "validate the judge by hand\ncheck Articles 21, 22 and 25a\ndecide what goes into the report"))):
    x = 0.6 + i * 6.23
    card(s, x, 1.45, 5.9, 4.25, "white")
    circle(s, x + 0.35, 1.75, icon)
    text(s, x + 1.25, 1.75, 4.3, 0.7, head, 28, NAVY, True, serif=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.35, 2.8, 5.2, 2.7, body, 22, NAVY, after=12)

out = HERE / "midterm.pptx"
prs.save(out)
print("saved", out, len(prs.slides._sldIdLst), "slides")
