# FEATURE ADDENDUM — Automated Report Generation Module
## Akriti Diagnostics Center — Pathology Lab Management System

**Document Type:** Feature Addendum (not a new system — see Context below)


---

**Scope note:** This adds one new feature to the existing, already-working Lab Management System. Nothing else in the system changes.

---

## 1. Feature Summary

This feature adds a **second, faster path** to producing a patient's report. Today, staff manually prepare a PDF outside the system and upload it — **this manual upload path is kept exactly as-is and remains fully available.** This feature adds an additional option alongside it: a structured form where staff/admin select a patient with a pending report, the patient's details and booked test(s) auto-fill from existing records, staff type in the actual result values against a pre-defined list of parameters for each test, and the system automatically generates the final formatted PDF — with the lab's letterhead, signature, and layout — with no manual PDF authoring required for that patient.

**Both paths are available side by side, per patient, at the same screen.** On the Pending Reports queue, each patient has two actions:
- **"Prepare Report"** — opens the new structured result-entry form (§2.2)
- **"Upload PDF"** — the existing manual upload flow, completely unchanged

Staff/Admin picks whichever is appropriate for that patient — e.g. structured entry for routine tests with defined parameters, manual upload for anything unusual, outsourced/franchise reports, or a test whose parameters aren't set up yet. Whichever path is used, the result lands in the same place (§4) and behaves identically from that point on.

---

## 2. New Functional Requirements

### 2.1 Test Parameter Master (Admin only — one-time setup per test)

- In the existing Test Section (test catalog management), each test gains a **"Manage Parameters"** action.
- Opens a screen where Admin defines the result fields for that specific test — for example, for "CBC 5 Part": Hemoglobin, Total WBC Count, RBC Count, Platelet Count, and so on (see Appendix A for the full recommended parameter set per test, based on standard Indian diagnostic lab reference ranges).
- Each parameter has:
  - **Name** (e.g. "Hemoglobin")
  - **Unit** (e.g. `g/dL`) — optional, some parameters are unit-less
  - **Input type**: `Numeric`, `Text`, or `Dropdown` (dropdown supplies its own option list, e.g. `["Positive","Negative"]` for a serology test like HIV or HBsAg)
  - **Reference range**: numeric Low–High (optionally different for Male/Female, since several values genuinely differ by gender — see Appendix A), or plain reference text for non-numeric parameters (e.g. "Non-Reactive", "Negative")
  - **Display order** (controls sequence on both the entry form and the final PDF)
- A test with zero parameters defined cannot yet be selected in the Report Preparation form — the system shows a clear message ("This test has no parameters configured yet — add them from Test Section first") rather than allowing a broken/empty report to be generated.
- **Note on non-numeric tests:** A handful of the lab's 65 tests are imaging/descriptive studies rather than numeric-parameter tests (the 5 Ultrasonography tests, and ECG). For these, "parameters" should simply be configured as a single `Text` input named "Findings / Impression" — the pathologist/radiologist types a free-text impression rather than filling in a parameter grid. This keeps the same form and pipeline working uniformly for every test type, numeric or descriptive.

### 2.2 Report Preparation Form (Admin + Staff)

