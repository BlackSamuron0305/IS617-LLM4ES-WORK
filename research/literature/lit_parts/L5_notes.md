# L5 literature notes: do humans tell Arab national origins apart, or lump them?

Internal research notes, telegraphic. **Not paper prose.** Do not paste into `paper/` (AI-usage rule in `CLAUDE.md`).

- Compiled: 2026-10-04. First search pass for the Arab-world setting (setting changed 2026-10-01).
- Companion files: `L5_matrix.csv` (23 rows), `L5_refs.bib` (same 23 keys).
- Verification levels as in `research/literature_review.md`: **fulltext** = relevant sections read; **abstract** = abstract or official summary page only; **metadata** = record confirmed, content not read.
- Counts: 15 fulltext, 8 abstract, 0 metadata. Strands: 17 `human_audit`, 6 `fairness_theory`.
- Every row confirmed through Crossref, OpenAlex, the publisher/repository page or the issuing organisation. Nothing cited from memory. Items recalled but not confirmed are under "Unverified leads" and are **not** in the bib.
- All rows are HUMAN or non-LLM. `novelty_threat` = `none` throughout.
- Grey literature (flagged in `venue`): `kapiszewski2006arab` (UN expert paper), `razzaz2017challenging` (ILO report), `mathews2017national` (Census Bureau report), `omb2024revisions` (Federal Register notice).

## 0. Merge warning: overlap with part L3

L3 (written in parallel, same day) contains three of the same papers. I did not edit L3.

| Paper | L3 key | L5 key | Note |
|---|---|---|---|
| Vernby & Dancygier 2019 | `vernby2019immigrants` | same | Both fulltext. Numbers agree (21 / 17 / 10 / 5 %; n = 1,492). Keep one row. |
| Martiniello & Verhaeghe 2022 | `martiniello2022signaling` | same | L3 abstract-level; L5 fulltext with recognition rates for Moroccan names (48.2% seen as non-European, 34% assigned to Morocco). Prefer the L5 row. Table 1 is row-shifted in the pdftotext output; only figures confirmed in the running text are used. |
| Valfort 2020 | `valfort2020anti` | same (renamed to match) | L3 abstract-level from the journal abstract; L5 read the **working-paper** version (IZA DP 11417). **Numbers differ**: DP gives religious Muslim men 4.7% vs religious Christian men 17.9%; L3 records 4.2% vs 10.9% for "ordinary religious men" from the journal abstract. Use the journal figures; treat the DP figures as superseded until the journal text is read. |

L3 also covers the pooled or single-origin Western audits I had as leads (Andriessen 2012, Bursell 2014, Busetta 2018, Dahl & Krog 2018, Duguet 2010, Edo 2019, Eid 2012, Pierné 2013, Widner & Chicoine 2011, Thijssen 2021). Not repeated here.

## 1. Verdict per sub-question

### 1.1 Nationality stratification in Gulf / Arab labour markets

- **Established:** nationality structures pay and treatment in the Gulf. But the comparison the literature makes is almost always **Western vs Arab vs Asian**, with "Arab" as one bloc (`alfarhan2019migrant`, `gardner2013portrait`; also Diop 2017, GulfTalent-type salary surveys in the leads).
- **Thin:** differences **among** Arab expatriate nationalities with qualifications controlled. One peer-reviewed study found: `alqudsi1991relative` (Kuwait 1983, nine nationality groups, about a third of earnings inequality unexplained). Abstract only; ranking of groups **not verified**. Old data.
- **Qualitative / grey only:** differential treatment of specific Arab nationalities for political reasons (`kapiszewski2006arab`: 1990-91 expulsions of Yemenis, Jordanians, Palestinians; Egyptians expelled from Qatar 1996); nationality-based sorting in Jordan (`razzaz2017challenging`); stereotype-based job allocation in the UAE (`alariss2016job`, abstract only).
- **Absent (not found):** a peer-reviewed content analysis of job ads that state a required or preferred nationality in the Gulf. Only news reports (The National, Gulf Business, Khaleej Times). ArabJobs corpus (El-Haj 2025, arXiv:2509.22589) has ads from Egypt, Jordan, Saudi Arabia, UAE but no nationality analysis (full text checked).
- Counter-reading: `alfarhan2019migrant` attributes the unexplained Western premium to outside options, not to employer perceptions.

