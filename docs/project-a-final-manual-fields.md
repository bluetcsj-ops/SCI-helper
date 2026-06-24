# Project A Final Manual Fields Checklist

This checklist tracks the real-world fields that must be completed by the investigator or institution before Project A can move from workflow validation to a submission-ready manuscript.

Current status: workflow-ready, not submission-ready.

## Summary

| Area | Current status | Required real content | Affected module | Submission blocker |
| --- | --- | --- | --- | --- |
| Ethics / IRB | Placeholder only | IRB committee name, approval number or exemption basis, consent or waiver statement | Vera Protocol, Writer, Reviewer | Yes |
| Data authorization | Placeholder only | Data-use approval, access boundary, approved user role, retention policy | Vera Protocol, Data Lin, Writer | Yes |
| De-identification | Placeholder only | De-identification method, removed identifiers, date shifting or coding rule, linkage risk review | Data Lin, Writer, Reviewer | Yes |
| Raw data boundary | Placeholder only | Whether raw clinical CSV/DICOM is retained, where it is stored, who can access it | Data Lin, Reviewer | Yes |
| Field dictionary | Placeholder only | Chinese field name, English column name, unit, source system, export format, missing-value code, derived rule | Vera Protocol, Data Lin, Writer | Yes |
| CSV export path | Placeholder only | Real export path or SOP, export owner, export timestamp rule, version control rule | Data Lin, Writer | Yes |
| TPS / planning software | Placeholder only | TPS name and version, online adaptation software version if applicable | Vera Protocol, Writer, Reviewer | Yes |
| Dose calculation algorithm | Placeholder only | Algorithm name, calculation grid, heterogeneity correction, dose-to-water or dose-to-medium convention | Writer, Reviewer | Yes |
| Machine / MLC model | Placeholder only | Linac or MR-Linac model, MLC model, delivery technique details | Writer, Reviewer | Yes |
| Structure naming | Placeholder only | Target and OAR naming rules, atlas or institutional convention, handling of renamed structures | Writer, Reviewer | Yes |
| QA / gamma criteria | Placeholder only | Gamma criterion, dose threshold, passing-rate threshold, measurement device, failure handling | Writer, Reviewer | Yes |
| Statistical review | Workflow sample only | Final primary endpoint, grouping rule, multiplicity plan, statistician review status | Data Lin, Writer, Reviewer | Yes |
| Target journal declarations | Placeholder only | Ethics, consent, funding, conflict of interest, data availability, AI assistance statement | Writer, Reviewer | Yes |

## Current Workflow Evidence

- Project A currently uses `radiotherapy_plan_quality_sample.csv` as a prepared workflow sample.
- The sample contains 20 rows and 18 columns.
- Data Lin generated quality control, descriptive statistics, chart specifications, and a formal-test workflow record.
- The formal-test workflow used `technique` as the grouping column and `ptv_d95_percent`, `ptv_v95_percent`, and `homogeneity_index` as outcome columns.
- The formal-test workflow completed three Kruskal-Wallis tests.
- At least one group had sample size below 5, so P values must be interpreted cautiously.
- The prepared sample is for workflow validation only and must not be presented as final institutional study evidence.

## Ethics / IRB / Consent

Fill these fields before submission:

- IRB or ethics committee name:
- Approval number:
- Approval date:
- Exemption basis, if exempt:
- Consent requirement:
- Consent waiver reason, if waived:
- Non-human-subjects determination, if applicable:
- Institution-approved ethics wording:

Impact when complete:

- Updates Vera Protocol ethics readiness.
- Replaces Writer placeholder ethics language.
- Resolves Reviewer ethics and submission-declaration risks.

## Data Authorization And Privacy

Fill these fields before real data analysis:

- Data owner or department:
- Data-use approval reference:
- Approved user role:
- Access location:
- Retention period:
- De-identification method:
- Direct identifiers removed:
- Indirect identifiers reviewed:
- Date handling rule:
- Original CSV retention rule:
- Original DICOM retention rule:
- Data destruction or archival policy:

Impact when complete:

- Lets Data Lin distinguish real analysis data from prepared samples.
- Supports Methods data-source wording.
- Reduces privacy and data-availability Reviewer risk.

## TPS / DICOM / QA Traceability

Fill these fields for each included planning workflow:

- TPS or online adaptive planning system:
- Software version:
- Dose calculation algorithm:
- Calculation grid:
- Dose reporting convention:
- Treatment machine model:
- MLC model:
- Imaging system:
- RTPLAN export rule:
- RTDOSE export rule:
- RTSTRUCT export rule:
- Structure naming convention:
- Target naming convention:
- OAR naming convention:
- QA measurement device:
- Gamma criterion:
- Dose threshold:
- Passing-rate threshold:
- QA failure handling:

Impact when complete:

- Resolves the Reviewer concern about treatment planning system version, dose calculation algorithm, gamma criteria, and structure naming.
- Gives Writer Methods enough technical detail for radiotherapy planning reproducibility.
- Lets Data Lin map real DICOM/QA columns to protocol requirements.

## Statistical Finalization

Fill or confirm these fields before final Results:

- Final primary endpoint:
- Final secondary endpoints:
- Final grouping variable:
- Whether observations are independent:
- Whether repeated plans from the same patient exist:
- Missing-data handling:
- Outlier definition:
- QA failure binary endpoint definition:
- Distribution check method:
- Variance check method:
- Multiplicity correction:
- Statistician or reviewer name:
- Final decision on P values and confidence intervals:

Impact when complete:

- Converts current workflow-test Kruskal-Wallis output into a manually approved analysis plan.
- Resolves Reviewer concerns about exploratory wording, sample size, and statistical boundary.
- Allows Writer to replace conservative placeholder language with final statistical reporting.

## Target Journal Declarations

Fill these before final submission:

- Target journal:
- Article type:
- Abstract word limit:
- Keyword limit:
- Ethics statement:
- Consent statement:
- Funding statement:
- Conflict of interest statement:
- Data availability statement:
- Code availability statement:
- Author contribution statement:
- Acknowledgments:
- Generative AI assistance disclosure:

Impact when complete:

- Resolves submission-declaration checks.
- Supports cover letter and final manuscript package.
- Prevents Reviewer from flagging missing journal-required statements.

## Immediate Next Actions

1. Replace every `[待填写]` item in Project A Protocol institutional field mapping with real institution-approved text.
2. Upload or load a final de-identified institutional CSV, not the prepared sample.
3. Re-run Data Lin quality control and statistics on the final dataset.
4. Re-run formal testing only after the statistical review checklist is complete.
5. Restore the final analysis record to Writer and save a new Writer version.
6. Re-run Reviewer checks and confirm there are no high-risk submission blockers.

