# Motivation and cost of bias: visa scenario (internal research note)

Written on 2026-10-10 by Claude at Laith's request. Internal research note, **not report
text and not slide text**. Nothing here is in `research/literature_matrix.csv` or
`research/references.bib` yet; the BibTeX block at the end is a proposal.

**How far each source was read.** The words used below and in the source table:

| word | meaning | matrix level it would get |
|---|---|---|
| **full text** | I read the text of the document or data file itself (PDF text or data file downloaded and searched locally) | fulltext |
| **page** | Official or publisher page read through a summarising fetch tool. Quotes must be re-checked against the original before they go anywhere | abstract |
| **abstract** | Abstract or repository record only, through the same tool | abstract |
| **snippet** | Search-result snippet or a secondary summary only | metadata |
| **own calculation** | A number I computed from an official data file. It is not a published figure | (none) |

Limits: one working session, about 90 searches and page reads. No systematic database
search. **No novelty claim is made anywhere in this note.**

---

## 1. Short answer

**Motivation.** There are solid, recent, official numbers on anti-Muslim discrimination
for the EU, Germany and the UK (section 3). They are about *Muslims*. Our experiment
changes a *nationality*. The link between the two has to be argued, and one experiment
found that people in the US penalise the label "Muslim" but not the label "Arab"
(section 3.3). The safe wording is "an Arab nationality is a noisy signal for Muslim",
not "Arab means Muslim".

**Real visas.** The 22 Arab League nationalities are treated very differently by real
visa systems. US visitor-visa refusal in 2025 runs from 2% (UAE) to 84% (Somalia). This
is by nationality and from the State Department itself (section 5.1). It is the best
single fact for the "one Arab category hides a lot" argument.

**LLM literature.** Strong anti-Muslim results exist for text generation. For decisions
with an explicit label, results are small, absent or reversed. One LLM study covers
immigration decisions with a few Arab countries. The best-known LLM decision audit
(Anthropic's) contains visa scenarios but never varies nationality or religion; I
checked this in the dataset (section 4.2).

**Money figure.** Three methods exist. The one that fits our outcomes best is the
"compensating amount": how many euros of extra savings an applicant of nationality X
needs to get the same risk score as the reference applicant. A published LLM audit does
exactly this with credit-score points and then turns it into dollars. Our applicant
files already have a savings ladder (section 6).

---

## 2. What the team already has that still helps

Checked against `literature_matrix.csv` (206 rows) and `references.bib`. Keys as in the
matrix. Level in brackets is the level recorded there.

**Anti-Muslim and anti-Arab bias in LLMs**

- `abid2021persistent` (fulltext): the classic. 66 of 100 GPT-3 completions of "Two
  Muslims walked into a" were violent; "Muslim" mapped to "terrorist" in 23% of
  analogies. Still the right opening citation.
- `hemmatian2023muslim` (fulltext): the effect became weak for the explicit label in
  later GPT models and stayed stronger for Muslim names. Important for us: an explicit
  label can show less than a name.
- `naous2024beer` (abstract): models prefer Western entities in Arabic contexts. About
  culture, not decisions.
- `saeed2024desert`, `saeed2026surfacing`, `shieh2026intersectional`,
  `plazadelarco2024divine`, `khorramrouz2026characterizing`, `arif2026grain`,
  `keleg2025arabs`: background for "LLMs treat Arabs and Muslims as one group, and
  sometimes over-protect them".
- `mohammad2026mirage`: **still do not cite its numbers** (the matrix says the results
  are placeholders). Search engines now repeat its "9 to 22 percentage points" as if it
  were a finding.

**Nationality in LLM outputs and decisions**

- `mao2025gatekeepers` (fulltext): the closest study. GPT-3.5 and GPT-4 choose between
  two immigrants; Iraq, Sudan and Somalia are among the origins; most country effects
  not significant.
- `venkit2023nationality` (fulltext): Libya, Sudan and Tunisia are among the five most
  negatively described demonyms. Supports "the 22 are not treated alike".
- `manvi2024geographic`, `kamruzzaman2024nation`, `kamruzzaman2024subtler`,
  `salinas2023unequal`, `nguyen2026representational`: models rate poorer countries
  lower. Supports the wealth hypothesis.
- `ghosh2025bias` (abstract): of LLM bias papers, 19.1% study religion and 13.2%
  nationality, against 79.9% for gender. Good one-line gap statement.

**Decision audits whose design we copy**

- `tamkin2023evaluating` (fulltext): now more useful than before, see section 4.2.
- `bowen2025measuring` (fulltext): one explicit line swapped, numeric outcome, a
  no-bias instruction, **and a money translation** (section 6.3).
- `vohra2026audit`, `gaebler2024auditing`, `karvonen2025robustly`,
  `arcuschin2026blind`, `bai2025explicitly`, `lippens2024computer`.

**Method**

- `sclar2024quantifying`, `rottger2024political` (wording), `miller2024adding`,
  `atil2024nondeterminism` (repeats and error bars), `needham2025large` (models notice
  tests), `kline2024discrimination` (ranking many groups with noisy estimates),
  `tonneau2026cues`, `chen2026competence`.

**Human evidence that carries over**

- `distasio2021muslim` (fulltext): "Muslim by default". People from Muslim-majority
  countries are penalised even without a religious signal. This is the main support
  for using nationality when the motivation is Islamophobia.
- `distasio2024same`, `bansak2016economic`, `hainmueller2015hidden`,
  `thijssen2022discrimination`, `bartkoski2018meta`, `maghbouleh2022middle`,
  `omb2024revisions`, `mathews2017national`, `arai2016reverse`,
  `valfort2015discriminations`.
- `bansak2016economic` is double-edged: Muslim asylum seekers were about 11 points
  less accepted, while country of origin moved acceptance by at most 4 points.

**No longer useful for the visa topic:** the `banking_aml` legal texts and vendor
pages, the Gulf labour-market studies, and most of the hiring-only entries.

---

## 3. Islamophobia as motivation

### 3.1 Numbers that could go on a slide

| # | statement | year | source | read |
|---|---|---|---|---|
| 1 | 47% of Muslims in 13 EU countries experienced racial discrimination in the five years before the survey, up from 39% in 2016 | survey Oct 2021 to Oct 2022, published 24 Oct 2024 | EU Fundamental Rights Agency, *Being Muslim in the EU* | page (press release and report page) |
| 2 | Highest rates: Austria 71%, Germany 68%, Finland 63% | same | same | page |
| 3 | When looking for work 39% (2016: 31%); when looking for housing 35% (2016: 22%) | same | same | page |
| 4 | Women wearing religious clothing: 45% discriminated when looking for work, against 31% of women who do not | same | same | page |
| 5 | Germany: 3,080 anti-Muslim incidents documented in 2024, 60% more than in 2023 (1,926), more than 8 a day | 2024, published June 2025 | CLAIM, *Zivilgesellschaftliches Lagebild antimuslimischer Rassismus*, short summary | full text |
| 6 | Germany 2024: 2 killings, 198 bodily injuries, 67 attacks on mosques; women affected in 71% of cases with known gender | same | same | full text |
| 7 | Germany: 4,096 incidents documented for 2025; 214 bodily injuries; 61 attacks on mosques | 2025, reported 24 June 2026 | CLAIM figures as reported by *taz* | page (press only; the CLAIM report was not opened) |
| 8 | Germany, police count: 1,848 Islamophobic offences in 2024; 1,543 in 2025 (preliminary) | 2024, 2025 | Federal Criminal Police figures as quoted in Bundestag printed paper 21/6530 of 16 June 2026 | full text of the Bundestag paper; the ministry's own table was not opened |
| 9 | England and Wales: 5,132 religious hate crimes targeted at Muslims, 46% of all religious hate crime, up 15% from 4,479 | year ending March 2026, published 8 Oct 2026 | Home Office, *Hate crime, England and Wales* | page |
| 10 | UK: 6,313 reports of anti-Muslim hate in 2024 (5,837 verified), up from 4,406 (3,767) in 2023; the most since counting began in 2012 | 2024, reported 19 Feb 2025 | Tell MAMA, via AFP | page (press) |
| 11 | US: 8,683 complaints of anti-Muslim and anti-Arab discrimination in 2025, the most since the series began in 1996 | 2025, reported 10 March 2026 | CAIR civil rights report, via Al Jazeera | page (press). The 2024 figure 8,658 is from a snippet |

### 3.2 What has to be said with these numbers

- **FRA counts "racial discrimination".** Its definition covers skin colour, ethnic or
  immigrant background and religion together. It is not a count of religious
  discrimination alone. The fieldwork ended before 7 October 2023.
- **The FRA sample is defined by origin.** Respondents were born in, or have a parent
  from, North Africa, sub-Saharan Africa, Syria or Türkiye, and then said they are
  Muslim. So the survey itself reaches Muslims through their country of origin.
- **CLAIM's rise is partly a rise in counting.** The number of reporting centres went
  from 10 (2022) to 17 (2023) to 26 (2024). The summary prints this under its chart and
  does not adjust for it. Incident totals: 898, 1,926, 3,080.
- **Police and civil-society counts differ a lot** (1,848 against 3,080 for 2024). They
  count different things: recorded offences against reported incidents.
- **The 2025 police figure is lower than 2024** (1,543 against 1,848) and still
  preliminary. Do not say "police figures keep rising".
- **UK rates per head.** The same Home Office bulletin gives 13 religious hate crimes
  per 10,000 Muslims and 117 per 10,000 Jewish people. A slide that shows only the 46%
  share will be challenged on this.
- **CAIR and Tell MAMA are advocacy organisations** that count complaints sent to them.
- **One figure I advise against:** "about half of people in Germany agree with
  anti-Muslim statements" (independent expert group on hostility towards Muslims,
  2023). I have it from press summaries only, and the interior ministry withdrew the
  report in March 2024 before a revised version appeared. Snippet level.

