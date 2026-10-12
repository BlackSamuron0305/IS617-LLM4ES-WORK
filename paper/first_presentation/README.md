# First presentation: project pitch

**13.10.2026.** 5 minutes for each team + 5 minutes of Q&A. 5 points.

Criteria, copied from the course
[grading rubric](https://github.com/dess-mannheim/LLM4ESS/blob/main/grading_rubric.md)
(read 2026-10-04 at commit bb225c7 and again 2026-10-12 at commit df7bbbf; unchanged):

- [ ] Research question and motivation [4]
- [ ] Project timeline [1]

Not every member has to present, but all members should be prepared to answer questions.
Keep to the allocated time.

## Status (2026-10-10): slides for the visa design exist as a draft

The project moved from bank customer checks to visitor visa applications on 2026-10-10.
The Q&A notes for the bank design are in
`research/old_design/bank_2026-10-08/first_presentation/`; the slides and notes for the
hiring design are in `research/old_design/hiring_2026-10-04/first_presentation/`.

## Files

| file | what it is |
|---|---|
| `pitch_v8.pptx` | `pitch_v7.pptx` as saved on 2026-10-12 at 19:10, with four new slides and a new order (Laith, 2026-10-12): 11 slides and 17 backup slides. See "Four new slides" below |
| `pitch_v7.pptx` | `pitch_v6.pptx` with one change on slide 3, "And in language models? What research found" (Laith, 2026-10-12): the three figures (66%, 78%, -15%) are replaced by the titles of twelve published studies, to show that many researchers work on this. Each title is an image cut from the first page of the paper; a caption gives authors, venue and year. Nothing else differs from v6. See "Slide 3" below |
| `pitch_v6.pptx` | `pitch_v5.pptx` as the team had saved it on 2026-10-12 at 19:00 (25 slides, reordered by hand), with one change on slide 2, "August 2026: two searches on Google": a screenshot of Google's own post on X of 20 August 2026 (`google2026aioverviewpost`) under the news article, which is cropped to its headline. Nothing else differs from v5 |
| `pitch_v5.pptx` | **The version to present, built on 2026-10-12 at Laith's request.** 9 slides and 13 backup slides: `pitch_v4.pptx` with one new backup slide (13) on Australia and on what is planned elsewhere, corrected speaker notes on slides 11 and 12, and three more entries on the sources slide |
| `pitch_v4.pptx` | 9 slides and 12 backup slides, also of 2026-10-12: `pitch_v3.pptx` with a new first slide, the Google AI Overview case of August 2026 with a screenshot of a news article (Islam Channel, 27 August 2026; taken from the live page on 2026-10-12) |
| `pitch_v3.pptx` | 8 slides and 12 backup slides. It opens with society, the title comes fifth |
| `pitch_v2.pptx` | The first short version of the same day: 8 slides (the first is a silent title screen) and 11 backup slides. It opens with the published GPT-3 example |
| `pitch.pptx` | The long version: 13 slides (the first is a silent title screen) and 6 backup slides. Built by Claude Code on 2026-10-10 at Laith's request. All text and the chart can be edited in PowerPoint. The 22 flags on the title slide come from the open-source set flag-icons (version 7.5.0, MIT licence); the Syrian flag is the one in use since the change of government |
| `muslim_majority_map.png` | the map on slide 4: the 53 countries and territories with a Muslim majority in 2020, the 22 Arab League members darker (Pew Research Center, Religious Composition by Country 2010-2020; outlines from Natural Earth, public domain). Mayotte is a dot |
| `arab_league_wealth_map.png` | the map on slide 5: the 22 in the three groups rich, normal and poor (World Bank income classes, `experiment/countries/applicant_nationalities.csv`) |
| `arab_league_grant_rates_map.png` | the map on slide 8: the 22 Arab League countries, darker = a larger share of Australian visitor visa applications granted in 2019-20; hatched = too few cases (Department of Home Affairs; outlines from Natural Earth, public domain) |
| `qa_prep.md` | likely questions with the facts and where they come from |

## Four new slides (`pitch_v8.pptx`)

Order of the eleven slides in front (new ones in bold): 1 title, 2 Google, 3 twelve paper
titles, **4 "The papers we found compare one big group"**, **5 "Why Arabs? Two
reasons"**, **6 "What scenario is best?"**, 7 spot the difference, 8 Australia, 9 what we
ask, **10 "Our experimental setup"**, 11 timeline.

What moved: the second title page (old slide 6) is gone, slide 6 took its place. The two
slides that slide 5 sums up ("53 Muslim-majority countries are not one group", "Born in
the Gulf, still a foreigner") are now the first two backup slides, with their notes and
animations. Nothing else was touched.

| slide | content | what to know before saying it |
|---|---|---|
| 4 | left: the usual study compares one group (Muslim, Arab, Middle Eastern) with the others, with three examples; right: the 22 flags, "And inside the group?" | **Do not say that nobody has looked inside the group.** Of the twelve titles on slide 3, Keleg, Venkit et al., Nguyen et al. and Mao and Zhao do, in other tasks. Say "in the papers we found". No novelty claim |
| 5 | reason 1, less noise: the map, 53 to 22; reason 2, realistic: 6.9 million citizens of other Arab countries in Saudi Arabia and the Emirates, seven flags with the millions | "Diaspora" is Laith's word; the UN counts foreign citizens and does not say who was born there |
| 6 | hiring and medicine crossed out: name, religion and nationality can be removed before a model sees the text; visa: the nationality stays on the form | **Say "can be removed", not "is removed".** Many hiring pipelines do not remove the nationality (`research/scenario_reviews/nationality_line_pipeline_review.md`). **For medicine no source was read**: it is the team's reasoning |
| 10 | 20 applicants, 22 passports, 4 models, score 0 to 100; "still open": hypotheses and analysis plan, pilot, model settings; tag "needs refinement" | the open points are those of `experiment/README.md`, "Open" |

- The quote on slide 6 was read word for word on 2026-10-12 in the documentation of
  Presidio, an open-source redaction tool (list of supported entities): `NRP`, "A
  person's Nationality, religious or political group."; `PERSON`, "A full person name,
  which can include first names, middle names or initials, and last names." Presidio is
  not in `research/literature_matrix.csv` and not on the sources slide.
- Eleven slides are too many for five minutes at the pace of the earlier versions. Slides
  7 and 8 are the first candidates for the backup.
- The speaker notes of the four slides have the facts and the limits.

## Slide 3: twelve paper titles (`pitch_v7.pptx`)

- The twelve: Abid, Farooqi and Zou 2021; Hemmatian, Baltaji and Varshney 2023;
  Plaza-del-Arco et al. 2024; Saeed et al. 2024; Naous et al. 2024; Demidova et al.
  2024; Shieh et al. 2026; Lippens 2024; Keleg 2025; Venkit et al. 2023; Nguyen et al.
  2026; Mao and Zhao 2025. All are in `research/literature_matrix.csv`; eight were read
  in full, four as abstracts (Saeed, Naous, Keleg, Nguyen). The first pages were
  downloaded on 2026-10-12 from arXiv, the ACL Anthology and Nature, and the titles are
  shown as printed there. For Lippens the picture is the arXiv preprint.
- The speaker notes say in one line what each study found, and keep the facts behind the
  three figures that were on the slide before. `pitch_v6.pptx` still has the old slide.
- **Do not say that all twelve found the same thing.** Demidova et al. and Mao and Zhao
  report mixed results.
- **Be careful with "huge".** Bias in language models is a large field. Religion and
  nationality are the smaller part of it: one review of 189 papers found gender in
  79.9%, religion in 19.1% and nationality in 13.2% (`ghosh2025bias`, abstract and first
  pages read). That smaller part is the gap the project works in, so "many studies, but
  few on nationality" is the line that fits both the slide and the proposal.
- Twelve is a selection from the team's list, not a count of the field.

## Google's post on slide 2 (`pitch_v6.pptx`)

- The screenshot shows the post itself, taken on 2026-10-12 from X's embed view. The
  text was also read directly from X. The time on it is Central European time.
- The picture attached to the post (a search for "i'm alone with an american" with a
  harmless answer) is switched off in the screenshot so that the text can be read.
- The post is a reply to another user, not to the post about the search for a Muslim.
  Google wrote about "these types of searches" in general and said the warnings
  "aren't unique to any one group". Do not say that Google apologised to Muslims.
- The same sentences went out three minutes earlier as a reply to Donald Trump Jr., with
  a search for "i'm alone with a christian". That post is not on the slide.
- The speaker notes of slide 2 have the links.

## The version to present (`pitch_v5.pptx`)

The nine spoken slides are those of `pitch_v4.pptx` (next section), unchanged. What is
new is in the backup, after Laith asked on 2026-10-12 whether countries really use AI to
rate visa applicants:

| slide | content |
|---|---|
| 11 | the pointer to the next slides now names Australia |
| 12 | "Machines already sort visa applicants" (United Kingdom, Netherlands, Canada): slide unchanged, speaker notes corrected |
| 13 | **new:** "And Australia, our destination?" The department's own words: machine learning is used to "predict risk in visa programs", and it "does not use machine learning to make administrative decisions". Beside it what is planned: the EU travel authorisation, the German bill, South Africa |
| 22 | sources: the Australian release on AI use, the EU regulation, the Bundestag page and the South African press report added |

Slide 13 is a backup slide. To say it in the talk, move it up and take the time from
another slide; the five minutes are full.

What was checked (2026-10-12), and how to say it:

- **True:** several countries let software sort or rate visa applicants. In use: the
  Netherlands, Canada and Australia; the United Kingdom until 2020. Planned: the EU
  travel authorisation, Germany, South Africa.
- **Say "AI" only where the source does.** Machine learning is named for Australia
  (`homeaffairs2024foi`) and for a US pilot that scores cases already decided
  (`state2026aiinventory`). Canada speaks of "advanced analytics". The British tool was
  a decision tree and the Dutch one is rules written by officials.
- **Not true:** that a visa office lets a language model rate or decide applications.
  None was found. Canada says it does not allow generative AI in support of decisions
  (`ircc2025qpnote`); one press report speaks against that for a residence case
  (`jagannathan2026human`, secondary, the original article was not read).
- **Do not say "Australia rates every applicant with AI".** The document says machine
  learning is used to "predict risk in visa programs" and not for decisions. It does not
  say what goes into the prediction, whether nationality does, or whether each
  application gets a rating.
- Every quote on slides 12 and 13 was compared with the document or page itself. The
  exact wording and how far each source was read: `research/literature_matrix.csv`, and
  the note "exact wording behind step 8" in `paper/final_paper/paper.pdf`.

## The fourth version (`pitch_v4.pptx`)

`pitch_v3.pptx` (next section) with one slide in front, so every other slide moves down
by one. Nine slides, about 5:00: 25 seconds for the new slide, and take a few seconds
off slides 2 to 5.

| slide | content | rubric | seconds |
|---|---|---|---|
| 1 | August 2026, two searches on Google: for "am alone with a Muslim" the AI Overview advised to leave the area or call 911; for "I am alone with a Brit" it suggested a cup of tea. With a screenshot of a news article and Google's own statement | motivation | 25 |

What was checked (2026-10-12), and how to say it:

- It is real. It was reported by several outlets (`islamchannel2026aioverview`),
  reproduced by a search researcher (`mitra2026reflections`) and acknowledged by Google.
- It was the **AI Overview in Google Search**, not the Gemini chat app. Say "Google's
  AI Overview".
- It was **not only about Muslims**. The same kind of warning came for searches about
  being alone with an African, an Indian or a Pakistani; harmless answers came for a
  Brit, an American or a Haitian (`futurism2026googleai`). Google said the warnings
  "aren't unique to any one group". Do not present it as proof of anti-Muslim bias
  alone; present it as: one word changed, a different answer.
- All three sources were read through a summarising tool. Compare the sentence on the
  slide with the original screenshot before the pitch.

## The third version (`pitch_v3.pptx`)

The order is Laith's (2026-10-12): society first; then what the research on language
models found; then from the 53 Muslim-majority countries to the 22 and why, with why
the applicant is realistic; then the title, said aloud; then the scenario, the questions
and the timeline.

| slide | content | rubric | seconds |
|---|---|---|---|
| 1 | Islamophobia in society: 47% of Muslims in the EU report racial discrimination (39% in 2016); 3,080 anti-Muslim incidents in Germany in 2024 | motivation | 30 |
| 2 | and in language models, what research found: 66% violent endings (GPT-3), 78% fewer Middle Eastern names in stories (five chat models), the same CV passes 15% less often with an Arab name (GPT-3.5) | motivation | 40 |
| 3 | 53 Muslim-majority countries are not one group: a map, and the step to the 22 | motivation | 40 |
| 4 | born in the Gulf, still a foreigner: why the applicant is realistic | motivation | 40 |
| 5 | title, with the flags of the 22 Arab League countries | | 10 |
| 6 | spot the difference: two applications, one line differs; a visa form asks for the passport, not the religion; the official rules are the same for both | research question | 45 |
| 7 | what we ask: (1) do the 22 differ, country by country; (2) separately, rich, normal, poor; one line on how | research question | 55 |
| 8 | timeline | timeline | 30 |
| backup | the published GPT-3 example ("Two Muslims walked into a ..."), then the backup of the short version below | Q&A | |

That is 4:50. The first slide does not show the names or the course: say them at the
start. The slide with society and the three model figures side by side, which the other
versions have, is not in this one.

## The first short version (`pitch_v2.pptx`)

The course asks for two things in five minutes: research question and motivation [4]
and a timeline [1]. The long version had twelve spoken slides. The short one has seven;
everything else is in the backup for the questions.

| slide | content | rubric | seconds |
|---|---|---|---|
| 1 | title, with the flags of the 22 Arab League countries: on screen before the talk starts, nothing is said | | 0 |
| 2 | the way in: a language model finishes "Two Muslims walked into a ..." (66 of 100 endings violent) | motivation | 30 |
| 3 | Islamophobia in society and in language models: five numbers | motivation | 40 |
| 4 | 53 Muslim-majority countries are not one group: a map, and the step to the 22 | motivation | 40 |
| 5 | born in the Gulf, still a foreigner: why the applicant is realistic | motivation | 45 |
| 6 | spot the difference: two applications, one line differs; a visa form asks for the passport, not the religion; the official rules are the same for both | research question | 45 |
| 7 | what we ask: (1) do the 22 differ, country by country; (2) separately, rich, normal, poor; one line on how | research question | 60 |
| 8 | timeline | timeline | 30 |
| backup | from the long version: the visa form, machines that sort applicants, same rules and real grant rates, the map of the three groups, how we measure it; then the 26 passports, run plan, what the model is told, the official rules, scope and limits, sources | Q&A | |

That is 4:50. If it runs long, shorten slide 3.

Question 1 compares the single countries (Laith, 2026-10-12): every one of the 22 gets
its own rating and they are compared with one another. The three groups are a second,
separate question and not the way the countries are compared. The question marks under
the flags on slide 7 are placeholders; there are no results.

## The slides of the long version (`pitch.pptx`)

Few words, many pictures and numbers, a question on most slides. The facts and sources
for each slide are in its speaker notes ("FACTS, NOT A SCRIPT").

| slide | content | rubric | seconds |
|---|---|---|---|
| 1 | title, with the flags of the 22 Arab League countries: on screen before the talk starts, nothing is said | | 0 |
| 2 | the way in: a language model finishes "Two Muslims walked into a ..." (three published endings, 66 of 100 violent) | motivation | 20 |
| 3 | Islamophobia in society (47% of Muslims in the EU, 3,080 incidents in Germany) and in language models: 23% "Muslim" to "terrorist" (GPT-3), 78% fewer Middle Eastern names in stories (five chat models), the same CV passes 15% less often with an Arab name (GPT-3.5) | motivation | 30 |
| 4 | 53 Muslim-majority countries are not one group: a map, and the step to the 22 Arab League countries | motivation | 25 |
| 5 | one label, 22 very different countries: a map of the rich, normal and poor group, what differs and what they share | motivation | 25 |
| 6 | the realistic setting: a visa form asks for the passport, not the religion; three reasons for a visa | motivation | 15 |
| 7 | machines already sort visa applicants: United Kingdom, Netherlands, Canada | motivation | 20 |
| 8 | same rules for all 22, very different outcomes: the rules, a map and a chart of real grant rates | motivation | 30 |
| 9 | born in the Gulf, still a foreigner: 6.9 million citizens of other Arab countries live in Saudi Arabia and the Emirates; birth there gives no passport; some of the 22 allow one passport only, some do not let a citizen go | motivation | 25 |
| 10 | spot the difference: an Emirati and a Syrian application, both born in Dubai, one line differs | research question | 30 |
| 11 | what we ask: is there a bias, and do the models sort the 22 into rich, normal and poor (the flags in three rows) | research question | 30 |
| 12 | how we measure it, and what a passport costs | research question | 30 |
| 13 | timeline | timeline | 20 |
| backup | the 26 passports, run plan, what the model is told, what the official rules say about the 22, scope and limits, sources | Q&A | |

That is 5:00 for twelve spoken slides, 25 seconds each, which is very tight. Slide 7 is
the first to move to the backup if rehearsal runs long, then slide 6.

The order is Laith's (2026-10-10): the title is only a screen before the start; then an
example to get attention; then Islamophobia as a problem of society that also shows in
language models, with numbers from published studies; then the Muslim-majority countries
are not all the same, so the project takes the Arab ones to reduce noise; then the 22
differ too; then the realistic setting, a visa application. The slide on machines that
sort applicants and the visa form come after that, not before. Slide 9 was added the
same day, also at Laith's request: why applicants who were born in the Gulf with another
Arab passport are realistic.

## Framing

The same line of argument as `paper/proposal/proposal.tex`:

- The motivation is Islamophobia. The first spoken slide is one published example of a
  language model writing violent endings for a sentence about Muslims (Abid, Farooqi and
  Zou 2021, Figure 1; read in the paper). Say that this is text a model wrote, quoted to
  show the problem.
- It is a problem of society, and language models show it too. The three model figures
  on slide 3 come from three published studies that were read in full (`abid2021persistent`,
  `shieh2026intersectional`, `lippens2024computer`). Two of them are about Middle Eastern
  or Arab names, not about religion; say so if asked.
- All Muslim-majority countries together are too mixed (53 countries and territories on
  three continents), so the project takes the 22 Arab League countries: one language,
  one label. About one in five of the world's Muslims lives in them.
- The 22 differ too: six rich, twelve normal and four poor countries.
- A visa application is the realistic setting: the form has no field for religion, it
  has a passport, and the nationality cannot be left out.
- The project is about LLM bias among these 22, with two questions: is there a bias,
  and can the countries be grouped into rich, normal and poor (World Bank income
  classes, fixed before any run). It does not compare Arab with non-Arab countries and
  it does not look at how strong a passport is.
- The yardstick is the official rules. For the Australian visitor visa they are the same
  for all 22: same visa, same form, same fee, same legal test, no ban.
- The person is held fixed: born, raised and working in the United Arab Emirates, the
  most realistic place to grow up with one of these passports without becoming a
  citizen. Every application states the same legal status.
- Why that is realistic (slide 9): about 6.9 million citizens of other Arab League
  countries live in Saudi Arabia and the Emirates (`undesa2024migrantstock`, data file
  read); birth in the Emirates gives no citizenship (`uae1972nationality`, abstract);
  and the passport of the origin stays: on 1 January 2020 four of the 21 coded countries
  took the citizenship away from anybody who took another one, and four did not let a
  citizen give it up (`vink2020macimide`, data file read). Do not say that becoming a
  citizen is impossible: the law of the Emirates allows it on paper after seven years
  for Arabs.
- So the one question is: same application, same rules, one applicant Syrian and one
  Emirati. Why should the answer differ?
- Real offices do grant these nationalities at very different rates (slide 8). Those are
  real people in different circumstances. Say that this may explain a bias and does not
  justify it.
- Say plainly: a passport is not a religion.
- Do not say that visa offices let language models decide or rate. None is documented as
  doing so. What can be said: several countries let software sort or rate visa
  applicants, and Australia uses machine learning to "predict risk in visa programs"
  (see "The version to present").

## To do before 13.10

- [ ] Decide as a team that the visa design is the project (Laith asked for the change
      on 2026-10-10).
- [ ] Go through the slides and put every sentence into the team's own words (see "AI
      use" below).
- [ ] Check every number against its source. Read only through a summarising tool:
      the 47% (EU Agency for Fundamental Rights) and "almost 9 in 10 residents of the
      UAE are foreigners" (official figures as reported by a newspaper in 2011; newer
      estimates are similar). The Dutch 3.5% and 33% (Lighthouse Reports) were checked
      on the page itself on 2026-10-12.
- [ ] Slide 3: read in the paper how Lippens (2024) defines the "discrimination ratio"
      of 0.85 before saying "15% less often". The slide's "-15%" is a rewording of that
      ratio.
- [ ] Slides 4 and 5: "one language" (Arabic is an official language in all 22) has no
      source in the literature matrix. Check it or drop the words.
- [ ] Slide 9: the citizenship rules are those of 1 January 2020. Mauritania is left off
      because it is reported to permit a second citizenship since 2021. Check the other
      seven countries on the slide against the GLOBALCIT Citizenship Law Dataset,
      version 3.0 (laws up to 2024; https://hdl.handle.net/1814/73190), which could not
      be downloaded here.
- [ ] Check the Australian legislation register for a new travel suspension by
      nationality (`experiment/countries/README.md`).
- [ ] Agree on the timeline. Only the four course dates are fixed.
- [ ] Decide the points marked "Open" in `qa_prep.md`, or agree to say they are open.
- [ ] Decide who presents and rehearse to 5:00.

## AI use

The course policy says that presentation text is written by the team. This deck was
built by Claude Code, including its wording. Either rewrite the wording, or keep it and
declare it; in both cases list the deck in the declaration of AI use
(`paper/final_paper/paper.tex`, "Use of AI Tools").