### 1.2 Field experiments / audits inside Arab countries

- **Absent (not found):** a correspondence audit in any Arab country with applicant **nationality or origin** as the treatment. Searched the English-language web and OpenAlex only; treat as "not found", not "does not exist".
- **Exists, other grounds:** gender audits in Egypt (`krafft2025employers`) and Tunisia (Alaref et al. 2020, not added).
- **Exists, non-hiring, nationality randomised:** `shockley2024sharing` (Qatar conjoint, permanent residency; nationality null), `blaydes2023arab` (Kuwait/Qatar framing experiment; pooled Arab vs Indian), `barron2023discrimination` (Jordan, children; Jordanian vs Syrian; small effect).
- Net: the experimental evidence inside the region points **toward little differentiation among Arab origins**, in non-hiring outcomes.

### 1.3 Origin hierarchies among Arab / MENA groups in Western settings

- **Established for specific pairs:** Iraq above Somalia in two Nordic audits (`vernby2019immigrants`, `ahmad2026name`). Iraqi singled out for a penalty in a US conjoint (`hainmueller2015hidden`, abstract). Syria above Iraq in a 15-country conjoint, but max origin gap 4 pp and religion 11 pp (`bansak2016economic`).
- **Thin:** studies with more than two Arab origins. Beyond `koopmans2019taste` and `distasio2024same` (already in the matrix) none found.
- **Absent (not found):** stereotype-content or social-distance studies that rate several Arab nationalities separately, in Western or Arab samples.
- Caveat: Somalia is an Arab League member but is plausibly perceived as Black African. Iraq-Somalia gaps are not clean "within-Arab" evidence.

### 1.4 Does "Arab" / "MENA" work as one category?

- **Established:** outsiders apply one MENA category across Arab, North African and Iranian cues (`maghbouleh2022middle`). Most Arab-origin groups self-identify as MENA when offered (`mathews2017national`). Names signal "foreign / Muslim", not a country: Moroccan names assigned to Morocco by only 34% of Flemish respondents (`martiniello2022signaling`).
- **Established limits of the category:** Somali 0.0% and Sudanese 8.0% chose MENA; 34.0% of Lebanese still chose White (`mathews2017national`). Caveat from the report: Somali was printed as an example under Black in every questionnaire version, which may have steered Somali respondents. Djiboutian and Mauritanian were also outside the working classification; their figures were not extracted. OMB adopted MENA in 2024 **and** requires detailed nationality subcategories by default (`omb2024revisions`).
- **Mixed on name signal:** a standard name classifier lumps 11 Arab countries into one leaf (`ye2017nationality`); a dedicated classifier recovers country from transliterated full names at 67% vs a 44.3% baseline (`mubarak2015classifying`). Machines, not human perceivers.
- **Absent (not found):** a human name-perception study that tests whether perceivers can tell Arab nationalities apart (e.g. Egyptian vs Syrian vs Moroccan names).

## 2. Evidence on both sides

**For differentiation among Arab origins**
- `vernby2019immigrants`: Iraq 10% vs Somalia 5% callbacks, p < .01 (Sweden).
- `ahmad2026name`: Iraqi 13.4% vs Somali 9.9% (2016); 20.2% vs 16.8% (2024) (Finland).
- `hainmueller2015hidden`: Iraqi penalised (US; abstract).
- `bansak2016economic`: Syria preferred to Iraq (small).
- `alqudsi1991relative`: earnings progress varies by "ethnic background" across nine nationality groups (Kuwait; abstract).
- `kapiszewski2006arab`: state-level differential treatment by Arab nationality; secondary 1980 quote on distinct attitudes toward Palestinians/Jordanians, Yemenis, Egyptians.
- `mathews2017national`: nationalities differ in how far they accept the pooled label.
- Already in matrix: `koopmans2019taste`, `distasio2024same`.