### 3.3 Are "Arab" and "Muslim" mixed up?

**In how the data are collected: yes, visibly.**

- CLAIM defines its subject as racism against Muslims "und auch gegen all jene
  Menschen, die als Muslim*innen gelesen werden – bspw. aufgrund äußerlicher Merkmale,
  der Sprache oder des Namens", and adds that people are hit "unabhängig davon, ob eine
  Religionszugehörigkeit besteht" (full text).
- The Home Office counts the "perceived religion targeted by the offender", not the
  victim's actual religion (page).
- CAIR reports "anti-Muslim and anti-Arab" complaints as one number (snippet).
- FRA finds its Muslim respondents through origin countries (page).
- Already in the matrix: `omb2024revisions` (the US had no separate category for people
  of Middle Eastern or North African origin until 2024) and `maghbouleh2022middle`
  (a Muslim cue adds 8 to 11 points to being classed as Middle Eastern or North
  African).

**In the population: the two groups overlap only partly.**

- 62% of the world's Muslims live in the Asia-Pacific region and 20% in the Middle East
  and North Africa (Pew Research Center, 2010 data; snippet).
- Germany: 5.3 to 5.6 million Muslims with a migration background; 45% have a Turkish
  background, Syria is second with 13% (Federal Office for Migration and Refugees,
  *Muslim Life in Germany 2020*; page). So most Muslims in Germany are not Arab.
- Arab Americans are often said to be mostly Christian (63% Christian, 24% Muslim,
  attributed to the Arab American Institute). **Not verified**: secondary sources only,
  based on an old survey, and the Muslim share is disputed.

**In people's minds: the evidence is mixed, and this matters for our design.**

- For conflation: `distasio2021muslim` (employers penalise origin from a
  Muslim-majority country even with no religious signal).
- Against conflation: Calfano, Lajevardi and Michelson (2021), a survey experiment in
  Ohio, California and Michigan. A community leader was rated less trustworthy when
  called "Muslim American" or "Arab Muslim", **but not when called only "Arab"**. The
  authors conclude that the public does not conflate the two and that the penalty
  attaches to "Muslim" (abstract).
- `bansak2016economic` points the same way: religion mattered far more than country.

**What follows.** A nationality line may trigger less than a religion line would. If
the models show little, that is one of the first explanations a reviewer will offer.
The design tests nationality, not religion, and the pitch should say so.

---

## 4. Anti-Muslim, anti-Arab and nationality bias in LLMs

### 4.1 The two papers named in the task

| paper | venue | method | finding | read |
|---|---|---|---|---|
| Abid, Farooqi and Zou 2021, *Persistent Anti-Muslim Bias in Large Language Models* | AIES 2021 | GPT-3: sentence completion, analogies, story generation | 66 of 100 completions of "Two Muslims walked into a" violent; "Muslim" to "terrorist" in 23% of analogies, "Jewish" to "money" in 5%; six positive adjectives lower the violent share from 66% to 20%, still above other religions | in matrix as fulltext; abstract re-read today |
| Naous, Ryan, Ritter and Xu 2024, *Having Beer after Prayer?* | ACL 2024 | CAMeL: 628 prompts, 20,368 entities of 8 types, 16 models; story generation, entity recognition, sentiment, text infilling | Models favour Western entities even in Arabic prompts; common Arabic training text such as Wikipedia may not suit culturally aware models | abstract |

Neither is about decisions on people.

### 4.2 Decision tasks: what exists

| study | task | what was varied | result | read |
|---|---|---|---|---|
| `mao2025gatekeepers` (Mao and Zhao 2025, arXiv) | US immigration officer chooses between two applicants; 10,000 choice sets; GPT-3.5, GPT-4 | Country of origin among other attributes; includes Iraq, Sudan, Somalia | Most country effects not significant; in follow-up interviews the models still suggest "additional scrutiny" for Iraq, Sudan, Somalia | in matrix as fulltext |
| `tamkin2023evaluating` (Tamkin et al. 2023, arXiv, Anthropic) | 70 yes-or-no decisions | Age, gender, race. **Not nationality, not religion** | Effects favour women and non-white groups; a "discrimination is illegal" instruction removes most of it | in matrix as fulltext. **New today:** I downloaded the public dataset (`explicit.jsonl`, 9,450 rows) and found a work-visa scenario (question 4), a two-week visitor visa to see a relative (74), a passport application (8), two entry decisions at the border (31, 61) and two security clearances (5, 59) |
| `bowen2025measuring` (Bowen et al. 2025, working paper) | Mortgage approval and interest rate | One `Race:` line | Approval 8.5 points lower, rate 35 basis points higher for Black applicants; a no-bias sentence removes the approval gap | full text, re-read today for the money translation (section 6.3) |
| `arcuschin2026blind` (ICML 2026) | Loans, hiring, admissions | Among others, an explicit religion | GPT-3.5 loan approval: Muslim slightly *above* Jewish (+0.057) and Buddhist (+0.042) | in matrix as fulltext |
| `bai2025explicitly` (PNAS 2025) | Job assignment | Names | GPT-4 more likely to give lower-status jobs to applicants with Arabic or Muslim names, among others | in matrix as abstract |
| `vohra2026audit` (workshop paper 2026) | Hiring, lending, medical triage | Names (race) | None of 36 contrasts survives correction; the format of the audit moves results as much as the group does | in matrix as fulltext |
| **New:** Liu, Wang, Cheng and Kurohashi 2025, *Assessing Agentic Large Language Models in Multilingual National Bias*, Findings of ACL 2025 | Scored advice on university applications, **travel** and relocation, in several languages | Country and language | "Local language bias is prevalent"; GPT-4 and Sonnet reduce bias for English-speaking countries compared with GPT-3.5 but not across languages. No numbers in the abstract | abstract |
| **New:** Toles et al. 2026, *MortarBench*, arXiv | Mortgage-agent tasks | Names | "systematic biases in LLM perception of foreignness related to non-English names". The figure for Arabic names quoted in `scenario_alternatives_review.md` is not in the abstract: **not verified** | abstract |
| **New:** Arzaghi, Carichon and Farnadi 2024, arXiv | One million sentences on socioeconomic status; GPT-2, Llama 2, Falcon | Demographic attributes and names | Socioeconomic bias in all models, stronger for combined attributes. The abstract names visa applications as a use where this would matter | abstract |

### 4.3 What the pattern looks like

- Text generation: clear anti-Muslim and anti-Arab content, weaker in newer models.
- Decisions with an explicit group label: small, absent or reversed effects, and very
  dependent on the format.
- Poorer countries are described and rated worse.

For our design this means: expect small effects, test in both directions, and treat a
gradient by wealth or passport strength as the more likely finding than a flat "Arab
penalty".

### 4.4 What I did not find

In about ten targeted searches I found **no LLM study that varies nationality or
religion in a visa decision**, apart from Mao and Zhao. I also found no LLM decision
audit with many individual Arab nationalities. This is the outcome of a short search.
It is not a novelty claim and must not be written as one.

---

## 5. Real visa decisions and nationality

### 5.1 Official refusal figures for the 22 nationalities

**United States, visitor visas (B), fiscal year 2025, by nationality.** State
Department table "Adjusted Refusal Rate – B-Visas Only by Nationality" (full text; I
downloaded the PDF and extracted all 199 rows).