- New **"Reports"** section in navigation (both dashboards).
- **Pending Reports queue:** lists all patients whose report is not yet ready, searchable by Patient ID/name/mobile, sorted latest-first — same search/filter/pagination conventions already used elsewhere in the system. Staff visibility here follows whatever staff-visibility rule the existing system already applies elsewhere (own-collected vs. all, per that staff member's configured setting). **Each row shows both a "Prepare Report" button and an "Upload PDF" button** — the existing manual upload button is not removed or hidden, it sits right alongside the new option.
- Selecting **"Prepare Report"** opens the structured entry form:
  - **Auto-fetched header (read-only, never re-typed):** Patient ID, Name, Age, Gender, Mobile, Sample Collection Date, Doctor Referred, and the test(s) booked — pulled directly from the patient's existing record. Nothing here is manually re-entered.
  - **Result entry, generated per booked test:** one input row per parameter defined in §2.1 for that test, in display order, showing the parameter name, unit, reference range alongside for reference, and the correct input control (numeric/text/dropdown).
  - **Abnormal-value flag:** a numeric entry outside its defined reference range is visually flagged (amber border + small "Outside normal range" note) — non-blocking, since a genuine abnormal result is often exactly the point of the test; it simply draws a second look before confirming.
  - **Interpretation/Remarks:** optional free-text field per test, included on the final PDF if filled.
  - **Submit:** required fields validated → a custom confirmation dialog (not a native browser alert) → on confirm, values are saved and PDF generation is queued as a background task (never inline in the request, so generating a report never makes the rest of the app feel slow for other users).
- **Editing an already-generated report:** re-opening this form for a patient whose report already exists pre-fills the previously entered values rather than starting blank, and follows whatever report-correction/versioning behavior the existing system already has (old version archived, new version active, reason logged) — this feature does not introduce a second, separate versioning mechanism.

### 2.3 Data Model (new tables only — nothing existing changes)

**`test_parameters`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| test_id | UUID | FK → tests.id, NOT NULL |
| parameter_name | VARCHAR(120) | NOT NULL |
| unit | VARCHAR(20) | NULL |
| input_type | ENUM('numeric','text','dropdown') | NOT NULL |
| dropdown_options | JSONB | NULL — used only when `input_type = 'dropdown'` |
| reference_low | NUMERIC(10,3) | NULL |
| reference_high | NUMERIC(10,3) | NULL |
| reference_text | VARCHAR(200) | NULL — for non-numeric reference display |
| applicable_gender | ENUM('all','male','female') | DEFAULT 'all' |
| display_order | SMALLINT | NOT NULL |

**`patient_test_results`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, NOT NULL |
| test_id | UUID | FK → tests.id, NOT NULL |
| parameter_id | UUID | FK → test_parameters.id, NOT NULL |
| entered_value | VARCHAR(100) | NOT NULL |
| is_abnormal | BOOLEAN | computed and stored at entry time |
| interpretation_note | TEXT | NULL |
| entered_by | UUID | FK → users.id, NOT NULL |
| entered_at | TIMESTAMPTZ | DEFAULT now() |

### 2.4 New API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/reports/pending` | List patients with a pending report |
| GET | `/api/v1/tests/{test_id}/parameters` | Get defined parameters for a test |
| POST | `/api/v1/tests/{test_id}/parameters` | Define/edit parameters for a test (Admin only) |
| POST | `/api/v1/patients/{patient_id}/report-entry` | Submit result values; queues PDF generation (Idempotency-Key required, consistent with every other mutating endpoint in the system) |

---

## 3. Report Template

PDF rendering uses the **same rendering approach already established in the existing system** (WeasyPrint, HTML/CSS template), matching the lab's exact required layout — letterhead, logo, QR/verification code, digital signature block, footer, reference-range columns, interpretation section.

**The specific template layout is to be supplied separately by Akriti Diagnostics Center.** Until it is provided, implementation should proceed with a clean placeholder layout containing all the same data fields (patient header, per-test parameter table with values + units + reference ranges, interpretation, signature/footer area) — so the rest of this feature is not blocked waiting on the final visual design. When the format is supplied, it replaces only the template file; no other part of this feature changes.

---

## 4. Reference Ranges — Researched and Pre-Filled for Seeding

The following parameter sets and reference ranges were compiled from standard Indian diagnostic laboratory references and are recommended as the **starting seed data** for Test Parameter Master (§2.1), for the tests that have well-established numeric/standard parameters. **Important caveat, standard across the industry:** reference ranges vary slightly by laboratory, analyzer/instrument, and reagent kit manufacturer — these values should be reviewed and adjusted to match Akriti Diagnostics Center's own analyzer manufacturer inserts before going live, exactly as any lab would calibrate reference ranges to their own equipment.

**CBC 5 Part**
| Parameter | Unit | Reference Range |
|---|---|---|
| Hemoglobin (Hb) | g/dL | Male: 13.0–17.0 · Female: 12.0–15.5 |
| Total RBC Count | million/µL | Male: 4.5–5.5 · Female: 3.5–4.5 |
| Total WBC Count | /µL | 4,000–11,000 |
| Platelet Count | /µL | 150,000–450,000 |
| Hematocrit (PCV) | % | Male: 40–52 · Female: 36–48 |
| MCV | fL | 80–100 |
| MCH | pg | 27–33 |
| MCHC | g/dL | 32–36 |
| RDW | % | 11.5–14.5 |
| Neutrophils | % | 40–70 |
| Lymphocytes | % | 20–40 |
| Eosinophils | % | 1–6 |
| Monocytes | % | 2–8 |
| Basophils | % | 0–1 |

**Blood Sugar (Fasting)** — mg/dL — 70–100
**Blood Sugar (Random)** — mg/dL — 70–140
**Blood Sugar Fasting/PP** — Fasting: 70–100 · PP (Post-Prandial): 70–140
**HbA1c** — % — Normal: <5.7 · Prediabetic: 5.7–6.4 · Diabetic: ≥6.5

**Lipid Profile**
| Parameter | Unit | Reference Range |
|---|---|---|
| Total Cholesterol | mg/dL | <200 desirable |
| Triglycerides | mg/dL | <150 |
| HDL Cholesterol | mg/dL | Male: >40 · Female: >50 |
| LDL Cholesterol | mg/dL | <100 desirable |
| VLDL Cholesterol | mg/dL | 5–40 |

**Liver Function Test (LFT)**
| Parameter | Unit | Reference Range |
|---|---|---|
| SGPT (ALT) | U/L | Up to 49 (some labs: up to 56) |
| SGOT (AST) | U/L | Male: 5–40 · Female: 9–32 |
| Total Bilirubin | mg/dL | 0.2–1.2 |
| Direct Bilirubin | mg/dL | 0–0.3 |
| Indirect Bilirubin | mg/dL | 0.2–0.9 |
| Alkaline Phosphatase (ALP) | U/L | 44–147 |
| Total Protein | g/dL | 6.0–8.3 |
| Albumin | g/dL | 3.5–5.0 |
| A/G Ratio | ratio | 1.1–2.5 |

**Kidney Function Test (KFT)**
| Parameter | Unit | Reference Range |
|---|---|---|
| Blood Urea | mg/dL | 15–45 |
| Serum Creatinine | mg/dL | Male: 0.7–1.3 · Female: 0.6–1.1 |
| Uric Acid | mg/dL | Male: 3.5–7.2 · Female: 2.6–6.0 |
| Serum Calcium | mg/dL | 8.5–10.5 |
| Serum Electrolytes — Sodium | mEq/L | 135–145 |
| Serum Electrolytes — Potassium | mEq/L | 3.5–5.1 |
| Serum Electrolytes — Chloride | mEq/L | 96–106 |

**Thyroid Profile (FT3, FT4, TSH)**
| Parameter | Unit | Reference Range |
|---|---|---|
| TSH | µIU/mL | 0.4–4.0 |
| T3 (Total) | ng/dL | 100–200 |
| T4 (Total) | µg/dL | 5–12 |
| Free T4 | ng/dL | 0.9–1.7 |

**Other commonly-quantified tests (standard ranges, review against lab analyzer):**
- **Vitamin D** — ng/mL — Deficient: <20 · Insufficient: 20–29 · Sufficient: 30–100
- **Vitamin B12** — pg/mL — 211–911
- **CRP (Quantitative)** — mg/L — <6 (normal), higher indicates inflammation
- **PSA** — ng/mL — <4.0 (age-dependent, higher cutoffs used for older men)
- **Testosterone Total** — ng/dL — Male: 280–1100 · Female: 15–70
- **PT/INR** — INR: 0.8–1.2 (normal, non-anticoagulated patient)
- **ASO Titer** — IU/mL — Up to 200

**Qualitative/Serology tests (Dropdown: Positive / Negative, or Reactive / Non-Reactive):**
HIV 1&2, TB Platinum, HBsAg, HCV, VDRL, Trust Test, Widal (titer-based, dropdown + titer value), Dengue IgE/IgM, RA Test, Montox Test, IgE (quantitative, follows numeric pattern instead), Aldehyde, Parahit Total, PBS for MP, RK 39, Preg Colour.

**Descriptive/imaging tests (single "Findings/Impression" text field per §2.1 note):**
USG Whole Abdomen, USG Upper Abdomen, USG Lower Abdomen, USG Uterus and Adnexa, USG Fetal Profile, ECG.

**Routine/Microscopy tests (mix of dropdown + numeric, define per lab's own reporting format):**
R/E of Urine, Stool R/E, Micral Test Albumin Urine, Urine Culture, Blood Group and Rh Typing (dropdown: A+/A-/B+/B-/AB+/AB-/O+/O-).

*(Tests not listed above with an explicit range — e.g. Anemia Profile's sub-components, Hypertension Profile, Arthritis Profile, Diabetic Profile, Kidney Profile — are bundled panels; their individual parameters are simply the relevant rows already listed above for CBC/LFT/KFT/Lipid, grouped under the bundle's own report layout rather than needing separate new reference values.)*

---

## 5. Update to Existing "Patient Report & History" View

The existing Patient Overview/Patient Detail view already has a section showing a patient's report(s) and history. This feature requires that view to correctly reflect **both** report sources going forward:

- A report generated via this new Report Preparation form appears in that same list, in the same place, formatted identically to a manually-uploaded report — same download button, same version-history behavior, same "Report Ready" status trigger, same notification dispatch.
- A small, non-intrusive tag distinguishes how each report was produced — e.g. "Auto-generated" vs. "Manually uploaded" — purely informational, not a different visual treatment or separate list. Both belong to the same underlying `reports` table and the same patient timeline already specified elsewhere in the system.
- Manual upload continues to work exactly as it does today — this feature adds a second way to arrive at a finished report, it does not deprecate or alter the first.

---

## 6. Integration Points With the Existing System (what this feature touches, and what it deliberately does not)

| Existing system component | How this feature interacts with it |
|---|---|
| Patients / patient_tests | **Read-only** — auto-fetches header data and booked tests; never modifies patient registration data |
| Tests (catalog) | **Extends** — adds the "Manage Parameters" action; does not change existing test CRUD |
| Reports module (upload, signature, verification hash, status flip, notification) | **Reused as-is** — this feature only adds a new way to produce the input data for that existing pipeline; the pipeline itself (signature application, hashing, status update, notification dispatch) is not duplicated or modified |
| Report Version Control | **Reused as-is** — corrections to an auto-generated report follow the same versioning already specified |
| Audit Log | **Extended** — result entry/edit is logged the same way every other sensitive write already is |
| Idempotency / background tasks | **Reused as-is** — result submission requires an Idempotency-Key and PDF generation runs as a background task, exactly like every other mutating/heavy operation in the existing system |

This feature introduces exactly two new tables and one new UI section — everything else it touches is existing, unmodified system behavior.