**Against differentiation / for lumping**
- `shockley2024sharing`: no significant nationality differences relative to Yemeni baseline; "matters very little" whether Western, South Asian or Arab.
- `blaydes2023arab`: Arab expatriates favour "fellow Arabs" as one in-group.
- `barron2023discrimination`: only small Jordanian-Syrian discrimination; none among Jordanians with Palestinian roots.
- `bansak2016economic`: origin "plays only a minor role"; religion dominates.
- `valfort2020anti`: with origin fixed (Lebanon), religion drives the gap.
- `martiniello2022signaling`, `maghbouleh2022middle`, `ye2017nationality`: perceivers and tools operate at the pooled level.
- `alfarhan2019migrant`, `gardner2013portrait`: researchers themselves pool "Arab".

## 3. Rankings reported (top / bottom)

| Source | Setting | Top | Bottom | Level |
|---|---|---|---|---|
| `vernby2019immigrants` | Sweden, callbacks | Sweden 21%, Poland 17% | Iraq 10%, Somalia 5% | fulltext |
| `ahmad2026name` | Finland, callbacks 2016 | Finnish 39.0%, English 26.9%, Russian 22.8% | Iraqi 13.4%, Somali 9.9% | fulltext |
| `ahmad2026name` | Finland, callbacks 2024 | Finnish 41.6%, English 30.3% | Iraqi 20.2%, Somali 16.8% | fulltext |
| `bansak2016economic` | 15 European countries, asylum | Syria, Ukraine | Kosovo (Afghanistan, Iraq, Pakistan, Eritrea in between); max gap 4 pp | fulltext |
| `hainmueller2015hidden` | US, admission | not stated in abstract | Iraqi | abstract |
| `gardner2013portrait` | Qatar, low-income pay | Egypt QR1,454, Philippines QR1,443 | Nepal QR853 | fulltext |
| `shockley2024sharing` | Qatar, residency | no significant ordering | British penalised by lower-income citizens | fulltext |
| `kapiszewski2006arab` | GCC, expulsions 1990-91 | n/a | Yemenis, Jordanians, Palestinians (also Iraqis, Sudanese "distrusted") | fulltext, grey |
| `mathews2017national` | US, takes MENA label | Jordanian 94.4% MENA | Somali 0.0%, Sudanese 8.0% | fulltext |
| `alqudsi1991relative` | Kuwait, earnings | not verified | not verified | abstract |

## 4. Flags for the design (no new factors)

1. **Arab League ≠ "Arab/MENA" as perceived.** Somalia, Sudan (and by extension Djibouti, Comoros, Mauritania; not tested in the sources) sit outside the MENA label and are treated as a racial contrast in the Nordic audits. A within-Arab dispersion estimate driven by these origins needs that caveat. Reporting dispersion with and without them would be an analysis choice, not a new factor; pre-register if wanted.
2. **Religion is the stronger channel in humans** (`bansak2016economic`, `valfort2020anti`). Origins with a visible non-Muslim share (Lebanon, Egypt) may behave differently for that reason. Keep the religion text flag.
3. **Politics drives origin-specific treatment in the Gulf** (`kapiszewski2006arab`): Yemeni, Palestinian, Jordanian, Iraqi, Sudanese, Egyptian episodes. Supports the conflict flag and the training-vintage threat (C9).
4. **Inside-region experiments mostly find little differentiation.** A small or null within-Arab dispersion in LLMs would match the human experimental evidence from the Gulf. Do not present heterogeneity as the expected result.
5. **Names:** our no-name design is supported by `martiniello2022signaling`; `mubarak2015classifying` shows surnames could leak region to a model, another reason to keep names out.
6. **Host-national line:** only weak human evidence on nationals vs Arab expatriates in hiring with qualifications fixed (none experimental). `host_national` contrasts have no human benchmark.

## 5. Verified but not added (kept out to hold the set near 20)

All confirmed to exist; level in brackets. Add later if needed.