| nationality | refused | nationality | refused |
|---|---|---|---|
| United Arab Emirates | 2.17% | Iraq | 39.86% |
| Oman | 3.14% | Egypt | 47.61% |
| Saudi Arabia | 5.98% | Syria | 50.69% |
| Kuwait | 6.06% | Algeria | 51.23% |
| Qatar | 9.69% | Jordan | 56.63% |
| Bahrain | 24.01% | Palestinian Authority travel document | 60.26% |
| Tunisia | 25.89% | Djibouti | 61.47% |
| Morocco | 26.91% | Sudan | 63.26% |
| Comoros | 30.19% | Mauritania | 67.61% |
| Libya | 31.78% | Yemen | 67.98% |
| Lebanon | 39.42% | Somalia | 83.52% |

For comparison, same table: Germany 12.22%, Turkey 22.25%, Indonesia 26.69%, Pakistan
52.32%, Nigeria 57.00%, Iran 62.44%. The middle value of all 199 listed nationalities
is 31.78% (own calculation).

Cautions: the German row is probably a small and unusual group, since most Germans
travel to the US without a visa (general knowledge, not checked in this pass). The year
includes the months after the entry ban of June 2025 for Libya, Somalia, Sudan and
Yemen. The table gives rates only, no counts.

**Schengen short-stay visas, 2025, by country where the consulate is.** European
Commission file "Visa statistics for consulates 2025" (full text of the data file; the
rates are the Commission's own "not issued rate" from the sheet of totals by country).

| consulates in | not issued | consulates in | not issued |
|---|---|---|---|
| Saudi Arabia | 5.2% | Jordan | 21.4% |
| Kuwait | 5.7% | Egypt | 24.2% |
| Oman | 10.5% | United Arab Emirates | 24.2% |
| Bahrain | 10.7% | Syria | 27.1% |
| Qatar | 15.1% | Algeria | 31.3% |
| Libya | 15.6% | Djibouti | 32.4% |
| Palestinian Authority | 16.7% | Iraq | 34.3% |
| Lebanon | 17.3% | Mauritania | 37.0% |
| Morocco | 19.2% | Comoros | 55.0% |
| Tunisia | 19.6% | | |

All consulates worldwide: 12,201,026 applications, 1,768,605 not issued, 14.6%. Türkiye
14.6%. In 2024: 11,716,723 applications, 14.8% not issued, Algeria 35.0%, Comoros 62.8%.
No rows for Somalia, Sudan and Yemen in 2025.

Cautions: **this is by place of application, not by nationality.** People living in the
Gulf who are not Gulf citizens apply there. For the United Arab Emirates, Maru (2025)
writes that over 90% of the refusals concern residents who are not Emirati (page). So
the Gulf rows say little about Gulf citizens. Syria has only 3,216 applications.

German consulates only, 2025 (own calculation from the same file): Kuwait 5.1%, Oman
6.4%, Saudi Arabia 8.0%, Qatar 10.9%, Tunisia 16.1%, Egypt 20.7%, Morocco 25.8%,
Algeria 34.0%, Iraq 36.9%, Jordan 38.6%, Lebanon 38.6%, Mauritania 48.9%; Türkiye 21.2%.

**Australia, the country of our scenario.** Department of Home Affairs, *Visitor visa
program report, 30 June 2025* (full text of the grant-rate section).

- Tourist stream of the Visitor visa (subclass 600): 79.4% granted in April to June
  2025, so about one in five refused.
- The two electronic products open only to certain passports: 98.6% (eVisitor) and
  98.3% (ETA) granted.
- By citizenship the report lists only the 15 largest countries. No Arab country is in
  the tourist table. In the family-sponsored stream Lebanon is listed with 23.9%
  granted (13.7% in the quarter before), against 52.7% for all countries.
- "Other countries" in the tourist table: 69.7% granted.
- I found no official refusal table for all nationalities. A migration company (Tern
  Visa) says it holds such figures from freedom-of-information requests but publishes
  no numbers for Arab countries (page; company source).
- Fee: AUD 200 until 30 June 2026, AUD 250 from 1 July 2026 for the tourist stream
  applied for outside Australia, not refunded on refusal (migration-law firm citing the
  department's price list; the official page returned an error, so **page level from a
  secondary source**).
- **To check before the design is fixed:** third-party pages say the free eVisitor is
  for European passports. If so, a German citizen would not apply for subclass 600, and
  the German benchmark file is less realistic than the others. Not verified on the
  official page.

### 5.2 Studies: is it the applicant or the passport?

| study | data and method | finding | read |
|---|---|---|---|
| Thomas and Lowe 2025, *Global Inequalities in US Visa Rejections*, International Migration Review | US visitor visas 2006 to 2021 (journal title) or 2022 (seminar abstract); mixed-effects regressions on country-year refusal rates | Refusal rates in Africa more than double those in Europe; the gap is not explained by social, economic and demographic differences; rates are lower with higher income per head and foreign investment | abstract of the 2024 seminar version (Duke). The journal page was blocked; a coefficient quoted by a search engine is not verified |
| Maggio and Tomasiewicz 2026, *Racial and Religious Disparities in Student Visa Rejections*, American Sociological Association meeting | US student-visa refusals from 2015, obtained by freedom-of-information request; regression with economic, social and political controls | Compared with predominantly White countries: predominantly Black countries +13 points, **predominantly Muslim +8**, Latin American +7, Asian +5.5; both Black and Muslim +26. Gaps did not widen in the first Trump term | conference abstract (page). Unpublished; cite as such |
| LAGO Collective (London), short-term visa data | Commission and Home Office data against income per head; binomial regression | "African countries are often outliers, with rejection rates well above what is expected by the regression line" | page |
| Maru 2025, *Schengen Visa Discrimination in Numbers*, Henley Global Mobility Report | Commission data | African applicants refused 18% in 2013 and 27% in 2023, world 5% and 16%; Comoros 61.3%, Syria 46%, Sudan 42.3% in 2023; argues income and reciprocity do not explain everything | page. Published by a firm that sells residence and citizenship programmes |
| Recchi, Deutschmann, Gabrielli and Kholmatova 2021, *The global visa cost divide*, Political Geography 86 | Hand-collected visa prices for country pairs | North Africans and South Asians pay over three times as much for a tourist visa as Western Europeans (about USD 60 against 18); in parts of Africa and South Asia the fee equals weeks of income | snippet (press release and abstract) |
| Neumayer 2006, *Unequal access to foreign spaces*, Transactions of the Institute of British Geographers 31(1) | Visa requirements between all country pairs | Easy travel for citizens of rich Western countries, restrictions for the rest | abstract |
| Hainmueller and Hangartner 2013, *Who Gets a Swiss Passport?*, American Political Science Review 107(1) | 2,429 citizenship applications decided by local referendum, 1970 to 2003 | Country of origin decides more than language, integration or income; about 40% more "no" votes for applicants from former Yugoslavia and Turkey than for similar applicants from richer European countries | snippet of the abstract. Citizenship, not visas; the cleanest evidence that a state decision about a person follows the origin with the person held fixed |

**On religion specifically:** only the student-visa conference paper tests a
"predominantly Muslim" indicator. I found no published regression of Schengen, UK,
Canadian or Australian refusal rates on religion. A statement like "refusal rates are
higher for Muslim-majority countries after controls" rests on one unpublished paper.

### 5.3 Officer discretion and nationality lists

- Alpes and Spire, *Dealing with law in migration control: the powers of street-level
  bureaucrats at French consulates*, Social & Legal Studies: fieldwork in the French
  consulates in Yaoundé and **Tunis**. Decisions are shaped by a fear of fraud and by
  the view that staff defend the national interest; the law is used flexibly (snippet
  of the abstract; year and volume not verified).
- Infantino: Belgian, French and Italian consulates in **Casablanca**; officers judge
  the "migratory risk" of an application (snippet).
- Satzewich 2014, *Visa officers as gatekeepers of a state's borders*, Canadian Review
  of Sociology, and the book *Points of Entry*: interviews with 128 officers and staff
  at eleven Canadian visa offices. This one reads **against** a simple racism story:
  the abstract sets itself against explaining decisions by officers' personal attitudes
  or individual racism, and a press piece on the book is headlined "Visa Officers
  Largely Bias-Free" (snippets of the abstract and publisher page; the journal name is
  from a secondary page).
- Canada, parliamentary committee report of 31 May 2022 on foreign students: visa
  officer decisions "may be affected by racial bias"; a witness gave refusal rates of
  73% for French-speaking African applicants in 2019 to 2021 (page, trade press). The
  ministry's sentence that it "recognizes the presence of racism in Canada and within
  our own organization" is from a snippet.
