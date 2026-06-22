# Prepared DATA samples

This folder documents the real public sources used for local workflow testing.

## CSV sample

`frontend/public/sample-data/radiotherapy_plan_quality_sample.csv` is a 20-row synthetic, de-identified radiotherapy plan quality sample for workflow testing. It is not real patient data and must not be described as a clinical dataset.

Columns:

- `plan_id`
- `site`
- `technique`
- `prescription_dose_gy`
- `fractions`
- `ptv_volume_cc`
- `ptv_d95_percent`
- `ptv_v95_percent`
- `ptv_d2_percent`
- `homogeneity_index`
- `conformity_index`
- `oar_max_dose_gy`
- `oar_mean_dose_gy`
- `gamma_pass_rate_percent`
- `delivery_time_min`
- `monitor_units`
- `plan_complexity_score`
- `qa_result`

This sample is intended to exercise radiation-therapy-specific field coverage, quality checks, descriptive statistics, model planning, Writer Methods / Results handoff, and Reviewer risk checks without using protected health information.

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

`frontend/public/sample-data/radiotherapy_survival_cox_sample.csv` is a 16-row synthetic, de-identified survival workflow sample for testing the first Cox proportional hazards model path. It is not real patient data and must not be described as clinical evidence.

Columns:

- `follow_up_months`
- `event_status`
- `age`
- `ptv_d95_percent`
- `plan_complexity_score`
- `gamma_pass_rate_percent`
- `site`
- `technique`

This sample is intended to exercise advanced model planning, Cox field detection, exploratory hazard-ratio output, Writer handoff, Reviewer HR boundary checks, and `advanced-cox-model-fit.md` export.

## Reference sample

`frontend/public/sample-data/prepared_references.json` contains source/reference metadata for the prepared data package. These records are not a replacement for manuscript reference review; they are seed references for testing Mentor and Alex Writer citation workflows.