- Ghekiere et al. 2025, *Scientific Data* 12, doi:10.1038/s41597-025-06153-8 [fulltext]. Name-perception dataset, 1,078 names, 9 European countries, 8,240 respondents; "Muslim" names = Moroccan, Turkish, Pakistani; congruence measured at **region** level.
- El-Sayed, Lauderdale & Galea 2010, *Ethnicity & Health* 15(6):639-647, doi:10.1080/13557858.2010.505979 [abstract]. Arab name algorithm vs self-reported Arab ancestry: specificity 98.9%, sensitivity 50.3%, PPV 57.0%. Pooled "Arab".
- d'Urso 2024, *Perspectives on Politics* 22(2):559-576, doi:10.1017/S1537592722003309 [fulltext]. Russia vs Iran × Muslim vs Christian, n = 1,091; origin and religion additive. States "I did not vary across different MENA countries of origin". No Arab country.
- Alrababa'h et al. 2021, *Comparative Political Studies* 54(1):33-76, doi:10.1177/0010414020919910 [abstract]. Jordan; conjoint on Syrian refugee profiles; humanitarian and cultural over economic concerns. Origin not varied.
- Alaref et al. 2020, World Bank PRWP 9361, doi:10.1596/1813-9450-9361 [abstract]. Tunisia; 1,571 resume pairs; gender; veiled women −8.5 pp. Grey.
- Hartnett 2018, *Review of Middle East Studies* 52(2):263-282, doi:10.1017/rms.2018.91 [abstract]. Jordan; more Syrians in a subdistrict, more informality for Egyptians.
- Almasri 2021, *Middle East Critique* 30(2):185-203, doi:10.1080/19436149.2021.1911459 [abstract]. Jordan Compact as nationality-based prioritisation of Syrians over other non-Jordanians.
- Lenner & Turner 2019, *Middle East Critique* 28(1):65-95, doi:10.1080/19436149.2018.1462601 [abstract]. Jordan Compact.
- Diop et al. 2017, *Social Inclusion* 5(1):66-79, doi:10.17645/si.v5i1.798 [abstract]. Qataris' preference for Arab vs Western migrant neighbours. Pooled "Arab".
- Diop et al. 2012, *J. Arabian Studies* 2(2):173-187, doi:10.1080/21534764.2012.735453 [abstract]. Qataris: high- vs low-skilled migrants.
- Diop et al. 2018, *Int. J. Event and Festival Management* 9(3):266-278, doi:10.1108/IJEFM-09-2017-0058 [abstract]. Qataris favourable toward "Arab and Asian expatriates". Pooled.
- Al-Khelaifi et al. 2025, *IJPOR* 37(4) edaf045, doi:10.1093/ijpor/edaf045 [abstract + summary]. Skill level only; no nationality split. Screened out.
- Jureidini 2014, *Migrant Labour Recruitment to Qatar*, Qatar Foundation, ISBN 978-9927-101-75-5 [fulltext, grey]. Same job, different pay by nationality (Turkish mason USD 1,135 vs Indian 202-243, Nepali labourer 162-176). Asian origins only; no Arab comparison.
- Ahmad 2020, *Sociological Inquiry* 90(3):468-496, doi:10.1111/soin.12276 [abstract]. Original report of the 2016 Finnish wave; numbers taken from `ahmad2026name` instead.
- Awad, Hashem & Nguyen 2021, *Identity* 21(2):115-130, doi:10.1080/15283488.2021.1883277 [abstract]. n = 146; 51% comfortable with the "Arab American" label.
- Thiollet 2011, *ILWCH* 79(1):103-121, doi:10.1017/S0147547910000293 [abstract]. Migration as Arab regional diplomacy.
- Parrillo & Donoghue 2005, *Social Science Journal* 42(2):257-271, doi:10.1016/j.soscij.2005.03.011 [abstract]. Bogardus replication, n = 2,916. Abstract does not state where Arabs or Muslims rank.
- ILO Policy Advisory Committee note, "Minimum wages and wage protection in the Arab States" (n.d.; PAC discussions May 2018), https://www.ilo.org/media/411481/download [fulltext, grey]. "De facto nationality-based wage scales". No Arab nationalities compared.
- El-Haj 2025, ArabJobs corpus, arXiv:2509.22589 [fulltext scan]. 8,546 ads from Egypt, Jordan, Saudi Arabia, UAE. No nationality-requirement analysis; could be used to count such ads.