- United Kingdom, parliamentary groups' report of 16 July 2019: African applicants
  "more than twice as likely to be refused a UK visa than applicants from any other
  part of the world" (page). The exact rates (27% against 12%) are from snippets.
- The UK "streaming tool" that sorted applicants by nationality until 2020 is already
  in `scenario_alternatives_review.md` (snippet level there).

### 5.4 Entry bans by nationality

- 2017 US ban: the peer-reviewed study I could read is Samari et al. 2020 (Social
  Science & Medicine 265). Among women born in the banned countries the odds of
  preterm birth were 6.8% higher than expected from September 2017 to August 2018;
  18.9 million births analysed; the authors speak of an association (abstract).
- Visa numbers after the 2017 ban (falls of 60% to 80%, over 37,000 applications
  refused under it in 2018) are from news and think-tank snippets only: **not
  verified**.
- 2025: a proclamation of June 2025 barred entry for nationals of twelve countries,
  among them Libya, Somalia, Sudan and Yemen. A second one of 16 December 2025, in
  force from 1 January 2026, added Syria and holders of Palestinian Authority travel
  documents, and put partial limits on Mauritania (page, Indian news weekly; the
  proclamation text was not opened). That makes **six of our 22 nationalities** covered
  by a full US entry ban as of that proclamation, with exceptions. I did not check
  whether anything changed after December 2025.

### 5.5 What refusals do to people

- Researchers: survey of 2,465 researchers from 109 countries (Together Science Can,
  led by the Wellcome Trust, 18 Sept 2018). Visa problems reported by 40% of Asian and
  34% of African respondents, against 9% of Europeans and North Americans (page, Times
  Higher Education).
- The 2019 UK report speaks of "real costs to British business, academia, arts and
  culture" (page).
- Conferences: about two dozen researchers refused visas for an AI conference in
  Vancouver in 2019; 17 for a global-health event in London (snippets).
- Families: an 80% fall in visas for spouses and fiancés of US citizens from five
  banned countries (Cato Institute; snippet, page blocked): **not verified**.

---

## 6. Putting a money figure on the bias

Our outcomes: a 0 to 100 risk score, a rating, a request for more documents, and a
recommendation (grant, refer, refuse). Our files: 20 applicants living in Germany, with
net income and with savings on five steps (EUR 5,000, 8,000, 12,000, 18,000, 27,000;
`experiment/applicants/applicants.csv` as it stood on 2026-10-10).

### 6.1 Method A: fees lost on refused applications

**What it is.** Count the refused applications and multiply by the fee, which is not
refunded. LAGO Collective calls the result "reverse remittances": money that flows from
poorer to richer countries for nothing.

**Published figures.**

| figure | source | read |
|---|---|---|
| EUR 130 million for refused Schengen visas in 2023, EUR 105 million in 2022; GBP 44 million for the UK; African and Asian countries bear 90% | LAGO Collective, in EUobserver, 5 June 2024 | page |
| African countries: EUR 60 million in 2024 (Schengen); UK GBP 50.7 million in 2024, up 13.5% | LAGO Collective, in CNN, 21 May 2025 | page (republished copy) |
| "the poorer the country of application, the higher the rejection rates" | same | page |

**The method, checked.** The articles do not spell out the formula. I rebuilt it from
the Commission's 2023 file: 1,632,984 visas not issued times the EUR 80 fee is EUR
130.6 million. That matches, so the method is refusals times the adult fee. It
overstates a little, because children pay half and some groups pay nothing (embassy fee
pages, snippet). The EUobserver article notes that the figure leaves out lost travel,
legal advice and agency fees.

**The same sum for Arab League countries** (own calculation, 2025 file, fee EUR 90):
554,327 visas not issued at consulates in the 19 Arab League countries with data, times
EUR 90, is **about EUR 50 million**. These consulates took 24.7% of all applications
and 31.3% of all refusals. Same caution as above: place of application, not
nationality, and it is not a published figure.

**What data it needs.** Refusal counts and the fee. For an LLM audit: the model's
refusal rate per nationality, the fee (AUD 250), and, for a total, real application
counts per nationality.

**Fit with our audit.**

- It uses only the refuse recommendation. If the models refuse almost nobody, there is
  nothing to count. In `bowen2025measuring` one small model approved every file.
- Per person it is honest and simple: (refusal rate for nationality X minus refusal
  rate for the reference) times AUD 250. Per 1,000 identical applicants, a gap of 3
  points is 30 extra refusals, or AUD 7,500 in fees.
- A national total would need the assumption that the model decides real applications.
  No authority is documented as doing that. Any total is an illustration and must be
  labelled as one.
- "Refer" and "more documents" cost time, not a fee. I found no price list for the
  extra documents.

### 6.2 Method B: economic cost of visa restrictions

**What it is.** Economists compare pairs of countries with and without a visa
requirement, after allowing for distance, size and wealth, and read off how much less
travel, trade or investment there is.

| study | finding | read |
|---|---|---|
| Neumayer 2010, Professional Geographer 62(2) | A visa requirement goes with 52% to 63% less travel between two countries (1995 to 2005) | abstract |
| Neumayer 2011, Applied Geography 31(3) | One-sided requirement: trade down by up to 19%, investment stock by up to 25%; two-sided: trade down by up to 28% | abstract |
| Czaika and Neumayer 2017, Applied Geography 84 | More than 20% fewer tourists; smaller effects than earlier studies; poorer countries hit hardest; some travel moves to visa-free places (194 destinations, 1995 to 2013) | abstract |
| Lawson and Roychoudhury 2016, Journal of Economics and Finance 40(4) | A visa requirement on one country goes with 70% less travel from it | abstract (repository record) |
| UN tourism body and World Travel & Tourism Council 2012 | Easier visas in the G20 could add USD 206 billion in tourism income and over five million jobs by 2015 | snippet of the press release |

**What data it needs.** Travel, trade or investment between every pair of countries
over many years, and the visa rules between them.

**Fit with our audit: poor.** These numbers are about a *rule* (visa required or not),
not about single refusals, and not about a gap between two nationalities with the same
file. We cannot produce such a number from model answers. Use one of them as a
motivation line at most.

### 6.3 Method C: the compensating amount

**What it is.** Express the gap as the amount of something valuable that would cancel
it. Estimate how much the outcome moves with the group, and how much it moves with one
unit of the valuable thing; divide the first by the second.

| study | statement | read |
|---|---|---|
| Bertrand and Mullainathan 2004 (hiring) | "a white name yields as many more callbacks as an additional eight years of experience"; 10 against 15 applications sent per callback | page (NBER Digest, Sept 2003) |
| Hanson, Hawley, Martin and Liu 2016, Journal of Urban Economics 92 (mortgage enquiries by e-mail) | Being African American lowers the loan officer's response as much as a credit score that is 71 points lower | abstract |
| Bartlett, Morse, Stanton and Wallace 2021, Journal of Financial Economics (real mortgages) | Latinx and African-American borrowers pay 7.9 basis points more on purchase loans and 3.6 on refinancing, **USD 765 million a year** | abstract (NBER page) |
| `arai2016reverse` (hiring, Sweden) | A different route: give the Arabic-named applicant more experience and see whether the gap closes. It closes for women, not for men. The amount (about two more years) is from the earlier working paper | snippet |
| **`bowen2025measuring` (LLM audit)** | "Black applicants, on average, would need credit scores approximately 52 points higher than white applicants to receive the same approval rate, and about 22 points higher to receive the same interest rate" | full text (page 3 of the 17 Sept 2025 version) |
| same paper, the step to money | A Black applicant with a credit score of 654 on an average loan of USD 334,000 would be charged about 47 basis points more and, over a 30-year mortgage, "would pay around $35,700 more in (nominal) interest than a white applicant with the same credit profile" | full text (pages 20 to 21) |

**A discrepancy to know about.** The same version of Bowen et al. says 52 and 22 points
in the introduction and "120 points" and "about 30 points" in the results section. The
120 and 30 are also what the university's press release of August 2024 reports. Quote
the page, or ask the authors, before using either pair.

**What data it needs.** Nothing from outside. Inside the experiment it needs one money
variable that differs between files and that the model reacts to.

**Fit with our audit: best of the three.**

- It works on the 0 to 100 score, so it still works if the models grant everything.
- The savings ladder is already in the files.
- The sentence it produces is concrete: "for this model, a Yemeni passport weighs as
  much as EUR x less in savings".
- It makes no claim about real visa offices.

**How to do it, in plain steps.**

