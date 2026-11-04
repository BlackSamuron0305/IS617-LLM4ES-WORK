# L3 literature notes (part 3): HUMAN field experiments on hiring discrimination against Middle Eastern / Arab / North African applicants

Internal research notes, telegraphic. Not report prose. Do not paste into `paper/` (AI-usage rule in `CLAUDE.md`).

- Compiled: 2026-10-04.
- Companion files: `L3_matrix.csv` (35 rows, strand `human_audit`), `L3_refs.bib` (same 35 keys).
- Verification levels as in `literature_review.md`: **fulltext** = relevant sections read; **abstract** = abstract or official summary only; **metadata** = record confirmed, content not read.
- Counts: 16 fulltext, 19 abstract, 0 metadata. Nothing unverified is in the matrix or the bib.
- All rows are HUMAN studies. None is LLM evidence. `novelty_threat` = none for 32 rows, low for 3 (`vernby2019immigrants`, `thijssen2021ethnic`, `polavieja2023face`).
- Scope: fills the gaps named in the brief (Maghrebi group in FR/BE/NL/IT/ES; Arab/Middle Eastern outside Europe; post-2020 syntheses; signal and pooling per study). The 19 `human_audit` rows already in `literature_matrix.csv` were not re-added.

## 1. Question and short answer

Question: does the evidence support "hiring discrimination against Middle Eastern and North African applicants is well documented"?

- **Yes, for name-signalled origin in Western labour markets.** Large, replicated gaps in France, Belgium, Netherlands, Sweden, Denmark, Italy, Australia. Pooled estimate already in the matrix: `lippens2023state` DR 0.5937. Re-checked in full text today: k = 31 effects, 69,311 observations, **I² = 87.37%**, i.e. effect sizes differ a lot between studies.
- **Not uniform.** French ratios alone run from about 1.3 (`foroni2016discrimination`) to 4 (`duguet2010young`; `arnoult2021discrimination` lists the range). Several nulls and sub-context reversals (section 4).
- **Not MENA-specific in many multi-group studies.** Other groups are penalised as much or more (section 5).
- **Thin outside Western Europe and Australia.** US: one small Arab-name study (`widner2011name`); the two US religion studies found are mixed (`wallace2014religious` penalty, `acquisti2020experiment` national null). Canada: two small Québec studies.
- **No field experiment found inside an Arab country.** Only MENA-region study: Israel (`ariel2015ethnic`), Arabs as native minority. Our stimuli are set in the Gulf, Jordan and Egypt: the human evidence does not cover that setting.
- **"MENA" in this literature is almost always a name.** North African-sounding names in FR/BE/NL/IT, "Arabic"/"Middle Eastern" names in SE/DK/AU/US. Nationality is deliberately absent in most designs.

## 2. Search log

