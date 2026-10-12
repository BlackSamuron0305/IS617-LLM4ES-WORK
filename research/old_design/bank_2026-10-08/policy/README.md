# Policy

The written policy the model is given, as the review products in this field are given
the institution's own procedures. Written on 2026-10-08. The bank, "Lindenufer Bank", is
invented; a web search on 2026-10-08 found no bank of that name. The name also appears in
`../prompts/main_prompt.txt`.

| file | what it is |
|---|---|
| `bank_policy.txt` | the policy. The last line is the placeholder `{nationality_rule}` |
| `nationality_rule.txt` | section 6, the paragraph on nationality |

**Two versions.** In the version *without the nationality rule* the placeholder is
removed. In the version *with the nationality rule* it is replaced by the text of
`nationality_rule.txt`. The two versions therefore differ only by that paragraph.

## Where each part comes from

The policy is a short paraphrase of public rules. It is not a real bank's policy and it
is not legal advice. All sources were read on 2026-10-08.

| section | based on |
|---|---|
| 2, first sentences | EBA guidelines on risk factors (EBA/GL/2021/02), guideline 3.3: "the presence of isolated risk factors does not necessarily move a relationship into a higher or lower risk category" |
| 2 (a), (c), (d) | the factor groups of annex 2 of the German anti-money-laundering act (GwG): customer; product, service, transaction and delivery channel. The single items are shortened and chosen for a private current account |
| 2 (b) | EBA/GL/2021/02, guideline 2.9: "the jurisdictions in which the customer is based or is resident", "main places of business", "relevant personal or business links, or financial or legal interests". "Main places of business" was turned into "where the income is earned" for a private customer |
| 3 | § 15 (3) GwG: higher risk where a relationship or transaction involves a high-risk third country identified by the European Commission "oder eine in diesem Drittstaat ansässige natürliche oder juristische Person" (or a person resident there). The 26 countries are the Commission's list as shown on its website, last changed with effect from 29 January 2026 |
| 4 and 5 | written for the experiment. Real banks use their own scales |
| 6 (`nationality_rule.txt`) | § 3 of the German payment accounts act (ZKG): consumers legally resident in the EU must not be disadvantaged on account of their nationality when opening a payment account; and EBA guidelines EBA/GL/2023/04, paragraphs 9 and 10: distinguish the risk of a category from the risk of the individual customer, no "blanket refusal or termination of business relationships with entire categories of customers" |

**Nationality in the rules.** The word "nationality" does not occur in the 225 pages of
EBA/GL/2021/02 (full-text search). In annex 2 of the GwG it occurs only for people who
obtain residence or citizenship in return for investments. The country factors are about
where a customer lives, earns and has ties. The policy without section 6 follows that: it
does not mention nationality at all.

## Rules when editing

- The two versions must differ only by section 6.
- If the list in section 3 is updated, update `eu_high_risk_list` in
  `../countries/customer_nationalities.csv` as well and note the date in both places.
- Fix the policy before the pilot. Do not change it after seeing results.

## Open

- Whether the list of countries stays in the policy. With the list the test is whether
  the model applies a rule about residence to a passport. Without it the model has to
  rely on what it has learned about countries.
- The policy is in English although a German bank's policy would be in German.
  German-language prompts are on the parked list (`CLAUDE.md`).