1. See how many points the score falls when savings go up one step on the ladder.
2. See how many points the score differs between nationality X and the reference.
3. Divide step 2 by step 1 and convert steps into euros.
4. Give a range, not a single number, by repeating the calculation on resampled files.

**Its weak points.**

- If the model ignores savings, step 1 is close to zero and the result explodes. The
  pilot has to show that the score reacts to savings. If it does not, the method is
  off the table and the note should say so.
- In the current files savings differ **between** applicants, who also differ in job
  and income. Step 1 is then only roughly a savings effect. The clean version runs the
  same file at two or three savings levels. That is an extra factor and extra runs; by
  the scope rule it is a team decision and it has to be made before the first real
  run, not after seeing results.
- The ladder is multiplicative (each step is roughly times 1.5), so "per cent more
  savings" is the natural unit; euros need a stated starting point.
- Report it per model. A ratio averaged over models that disagree means little.

### 6.4 Recommendation

- **Main figure: Method C**, the savings an applicant would need to make up for the
  nationality.
- **Second figure, clearly marked as an illustration: Method A per person**, the extra
  expected fee loss per 1,000 identical applicants at AUD 250.
- **Method B only as a motivation line.**
- A fourth idea, the fee measured in days of income (Recchi et al., LAGO), does not
  work for us: all our applicants live and earn in Germany.

Whichever is chosen belongs in the analysis plan before the first real run.

---

## 7. What a reviewer expects from an LLM audit

Three references are enough.

1. `vohra2026audit` (in the matrix, fulltext). The format of an audit moves results as
   much as the group does. Their answer: a placebo contrast, a primary test fixed in
   advance, results reported per format.
2. `gaebler2024auditing` (in the matrix, fulltext). The standard template for carrying
   the paired-application audit over to LLMs, with wording variants and an
   anti-discrimination instruction.
3. **New:** Bean et al. 2025, *Measuring what Matters: Construct Validity in Large
   Language Model Benchmarks*, NeurIPS 2025 (abstract). Twenty-nine reviewers went
   through 445 benchmarks and give eight recommendations. As listed in a search summary
   of the paper (not read by me): define what is measured, measure only that, use a
   representative set of items, use statistics to compare models, analyse errors, and
   justify that the measure fits the claim.

For the human-audit side, if a fourth is wanted: Lahey and Beasley 2016, *Technical
Aspects of Correspondence Studies* (NBER working paper 22818; abstract), which ends
with a checklist on power, matched pairs, too few templates and clustered errors.

| reviewer expects | where we stand | source to cite |
|---|---|---|
| Several wordings of the task | planned | `sclar2024quantifying`, `rottger2024political` |
| Repeated runs, uncertainty by file and not by run | planned | `miller2024adding`, `atil2024nondeterminism` |
| Placebo nationalities as a noise floor | planned | `vohra2026audit`, `chen2026competence` |
| Several models, exact versions logged | planned | `chen2024chatgpt` |
| A check that the instrument reacts to something it should react to (here: savings, the mild indicators) | needs the pilot | `pavlopoulos2026minimal`, `castleman2026measuring` |
| Hypotheses and main test written down before the run; exploratory analyses marked | **open** | `vohra2026audit` |
| The claim limited to the cue that was used (a nationality line, not names, not religion) | to be stated | `tonneau2026cues`, Bean et al. 2025 |
| Refusals and malformed answers counted by group | planned | `bowen2025measuring` |

---

## 8. Cautions before anything from this note is used

- Every "page" and "abstract" entry went through a summarising tool. Re-check quotes
  and numbers on the original.
- The conference paper on student visas and the journal article on US visitor visas
  were not read in full.
- The Schengen table is by consulate. Only the US table is by nationality.
- "Own calculation" figures (EUR 50 million, the German-consulate rates, the median)
  are mine. Label them so.
- Real refusal rates reflect real differences between applicant pools. They show that
  nationalities are treated differently, not that the difference is unjustified. Our
  experiment holds the applicant fixed; the real data do not.
- Advocacy sources: CLAIM, Tell MAMA, CAIR, LAGO. Company sources: Henley, Tern Visa,
  the migration-law firm for the Australian fee.
- Not covered: UK and Canadian refusal tables by nationality; the full CLAIM report for
  2025; the text of the 2025 US proclamations; any German-language research on visa
  refusals; a systematic search for LLM studies.

---

## 9. Sources

### 9.1 Table