| # | Source | Query / action | Hits | Added / outcome |
|---|---|---|---|---|
| S1 | Crossref `query.bibliographic` | 36 author+title look-ups for leads (FR, BE, NL, IT, SE, DK, FI, US, CA, AU, IL, multi-country) | published version found every time (first or second hit); for Booth, Acquisti and Brière the top hit was the SSRN version | DOI and record for every added source |
| S2 | Crossref `/works/<DOI>` | about 50 DOI look-ups | all resolved | authors, title, volume, issue, pages for all 31 DOI-bearing rows; 9 existing-matrix DOIs re-checked |
| S3 | OpenAlex `/works/doi` | same DOIs, for abstracts and open-access locations | abstracts for most; none for Valfort 2020, Edo 2019, Duguet 2010, Baert 2017, Challe 2024, Wright 2013, Rooth 2010, Carlsson & Rooth 2007 | abstracts; OA copies located |
| S4 | OpenAlex search | "correspondence study hiring discrimination Arab American resume audit" | 152, top 12 read | none new for the US. Screened: Rémy & Valat 2025 (survey, out), Quillian & Midtbøen 2021 (review) |
| S5 | OpenAlex search | "field experiment hiring discrimination Arab applicants Israel correspondence" | 188, top 12 | `ariel2015ethnic` |
| S6 | OpenAlex search | "correspondence experiment hiring discrimination nationality Gulf OR Qatar OR "United Arab Emirates" OR "Saudi Arabia" OR Lebanon OR Jordan" | 2,005, top 12 | **nothing**: no audit set in an Arab country |
| S7 | OpenAlex search | "meta-analysis hiring discrimination correspondence Muslim OR Arab OR "Middle Eastern" 2021 2022 2023 2024" | 954, top 12 | nothing new; no post-2020 meta-analysis with separate Middle Eastern / North African / single-origin estimates |
| S8 | OpenAlex search | "correspondence study Syrian refugees hiring discrimination field experiment" | 262, top 12 | none added. Screened: Erlandsson 2024 (origin not stated in abstract) |
| S9 | Web (FR) | `DARES Analyses 2021 "discrimination à l'embauche" personnes d'origine supposée maghrébine testing grande étude` | 9 | `arnoult2021discrimination` (IPP note PDF) |
| S10 | Web (FR) | `"discrimination à l'embauche" testing "prénom maghrébin" OR "origine maghrébine" étude correspondance taux de rappel résultats` | 9 | `enejones2013discrimination`; INSEE and press pages not used |
| S11 | Web (FR) | `Valfort Institut Montaigne "Discriminations religieuses à l'embauche : une réalité" testing libanais musulman catholique juif résultats` | 9 | `valfort2015discriminations` (report PDF) |
| S12 | Web (EN) | `Duguet Leandri L'Horty Petit "Are young French jobseekers of ethnic immigrant origin discriminated against" Moroccan nationality name pdf` | 10 | `duguet2010young`; surfaced `challe2024cyclical` |
| S13 | Web (EN) | `Cediey Foroni 2008 ILO "Discrimination in access to employment on grounds of foreign origin in France" ...` | 10 | `cediey2008discrimination` (ILO PDF) |
| S14 | Web (FR) | `Foroni Ruault Valat 2016 Dares Analyses 076 ...` and the exact title | 9 + 9 | `foroni2016discrimination` (read via web.archive.org) |
| S15 | HAL API (`api.archives-ouvertes.fr`) | halId halshs-02973605; title search for Duguet et al. | 1; 2 | abstract of `valfort2020anti`; abstract of `duguet2010young` |
| S16 | Europe PMC full-text XML | PMC9963383, PMC10148976 | 2 | full text of `quillian2023trends`, `challe2024cyclical` |
| S17 | RePEc/IDEAS pages | version links for Duguet et al. | 3 | TEPP WP 2010-1 PDF |
| S18 | Semantic Scholar | 2 DOI look-ups only (no searches) | Wright 2013: abstract elided by publisher; Carlsson & Rooth 2007: abstract returned | confirms the existing `carlsson2007evidence` row |
| S19 | Page reader (WebFetch) | OUP pages for Polavieja, Fernández-Reino, Blommaert | 3 | Blommaert abstract verbatim; Polavieja details recorded as **unchecked**; Fernández-Reino abstract only |
| S20 | Reference lists | IPP note n°76; thijssen2021ethnic; lippens2023understanding | – | leads: Foroni 2016, Pierné 2013, Baert 2017, Martiniello 2022, Berson 2012, Challe 2020 |

Full texts read (PDF or XML, relevant sections): IPP note n°76; Dares Analyses 076; ILO IMP 85E; TEPP WP 2010-1 (Duguet); CEPREMAP Docweb 1313 (Edo); Pierné 2013; Institut Montaigne 2015; Challe 2024; IZA DP 8517 (Behaghel, intro only); Baert 2017; Lippens 2023 (Labour Economics); Thijssen 2021; Busetta 2018; Vernby 2019; IZA DP 4947 (Booth); Adamovic 2023; Quillian & Lee 2023; plus Lippens 2023 (EER) to re-check the existing row.

Stopping rule: OpenAlex S4 to S8 and the reference lists returned only already-known studies or off-topic hits.

Not searched: Google Scholar (not accessible); Semantic Scholar search (rate limits, per brief); Dutch-, Italian- and Spanish-language queries; Cairn/Persée full-text search; Belgian city reports (Ghent, Antwerp, Brussels testing); SCP and Panteia reports for the Netherlands.

## 3. How each study signals the group, and whether it pools

"Split" = separate estimates for more than one MENA origin country.

