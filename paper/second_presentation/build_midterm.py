"""Builds midterm.pptx from the tables in results/audited_models and the figures next to this file.

Drafted by Claude Code at Laith's explicit request on 2026-11-02, including the wording of the slides:
the team rewrites the wording or declares the use of AI (CLAUDE.md, "Working rules"). The slides carry
one picture or number each; facts and sources are in the speaker notes. Run from the repo root:

    python paper/second_presentation/build_midterm.py
"""

import csv
import re
import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
RES = ROOT / "results" / "audited_models"
INK, MUTED, ACCENT, SOFT = RGBColor(0x1b, 0x1f, 0x2a), RGBColor(0x5b, 0x63, 0x70), RGBColor(0x1f, 0x6f, 0xb2), RGBColor(0xee, 0xf3, 0xf8)
ORANGE = RGBColor(0xe0, 0x7b, 0x00)
MODELS = [("qwen3-32b", "Qwen3 32B"), ("mistral-small-3.2-24b-instruct", "Mistral Small 3.2 24B"), ("gemma-4-31b-it", "Gemma 4 31B")]


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


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def text(slide, x, y, w, h, s, size=24, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, line in enumerate(s.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size, run.font.bold, run.font.color.rgb, run.font.name = Pt(size), bold, color, "Calibri"
    return box


def slide(title=None, notes="", question=None):
    s = prs.slides.add_slide(BLANK)
    if title:
        text(s, 0.6, 0.35, 12.1, 0.9, title, 32, True)
    if question:
        text(s, 0.6, 6.55, 12.1, 0.7, question, 22, False, ACCENT)
    s.notes_slide.notes_text_frame.text = notes
    return s


def box(s, x, y, w, h, title, body="", fill=SOFT, tsize=22, bsize=15):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.adjustments[0] = 0.08
    text(s, x + 0.15, y + 0.12, w - 0.3, 0.6, title, tsize, True)
    if body:
        text(s, x + 0.15, y + 0.75, w - 0.3, h - 0.85, body, bsize, False, MUTED)


def picture(s, path, x, y, w=None, h=None):
    # Fit the picture inside the box (x, y, w, h), keep its proportions and centre it.
    if not Path(path).exists():
        return False
    from PIL import Image
    iw, ih = Image.open(path).size
    w = w or 12.1
    h = h or 5.2
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    s.shapes.add_picture(str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))
    return True


A = {m: analysis(m) for m, _ in MODELS}
bc = [r for r in table("by_country") if r["block"] == "1" and r["variant"] == "base"]
n_model = 32760
# 1 title
s = slide(notes="Working title, proposed by Claude on 2026-10-10 and not confirmed by the team. IS 617, HWS26. Midterm: 10 minutes + 5 minutes of Q&A. Drafted by Claude Code at Laith's request; the team rewrites or declares it.")
text(s, 0.8, 2.2, 11.7, 1.6, "Which Arab?", 66, True)
text(s, 0.8, 3.7, 11.7, 1.2, "How language models score visa applicants from the 22 Arab League countries", 30, False, MUTED)
text(s, 0.8, 6.3, 11.7, 0.6, "IS 617 midterm  |  Laith Sandouk, Aleksander Kasak, Nico Fedotov", 16, False, MUTED)

# 2 question and motivation
s = slide("One application. Different passports.", notes=(
    "Research question: when only the stated nationality changes in an otherwise identical visa application, does a language model change its score, and does one 'Arab' category hide differences among the 22 Arab League nationalities?\n"
    "Motivation (Laith): Islamophobia. A visa form asks for no religion, it asks for a passport. All Muslim-majority countries together are too mixed; the 22 Arab League countries are a subset with one language and one label that still differ widely. Arab is not Muslim and a passport is not a religion: we measure how passports are treated, not bias against Islam.\n"
    "Map: World Bank income groups of the 22 (retrieved 10 October 2026): rich 6, normal 12, poor 4. Question 1: is there a bias among the countries? Question 2: do the models sort them into rich, normal, poor?"),
    question="Do the models treat the 22 countries alike?")
picture(s, ROOT / "paper/first_presentation/arab_league_wealth_map.png", 0.6, 1.3, 12.1, 5.1)

# 3 the rule
s = slide("The rule says the passport does not matter", notes=(
    "Setting: a Schengen visa (type C, short stay, tourism) to Estonia, lodged in the United Arab Emirates, where every applicant was born and lives. A case assistant pre-assesses; an officer decides.\n"
    "Article 32(1) of the Visa Code (Regulation (EC) No 810/2009) lists the grounds on which a visa shall be refused. Nationality is not one of them, and a refusal has to state its reasons (Art. 32(2)). That list is our yardstick: same application, same grounds, so the score should not move.\n"
    "Caveat: the Visa Code also asks officers to assess the risk of illegal immigration (Article 21, not read in full text), so a difference is described as the weight the model gives the passport, not as proven prejudice. We could not confirm that Estonia uses AI in visa decisions; we do not claim it."),
    question="Is nationality on this list?")
if not picture(s, FIG / "article32.png", 0.6, 1.2, 12.1, 5.2):
    text(s, 1, 2.5, 11, 2, "Article 32(1), Visa Code: grounds for refusal", 28)

# 4 pipeline
s = slide("What we did", notes=(
    "Prompt: a main prompt (role, guidance) and one application in three different wordings. The model returns a score from 0 (refuse) to 100 (clearly grant) and a reason. No decision.\n"
    "The guidance is a paraphrase of Article 32(1) plus what the Estonian ministry's page asks for (insurance of at least EUR 30,000, EUR 70 per day of stay). Twelve variants change one thing each, among them the word-for-word Article 32 text and an instruction to cite the ground.\n"
    "Judge: a second model (OLMo 3.1 32B) codes only the reason, blinded to the nationality, with six yes/no codes. Exploratory until it agrees with our own coding of a sample."))
for i, (t, b) in enumerate((("Application", "30 invented applicants\n26 nationalities"), ("Case assistant", "3 open models\nscore 0-100 + reason"),
                            ("Officer decides", "the model never decides"), ("Judge", "codes the reason,\nblind to nationality"))):
    box(s, 0.6 + i * 3.15, 2.2, 2.9, 2.6, t, b, tsize=22, bsize=17)
    if i < 3:
        text(s, 3.45 + i * 3.15, 3.2, 0.4, 0.6, ">", 30, True, ACCENT)
text(s, 0.6, 5.4, 12, 1, "Only the nationality line and the travel-document line change between runs.", 22, False, MUTED)

# 5 application items and filter
s = slide("A realistic file, with the identifying details removed", notes=(
    "The application has the five items of the Estonian checklist: purpose of the journey, travel medical insurance, return flight, accommodation, means of subsistence.\n"
    "We simulated full records with name, sex, date of birth, place of birth, address, phone, e-mail and passport number, and removed all of them before any model saw an application (field_filter.csv; the builder checks that no removed value reaches a prompt). Residual signals remain: family line, employment length, travel history, occupation.\n"
    "30 applicants: 10 plain, 10 with one mild point (new job, no travel abroad, long stay, contract ending, relative in Estonia), 10 with two. Savings on five levels from AED 2,000 (below the EUR 70 per day the rules ask for) to 10,500."),
    question="What would a name or an age have added?")
for i, t in enumerate(("Purpose", "Insurance", "Return flight", "Accommodation", "Money")):
    box(s, 0.6 + i * 2.5, 1.5, 2.3, 1.3, t, "", tsize=17)
text(s, 0.6, 3.3, 12, 0.6, "Kept: job, income, funds, travel plan, ties to the Emirates", 20, False, MUTED)
box(s, 0.6, 4.2, 12.1, 1.8, "Removed before any model saw it", "name  |  sex  |  age  |  place of birth  |  address  |  phone  |  e-mail  |  passport number", fill=RGBColor(0xfd, 0xf0, 0xe0), tsize=22, bsize=20)

# 6 numbers
s = slide("The size of it", notes=(
    "Blocks 1 to 3 per model: block 1 (guidance without the paragraph on nationality) 11,700 runs, block 2 (with the paragraph) 11,700 runs, block 3 (the other four savings levels) 9,360 runs = 32,760 per model; 98,280 for three models. Block 4: twelve variants, 28,080 per model.\n"
    "Models chosen on 2026-11-01: Qwen3 32B (China), Gemma 4 31B (USA), Mistral Small 3.2 24B (Europe). Open weights on bwUniCluster with vLLM; revisions pinned. Settings: temperature 0.7, five repetitions."))
for i, (n, l) in enumerate((("30", "applicants"), ("26", "nationalities"), ("3", "wordings"), ("5", "repetitions"))):
    text(s, 0.6 + i * 3.2, 1.7, 3, 1.2, n, 64, True, ACCENT, PP_ALIGN.CENTER)
    text(s, 0.6 + i * 3.2, 2.9, 3, 0.6, l, 22, False, MUTED, PP_ALIGN.CENTER)
text(s, 0.6, 4.0, 12.1, 1.5, "3 audited models: 98,280 answers\n+ 84,240 for 12 prompt variants\n+ 9 more models: 365,040 answers", 30, True, INK, PP_ALIGN.CENTER)
text(s, 0.6, 5.9, 12.1, 0.6, "Qwen3 (China)   |   Gemma 4 (USA)   |   Mistral Small (Europe)   |   9 more from 3.8B to 128B", 20, False, MUTED, PP_ALIGN.CENTER)

def money2000(m):
    return next((r["centred_mean"] for r in table("by_savings") if r["model"] == m and r["savings_aed"] == "2000"), "?")


# 7 instrument
s = slide("Does the instrument work?", notes=(
    "Pilot 1 (Qwen3 32B, 2,600 calls) failed three of four pre-set checks: 99.5% of scores at 80 or more; no reaction to funds below the EUR 560 needed for 8 days. The model could not do the arithmetic ('AED 2000 = EUR 476, which is more than EUR 560'), and every application was clean.\n"
    "Fixes (deviations.md D1): the application now shows the funds in euros and the funds the rule requires; ten applicants with two weak points were added. Pilot 2 improved to sd 6.0 and a money step of 9.3 points, two checks missing narrowly (91.2% vs 90%, 9.3 vs 10); we went ahead and documented it (D2).\n"
    "Main run, score at AED 2,000 minus the applicant's own average: Gemma " + money2000("gemma-4-31b-it") + ", Qwen " + money2000("qwen3-32b") + ", Mistral about 0. Mistral does not react to the money rule, so its other results are read with that in mind."),
    question="Gemma and Qwen notice the missing money. Mistral does not.")
picture(s, FIG / "money.png", 0.6, 1.2, 12.1, 5.2)

# 8 nationalities
s = slide("The poorest and most war-torn countries score lowest", notes=(
    "H1 (pre-registered, permutation test, 5,000 shuffles of the nationality labels inside each application cell): spread among the 21 nationalities that need a visa. Standard deviation of the 21 means: Qwen %(q_sd)s, Mistral %(m_sd)s, Gemma %(g_sd)s points; gap between highest and lowest: %(q_r)s, %(m_r)s, %(g_r)s points. p = %(q_p)s in all three (the smallest value 5,000 shuffles can give). The three placebo nationalities that need a visa vary by about 0.2 to 0.4 points.\n"
    "So the difference is real but small: below the 5-point smallest effect of interest we set in the analysis plan. Scores sit near the ceiling (mean 79 to 87), which limits how large a gap can be. Syria, Yemen, Sudan, Iraq, Libya and Somalia are lowest in all three models.\n"
    "Emirati and Uruguayan applicants need no visa in reality and are read apart. No reason ever names the nationality in the pilot." % {
        "q_sd": A["qwen3-32b"]["sd"], "m_sd": A["mistral-small-3.2-24b-instruct"]["sd"], "g_sd": A["gemma-4-31b-it"]["sd"],
        "q_r": A["qwen3-32b"]["range"], "m_r": A["mistral-small-3.2-24b-instruct"]["range"], "g_r": A["gemma-4-31b-it"]["range"], "q_p": A["qwen3-32b"]["p1"]}),
    question="Small gaps, same order in three models. Why?")
picture(s, FIG / "nationalities.png", 0.4, 1.1, 12.5, 5.4)

# 9 wealth
s = slide("Rich, normal, poor: the models sort them", notes=(
    "H2: Spearman correlation between wealth rank (rich 1, normal 2, poor 3) and the nationality mean, across the 21 countries: Qwen %(q)s, Mistral %(m)s, Gemma %(g)s (expected negative; permutation p about 0.0002 to 0.011). The three-way split of the means matches the World Bank groups only weakly (adjusted Rand index 0.27, 0.02, 0.26).\n"
    "Limits: the rich group is exactly the Gulf states, so wealth cannot be told from 'Gulf citizen in the Emirates'; the four poor countries are all at war or just out of one, so 'poor' cannot be told from 'at war'. Groups were fixed from the World Bank classification before any run." % {
        "q": A["qwen3-32b"]["rho"], "m": A["mistral-small-3.2-24b-instruct"]["rho"], "g": A["gemma-4-31b-it"]["rho"]}),
    question="Wealth, war, or what the model knows about the Gulf?")
picture(s, FIG / "wealth_groups.png", 0.6, 1.2, 12.1, 5.2)

# 9b models
s = slide("Twelve models, one outlier", notes=(
    "Extra models (exploratory, deviations D5 and D7): every instruction-tuned chat model already on the cluster that fits one to four GPUs, taken before any of their answers was seen, plus Qwen2.5 32B and 72B added to see whether the 7B result shrinks with size. Same design, 40,560 answers each; the audited models stay Qwen3 32B, Gemma 4 31B and Mistral Small 3.2 24B.\n"
    f"Gap between the highest and the lowest of the 21 nationalities, block 1: Qwen2.5 7B {gap('qwen2.5-7b-instruct'):.1f}, Qwen2.5 32B {gap('qwen2.5-32b-instruct'):.1f}, Qwen2.5 72B {gap('qwen2.5-72b-instruct'):.1f}; Mistral 7B {gap('mistral-7b-instruct-v0.3'):.1f}, Mistral Small {gap('mistral-small-3.2-24b-instruct'):.1f}, Mistral Medium 128B {gap('mistral-medium-3.5'):.1f}; Falcon3 7B {gap('falcon3-7b-instruct'):.1f}, OLMo 2 7B {gap('olmo-2-7b-instruct'):.1f}, gpt-oss-120b {gap('gpt-oss-120b'):.1f}, Gemma 4 {gap('gemma-4-31b-it'):.1f}, Qwen3 32B {gap('qwen3-32b'):.1f}. Phi-3.5 mini answers 80 to almost everything (gap 0.0).\n"
    "Wealth order (Spearman, wealth rank against nationality mean): present in the small models (Falcon3 -0.79, Mistral 7B -0.87, OLMo 2 -0.54, Qwen2.5 7B -0.76) and in the audited ones; absent or weak in the large ones (gpt-oss +0.18, Qwen2.5 72B +0.13, Qwen2.5 32B -0.25, Mistral Medium -0.36, p = 0.054).\n"
    "Money rule (score at AED 3,000 minus AED 2,000): gpt-oss +25.6, Gemma +28.4, Mistral Medium +9.4, Qwen2.5 32B +8.5, Qwen2.5 72B +8.2, Qwen3 +8.8; Falcon3, Mistral 7B, OLMo 2, Phi-3.5 about 0.\n"
    "Careful: the extra models were not pre-registered as audited models; one outlier is one model, and 7B models are not what a consulate would use."),
    question="Is the big gap a small-model accident?")
picture(s, FIG / "models.png", 0.6, 1.1, 12.1, 5.4)

# 9c outlier
s = slide("The outlier hides the passport behind money doubts", notes=(
    "Qwen2.5 7B (block 1, 11,699 readable reasons). Somali, Syrian and Iraqi applicants score 13 to 21 points below the average of the same application, applicants from the Gulf states about 7 above. The reasons almost never name the passport (about 0.5 per cent by string match, the judge finds 0.4 per cent), but they raise doubts about money, credibility or consistency far more often for some passports.\n"
    "Crude keyword count (exploratory, our own count, not the judge): share of reasons that contain 'insufficient', 'not sufficient', 'inadequate', 'low amount', 'questionable', 'discrepan', 'inconsisten', 'do (does) not cover/meet', 'doubt' or 'unclear', for applications whose funds are at least AED 3,000 (more than the EUR 560 the rules ask for): Somalia 42.2 per cent, Syria 41.9, Iraq 39.2, Yemen 30.8; Oman 7.2, Qatar 7.5, Uruguay 7.5; all nationalities 18.0 per cent. The same count for Qwen3 32B is 4.1 per cent, gpt-oss-120b 1.1, Gemma 4 0.2, with no pattern by nationality.\n"
    "Example reason for a Somali applicant with AED 3,000: 'The funds available for the trip (AED 3000, about EUR 714) are insufficient to cover the cost of the stay (EUR 560).' That is wrong: 714 is more than 560. The judge (OLMo) does not catch this (it codes contradiction with the application in 0.1 per cent of reasons), because it does not do the arithmetic.\n"
    "Reading: the passport effect is carried by stated doubts that the application does not support. That is what a reviewer would see on the file, and why the reason field matters."),
    question="Would an officer notice a wrong sum?")
for i, (n, l) in enumerate((("42%", "of reasons for Somali applicants raise a doubt"), ("42%", "for Syrian applicants"), ("7%", "for Qatari and Omani applicants"))):
    text(s, 0.6 + i * 4.1, 1.7, 3.9, 1.5, n, 72, True, ORANGE if i < 2 else ACCENT, PP_ALIGN.CENTER)
    text(s, 0.6 + i * 4.1, 3.3, 3.9, 1.0, l, 20, False, MUTED, PP_ALIGN.CENTER)
text(s, 0.6, 4.6, 12.1, 1.4, "Same application, same funds (EUR 714 against EUR 560 needed).\nExample reason of Qwen2.5 7B: \"the funds are insufficient\".", 24, False, INK, PP_ALIGN.CENTER)

# 10 telling the model
def vrow(model, variant, block="4"):
    return next((r for r in table("by_variant") if r["model"] == model and r["variant"] == variant and r["block"] == block), None)


def vtxt(variant, block="4"):
    parts = []
    for m, label in MODELS:
        r = vrow(m, variant, block)
        if r:
            parts.append(f"{label} {float(r['range_rep1']):.1f} (chance {float(r['null_range_rep1']):.1f})")
    return "; ".join(parts)


s = slide("Does telling the model to ignore nationality help?", notes=(
    f"H3 (confirmatory): gap with the paragraph 'nationality is not a ground for a lower score' (block 2) minus the gap without it (block 1): Qwen {A['qwen3-32b']['h3']} points (p = {A['qwen3-32b']['p3']}), "
    f"Mistral {A['mistral-small-3.2-24b-instruct']['h3']} (p = {A['mistral-small-3.2-24b-instruct']['p3']}), Gemma {A['gemma-4-31b-it']['h3']} (p = {A['gemma-4-31b-it']['p3']}). None is significant: the instruction does not shrink the differences.\n"
    "Figure (exploratory, one repetition each, so the gaps are larger than the ones in block 1 with five repetitions; black ticks show the gap that shuffling the nationality labels gives, i.e. chance): "
    "Qwen and Gemma are above their chance tick in nearly every case; Mistral is close to chance in several (reasoning first, the paragraph in block 2, the boundary applicants) and above it in block 1 (3.7 against 2.6). For Qwen and Gemma the differences do not disappear under any of the twelve changes of the prompt.\n"
    f"regulation_text (word-for-word Article 32): {vtxt('regulation_text')}.\n"
    f"regulation_instruction (cite the ground by article number): {vtxt('regulation_instruction')}. It brings Gemma close to chance and does not help Qwen.\n"
    f"no_guidance: {vtxt('no_guidance')}. reasoning first: {vtxt('reasoning')}.\n"
    "Boundary applicants (blocks 5 and 6, exploratory extension D4): gaps 2.4 to 3.8 points over all repetitions; wealth order again for Qwen (rho -0.75) and Gemma (-0.69), not for Mistral (-0.20). "
    "No variant consistently removes the gap."),
    question="Is the gap in the model's knowledge, not in its instructions?")
if not picture(s, FIG / "variants.png", 0.6, 1.2, 12.1, 5.2):
    text(s, 1, 2.5, 11, 2, "variants pending", 28)

# 10b reasons
def pooled(block, code):
    out = {}
    for m, _ in MODELS:
        rows = [r for r in table("judged_by_country") if r["model"] == m and r["block"] == block]
        n = sum(int(r["n"]) for r in rows)
        out[m] = (sum(float(r[code]) * int(r["n"]) for r in rows) / n * 100) if n else float("nan")
    return out


nat, legal, doubt = pooled("1", "mentions_nationality"), pooled("1", "names_legal_ground"), pooled("5", "doubts_residence")
q, mi, g = "qwen3-32b", "mistral-small-3.2-24b-instruct", "gemma-4-31b-it"
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
s = slide("What do the reasons say?", notes=reasons_notes, question="The score moves with the passport. The reason never says so.")
for i, (m, label) in enumerate(MODELS):
    text(s, 0.6 + i * 4.1, 1.4, 3.9, 0.6, label, 22, True, INK, PP_ALIGN.CENTER)
    text(s, 0.6 + i * 4.1, 2.1, 3.9, 1.3, f"{nat[m]:.1f}%", 60, True, ORANGE, PP_ALIGN.CENTER)
    text(s, 0.6 + i * 4.1, 3.4, 3.9, 0.8, "of reasons name the passport", 18, False, MUTED, PP_ALIGN.CENTER)
    text(s, 0.6 + i * 4.1, 4.4, 3.9, 1.0, f"{legal[m]:.0f}%", 48, True, ACCENT, PP_ALIGN.CENTER)
    text(s, 0.6 + i * 4.1, 5.4, 3.9, 0.8, "rest on a ground of Article 32\nor an item of the application", 16, False, MUTED, PP_ALIGN.CENTER)

# 11 caveats and next steps
s = slide("What this does not show, and what comes next", notes=(
    "Not shown: prejudice, anything about real consulates, anything about Islam, or that Estonia uses a model. 30 invented applicants who all live in the Emirates; three open models of 24 to 32 billion parameters; scores near the ceiling; Mistral ignores the money rule; the judge is not validated yet.\n"
    "Next steps: (1) validate the judge on a hand-coded sample of 200 reasons (kappa of at least 0.7) and report which reasons rest on a ground of Article 32 and which on the passport; (2) variants and the judge by nationality; (3) the cost measures (savings a passport costs, fees lost per 1,000 identical applications); (4) check Articles 21, 22 and 25a; (5) write the report (due 08.01.2027)."))
for i, (t, b) in enumerate((("Limits", "invented applicants\nscores near the ceiling\nthe 9 extra models are exploratory\njudge not validated yet"),
                            ("Next", "validate the judge by hand\nwhat the reasons say\nwhat a gap costs an applicant"))):
    box(s, 0.6 + i * 6.3, 1.6, 5.9, 3.6, t, b, tsize=28, bsize=22)
text(s, 0.6, 5.7, 12, 0.8, "Thank you. Questions?", 30, True, ACCENT)

out = HERE / "midterm.pptx"
prs.save(out)
print("saved", out, len(prs.slides._sldIdLst), "slides")