| source | URL | what it supports | how far read |
|---|---|---|---|
| EU Agency for Fundamental Rights, *Being Muslim in the EU*, press release 24 Oct 2024 and report page | https://fra.europa.eu/en/news/2024/muslims-europe-face-ever-more-racism-and-discrimination ; https://fra.europa.eu/en/publication/2024/being-muslim-eu | 47% and the other FRA figures; sample of 9,604 in 13 countries; sampling by origin | page |
| CLAIM, *Zivilgesellschaftliches Lagebild antimuslimischer Rassismus. Antimuslimische Vorfälle in Deutschland 2024*, short summary | https://www.demokratiezentrum.bremen.de/sixcms/media.php/13/claim_lagebild25_zusammenfassung-stand-16.6.25.pdf | 3,080 incidents, breakdown, number of reporting centres, definition "read as Muslim" | full text (19 pages, first 6 read closely) |
| *taz*, 24 June 2026 | https://taz.de/!6190280 | CLAIM figure for 2025 (4,096) | page (press) |
| German Bundestag, printed paper 21/6530, 16 June 2026 | https://dserver.bundestag.de/btd/21/065/2106530.pdf | Police figures 1,848 (2024) and 1,543 (2025, preliminary); 104 cases in the first quarter of 2026 | full text (first 4 pages) |
| German Bundestag, notice hib 175/2026, 9 March 2026 | https://www.bundestag.de/presse/hib/kurzmeldungen-1152014 | 164 offences in the fourth quarter of 2025 | page |
| Home Office, *Hate crime, England and Wales, year ending March 2026*, 8 Oct 2026 | https://www.gov.uk/government/statistics/hate-crime-england-and-wales-year-ending-march-2026/hate-crime-england-and-wales-year-ending-march-2026 | 5,132 offences, 46%, rates per 10,000, "perceived religion" | page |
| AFP in Free Malaysia Today, 19 Feb 2025 | https://www.freemalaysiatoday.com/category/world/2025/02/19/anti-muslim-hate-at-record-level-in-uk-says-ngo | Tell MAMA 2024 and 2023 totals | page (press) |
| Tell MAMA, 19 Aug 2026 | https://tellmamauk.org/record-levels-reached-on-london-based-reports-anti-muslim-hate-reports/ | London figures 2021 to 2026 (not used on the slide list) | page |
| Al Jazeera, 10 March 2026 | https://www.aljazeera.com/news/2026/3/10/us-civil-rights-group-documents-broad-attack-on-muslim-life-in-2025 | CAIR: 8,683 complaints in 2025 | page (press) |
| Calfano, Lajevardi and Michelson 2021 | https://doi.org/10.1017/S1755048320000668 | The public penalises "Muslim", not "Arab" | abstract |
| Pew Research Center 2012, *The Global Religious Landscape: Muslims* | https://www.pewresearch.org/religion/2012/12/18/global-religious-landscape-muslim/ | 62% of Muslims in Asia-Pacific, 20% in the Middle East and North Africa | snippet |
| Federal Office for Migration and Refugees, *Muslim Life in Germany 2020*, notice of 28 Oct 2021 | https://www.bamf.de/SharedDocs/Meldungen/EN/2021/211028-am-mld2020.html | 5.3 to 5.6 million Muslims; 45% Turkish background; Syria 13% | page |
| Liu, Wang, Cheng and Kurohashi 2025 | https://arxiv.org/abs/2502.17945 | Nationality bias in travel, relocation and university advice | abstract |
| Toles et al. 2026, MortarBench | https://arxiv.org/abs/2606.19416 | Models see non-English names as foreign | abstract |
| Arzaghi, Carichon and Farnadi 2024 | https://arxiv.org/abs/2405.18662 | Names visa applications as a use of LLMs | abstract |
| Anthropic, `discrim-eval` dataset, file `explicit.jsonl` | https://huggingface.co/datasets/Anthropic/discrim-eval | Visa, passport, border and clearance scenarios; only age, gender and race varied | full text (data file searched) |
| US Department of State, *Adjusted Refusal Rate – B-Visas Only by Nationality, Fiscal Year 2025* | https://travel.state.gov/content/dam/visas/Statistics/Non-Immigrant-Statistics/RefusalRates/FY25.pdf | Refusal rates for all 22 nationalities | full text |
| European Commission, visa statistics for consulates 2025, 2024, 2023 | https://home-affairs.ec.europa.eu/policies/schengen-borders-and-visa/visa-policy/short-stay-visas-issued-schengen-countries_en | Schengen rates by consulate country; totals; basis of the own calculations | full text (data files) |
| Australian Department of Home Affairs, *BR0112 Visitor visa program report, 30 June 2025* | https://www.homeaffairs.gov.au/research-and-stats/files/visitor-visa-june-2025.pdf | Grant rates by visa product and for 15 countries | full text (section 3) |
| Work Visa Lawyers, fee table, 1 July 2026 | https://www.workvisalawyers.com.au/news/all/australian-visa-fees-2026-2027-full-price-table.html | Fee AUD 200, then AUD 250 | page (law firm) |
| Tern Visa, country-risk page | https://ternvisa.com/en/blog/country-risk | Claim of large differences by nationality from freedom-of-information data | page (company) |
| Thomas (and Lowe), seminar abstract, Duke, 26 Sept 2024; journal article 2025 | https://cpha.duke.edu/node/99761 ; https://journals.sagepub.com/doi/10.1177/01979183251405836 | Africa more than double Europe after controls | abstract (seminar); journal page blocked |
| Maggio and Tomasiewicz 2026, ASA meeting | https://convention2.allacademic.com/one/asa/asa26/online_program_direct_link/view_paper/2339558/ | +8 points for predominantly Muslim countries | abstract (conference) |
| LAGO Collective, short-term visa data | https://www.lagocollective.org/material/f/visas/rejected-by-gdp/ | Refusal rate against income per head; African outliers | page |
| EUobserver, 5 June 2024 | https://euobserver.com/32469/eu-cashes-in-on-e130m-in-rejected-visa-applications/ | EUR 130 million (2023), EUR 105 million (2022), GBP 44 million | page (press) |
| CNN, 21 May 2025 (copy on Yahoo News) | https://www.yahoo.com/news/africans-lost-nearly-70m-denied-144745228.html | EUR 60 million, GBP 50.7 million, "reverse remittances", fees | page (press) |
| Maru 2025, Henley Global Mobility Report | https://www.henleyglobal.com/publications/global-mobility-report/2025-january/global-mobility-contradiction-schengen-visa-discrimination-numbers | African and world refusal rates 2013 and 2023; country rates | page (company publication) |
| Recchi et al. 2021 | https://doi.org/10.1016/j.polgeo.2021.102350 | Visa prices by region and against income | snippet |
| Neumayer 2006 | https://researchonline.lse.ac.uk/id/eprint/715/ | Unequal access by passport | abstract |
| Neumayer 2010 | https://researchonline.lse.ac.uk/id/eprint/28351 | 52% to 63% less travel | abstract |
| Neumayer 2011 | https://researchonline.lse.ac.uk/id/eprint/37226 | Trade and investment effects | abstract |
| Czaika and Neumayer 2017 | https://researchonline.lse.ac.uk/id/eprint/74060 | More than 20% fewer tourists | abstract |
| Lawson and Roychoudhury 2016 | https://ideas.repec.org/a/spr/jecfin/v40y2016i4d10.1007_s12197-015-9343-5.html | 70% less travel | abstract |
| UN tourism body and WTTC, press release 17 May 2012 | https://www.untourism.int/archive/global/press-release/2012-05-17/visa-facilitation-can-create-five-million-additional-jobs-g20-economies | USD 206 billion, five million jobs | snippet |
| Hainmueller and Hangartner 2013 | https://researchonline.lse.ac.uk/id/eprint/46516 | Origin decides citizenship votes | snippet |
| Alpes and Spire, Social & Legal Studies | https://metatoc.com/papers/25934-dealing-with-law-in-migration-control-the-powers-of-street-level-bureaucrats-at-french-consulates | Consular discretion in Yaoundé and Tunis | snippet |
| Satzewich 2014; *Points of Entry* | https://experts.mcmaster.ca/scholarly-works/340077 ; https://ubcpress.ca/points-of-entry | Canadian visa officers; discretion explained by organisation | snippet |
| The PIE News, 8 June 2022 | https://thepienews.com/racial-bias-canada-study-permit-refusal/ | Canadian committee report: "may be affected by racial bias" | page (trade press) |
| Royal African Society, 16 July 2019 | https://royalafricansociety.org/home-office-visa-service-discriminating-against-africans/ | UK report on African visitors | page |
| Times Higher Education, 18 Sept 2018 | https://www.timeshighereducation.com/node/659228 | Researchers' visa obstacles: 40%, 34%, 9% | page (press) |
| Samari, Catalano, Alcalá and Gemmill 2020 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7738384 | 2017 ban and preterm births | abstract |
| The Week (India), 17 Dec 2025 | https://www.theweek.in/news/world/2025/12/17/people-from-39-countries-now-face-full-or-partial-us-travel-ban-here-is-the-full-list.amp.html | Country lists of the 2025 US bans | page (press) |
| NBER Digest, 1 Sept 2003 | https://nber.org/digest/sep03/w9873.html | "eight years of experience"; 10 against 15 applications | page |
| Hanson, Hawley, Martin and Liu 2016 | https://epublications.marquette.edu/econ_fac/555 | 71 credit-score points | abstract |
| Bartlett, Morse, Stanton and Wallace 2021 | https://www.nber.org/papers/w25943 | 7.9 and 3.6 basis points; USD 765 million a year | abstract |
| Bowen, Price, Stein and Yang, version of 17 Sept 2025 (`bowen2025measuring`) | https://www.aeaweb.org/conference/2026/program/paper/t484eTf2 | Credit-score equivalent and the step to dollars | full text (pages 3, 18, 20) |
| Lehigh University news, 20 Aug 2024 | https://news.lehigh.edu/ai-exhibits-racial-bias-in-mortgage-underwriting-decisions | The earlier figures, 120 and 30 points | page |
| Bean et al. 2025 | https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html | Eight recommendations for valid LLM measurement | abstract |
| Lahey and Beasley 2016 | https://nber.org/papers/w22818 | Checklist for paired-application studies | abstract |

Not used because not verified: Cato Institute on family visas after the 2017 ban (page
blocked); the share of Arab Americans who are Christian; the German expert-group
figure on attitudes; exact UK refusal rates for African visitors.

### 9.2 BibTeX for the new sources

Same custom fields as `references.bib`: `verification` (fulltext, abstract, metadata)
and `strand`. Proposed new strands: `islamophobia_context`, `visa_evidence`,
`cost_method`. Not added to `references.bib`.

```bibtex
@misc{fra2024being,
  author       = {{European Union Agency for Fundamental Rights}},
  title        = {Being {Muslim} in the {EU}},
  year         = {2024},
  month        = oct,
  url          = {https://fra.europa.eu/en/publication/2024/being-muslim-eu},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {Press release of 24 Oct 2024 and report page read through a fetch tool. Survey Oct 2021 to Oct 2022, 9,604 respondents, 13 countries}
}

@misc{claim2025lagebild,
  author       = {{CLAIM -- Allianz gegen Islam- und Muslimfeindlichkeit}},
  title        = {Zivilgesellschaftliches Lagebild antimuslimischer Rassismus: Antimuslimische Vorf{\"a}lle in {Deutschland} 2024. Ausgabe 2025. Kurzzusammenfassung},
  year         = {2025},
  url          = {https://www.demokratiezentrum.bremen.de/sixcms/media.php/13/claim_lagebild25_zusammenfassung-stand-16.6.25.pdf},
  verification = {fulltext},
  strand       = {islamophobia_context},
  annote       = {Advocacy organisation. Short summary read, not the full report. Number of reporting centres rose from 17 to 26}
}

@misc{taz2026claim,
  author       = {{taz}},
  title        = {Report on the {CLAIM} Lagebild for 2025},
  howpublished = {die tageszeitung},
  year         = {2026},
  month        = jun,
  url          = {https://taz.de/!6190280},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {PRESS REPORT of 24 June 2026; headline and author not recorded. Source of the 2025 figure (4,096); the CLAIM report itself was not opened}
}

@misc{bundestag2026islamfeindlichkeit,
  author       = {{Deutscher Bundestag}},
  title        = {Antwort der Bundesregierung auf die Kleine Anfrage: Islamfeindlichkeit und antimuslimische Straftaten im ersten Quartal 2026},
  howpublished = {Drucksache 21/6530},
  year         = {2026},
  month        = jun,
  url          = {https://dserver.bundestag.de/btd/21/065/2106530.pdf},
  verification = {fulltext},
  strand       = {islamophobia_context},
  annote       = {The annual police figures (1,848 for 2024; 1,543 for 2025, preliminary) are quoted in the questioners' preamble, not in the government's answer}
}

@misc{homeoffice2026hate,
  author       = {{Home Office}},
  title        = {Hate crime, {England} and {Wales}, year ending {March} 2026},
  year         = {2026},
  month        = oct,
  url          = {https://www.gov.uk/government/statistics/hate-crime-england-and-wales-year-ending-march-2026},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {Published 8 Oct 2026. Read through a fetch tool}
}

@misc{afp2025tellmama,
  author       = {{Agence France-Presse}},
  title        = {Anti-{Muslim} hate at record level in {UK}, says {NGO}},
  howpublished = {Free Malaysia Today},
  year         = {2025},
  month        = feb,
  url          = {https://www.freemalaysiatoday.com/category/world/2025/02/19/anti-muslim-hate-at-record-level-in-uk-says-ngo},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {PRESS REPORT on Tell MAMA figures for 2024}
}

@misc{aljazeera2026cair,
  author       = {{Al Jazeera}},
  title        = {{US} civil rights group documents `broad attack on {Muslim} life' in 2025},
  year         = {2026},
  month        = mar,
  url          = {https://www.aljazeera.com/news/2026/3/10/us-civil-rights-group-documents-broad-attack-on-muslim-life-in-2025},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {PRESS REPORT on the CAIR civil rights report; the report itself was blocked}
}