| key | country | signal | MENA category |
|---|---|---|---|
| arnoult2021discrimination | FR | first name + surname; nationality deliberately absent | pooled Maghrebi |
| foroni2016discrimination | FR | first name + surname | pooled Maghrebi |
| cediey2008discrimination | FR | first name + surname; all French nationals; partly in person | pooled North African |
| duguet2010young | FR | **explicit Moroccan nationality line**, surname, first name, varied separately | one origin (Morocco) |
| edo2019language | FR | names (North African vs unidentifiable foreign) | pooled North African |
| pierne2013hiring | FR | name for origin; volunteering organisation for religion | pooled North African |
| valfort2015discriminations / valfort2020anti | FR | **birth in Lebanon and naturalisation stated**; religion via first name, school, scouting | one origin (Lebanon), held constant |
| challe2024cyclical | FR | first name + surname | pooled North African |
| enejones2013discrimination | FR | first name + surname (per report version) | pooled Maghrebi |
| baert2017does | BE | names; all Belgian nationals | Moroccan only |
| lippens2023understanding | BE | names; all Belgian nationals | Moroccan only ("Maghrebian") |
| thijssen2021ethnic | NL | name + mother tongue + cover-letter sentence on birth abroad | pooled MENA region; Moroccan (and Turkish) separate |
| andriessen2012ethnic | NL | names | Moroccan among four groups (per secondary source) |
| ramos2021labour | NL, ES | not stated in abstract (GEMM) | Moroccan only |
| derous2012multiple, derous2015double | NL | not stated in abstract | pooled Arab |
| busetta2018immigrants | IT | name, city of birth, mother tongue, schooling; **nationality defines the group** | Moroccan only |
| bursell2014multiple | SE | names | pooled Arabic and North African |
| vernby2019immigrants | SE | **country of birth stated** + name; citizenship randomised | **split: Iraq vs Somalia** (both Arab League members) |
| carlsson2010experimental | SE | not stated in abstract | pooled Middle East |
| dahl2018experimental | DK | names | pooled Middle Eastern |
| widner2011name | US | names | pooled Arab |
| wallace2014religious | US | religion on résumé | Muslim (religion) |
| acquisti2020experiment | US | religion on social-media profile | Muslim (religion) |
| eid2012inegalites | CA | names | pooled Arab |
| beauregard2019testing | CA | not stated in abstract | pooled Maghrebi |
| booth2012does | AU | names | pooled Middle Eastern |
| adamovic2023glass | AU | names | pooled Arabic |
| quillian2023trends | 6 countries | meta-analysis | pooled MENA incl. Turkish |
| polavieja2023face | DE, NL, ES | name + photo | pooled MENA region (unchecked detail) |
| fernandezreino2023discrimination | DE, NL, ES | volunteering in Muslim centre; headscarf | Muslim (religion) |
| ariel2015ethnic | IL | generic (name) | pooled Arab-Israeli |

Take-aways for the `Cannot answer` bullet in `literature_review.md` §2.3:
- Only **one** new study splits by Arab origin country (`vernby2019immigrants`: Iraq 10% vs Somalia 5%). With the existing `koopmans2019taste`, `distasio2021muslim`, `distasio2024same`, that is the whole human evidence on within-Arab differences found so far.
- Four studies put origin or citizenship on the CV explicitly (`duguet2010young`, `valfort2015discriminations`, `vernby2019immigrants`, `busetta2018immigrants`). The statement that human studies never use an explicit nationality cue needs softening.
- `martiniello2022signaling` and `lippens2023understanding`: respondents tell native from non-native names, not specific origins. `quillian2023trends` uses the same argument to justify pooling. Name-based studies may be unable to detect within-MENA differences even if employers held them.

## 4. Nulls, reversals, small or context-dependent effects

Nulls and near-nulls:
- `challe2024cyclical`: gap "not always significant". Wave 1 significant only in the public sector; waves 2-3 "very few significant differences"; wave 4 (lockdown) none in either sector; wave 5 private sector 17.2 points. Small waves, low power.
- `foroni2016discrimination`: 28 of 40 large firms show no statistically significant gap. Low power per firm.
- `baert2017does`: no unequal treatment at 20 years' experience (ratio slightly above 1). Moroccan-named applicants not different from Slovakian-named.
- `lippens2023understanding`: Maghrebian gap significant on "any positive response" (21.49% fewer), not on interview invitations.
- `arnoult2021discrimination`: store managers are the stated exception; oldest age band 14.0% vs 12.7% with no significance stars (table garbled, re-check).
- `valfort2020anti`: no discrimination against non-religious Muslims of Lebanese origin (comparator: Lebanese Christians, not native French).
- `acquisti2020experiment`: no national Muslim-Christian difference in the US; bias only in Republican areas.
- `duguet2010young`: the explicit nationality line adds only 1.45 points on top of a Moroccan name (significant at 10% only).
- `ariel2015ethnic`: in low-wage jobs, no preference in some regions.
- `thijssen2021ethnic`: Polish applicants show no significant gap (non-MENA, relevant to our Polish benchmark).

Reversals:
- `bursell2014multiple`: female-dominated occupations favour foreign-named men.
- `behaghel2015unintended`: among volunteering firms, anonymising résumés lowered minority interview rates. Not MENA-specific.
- `derous2015double`: Arab women rated above Arab men.