## 6. Unverified leads (not in the bib; do not cite)

- Birks & Sinclair 1980 (*Arab Manpower*), p. 116: the quote on GCC nationals' attitudes toward Palestinians/Jordanians, Yemenis, Egyptians. Seen only as quoted in `kapiszewski2006arab`. Original not located.
- Al-Qudsi & Shah 1991 full text: which nine groups, and their ranking. Paywalled.
- Alfarhan & Al-Busaidi 2019 full text: data source, countries, size of Western-Arab and Arab-Asian gaps. Paywalled.
- Hainmueller & Hopkins 2015 full text: effects for origins other than Iraq (the abstract names only Iraqi). No open copy reachable.
- Babar (ed.) 2017, *Arab Migrant Communities in the GCC* (book). Only an SSRN "summary report" record found (doi:10.2139/ssrn.2840380); book not verified.
- GulfTalent "Employment and Salary Trends in the Gulf" (commercial reports; press coverage quotes pay gaps by Western / Arab / Asian). Reports not read.
- The National (UAE), 2018-2019 news scans of job ads stating nationality. News, not research.
- KAS Regional Programme Gulf States, "Regulating Passport-Based Wage Differentials in the Gulf". Surfaced, not read.
- "Exploring Salary Brackets for Different Nationalities in the UAE" (ResearchGate, 2025). Unvetted; venue unknown.
- "Expatriate jobs and productivity: Evidence from two GCC economies" (ScienceDirect S0954349X24001012). Nationals vs migrants; not read.
- Shah 2000, *IMR*, "Relative Success of Male Workers in the Host Country, Kuwait" (doi:10.1177/019791830003400103 per search result). Groups not checked.
- UAE wage-structure working papers (Tong; Al Awad; Vazquez-Alvarez), recalled from memory. Not found in OpenAlex. Unverified.
- Hagendoorn 1995 (ethnic hierarchies); Snellman & Ekehammar 2005. Recalled from memory; not found by OpenAlex title search. Unverified.
- Arab Opinion Index (ACRPS) item on Arabs as one nation; Stereotype Content Model samples collected in Arab countries. Recalled, not checked.
- Al-Waqfi & Forstenlechner 2010 (stereotyping of citizens, UAE). OpenAlex title search did not return it. Unverified.
- Emarat Al Youm (2011) news item on a "specialised study" of Western pay premia. Study not identified.

## 7. Sources not accessible

