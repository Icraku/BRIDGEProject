from enum import Enum
from typing import Dict, Any, List, Optional


# ==================== ENUMS ====================

class FormType(Enum):
    """Supported form types."""
    ITF = "ITF"  # Internal Transfer Form (1 page)
    NAR = "NAR"  # Neonatal Activity Record (2 pages)
    DSC = "DSC"  # Discharge Summary Card (1 page)


class FieldType(Enum):
    """Field data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    ENUM = "enum"
    MULTILINE = "multiline"


class SectionType(Enum):
    """Section types for ITF."""
    MOTHER_DETAILS = "mother_details"
    LABOUR_BIRTH = "labour_birth"
    INFANT_DETAILS = "infant_details"


class ClinicalCategory(Enum):
    """Clinical significance categories."""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    OBSERVATION = "observation"
    ADMINISTRATIVE = "administrative"


# ==================== SECTION VARIATIONS ====================

ITF_SECTION_VARIATIONS = {
    "MOTHER_DETAILS": [
        "A: Mother's details",
        "A: Mothers details",
        "Mother's details",
        "Mother details",
        "A: Maternal Details",
    ],
    "LABOUR_BIRTH": [
        "B: Labour and Birth",
        "B: Labour and birth",
        "Labour and Birth",
        "Labour and birth",
        "B: Labour Details",
    ],
    "INFANT_DETAILS": [
        "C: Infant Details",
        "C: Infant details",
        "Infant Details",
        "Infant details",
        "C: Baby Details",
        "C: Neonatal Details",
    ],
}


# ==================== ITF PAGE 1 SCHEMA ====================

ITF_PAGE_1_SCHEMA = {
    # ==================== SECTION A: MOTHER'S DETAILS ====================

    "Date": {
        "field_name": "Date",
        "type": FieldType.DATE,
        "format": "DD-MM-YYYY",
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": False,
        "description": "Date form completed"
    },

    "Time": {
        "field_name": "Time",
        "type": FieldType.TIME,
        "format": "HH:MM",
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": False,
        "description": "Time form completed"
    },

    "Age (in years)": {
        "field_name": "Age (in years)",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Mother's age in years",
        "validation": {"min": 10, "max": 60}
    },

    "Parity": {
        "field_name": "Parity",
        "type": FieldType.STRING,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Number of prior pregnancies (e.g., 3+0)"
    },

    "Gravida": {
        "field_name": "Gravida",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Total number of pregnancies"
    },

    "Gestation (in weeks)": {
        "field_name": "Gestation (in weeks)",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Gestational age at delivery in weeks",
        "validation": {"min": 14, "max": 45},
        "risk_thresholds": {
            "critical_low": 22,  # Periviable
            "high_low": 28,  # Very preterm
            "moderate_low": 32  # Preterm
        }
    },

    "Attended ANC?": {
        "field_name": "Attended ANC?",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Mother attended antenatal care",
        "enum_mapping": {"Y": True, "N": False}
    },

    "ANC no. of visits": {
        "field_name": "ANC no. of visits",
        "type": FieldType.INTEGER,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Number of ANC visits attended",
        "validation": {"min": 0, "max": 20}
    },

    "ANC U/S": {
        "field_name": "ANC U/S",
        "type": FieldType.BOOLEAN,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Antenatal ultrasound performed",
        "enum_mapping": {"Y": True, "N": False}
    },

    "U/S findings": {
        "field_name": "U/S findings",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,  # CLINICAL CONCEPT
        "description": "Ultrasound findings - anomalies, size, fluid, placenta, etc.",
        "keywords": {
            "critical": ["anomaly", "anomalies", "defect", "malformation", "absent", "severe"],
            "high": ["restriction", "iugr", "polyhydramnios", "oligohydramnios", "abnormal"],
            "moderate": ["normal", "adequate", "appropriate"]
        }
    },

    "EDD": {
        "field_name": "EDD",
        "type": FieldType.DATE,
        "format": "DD-MM-YYYY",
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Expected date of delivery"
    },

    "LMP": {
        "field_name": "LMP",
        "type": FieldType.DATE,
        "format": "DD-MM-YYYY",
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Last menstrual period"
    },

    "Blood group": {
        "field_name": "Blood group",
        "type": FieldType.ENUM,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "values": ["A", "B", "AB", "O", "Unkn"],
        "enum_mapping": {"Unkn": "Unknown"},
        "description": "Mother's blood group"
    },

    "Rhesus": {
        "field_name": "Rhesus",
        "type": FieldType.ENUM,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "values": ["Pos", "Neg", "Unkn"],
        "enum_mapping": {"Pos": "Positive", "Neg": "Negative", "Unkn": "Unknown"},
        "description": "Rhesus factor status"
    },

    "Fever": {
        "field_name": "Fever",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Maternal fever present",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True  # Flag if True
    },

    "Treated for TB": {
        "field_name": "Treated for TB",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Mother on TB treatment",
        "enum_mapping": {"Y": True, "N": False, "Unkn": "Unknown"},
        "risk_flag": True
    },

    "VDRL": {
        "field_name": "VDRL",
        "type": FieldType.ENUM,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "values": ["Pos", "Neg", "Unkn"],
        "enum_mapping": {"Pos": "Positive", "Neg": "Negative", "Unkn": "Unknown"},
        "description": "Syphilis screening (VDRL test)",
        "risk_flag_value": "Pos"
    },

    "Diabetes": {
        "field_name": "Diabetes",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Mother has diabetes",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "PMTCT status": {
        "field_name": "PMTCT status",
        "type": FieldType.ENUM,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": False,
        "values": ["Pos", "Neg", "Unkn"],
        "enum_mapping": {"Pos": "Positive", "Neg": "Negative", "Unkn": "Unknown"},
        "description": "HIV status (Prevention of Mother-to-Child Transmission)",
        "risk_flag_value": "Pos"
    },

    "Mother on ARVs": {
        "field_name": "Mother on ARVs",
        "type": FieldType.BOOLEAN,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Mother on antiretroviral therapy",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "APH": {
        "field_name": "APH",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": False,
        "description": "Antepartum hemorrhage",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Antibiotics": {
        "field_name": "Antibiotics",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Mother on antibiotics",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Multiple PG": {
        "field_name": "Multiple PG",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Multiple pregnancy",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "If YES, number": {
        "field_name": "If YES, number",
        "type": FieldType.INTEGER,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Number of fetuses in multiple pregnancy",
        "validation": {"min": 2, "max": 10}
    },

    "HTN in pregnancy": {
        "field_name": "HTN in pregnancy",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,
        "description": "Hypertension in pregnancy",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Pre-eclampsia": {
        "field_name": "Pre-eclampsia",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": True,
        "description": "Pre-eclampsia",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Eclampsia": {
        "field_name": "Eclampsia",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": True,
        "description": "Eclampsia",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Any other maternal condition": {
        "field_name": "Any other maternal condition",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,  # CLINICAL CONCEPT
        "description": "Additional maternal complications (PROM, PPROM, etc.)",
        "keywords": {
            "critical": ["eclampsia", "abruption", "rupture", "embolism"],
            "high": ["prom", "pprom", "chorioamnionitis", "hemorrhage"],
            "moderate": ["gd", "anemia"]
        }
    },

    "Current Maternal Drugs": {
        "field_name": "Current Maternal Drugs",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Current maternal medications"
    },

    # ==================== SECTION B: LABOUR AND BIRTH ====================

    "1st Stage": {
        "field_name": "1st Stage",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "First stage of labour details"
    },

    "2nd Stage": {
        "field_name": "2nd Stage",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Second stage of labour details"
    },

    "ROM": {
        "field_name": "ROM",
        "type": FieldType.STRING,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Rupture of membranes (timing, e.g., >18h)"
    },

    "Fetal distress": {
        "field_name": "Fetal distress",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": False,
        "description": "Fetal distress during labour",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Meconium": {
        "field_name": "Meconium",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Meconium-stained amniotic fluid",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "If yes, grade": {
        "field_name": "If yes, grade",
        "type": FieldType.ENUM,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "values": ["1", "2", "3"],
        "description": "Grade of meconium staining",
        "risk_flag_values": ["2", "3"]
    },

    "Antenatal steroids": {
        "field_name": "Antenatal steroids",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Corticosteroids given",
        "enum_mapping": {"Y": True, "N": False}
    },

    "No of doses": {
        "field_name": "No of doses",
        "type": FieldType.INTEGER,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Number of steroid doses",
        "validation": {"min": 0, "max": 10}
    },

    "Delivery": {
        "field_name": "Delivery",
        "type": FieldType.ENUM,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "values": ["SVD", "CS", "VD", "Assisted", "Other"],
        "description": "Mode of delivery"
    },

    "If CS, type": {
        "field_name": "If CS, type",
        "type": FieldType.ENUM,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "values": ["Emergency", "Elective"],
        "description": "Type of caesarean section",
        "risk_flag_value": "Emergency"
    },



    "Reasons for emergency CS": {
        "field_name": "Reasons for emergency CS",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,  # CLINICAL CONCEPT
        "description": "Clinical indication for emergency caesarean",
        "keywords": {
            "critical": ["abruption", "rupture", "prolapse", "catastrophic"],
            "high": ["distress", "failure", "psc", "pph"]
        }
    },

    "Placenta Complete?": {
        "field_name": "Placenta Complete?",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Placenta completely delivered",
        "enum_mapping": {"Y": True, "N": False}
    },

    "Abnormal placenta?": {
        "field_name": "Abnormal placenta?",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Placental abnormalities",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "If yes, describe": {
        "field_name": "If yes, describe",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,  # CLINICAL CONCEPT
        "description": "Description of placental abnormalities",
        "keywords": {
            "critical": ["abruption", "infarction"],
            "high": ["calcification", "abnormal"]
        }
    },

    "BVM resuscitation": {
        "field_name": "BVM resuscitation",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Bag and mask ventilation given",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Chest compressions?": {
        "field_name": "Chest compressions?",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": False,
        "description": "Chest compressions performed",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Resuscitation duration (min)": {
        "field_name": "Resuscitation duration (min)",
        "type": FieldType.INTEGER,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Duration of resuscitation in minutes",
        "validation": {"min": 0, "max": 60}
    },

    "Vitamin K": {
        "field_name": "Vitamin K",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Vitamin K prophylaxis given",
        "enum_mapping": {"Y": True, "N": False}
    },

    "TEO": {
        "field_name": "TEO",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Thermal care",
        "enum_mapping": {"Y": True, "N": False}
    },

    "OPV": {
        "field_name": "OPV",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Oral Polio Vaccine",
        "enum_mapping": {"Y": True, "N": False}
    },

    "BCG": {
        "field_name": "BCG",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "BCG vaccine",
        "enum_mapping": {"Y": True, "N": False}
    },

    "Hep B": {
        "field_name": "Hep B",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Hepatitis B vaccine",
        "enum_mapping": {"Y": True, "N": False}
    },

    "CPAP": {
        "field_name": "CPAP",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "CPAP support",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Oxygen": {
        "field_name": "Oxygen",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Supplemental oxygen",
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Chlorhexidine": {
        "field_name": "Chlorhexidine",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Chlorhexidine cord care",
        "enum_mapping": {"Y": True, "N": False}
    },

    "Maternal Status": {
        "field_name": "Maternal Status",
        "type": FieldType.STRING,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Mother's general status"
    },

    "Where is the mother currently": {
        "field_name": "Where is the mother currently",
        "type": FieldType.STRING,
        "required": False,
        "section": SectionType.LABOUR_BIRTH,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": True,  # CLINICAL CONCEPT
        "description": "Mother's current location"
    },

    # ==================== SECTION C: INFANT DETAILS ====================

    "Date of birth": {
        "field_name": "Date of birth",
        "type": FieldType.DATE,
        "format": "DD-MM-YYYY",
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": False,
        "description": "Baby's date of birth"
    },

    "Sex": {
        "field_name": "Sex",
        "type": FieldType.ENUM,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "values": ["M", "F", "Indeterminate"],
        "description": "Baby's sex"
    },

    "Age": {
        "field_name": "Age",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Neonatal age"
    },

    "Birth Weight (grams)": {
        "field_name": "Birth Weight (grams)",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": False,
        "description": "Birth weight in grams",
        "validation": {"min": 500, "max": 8000},
        "risk_thresholds": {
            "critical_low": 1000,
            "high_low": 1500,
            "moderate_low": 2500
        }
    },

    "Weight now (grams)": {
        "field_name": "Weight now (grams)",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Current weight in grams",
        "validation": {"min": 500, "max": 8000}
    },

    "Pulse Rate": {
        "field_name": "Pulse Rate",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Heart rate (beats per minute)",
        "validation": {"min": 40, "max": 200}
    },

    "Temp": {
        "field_name": "Temp",
        "type": FieldType.FLOAT,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Temperature in °C",
        "validation": {"min": 28.0, "max": 44.0}
    },

    "Resp Rate": {
        "field_name": "Resp Rate",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "Respiratory rate",
        "validation": {"min": 60, "max": 100}
    },

    "APGAR Score 1M": {
        "field_name": "APGAR Score 1M",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": False,
        "description": "APGAR score at 1 minute",
        "validation": {"min": 0, "max": 10},
        "risk_thresholds": {
            "critical": 3,
            "high": 5,
            "moderate": 7
        }
    },

    "APGAR Score 5M": {
        "field_name": "APGAR Score 5M",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": False,
        "description": "APGAR score at 5 minutes",
        "validation": {"min": 0, "max": 10},
        "risk_thresholds": {
            "critical": 3,
            "high": 5,
            "moderate": 7
        }
    },

    "APGAR Score 10M": {
        "field_name": "APGAR Score 10M",
        "type": FieldType.INTEGER,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": False,
        "description": "APGAR score at 10 minutes",
        "validation": {"min": 0, "max": 10}
    },

    "Baby from?": {
        "field_name": "Baby from?",
        "type": FieldType.STRING,
        "required": True,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": False,
        "description": "Location baby originated from"
    },

    "Reason for referral to NBU": {
        "field_name": "Reason for referral to NBU",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.INFANT_DETAILS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "is_clinical_concept": True,  # CLINICAL CONCEPT
        "description": "Primary clinical indication for referral",
        "keywords": {
            "critical": ["distress", "asphyxia", "seizure", "sepsis"],
            "high": ["rds", "respiratory", "prematurity", "low birth weight", "lbw"],
            "moderate": ["observation", "monitoring"]
        }
    },
}