MENA not the most penalised group (when several groups are tested):
- `booth2012does`: Middle Eastern 22%, Chinese 21%.
- `edo2019language`: North African 9.9%, unidentifiable foreign 10.1%.
- `lippens2023understanding`: Eastern European 26.51% fewer vs Maghrebian 21.49%.
- `thijssen2021ethnic`: MENA 31%, South/Central African 32%, Latin American 33%, Antillean 27%.
- `cediey2008discrimination`: sub-Saharan origin as high or higher than North African.
- `adamovic2023glass`: Arabic lowest for leadership jobs; Indian lowest for non-leadership jobs.
- `busetta2018immigrants`: Moroccan and Chinese jointly worst.

Gender:
- Men penalised more: `edo2019language` (ratio about 2 vs 1.6), `cediey2008discrimination` (46-49% vs 27%), `dahl2018experimental`, `valfort2015discriminations` (4x vs 1.4x), `vernby2019immigrants`, `derous2015double`; existing `arai2016reverse`.
- No gender difference: `arnoult2021discrimination`, `thijssen2021ethnic`, `beauregard2019testing`, `booth2012does` (p = 0.15), `foroni2016discrimination`.
- Women penalised more in one sub-study: `derous2012multiple` Study 3 (high-status jobs, prejudice controlled).

Context:
- Destination country: `ramos2021labour` 6 points (Spain) vs 14 (Netherlands); `polavieja2023face` weaker in Spain.
- Time: `quillian2023trends` MENA discrimination higher after 2000 than in the 1990s; linear trend n.s.
- Qualification: weaker gap in qualified jobs (`arnoult2021discrimination`); not offset by a higher diploma (`enejones2013discrimination`); gone at 20 years' experience (`baert2017does`).
- Religion vs origin: both matter separately (`pierne2013hiring`); religiosity rather than affiliation (`valfort2020anti`).

## 5. Checks on rows already in `literature_matrix.csv`

No edits made (brief: edit nothing else). For the maintainer:

1. **`adida2010identifying` is not an Arab audit.** `literature_review.md` §2.3 lists it under "Pooled Arab-name audits". The applicants were of **Senegalese** origin (stated in the full text of `pierne2013hiring`: "one female applicant with a French sounding name and two female applicants with Senegalese sounding names"; also in `valfort2015discriminations`). The matrix row does not name the origin. The 2.5x figure itself matches the abstract.
2. **§2.3 "Cannot answer", second bullet** says human studies do not use an explicit nationality line. `duguet2010young` does (Moroccan nationality on the CV); `vernby2019immigrants` states country of birth and citizenship; `valfort2015discriminations` states birth country and naturalisation; `busetta2018immigrants` defines groups by nationality. Soften to "rarely".
3. `lippens2023state`: numbers confirmed in the full text (DR 0.5937 [0.5548; 0.6353]; Western Asian 0.7508). Row could add k = 31, n = 69,311, I² = 87.37%.
4. `blommaert2014discrimination`: matrix wording matches the abstract (Dutch-named 60% more likely). `thijssen2021ethnic` paraphrases it as Moroccan names "60% less likely"; do not copy the secondary wording. The "Arabic" names are described there as Moroccan.
5. Bibliographic data and quoted figures re-checked and fine: `koopmans2019taste`, `arai2016reverse`, `bartkoski2018meta`, `thijssen2022discrimination`, `zschirnt2016ethnic`, `carlsson2007evidence`.
6. Not re-checked: `quillian2026racialized`, `quillian2019countries`, `distasio2024same`, `distasio2021muslim`, `distasio2020understanding`, `lancee2021ethnic`, `kaas2012ethnic`, `weichselbaumer2020multiple`, `krause2012anonymous`, `bertrand2004emily`.

## 6. Sources that could not be accessed