- SAGE (403): *International Migration Review* (Al-Qudsi & Shah; Ewers et al.), *Research & Politics* landing page (Blaydes & Gengler read from the author's posted PDF instead).
- Wiley (paywall): *International Labour Review* (Alfarhan), *AJPS* (Hainmueller & Hopkins), *Sociological Inquiry* (Ahmad 2020).
- tandfonline (paywall): *JEMS* (Abdulrahim & Khawaja).
- ScienceDirect (paywall): *International Business Review* (Al Ariss & Guo), *JDE* (Krafft), *World Development* (Valfort; DP version read).
- un.org live URL for Kapiszewski: 404 / HTML on 2026-10-04. Read from a Wayback capture.
- University of Helsinki repository (bot wall), HAL (blocked), Cogitatio PDF (empty file), Stanford and MIT copies of Hainmueller & Hopkins (HTML), SSRN (blocked).
- Semantic Scholar: not used (rate limits). Google Scholar: not accessible.

## 8. Search log (2026-10-04)

### Web search (general engine; candidates then verified via Crossref / OpenAlex / source)

| # | Query | Relevant hits | Added |
|---|---|---|---|
| 1 | wage differentials by nationality Gulf GCC Arab expatriates Egyptian Jordanian Lebanese controlling for education study | Alfarhan; news (muwatin, Khaleej Times, WTW) | `alfarhan2019migrant` |
| 2 | correspondence study field experiment hiring discrimination Syrian refugees Jordan Lebanon employers nationality callback | Vernby; Caria et al. job-search RCT (not origin) | `vernby2019immigrants` |
| 3 | job advertisements nationality requirement preferred nationality Gulf UAE Qatar discrimination content analysis study | news only | none |
| 4 | Census Bureau 2015 National Content Test MENA category research findings … | NCT report | `mathews2017national` |
| 5 | "nationality" wage gap Qatar OR Kuwait OR "Saudi Arabia" "Arab" migrants "Egyptian" "Jordanian" earnings regression … | Alfarhan again | none new |
| 6 | Maghbouleh Schachter Flores "…may not be perceived, nor perceive themselves, to be White" PNAS | PNAS paper | `maghbouleh2022middle` |
| 7 | field experiment resume audit Egypt OR Jordan OR Lebanon OR Morocco OR Tunisia labor market discrimination correspondence study … | Egypt (gender), Tunisia (gender) | `krafft2025employers` |
| 8 | Arabic names country of origin signal perception validation study … | Martiniello; Ghekiere; Mubarak & Darwish | `martiniello2022signaling`, `mubarak2015classifying` |
| 9 | Palestinians Lebanon labour market discrimination employers survey ILO wage gap … | ILO/CEP reports (not read) | `abdulrahim2011cost` (via OpenAlex) |
| 10 | conjoint experiment Jordan attitudes toward Syrian refugees Alrababa'h … | Alrababa'h; Barron | `barron2023discrimination` |
| 11 | survey experiment Qatar citizens attitudes toward immigrants nationality Arab Western Asian conjoint … SESRI | Shockley & Gengler; Blaydes & Gengler; Diop | `shockley2024sharing`, `blaydes2023arab` |
| 12 | social distance scale Arab nationalities Kuwait OR Saudi OR Emirati OR Jordanian students attitudes toward Egyptians Palestinians Syrians Lebanese study | none relevant | none |
| 13 | "nationality" "job advertisements" Saudi Arabia OR Kuwait OR UAE OR Qatar content analysis discrimination academic study … | news; ArabJobs corpus | none |
| 14 | ILO Jordan employers preference Egyptian Syrian Jordanian workers "A challenging market becomes more challenging" Razzaz … | ILO report; Almasri; Hartnett | `razzaz2017challenging` |
| 15-18 | title look-ups: Blaydes & Gengler pdf; Diop et al. 2012; Al Ariss & Guo; Gardner et al. | open copies / abstracts | `gardner2013portrait`, `alariss2016job` |
| 19 | Kapiszewski "Arab versus Asian migrant workers in the GCC countries" UN/POP/EGM/2006/02 pdf | UN paper | `kapiszewski2006arab` |
| 20 | correspondence experiment fictitious resumes Jordan OR Lebanon OR Kuwait OR "Saudi Arabia" OR UAE … refugee OR nationality OR sect "callback" | none in region | none |
| 21 | stereotypes of Arab nationalities among Arabs survey Egyptians Lebanese Saudis Syrians perceived traits intra-Arab stereotypes study | Quora; dialect-attitude studies | none |
| 22 | Lebanon hiring discrimination field experiment sectarian names OR Syrian applicants correspondence audit study employers Beirut | none in Lebanon; Valfort (France) | `valfort2020anti` |
| 23 | GulfTalent "Employment and Salary Trends in the Gulf" salary by nationality … | commercial reports | none (lead) |
| 24 | Lebanese OR Egyptian OR Jordanian OR Syrian expatriates Gulf "wage" "nationality" hierarchy among Arab migrants … | Al-Qudsi & Shah; ILO note | `alqudsi1991relative` |
| 25 | (AR) التمييز في الأجور حسب الجنسية بين الوافدين العرب في دول الخليج دراسة المصريين الأردنيين اللبنانيين | news and think-tank pages; no study comparing Arab nationalities | none |
| 26 | Babar "Arab Migrant Communities in the GCC" … | search failed | none (lead) |
| 27 | study analysis online job postings Gulf "nationality" requirement "Arab nationals" OR "Arabic speakers" preferred … | none | none |
| 28 | Jureidini "Migrant Labour Recruitment to Qatar" … | QF report | none (section 5) |
| 29 | Ewers Diop Le Bader "Migrant worker well-being …" | not about nationality | none |
| 30 | Ahmad "When the Name Matters" Finnish labor market … | Ahmad 2020; Ahmad 2026 | `ahmad2026name` |
| 31-32 | full-text hunts: Al-Qudsi & Shah 1991; Alfarhan & Al-Busaidi 2019 | no open copy | none |

### OpenAlex (`works?search=`; about 45 queries, top 2-8 read)

- Title / author verification for every candidate.
- Discovery queries with no new relevant hit: "wage inequality nationality United Arab Emirates labor market …"; "job advertisements nationality discrimination Gulf …" (352 hits, top 8); "nationality-based wage discrimination expatriates Gulf passport premium" (31); "Arab versus Asian migrant workers …" (201; Thiollet, Baldwin-Edwards); and the six saturation queries: stereotype content of Arab national groups (19), social-distance ratings of Arab nationalities (66), ethnic hierarchy Moroccans/Turks/Iraqis/Syrians/Somalis (163), correspondence study Syrian refugees Jordan employers (96), job-ad nationality content analysis GCC (279), intra-Arab national stereotypes (143). All off-topic in the top 8.
- New from OpenAlex: `ewers2021bargaining`, `bansak2016economic`, `hainmueller2015hidden`, `ye2017nationality`; El-Sayed 2010; d'Urso; Awad 2021; Hartnett; Almasri.

### Other APIs

- Crossref `works/<DOI>`: 29 look-ups (authors, volume, issue, pages, dates). Caught one wrong author list recalled from memory (the Egypt audit is Krafft, single author).
- Europe PMC: full-text XML for Maghbouleh 2022, Ghekiere 2025, Ahmad 2026.
- Unpaywall: 9 DOIs checked for open copies (3 open).
- Federal Register API: document 2024-06469 (record and raw text).
- arXiv abs page: 2509.22589.

### Full texts read (curl + pdftotext, or XML)

Vernby & Dancygier 2019; Martiniello & Verhaeghe 2022; Maghbouleh et al. 2022; Ghekiere et al. 2025; Census NCT report (exec. summary, section 5.2); Shockley & Gengler 2024; Blaydes & Gengler 2023; Gardner et al. 2013; Bansak et al. 2016 (accepted ms.); Valfort (IZA DP 11417); d'Urso 2024; Mubarak & Darwish 2015; Ye et al. 2017 (arXiv); Razzaz 2017 (parts); Kapiszewski 2006 (Wayback); Jureidini 2014 (parts); Barron et al. 2023 (accepted ms., abstract and design only, so the row stays at abstract level); Ahmad 2026; OMB 2024 notice; ILO PAC note; ArabJobs.

## 9. Coverage limits

- One day, one researcher pass. Stopped when the six saturation queries returned nothing new.
- Arabic: one web query. No Arabic bibliographic index searched. Arabic-language Gulf sociology (e.g. Kuwait University, Qatar University journals) is **not covered**; within-Arab attitude studies may exist there.
- No Google Scholar, no Semantic Scholar, no SSRN or EconLit search. Gulf HRM journals not browsed.
- Books not covered (Longva; Kapiszewski 2001; Babar 2017; Lori 2019). These are where most within-Arab qualitative evidence is likely to sit.
- 8 of 23 rows are abstract-level. For `alqudsi1991relative`, `alfarhan2019migrant` and `hainmueller2015hidden` the full text is needed before any ranking or effect size is cited. `barron2023discrimination`: results from the abstract; only sample size and setting were read in the manuscript.
- "fulltext" here means the sections relevant to nationality or origin were read, often through keyword extraction of the PDF text, not a cover-to-cover reading. `razzaz2017challenging` (158 pages) and `mathews2017national` (long report) were read in part.
