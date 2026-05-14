# OSF Pre-Registration Submission Instructions

Step-by-step for submitting the gun-violence cross-geography pre-registration to OSF.io.

**Target audience:** Nate (manual submission, OSF requires authenticated account action).

**Two artifacts you produce locally before going to OSF:**

1. **`gun_violence_research_design_v2.pdf`** — merge `D:/Gun Violence/notes/pre_reg_redline.md` revisions into your source design doc, export as PDF. This is the PDF you upload as the primary pre-registration document.
2. **`D:/Gun Violence/notes/osf_structured_form.md`** — already drafted. Each section maps to an OSF form field; paste verbatim during the structured-form step.

---

## Step 1 — Generate v2 PDF (LOCAL)

Open your source design doc (the one that produced `D:/Gun Violence/notes/gun_violence_research_design.pdf`). Apply each redlined change from `pre_reg_redline.md`:

| § | Action |
|---|---|
| §2 | Replace cell-inclusion criteria + cell-size table |
| §3 | Replace entire §3 with the v2 "Socioeconomic covariate adjustment" text |
| §4 | Replace non-fatal-injury sub-bullet + add Non-fatal coverage caveat before "Secondary outcomes" |
| §5 | Add "Socioeconomic covariates" subsection after "Inequity features" |
| §7 | Move RW-HI from Tier 1 to Tier 2 |
| §8 | Add 5 covariate terms to the model spec block |
| §9 | Add Threat 5b — Socioeconomic-covariate residual confounding + new Threat 1 sub-bullet (d) |

After merging, change the status banner at the top of the doc to:
> **Status: Pre-registration v2 (locked 2026-MM-DD). Revisions from v1 documented in `pre_reg_redline.md`. All revisions made BEFORE outcome data inspection.**

Export to PDF as `gun_violence_research_design_v2.pdf`. Save to `D:/Gun Violence/`.

---

## Step 2 — Create OSF account (if needed)

If you don't have an OSF account: go to https://osf.io/register and sign up with your `mr.nathanhumphrey@gmail.com` email. Email confirmation required. Free tier suffices for pre-registration.

If you have one: log in at https://osf.io.

---

## Step 3 — Create new OSF project