- **dares.travail-emploi.gouv.fr**: bot wall (Cegedim) on every page and PDF. Dares Analyses n°67 not read (the identical IPP note was); n°076 read from web.archive.org.
- **HAL PDFs** (shs.hal.science, hal.science): Anubis bot wall. HAL API worked for abstracts.
- **ScienceDirect**: 403 (Wright 2013; Valfort 2020).
- **Wiley**: Widner & Chicoine, Derous 2012 and 2015, Carlsson 2010, Ahmad 2020, Booth journal version. Abstracts only.
- **SAGE**: Andriessen 2012, Wallace 2014. Abstracts only.
- **tandfonline**: Ramos 2021. Abstract only.
- **OUP PDFs**: Bursell 2014, Dahl & Krog 2018, Polavieja 2023, Fernández-Reino 2023. HTML reachable only through the page reader.
- **érudit PDFs** (Eid 2012, Beauregard 2019): returned HTML, not the PDF.
- **helda.helsinki.fi** (Ahmad 2020), **digital.csic.es** (Fernández-Reino): Anubis bot wall.
- **INFORMS** (Acquisti & Fong), **JSTOR** (Duguet journal version), **De Gruyter** (Ariel): not attempted beyond the abstract.
- **web.archive.org availability API**: 429; direct snapshot URL worked.
- Supplementary materials not read: Thijssen 2021 Table S2 (list of 35 groups); Quillian & Lee 2023 SI Tables S3, S4, S8.

## 7. Unverified leads and screened-out items (not in the matrix or the bib)

Record confirmed, content not read or not sufficient:
- Wright, Wallace, Bailey & Hyde (2013), "Religious affiliation and hiring discrimination in New England: A field experiment", RSSM 34, 111-126, doi 10.1016/j.rssm.2013.10.002. Crossref record confirmed; abstract not retrievable. Companion of `wallace2014religious`.
- Ahmad (2020), "When the name matters", Sociological Inquiry 90(3), 468-496, doi 10.1111/soin.12276. Abstract read: five backgrounds, Finnish preferred, European over non-European names. The groups are **not named in the abstract**; an Iraqi group is a lead from memory only.
- Brière, Fortin & Lacroix (2020), L'Actualité économique 94(3), 285-307, doi 10.7202/1068040ar. Abstract read: about 10 points lower for a Maghrebi-named woman, Québec City. The CIRANO working-paper version reports 100 CVs to 50 ads. Too small to add.
- Erlandsson (2024), Acta Sociologica 67(2), 232-250, doi 10.1177/00016993231201482. Abstract read: Sweden, 5,641 applications, "foreign-sounding" names, men discriminated more. Origin not stated in abstract.
- Ahmed & Gorey (2023), J. Ethnic & Cultural Diversity in Social Work 32(3), 115-123, doi 10.1080/15313204.2020.1870601. Abstract read: hijab meta-analysis, 7 studies, RR 0.60 [0.54, 0.67]. Religious dress, not origin.
- Quillian & Midtbøen (2021), Annual Review of Sociology 47, 391-415, doi 10.1146/annurev-soc-090420-035144. Abstract read: review of 140+ field experiments in 30 countries. Nothing MENA-specific in the abstract. Possible background cite.
- Heath & Di Stasio (2019), BJS 70(5), 1774-1798, doi 10.1111/1468-4446.12676. Abstract read: British meta-analysis; groups are Caribbean, African, Pakistani, Indian, Chinese, white minorities. No MENA group in abstract.
- Rémy & Valat (2025/2026), Industrial Relations 65(1), 3-23, doi 10.1111/irel.12390. Abstract read: establishment survey on recruitment of candidates with Arab-Muslim names. Not a field experiment.
- King & Ahmad (2010), Personnel Psychology 63(4), 881-906; Ghumman & Ryan (2013), Human Relations 66(5), 671-698; Rooth (2010), Labour Economics 17(3), 523-534. Crossref records confirmed; content not read.

Known only from reference lists or secondary mentions (existence not independently confirmed):
- Berson (2012), "Does competition induce hiring equity?", CES working paper 12019 (ratio 4 per IPP note n°76).
- Challe, Chareyron, L'Horty & Petit (2020), "Discrimination dans le recrutement des grandes entreprises : une approche multicanal", HAL hal-02441144 (20% gap, 110 large firms, per IPP note n°76).
- Andriessen, Nievers, Faulk & Dagevos (2010), "Liever Mark dan Mohammed?", SCP report; Panteia (2015); Bovenkerk, Gras & Ramsoedh (1995) (all via `thijssen2021ethnic`).
- Baert, Cockx, Gheyle & Vandamme (2015), Turkish names in Flanders (via `baert2017does`, `lippens2023understanding`).
- Public-sector testing in France, 2016 (mentioned in `foroni2016discrimination`).

Leads from memory that were **not checked at all** (may not exist as described):
- ILO national studies for Italy (Allasino et al.) and Spain (Colectivo IOE / de Prada et al.) with Moroccan testers.
- Belgian city-commissioned correspondence tests (Ghent, Antwerp, Brussels).
- US in-person audits of Muslim attire after 2001.

Could not confirm, left out: any correspondence or audit study in which applicants of different Arab nationalities apply to employers inside an Arab country.
