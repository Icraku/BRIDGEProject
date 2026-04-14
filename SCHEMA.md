**Infant Details (Section A)**

date → Date of Admission

time_seen → Time baby seen (24 hr clock)

sex → Sex (F [x] → "female", M [x] → "male")

birth_date → DOB

time_birth → Time of birth (24 hr clock)

gestation_in_weeks → Gestation (in weeks)

baby_age_in_days → Age (in days)

gestation_type → Gestation age from? (U/S or LMP)

**APGAR**

apgar_1m → APGAR Score 1M

apgar_5m → APGAR Score 5M

apgar_10m → APGAR Score 10M

**Delivery**

delivery_type → Delivery (SVD / CS / Breech / Forceps / Vacuum)

had_cs → If CS, type (any checked → true)

was_resuscitated → BVM resus at birth

rapture_of_membrane → ROM <18 / >=18h / Unkn

**Birth Context**

is_multiple_delivery → Multiple delivery

multiple_delivery_num → If YES, number

born_before_arrival → Born outside facility?

born_where → If yes, where?

**Mother’s Details (Section B)**

mum_age_in_years → Age (years)

parity_live → Parity (first number)

parity_abortions → Parity (second number)

date_estimated_delivery_date → EDD

anc_visits → ANC no. of visits

mum_has_anc_ultrasound → ANC U/S

**Mother Medical Info**

blood_group → Blood group

rhesus → Rhesus

given_anti_D_medication → Anti D

mum_had_vdrl → VDRL

mum_pmtct_status → PMTCT status

mum_on_arvs → Mother on ARVs

mum_had_hepatitis_b → Hep B

mum_given_HBIG_treatment → Hep B IG given

mum_had_hypertension_in_pregnancy → HTN in pregnancy?

mum_had_antepartum_haemorrhage → APH

mum_had_diabetes → Diabetes

prolonged_labour → Prolonged 2nd Stage?

**Section C (Maternal Problems)**

Not structured in Tuti's metadata

**Section D (Infant Problems)**

primary_admission_diagnosis → Infant's presenting problems

secondary_admission_diagnosis → Additional description if present

**Anthropometry & Vitals (Section E)**

head_circumference → Head circumference (cm)

length → Length (cm)

temparature → Temp

respiratory_rate → Resp Rate

systolic_blood_pressure → Blood Pressure (first value)

diastolic_blood_pressure → Blood Pressure (second value)

pulse_rate → Pulse

pulse_oximetry → O2 Sat

birth_weight → Birth Weight (grams)

weight → Weight now (grams)

**Symptoms Checklist**

has_fever → Fever

passed_meconium → Passed meconium/stool

has_difficulty_breathing → Difficulty breathing

passed_urine → Passed urine in the last 12 hours

has_difficulty_feeding → Inability to feed

has_convulsions → Convulsions / Twitching

has_apnoea → Apnoea

is_floppy → Reduced / Absent movement

has_vomiting → Bilious Vomiting

has_diarhoea → Bloody stool

**Other**

hospital →  Not in markdown

record_type → constant "NAR"