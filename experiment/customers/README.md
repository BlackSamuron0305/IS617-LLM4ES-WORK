# Customers

Written on 2026-10-08. Everything here is invented. No real person, bank customer or
employer was used.

| file | what it is |
|---|---|
| `customers.csv` | one row per customer. No nationality: it is filled in when the prompt is built |
| `customer_file_template.txt` | the layout that turns one row into the customer file the model reads |

## How a customer file reaches the model

1. Take one row of `customers.csv` and fill it into `customer_file_template.txt`
   (`{{NAME}}` placeholders).
2. Fill the three lines that depend on the nationality from one row of
   `../countries/customer_nationalities.csv`: `{nationality}`, `{identity_document}` and
   `{residence_status}`.

Every version of a customer file is therefore identical except for those three lines.
For the 27 nationalities other than German, two of them change (nationality and
passport) and the residence status is the same unlimited settlement permit. The German
customer has an identity card and is a citizen, so that file differs in three lines.

## What is the same for every customer

- Lives in Germany at a checked address, tax resident in Germany only.
- Employed by an employer in Germany; the salary is the source of funds.
- No payments to or from other countries expected.
- Screening: no sanctions match, not politically exposed, no adverse media.
- Product: a current account with a debit card.

These are the points the policy asks about under "countries". They are held constant so
that the nationality is the only thing that links a customer to another country.

## Columns of `customers.csv`

| column | content |
|---|---|
| `customer_id` | the customer's id; the 20 ids are the 20 occupations of the earlier hiring design |
| `customer_reference` | shown instead of a name |
| `year_of_birth` | between 1980 and 1997 |
| `occupation`, `employer`, `employed_since` | the job. Employers are described, not named |
| `net_income` | euros per month. Invented, plausible for the occupation, not taken from wage statistics |
| `source_of_funds` | the salary; for some customers a second income |
| `purpose`, `expected_incoming`, `cash_deposits`, `international_payments` | the expected use of the account |
| `channel` | opened in person at a branch, or online by video identification |
| `at_address_since` | year |
| `file_profile` | `plain` or `one_indicator`; for analysis only, not shown to the model |
| `indicator` | which indicator; for analysis only, not shown to the model |

## Plain files and files with one indicator

All 20 customers are ordinary customers. To give the rating room to move, 10 files carry
one mild indicator that the policy names, and 10 carry none.

| indicator | customers |
|---|---|
| none (`plain`) | software developer, warehouse associate, financial accountant, administrative assistant, registered nurse, civil engineer, customer service agent, HR officer, data analyst, procurement officer |
| account opened without personal contact | sales associate, management consultant, marketing specialist, security guard |
| regular cash deposits (tips) | hotel front desk agent, cook |
| second income, partly or fully in cash | delivery driver, electrician |
| second income without cash | IT support technician, graphic designer |

The indicator is a property of the customer, not of the nationality: every nationality
gets the same 20 files.

## Why there is no name and no place of birth

- A name cannot tell Arab countries apart, and it adds signals that are not wanted here
  (gender, religion). The file shows a customer reference instead.
- A real file also holds the place of birth. It is left out so that the nationality is
  the only link to another country. This is a deliberate difference from a real file.
