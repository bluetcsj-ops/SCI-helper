# Prepared DATA samples

This folder documents the real public sources used for local workflow testing.

## CSV sample

`frontend/public/sample-data/mimic_iv_demo_los_sample.csv` is a 50-row derived sample from the PhysioNet MIMIC-IV Clinical Database Demo v2.2.

Source files used:

- `hosp/patients.csv.gz`
- `hosp/admissions.csv.gz`

Source page: https://physionet.org/content/mimic-iv-demo/2.2/

Derived columns:

- `subject_id`
- `hadm_id`
- `gender`
- `anchor_age`
- `admission_type`
- `admission_location`
- `insurance`
- `language`
- `marital_status`
- `race`
- `length_of_stay_days`
- `hospital_expire_flag`

The sample is intended only for product workflow integration testing: CSV upload, privacy/quality checks, descriptive statistics, formal-test guardrails, and writer handoff.

## Reference sample

`frontend/public/sample-data/prepared_references.json` contains source/reference metadata for the prepared data package. These records are not a replacement for manuscript reference review; they are seed references for testing Mentor and Alex Writer citation workflows.
