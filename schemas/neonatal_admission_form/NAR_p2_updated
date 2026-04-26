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

class NARSectionType(Enum):
    MOTHER_DETAILS = "mother_details"
    BIRTH_DETAILS = "birth_details"
    INFANT_ADMISSION = "infant_admission"
    EXAMINATION = "examination"
    DIAGNOSIS = "diagnosis"
    INTERVENTIONS = "interventions"
    
class ClinicalCategory(Enum):
    """Clinical significance categories."""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    OBSERVATION = "observation"
    ADMINISTRATIVE = "administrative"
    

# ==================== SECTION VARIATIONS FOR PAGE 2 ====================

class NARSectionType(Enum):
    GENERAL_EXAMINATION = "general_examination"   # F1
    FURTHER_EXAMINATION = "further_examination"   # F2
    SUMMARY = "summary"                           # G
    INVESTIGATIONS = "investigations"             # H
    DIAGNOSIS = "diagnosis"                       # I
    INTERVENTIONS = "interventions"               # J
    ACTION_PLAN = "action_plan"                   # K


# ==================== NAR PAGE 2 SCHEMA ====================

NAR_PAGE_2_SCHEMA = {

    # ==================== F1: GENERAL EXAMINATION ====================

    "Skin": {
        "field_name": "Skin",
        "type": FieldType.ENUM,
        "values": ["Normal", "Bruising", "Rash", "Pustules", "Mottling", "Dry/peeling/Wrinkled"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.OBSERVATION,
        "is_clinical_concept": True,
        "description": "Baby's skin condition"
    },

    "Jaundice": {
        "field_name": "Jaundice",
        "type": FieldType.ENUM,
        "values": ["None", "+", "+++"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,
        "description": "Level of jaundice",
        "risk_flag_values": ["+++"]
    },

    "Appearance": {
        "field_name": "Appearance",
        "type": FieldType.ENUM,
        "values": ["Well", "Sick", "Dysmorphic"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,
        "description": "General appearance of baby",
        "risk_flag_values": ["Sick", "Dysmorphic"]
    },

    "Cry": {
        "field_name": "Cry",
        "type": FieldType.ENUM,
        "values": ["Normal", "Weak/Absent", "Hoarse"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,
        "description": "Baby's cry",
        "risk_flag_values": ["Weak/Absent"]
    },

    "Crackles": {
        "field_name": "Crackles",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Grunting": {
        "field_name": "Grunting",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "risk_flag": True
    },

    "Good bilateral air entry": {
        "field_name": "Good bilateral air entry",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Air entry in baby's lungs",
        "risk_flag": True
    },

    "Central cyanosis": {
        "field_name": "Central cyanosis",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Cyanosis present in baby's central body",
        "risk_flag": True
    },

    "Lower chest indrawing": {
        "field_name": "Lower chest indrawing",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Indrawing of lower chest",
        "risk_flag": True
    },

    "Xiphoid retraction": {
        "field_name": "Xiphoid retraction",
        "type": FieldType.ENUM,
        "values": ["None", "Mild", "Severe"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "enum_mapping": {"None": "None", "Mild": "Mild", "Severe": "Severe"},
        "description": "Retraction of xiphoid process",
        "risk_flag_values": ["Severe"]
    },

    "Intercostal retraction": {
        "field_name": "Intercostal retraction",
        "type": FieldType.ENUM,
        "values": ["None", "Mild", "Severe"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "enum_mapping": {"None": "None", "Mild": "Mild", "Severe": "Severe"},
        "description": "Retraction of intercostal muscles",
        "risk_flag_values": ["Severe"]
    },

    "Capillary refill (seconds)": {
        "field_name": "Capillary refill (seconds)",
        "type": FieldType.FLOAT,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "description": "Capillary refill time in seconds",
        "validation": {"min": 0, "max": 10}
    },

    "Pallor/Anaemia": {
        "field_name": "Pallor/Anaemia",
        "type": FieldType.ENUM,
        "values": ["None", "+", "+++"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "description": "Pallor or anaemia present in baby",
        "risk_flag_values": ["+","+++"]
    },

    "Murmur": {
        "field_name": "Murmur",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Presence of heart murmur",
        "risk_flag": True
    },

    "Bulging fontanelle": {
        "field_name": "Bulging fontanelle",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Does baby have bulging fontanelle",
        "risk_flag": True
    },

    "Irritable": {
        "field_name": "Irritable",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Irritable",
        "risk_flag": True
    },

    "Tone": {
        "field_name": "Tone",
        "type": FieldType.ENUM,
        "values": ["Normal", "Increased", "Reduced"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "description": "Tone",
        "risk_flag_values": ["Reduced"]
    },

    "Distension": {
        "field_name": "Distension",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "description": "Distension",
        "enum_mapping": {"Y": True, "N": False}
    },

    "Umbilicus": {
        "field_name": "Umbilicus",
        "type": FieldType.ENUM,
        "values": ["Clean", "Local pus", "Pus + Red skin", "Others"],
        "required": True,
        "section": NARSectionType.GENERAL_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "description": "Condition of the umbilicus",
        "risk_flag_values": ["Pus + Red skin", "Others"]
    },

    # ==================== F2 ====================

    "Further examination notes": {
        "field_name": "Further examination notes",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": NARSectionType.FURTHER_EXAMINATION,
        "clinical_category": ClinicalCategory.HIGH,
        "description": "Further medical notes",
        "is_clinical_concept": True
    },

    "Birth defects?": {
        "field_name": "Birth defects?",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.FURTHER_EXAMINATION,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Birth defects the baby might have",
        "risk_flag": True
    },

    "Birth defects description": {
        "field_name": "Birth defects description",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": NARSectionType.FURTHER_EXAMINATION,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "Birth defects description",
        "is_clinical_concept": True
    },

    # ==================== G ====================

    "Summary of problems": {
        "field_name": "Summary of problems",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": NARSectionType.SUMMARY,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "Summary of baby's problems",
        "is_clinical_concept": True
    },

    # ==================== H ====================

    "RBS measured": {
        "field_name": "RBS measured",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.INVESTIGATIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "RDS measurement"
    },

    "RBS value": {
        "field_name": "RBS value",
        "type": FieldType.FLOAT,
        "required": False,
        "section": NARSectionType.INVESTIGATIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "RDS value"
    },

    "Bilirubin measured": {
        "field_name": "Bilirubin measured",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.INVESTIGATIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Bilirubin value"
    },

    "Other investigations": {
        "field_name": "Other investigations",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": NARSectionType.INVESTIGATIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "Other investigations"
    },

    # ==================== I ====================

    "Primary diagnosis": {
        "field_name": "Primary diagnosis",
        "type": FieldType.STRING,
        "required": True,
        "section": NARSectionType.DIAGNOSIS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "Primary diagnosis"
    },

    "Secondary diagnosis": {
        "field_name": "Secondary diagnosis",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": NARSectionType.DIAGNOSIS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "Secondary diagnosis"
    },

    # ==================== J ====================

    "Oxygen": {
        "field_name": "Oxygen",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.INTERVENTIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Oxygen therapy",
        "risk_flag": True
    },

    "CPAP": {
        "field_name": "CPAP",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.INTERVENTIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "CPAP therapy",
        "risk_flag": True
    },

    "Antibiotics": {
        "field_name": "Antibiotics",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.INTERVENTIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "description": "Antibiotic therapy",
        "enum_mapping": {"Y": True, "N": False}
    },

    "Feeds": {
        "field_name": "Nutrition/Feeds",
        "type": FieldType.BOOLEAN,
        "required": True,
        "section": NARSectionType.INTERVENTIONS,
        "clinical_category": ClinicalCategory.CRITICAL,
        "enum_mapping": {"Y": True, "N": False},
        "description": "Nutrition/Feeds for baby"
    },

    # ==================== K ====================

    "Time (24 hour)": {
        "field_name": "Time (24 hour)",
        "type": FieldType.TIME,
        "format": "HH:MM",
        "required": False,
        "section": NARSectionType.ACTION_PLAN,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": False,
        "description": "Time form completed"
    },

    "Date": {
        "field_name": "Date",
        "type": FieldType.DATE,
        "format": "DD-MM-YYYY",
        "required": True,
        "section": NARSectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.ADMINISTRATIVE,
        "is_clinical_concept": False,
        "description": "Date form completed"
    }
}