1. From your OSF dashboard, click **"Create new project"** (top right).
2. **Title:** `Cross-Geography Decoupling of Race and Structural Inequity Effects on Gun Violence Rates in Working-Class American Communities`
3. **Description:** (paste the 1–2 paragraph description from `osf_structured_form.md` Study Information → Description)
4. **Storage:** US (default)
5. Leave project public for now (you'll set the embargo at the registration step, not the project step).
6. Click **"Create"**.

You now have an OSF project page at `https://osf.io/<random-id>/`. Note this URL.

---

## Step 4 — Upload the v2 PDF

1. On the project page, click **"Files"** in the left navigation.
2. Click **"OSF Storage"** → **"Upload"**.
3. Upload `gun_violence_research_design_v2.pdf`.
4. Wait for upload confirmation.

The PDF is now attached to the project but **not yet registered** (no timestamp lock).

---

## Step 5 — Create the pre-registration

1. From the project page, click **"Registrations"** in the top tabs.
2. Click **"New registration"**.
3. **Select form:** "OSF Preregistration" (the standard pre-data-collection template). If unavailable, "OSF Standard Pre-Data Collection Registration" is equivalent.
4. The structured form opens. Fill each field by pasting from `osf_structured_form.md`:
   - **Study Information** → Title, Description, Hypotheses
   - **Design Plan** → Study type, Blinding, Study design, Randomization
   - **Sampling Plan** → Existing data, Explanation, Data collection procedures, Sample size, Sample size rationale, Stopping rule
   - **Variables** → Manipulated, Measured (outcomes + independent + control covariates), Indices
   - **Analysis Plan** → Statistical models, Transformations, Inference criteria, Data exclusion, Missing data, Exploratory analysis
   - **Other Information** → Methodology corpus integration + provenance trail
5. **Attach the v2 PDF**: at the "Files" step of the registration, select `gun_violence_research_design_v2.pdf` from the project's OSF Storage. The PDF will be locked into the registration.
6. Review every field once. Once registered, fields cannot be edited without explicit "post-hoc revision" labeling.

---

## Step 6 — Set embargo

OSF offers three options at the final registration step:
- **Public immediately** — anyone can view from the moment you click Submit
- **Embargo (up to 4 years)** — registration is locked + timestamped immediately but contents are hidden until embargo expires; you can release early on request to reviewers
- **Private** (no public timestamp) — not recommended; defeats the purpose of pre-registration

**Recommendation: Embargo, 12 months.** Locks the timestamp publicly (so anyone can verify the registration date) but hides the content until approximately when you expect the manuscript to be in review. You can release the content early to any reviewer who requests it. This balances pre-registration credibility against staying ahead of competing research.

Click **"Submit registration"**.

---

## Step 7 — Verify timestamp lock

After submission:

1. Go to the project's **"Registrations"** tab.
2. The new registration appears with status "Pending" briefly, then "Public Registration" (with embargo, it appears as "Embargoed Registration").
3. Click into it. The page header shows the immutable timestamp ("Registered: YYYY-MM-DD HH:MM:SS UTC") and the OSF DOI.
4. Copy the OSF DOI (format: `10.17605/OSF.IO/<id>`) and the registration URL.

---

## Step 8 — Save the registration record locally

After successful submission, populate `D:/Gun Violence/osf_registration.json` with the OSF DOI, timestamp, embargo end date, and SHA-256 hash of the registered PDF (the hash locks future revisions against the registered content).

I've placed an empty template at `D:/Gun Violence/osf_registration.json`. Fill it in after Step 7.

---

## Step 9 — Cross-check before proceeding to analysis

Before running any §8 model fit:
1. Verify the OSF registration URL resolves and shows the registered PDF.
2. Verify the timestamp predates any outcome rate inspection on your local machine (Phase 3 of Prompt 2).
3. Confirm `osf_registration.json` is filled and the SHA-256 hash matches the PDF you uploaded.

Once these three are verified, Phase 1 (data assembly) gate-after-Phase-1 review is complete from the pre-reg side. You're cleared to proceed to Phase 2 (cell construction) and Phase 3 (outcome variable construction) per Prompt 2.

---

## Common pitfalls

- **Editing the PDF after upload but before registration**: the OSF Storage version is what gets registered. If you re-upload after submitting, it doesn't replace the registered version — but if you re-upload BEFORE registering, OSF Storage holds the latest version. Verify the right PDF version is selected at the registration "Files" step.
- **Embargo length**: OSF caps at 4 years. 12 months is the standard for pre-data-collection studies headed for journal submission. Shorter (6 months) if you expect faster turnaround; longer (24 months) if the analysis is multi-phase.
- **OSF account two-factor**: enable 2FA on the account before submission. Pre-registration credibility depends on account integrity.
- **Hypotheses field length**: OSF has character limits per field. If H_INEQUITY through H_GEOGRAPHIC_MECHANISM combined exceed the field cap, paste each hypothesis as a separate sub-section under "Hypotheses" or use the "Other Information" field for the overflow.

---

## What I (Claude Code) cannot do for you

- Create or log into your OSF account (authentication is yours)
- Submit the form on your behalf (OSF requires user click-through)
- Set the embargo (your call)
- Sign the registration with your name and credentials

What I have done:
- Drafted `osf_structured_form.md` (every field text ready to paste)
- Drafted `pre_reg_redline.md` (v1 → v2 changes for the source design doc)
- Drafted these instructions
- Set up the empty `osf_registration.json` template for post-submission record-keeping

Ping me after Step 8 with the DOI + timestamp and I'll fill the JSON + run a sanity check that the registered PDF's SHA-256 matches what's on disk.