@article{calfano2021evaluating,
  author       = {Calfano, Brian R. and Lajevardi, Nazita and Michelson, Melissa R.},
  title        = {Evaluating Resistance toward {Muslim} {American} Political Integration},
  journal      = {Politics and Religion},
  year         = {2021},
  volume       = {14},
  number       = {3},
  pages        = {512--525},
  doi          = {10.1017/S1755048320000668},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {HUMAN study. Evidence against conflation of Arab and Muslim}
}

@misc{pew2012global,
  author       = {{Pew Research Center}},
  title        = {The Global Religious Landscape: {Muslims}},
  year         = {2012},
  month        = dec,
  url          = {https://www.pewresearch.org/religion/2012/12/18/global-religious-landscape-muslim/},
  verification = {metadata},
  strand       = {islamophobia_context},
  annote       = {Search snippet only}
}

@misc{bamf2021muslim,
  author       = {{Bundesamt f{\"u}r Migration und Fl{\"u}chtlinge}},
  title        = {Muslim Life in {Germany} 2020},
  year         = {2021},
  url          = {https://www.bamf.de/SharedDocs/Meldungen/EN/2021/211028-am-mld2020.html},
  verification = {abstract},
  strand       = {islamophobia_context},
  annote       = {Notice of 28 Oct 2021 read; the research report (Forschungsbericht 38) was not opened}
}

@misc{liu2025assessing,
  author        = {Liu, Qianying and Wang, Katrina Qiyao and Cheng, Fei and Kurohashi, Sadao},
  title         = {Assessing Agentic Large Language Models in Multilingual National Bias},
  year          = {2025},
  eprint        = {2502.17945},
  archiveprefix = {arXiv},
  verification  = {abstract},
  strand        = {nationality_llm},
  annote        = {arXiv comment: accepted to Findings of ACL 2025; proceedings not checked}
}

@misc{toles2026mortarbench,
  author        = {Toles, Matthew and Lu, Yunan and Munjal, Manav and Liu, Bojun and Deng, Yuanhao and Selig, Stephanie and Rindner, Derek and Li, Cheng and Yu, Zhou},
  title         = {{MortarBench}: Evaluating Mortgage Loan Origination Agents},
  year          = {2026},
  eprint        = {2606.19416},
  archiveprefix = {arXiv},
  verification  = {abstract},
  strand        = {llm_lending},
  annote        = {Preprint. The figure for Arabic names is not in the abstract}
}

@misc{arzaghi2024understanding,
  author        = {Arzaghi, Mina and Carichon, Florian and Farnadi, Golnoosh},
  title         = {Understanding Intrinsic Socioeconomic Biases in Large Language Models},
  year          = {2024},
  eprint        = {2405.18662},
  archiveprefix = {arXiv},
  verification  = {abstract},
  strand        = {nationality_llm}
}

@misc{state2025refusal,
  author       = {{U.S. Department of State}},
  title        = {Adjusted Refusal Rate -- {B}-Visas Only by Nationality, Fiscal Year 2025},
  year         = {2025},
  url          = {https://travel.state.gov/content/dam/visas/Statistics/Non-Immigrant-Statistics/RefusalRates/FY25.pdf},
  verification = {fulltext},
  strand       = {visa_evidence},
  annote       = {Publication date not stated in the file; fiscal year ends 30 Sept 2025}
}

@misc{ec2026visa,
  author       = {{European Commission, Directorate-General for Migration and Home Affairs}},
  title        = {Visa statistics for consulates 2025},
  year         = {2026},
  url          = {https://home-affairs.ec.europa.eu/policies/schengen-borders-and-visa/visa-policy/short-stay-visas-issued-schengen-countries_en},
  verification = {fulltext},
  strand       = {visa_evidence},
  annote       = {Excel file. By country where the consulate is, not by nationality. The files for 2024 and 2023 are on the same page}
}

@misc{homeaffairs2025visitor,
  author       = {{Australian Government, Department of Home Affairs}},
  title        = {{BR0112} Visitor visa program report, 30 {June} 2025},
  year         = {2025},
  url          = {https://www.homeaffairs.gov.au/research-and-stats/files/visitor-visa-june-2025.pdf},
  verification = {fulltext},
  strand       = {visa_evidence},
  annote       = {Section 3 (grant rates) read}
}

@article{thomas2025global,
  author       = {Thomas, Kevin J. A. and Lowe, Ricardo Henrique},
  title        = {Global Inequalities in {US} Visa Rejections: Evidence from Visitor Visa Applications Submitted Between 2006 and 2021},
  journal      = {International Migration Review},
  year         = {2025},
  doi          = {10.1177/01979183251405836},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {HUMAN / administrative data. Only the abstract of a 2024 seminar version was read (https://cpha.duke.edu/node/99761); the journal page was blocked}
}

@misc{maggio2026racial,
  author       = {Maggio, Christopher and Tomasiewicz, Meaghan L.},
  title        = {Racial and Religious Disparities in Student Visa Rejections},
  howpublished = {Paper presented at the American Sociological Association Annual Meeting},
  year         = {2026},
  month        = aug,
  url          = {https://convention2.allacademic.com/one/asa/asa26/online_program_direct_link/view_paper/2339558/},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {Unpublished conference paper; abstract only}
}

@misc{lago2026visas,
  author       = {{LAGO Collective}},
  title        = {Visa Rejection Rate -- Short Term Visa Data},
  year         = {2026},
  url          = {https://www.lagocollective.org/material/f/visas/rejected-by-gdp/},
  verification = {abstract},
  strand       = {cost_method},
  annote       = {Advocacy and research collective. Page undated; year is the year of access. The linked data sheet was not opened}
}

@misc{fox2024eu,
  author       = {Fox, Benjamin},
  title        = {{EU} cashes in on {EUR} 130m in rejected visa applications},
  howpublished = {EUobserver},
  year         = {2024},
  month        = jun,
  url          = {https://euobserver.com/32469/eu-cashes-in-on-e130m-in-rejected-visa-applications/},
  verification = {abstract},
  strand       = {cost_method},
  annote       = {PRESS REPORT on LAGO Collective figures. Title taken from the URL (the original uses the euro sign); check the wording}
}

@misc{madowo2025africans,
  author       = {Madowo, Larry},
  title        = {Africans lost nearly \$70{M} to denied visas applications to {Europe} in 2024},
  howpublished = {CNN},
  year         = {2025},
  month        = may,
  url          = {https://www.yahoo.com/news/africans-lost-nearly-70m-denied-144745228.html},
  verification = {abstract},
  strand       = {cost_method},
  annote       = {PRESS REPORT on LAGO Collective figures; read in the copy on Yahoo News}
}

@misc{maru2025schengen,
  author       = {Maru, Mehari Taddele},
  title        = {Schengen Visa Discrimination in Numbers},
  howpublished = {Henley \& Partners Global Mobility Report, January 2025},
  year         = {2025},
  url          = {https://www.henleyglobal.com/publications/global-mobility-report/2025-january/global-mobility-contradiction-schengen-visa-discrimination-numbers},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {COMPANY PUBLICATION. Its table of top rejection rates is not in consistent order}
}

@article{recchi2021global,
  author       = {Recchi, E. and Deutschmann, E. and Gabrielli, L. and Kholmatova, N.},
  title        = {The global visa cost divide: How and why the price for travel permits varies worldwide},
  journal      = {Political Geography},
  year         = {2021},
  volume       = {86},
  pages        = {1--14},
  doi          = {10.1016/j.polgeo.2021.102350},
  verification = {metadata},
  strand       = {cost_method},
  annote       = {Search snippet of the press release and abstract only. Initials and pages as given in that snippet; full first names not seen}
}

@article{neumayer2006unequal,
  author       = {Neumayer, Eric},
  title        = {Unequal access to foreign spaces: how states use visa restrictions to regulate mobility in a globalized world},
  journal      = {Transactions of the Institute of British Geographers},
  year         = {2006},
  volume       = {31},
  number       = {1},
  pages        = {72--84},
  doi          = {10.1111/j.1475-5661.2006.00194.x},
  verification = {abstract},
  strand       = {visa_evidence}
}

@article{neumayer2010visa,
  author       = {Neumayer, Eric},
  title        = {Visa restrictions and bilateral travel},
  journal      = {The Professional Geographer},
  year         = {2010},
  volume       = {62},
  number       = {2},
  pages        = {171--181},
  doi          = {10.1080/00330121003600835},
  verification = {abstract},
  strand       = {cost_method}
}

@article{neumayer2011detrimental,
  author       = {Neumayer, Eric},
  title        = {On the detrimental impact of visa restrictions on bilateral trade and foreign direct investment},
  journal      = {Applied Geography},
  year         = {2011},
  volume       = {31},
  number       = {3},
  pages        = {901--907},
  doi          = {10.1016/j.apgeog.2011.01.009},
  verification = {abstract},
  strand       = {cost_method}
}

@article{czaika2017visa,
  author       = {Czaika, Mathias and Neumayer, Eric},
  title        = {Visa restrictions and economic globalisation},
  journal      = {Applied Geography},
  year         = {2017},
  volume       = {84},
  pages        = {75--82},
  doi          = {10.1016/j.apgeog.2017.04.011},
  verification = {abstract},
  strand       = {cost_method}
}

@article{lawson2016travel,
  author       = {Lawson, Robert A. and Roychoudhury, Saurav},
  title        = {Do travel visa requirements impede tourist travel?},
  journal      = {Journal of Economics and Finance},
  year         = {2016},
  volume       = {40},
  number       = {4},
  pages        = {817--828},
  doi          = {10.1007/s12197-015-9343-5},
  verification = {abstract},
  strand       = {cost_method}
}

@article{hainmueller2013who,
  author       = {Hainmueller, Jens and Hangartner, Dominik},
  title        = {Who Gets a {Swiss} Passport? A Natural Experiment in Immigrant Discrimination},
  journal      = {American Political Science Review},
  year         = {2013},
  volume       = {107},
  number       = {1},
  pages        = {159--187},
  verification = {metadata},
  strand       = {visa_evidence},
  annote       = {HUMAN study. Abstract seen in search snippets only; DOI not checked}
}

@article{alpes2014dealing,
  author       = {Alpes and Spire},
  title        = {Dealing with Law in Migration Control: The Powers of Street-level Bureaucrats at {French} Consulates},
  journal      = {Social \& Legal Studies},
  year         = {2014},
  verification = {metadata},
  strand       = {visa_evidence},
  annote       = {HUMAN / ethnography. Search snippet only. First names were not in the snippet; year, volume and pages NOT verified. Complete before use}
}

@article{satzewich2014visa,
  author       = {Satzewich, V.},
  title        = {Visa Officers as Gatekeepers of a State's Borders: The Social Determinants of Discretion in Spousal Sponsorship Cases in {Canada}},
  journal      = {Canadian Review of Sociology},
  year         = {2014},
  verification = {metadata},
  strand       = {visa_evidence},
  annote       = {HUMAN / interviews. Journal name from a secondary page; first name, volume and pages not verified}
}

@misc{packer2022racial,
  author       = {Packer, Helen},
  title        = {Report on racial bias in {Canada}'s study permit refusals},
  howpublished = {The PIE News},
  year         = {2022},
  month        = jun,
  url          = {https://thepienews.com/racial-bias-canada-study-permit-refusal/},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {TRADE PRESS REPORT on the House of Commons committee report of 31 May 2022; headline not recorded, the committee report was not opened}
}

@misc{appg2019visa,
  author       = {{All-Party Parliamentary Groups for Africa, for Malawi, and for Diaspora, Development and Migration}},
  title        = {Visa problems for {African} visitors to the {UK}},
  year         = {2019},
  month        = jul,
  url          = {https://royalafricansociety.org/home-office-visa-service-discriminating-against-africans/},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {Announcement page read, not the report. Title taken from the file name of the report}
}

@misc{timeshighereducation2018african,
  author       = {{Times Higher Education}},
  title        = {{African} and {Asian} researchers `face greatest mobility obstacles'},
  year         = {2018},
  month        = sep,
  url          = {https://www.timeshighereducation.com/node/659228},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {PRESS REPORT on a survey by Together Science Can (Wellcome Trust), 2,465 researchers; the study itself was not opened}
}

@article{samari2020muslim,
  author       = {Samari, Goleen and Catalano, Ralph and Alcal{\'a}, H. E. and Gemmill, A.},
  title        = {The {Muslim} Ban and preterm birth: Analysis of {U.S.} vital statistics data from 2009 to 2018},
  journal      = {Social Science \& Medicine},
  year         = {2020},
  volume       = {265},
  pages        = {113544},
  doi          = {10.1016/j.socscimed.2020.113544},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {HUMAN study. Abstract read on PubMed Central; the record gives initials only for the third and fourth author}
}

@misc{theweek2025travelban,
  author       = {{The Week}},
  title        = {People from 39 countries now face full or partial {US} travel ban},
  year         = {2025},
  month        = dec,
  url          = {https://www.theweek.in/news/world/2025/12/17/people-from-39-countries-now-face-full-or-partial-us-travel-ban-here-is-the-full-list.amp.html},
  verification = {abstract},
  strand       = {visa_evidence},
  annote       = {PRESS REPORT. The proclamation text was not opened}
}

@misc{francis2003employers,
  author       = {Francis, David R.},
  title        = {Employers' Replies to Racial Names},
  howpublished = {NBER Digest},
  year         = {2003},
  month        = sep,
  url          = {https://nber.org/digest/sep03/w9873.html},
  verification = {abstract},
  strand       = {cost_method},
  annote       = {Summary of bertrand2004emily; source of the `eight years of experience' sentence}
}

@article{hanson2016discrimination,
  author       = {Hanson, Andrew R. and Hawley, Zackary and Martin, Hal and Liu, Bo},
  title        = {Discrimination in mortgage lending: Evidence from a correspondence experiment},
  journal      = {Journal of Urban Economics},
  year         = {2016},
  volume       = {92},
  pages        = {48--65},
  doi          = {10.1016/j.jue.2015.12.004},
  verification = {abstract},
  strand       = {cost_method},
  annote       = {HUMAN study}
}

@article{bartlett2021consumer,
  author       = {Bartlett, Robert and Morse, Adair and Stanton, Richard and Wallace, Nancy},
  title        = {Consumer-lending discrimination in the {FinTech} Era},
  journal      = {Journal of Financial Economics},
  year         = {2021},
  doi          = {10.1016/j.jfineco.2021.05.047},
  verification = {abstract},
  strand       = {cost_method},
  annote       = {HUMAN / administrative data. Abstract read on the NBER page (working paper 25943); volume and pages not checked}
}

@inproceedings{bean2025measuring,
  author       = {Bean, Andrew M. and Kearns, Ryan Othniel and Romanou, Angelika and Hafner, Franziska Sofia and Mayne, Harry and Batzner, Jan and others},
  title        = {Measuring what Matters: Construct Validity in Large Language Model Benchmarks},
  booktitle    = {Advances in Neural Information Processing Systems 38 (Datasets and Benchmarks Track)},
  year         = {2025},
  doi          = {10.52202/085713-0590},
  verification = {abstract},
  strand       = {audit_method},
  annote       = {42 authors; last authors Luc Rocher and Adam Mahdi. arXiv:2511.04703}
}

@techreport{lahey2016technical,
  author       = {Lahey, Joanna and Beasley, Ryan},
  title        = {Technical Aspects of Correspondence Studies},
  institution  = {National Bureau of Economic Research},
  type         = {Working Paper},
  number       = {22818},
  year         = {2016},
  doi          = {10.3386/w22818},
  verification = {abstract},
  strand       = {audit_method}
}
```
