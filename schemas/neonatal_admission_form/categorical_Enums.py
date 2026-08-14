"""
schemas/neonatal_admission_form/categorical_Enums.py
=====================================================
Enum classes for every categorical (closed-vocabulary) field on the NAR form.

IMPORTANT — _SYNONYMS design
--------------------------------------------
Defining ``_SYNONYMS`` as a class attribute inside a ``(str, Enum)`` subclass
makes it an enum member (visible in iteration and breaking _missing_).
All synonym dicts are therefore stored in the MODULE-LEVEL ``_SYNONYMS`` dict,
keyed by class name, and populated AFTER each class definition.
Each enum's ``_missing_`` delegates to the module-level ``_resolve`` helper.

Shared enums
------------
``YesNoUnknownEnum`` and ``PositiveNegativeUnknownEnum`` are for (ArvsEnum, HbigEnum,
HypertensionEnum, HaemorrhageEnum, DiabetesEnum, ProlongedLabourEnum, and
VdrlEnum, PmctEnum, HepBEnum respectively).
The shared PositiveNegativeUnknownEnum uses "Positive"/"Negative" consistently.
"""

from __future__ import annotations

from enum import Enum

# Module-level synonym registry — keyed by class name
# Populated after each class definition below
_SYNONYMS: dict[str, dict[str, str]] = {}


def _resolve(cls: type, value: object) -> object:
    """Look up value in the module-level synonym registry for cls."""
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    canonical = _SYNONYMS.get(cls.__name__, {}).get(v)
    if canonical:
        try:
            return cls(canonical)
        except ValueError:
            return None
    for member in cls:
        if member.value.lower() == v:
            return member
    return None


# ---------------------------------------------------------------------------
# Section A — Infant details
# ---------------------------------------------------------------------------

class SexEnum(str, Enum):
    """Sex of the infant: F / M / I (Indeterminate)."""
    F = "F"
    M = "M"
    I = "I"

    @classmethod
    def _missing_(cls, value: object) -> "SexEnum | None":
        return _resolve(cls, value)

_SYNONYMS["SexEnum"] = {
    "f": "F", "female": "F", "girl": "F",
    "m": "M", "male": "M",  "boy": "M",
    "i": "I", "indeterminate": "I", "intersex": "I",
}


class GestationTypeEnum(str, Enum):
    """Source used to determine gestational age: US or LMP."""
    US  = "US"
    LMP = "LMP"

    @classmethod
    def _missing_(cls, value: object) -> "GestationTypeEnum | None":
        return _resolve(cls, value)

_SYNONYMS["GestationTypeEnum"] = {
    "us": "US", "u/s": "US", "u / s": "US", "u/ s": "US", "u /s": "US",
    "ultrasound": "US", "scan": "US",
    "lmp": "LMP", "last menstrual period": "LMP",
    "us lmp": "US", "lmp us": "LMP",
    "u/s lmp": "US", "lmp u/s": "LMP",
}


class DeliveryTypeEnum(str, Enum):
    """Mode of delivery."""
    SVD     = "SVD"
    CS      = "CS"
    VACUUM  = "Vacuum"
    FORCEPS = "Forceps"
    BREECH  = "Breech"

    @classmethod
    def _missing_(cls, value: object) -> "DeliveryTypeEnum | None":
        return _resolve(cls, value)

_SYNONYMS["DeliveryTypeEnum"] = {
    "svd": "SVD", "normal": "SVD", "vaginal": "SVD",
    "normal vaginal": "SVD", "spontaneous": "SVD",
    "cs": "CS", "c/s": "CS", "caesarean": "CS", "cesarean": "CS",
    "c section": "CS", "c-section": "CS",
    "vacuum": "Vacuum", "ventouse": "Vacuum",
    "forceps": "Forceps", "instrumental": "Forceps",
    "breech": "Breech", "breach": "Breech",
}


class CSTypeEnum(str, Enum):
    """Type of Caesarean section: Emergency or Elective."""
    EMERGENCY = "Emergency"
    ELECTIVE  = "Elective"

    @classmethod
    def _missing_(cls, value: object) -> "CSTypeEnum | None":
        return _resolve(cls, value)

_SYNONYMS["CSTypeEnum"] = {
    "emergency": "Emergency", "emcs": "Emergency",
    "emergency cs": "Emergency", "emergency c/s": "Emergency",
    "elective": "Elective", "elcs": "Elective",
    "elective cs": "Elective", "elective c/s": "Elective",
}


class ROMEnum(str, Enum):
    """Rupture of membranes duration."""
    LT18    = "lt18"
    GTE18   = "gte18"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "ROMEnum | None":
        return _resolve(cls, value)

_SYNONYMS["ROMEnum"] = {
    "lt18": "lt18", "<18": "lt18", "<18h": "lt18",
    "<18 hours": "lt18", "less than 18": "lt18",
    "gte18": "gte18", ">=18": "gte18", ">=18h": "gte18",
    ">=18 hours": "gte18", "greater than 18": "gte18",
    "unknown": "unknown", "unkn": "unknown", "unk": "unknown",
    "not known": "unknown", "n/a": "unknown",
}


class BornWhereEnum(str, Enum):
    """Location of birth if born outside the facility.

    The NAR form has exactly two checkboxes:
      [ ] Home/Roadside
      [ ] Other facility
    """
    HOME_ROADSIDE  = "Home/Roadside"
    OTHER_FACILITY = "Other facility"

    @classmethod
    def _missing_(cls, value: object) -> "BornWhereEnum | None":
        return _resolve(cls, value)

_SYNONYMS["BornWhereEnum"] = {
    "home/roadside": "Home/Roadside",
    "home": "Home/Roadside", "home delivery": "Home/Roadside",
    "domiciliary": "Home/Roadside", "roadside": "Home/Roadside",
    "road": "Home/Roadside", "in transit": "Home/Roadside",
    "other facility": "Other facility", "other hospital": "Other facility",
    "facility": "Other facility", "clinic": "Other facility",
    "referred": "Other facility", "transferred": "Other facility",
}


# ---------------------------------------------------------------------------
# Section B — Mother's details
# ---------------------------------------------------------------------------

class PositiveNegativeUnknownEnum(str, Enum):
    """Shared enum for any Pos / Neg / Unkn checkbox group."""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    UNKNOWN  = "Unknown"

    @classmethod
    def _missing_(cls, value: object) -> "PositiveNegativeUnknownEnum | None":
        return _resolve(cls, value)

_SYNONYMS["PositiveNegativeUnknownEnum"] = {
    "positive": "Positive", "pos": "Positive",
    "negative": "Negative", "neg": "Negative",
    "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown", "?": "Unknown",
}

class ANCTrimesterEnum(str, Enum):
    """Trimester in which ANC ultrasound was performed."""
    FIRST  = "1st"
    SECOND = "2nd"
    THIRD  = "3rd"

    @classmethod
    def _missing_(cls, value: object) -> "ANCTrimesterEnum | None":
        return _resolve(cls, value)

_SYNONYMS["ANCTrimesterEnum"] = {
    "1st": "1st", "first": "1st", "1": "1st", "t1": "1st",
    "2nd": "2nd", "second": "2nd", "2": "2nd", "t2": "2nd",
    "3rd": "3rd", "third": "3rd", "3": "3rd", "t3": "3rd",
}


class BloodGroupEnum(str, Enum):
    """ABO blood group."""
    A       = "A"
    B       = "B"
    AB      = "AB"
    O       = "O"
    UNKNOWN = "Unknown"

    @classmethod
    def _missing_(cls, value: object) -> "BloodGroupEnum | None":
        return _resolve(cls, value)

_SYNONYMS["BloodGroupEnum"] = {
    "a": "A", "a+": "A", "a-": "A",
    "b": "B", "b+": "B", "b-": "B",
    "ab": "AB", "ab+": "AB", "ab-": "AB",
    "o": "O", "o+": "O", "o-": "O",
    "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown", "?": "Unknown",
}


class RhesusEnum(str, Enum):
    """Rhesus status: Positive / Negative / Unknown."""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    UNKNOWN  = "Unknown"

    @classmethod
    def _missing_(cls, value: object) -> "RhesusEnum | None":
        return _resolve(cls, value)

_SYNONYMS["RhesusEnum"] = {
    "positive": "Positive", "pos": "Positive", "+": "Positive", "rh+": "Positive",
    "negative": "Negative", "neg": "Negative", "-": "Negative", "rh-": "Negative",
    "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown", "?": "Unknown",
}


#class AntiDEnum(str, Enum):
#    """Whether Anti-D was given: Y or N.

#    The form has two checkboxes only. Blank field -> None (Optional).
#    """
#    Y = "Y"
#    N = "N"

#    @classmethod
#    def _missing_(cls, value: object) -> "AntiDEnum | None":
#        return _resolve(cls, value)

#_SYNONYMS["AntiDEnum"] = {
#    "y": "Y", "yes": "Y", "given": "Y", "administered": "Y",
#    "n": "N", "no": "N", "not given": "N", "not administered": "N",
#}


class YesNoUnknownEnum(str, Enum):
    """Shared enum for any Y / N / Unkn checkbox group.

    Replaces the previously separate ArvsEnum, HbigEnum, HypertensionEnum,
    HaemorrhageEnum, DiabetesEnum, and ProlongedLabourEnum, which were all
    structurally identical (same Y/N/Unknown values, only synonym lists
    differed). Synonym lists below are the union of all six.
    """
    Y       = "Y"
    N       = "N"
    UNKNOWN = "Unknown"

    @classmethod
    def _missing_(cls, value: object) -> "YesNoUnknownEnum | None":
        return _resolve(cls, value)

_SYNONYMS["YesNoUnknownEnum"] = {
    "y": "Y", "yes": "Y",
    "given": "Y", "administered": "Y", "present": "Y",
    "on arvs": "Y", "taking arvs": "Y", "receiving arvs": "Y",
    "hbig given": "Y", "hbig administered": "Y",
    "hypertension": "Y", "had hypertension": "Y",
    "had aph": "Y", "aph": "Y", "antepartum haemorrhage": "Y",
    "had diabetes": "Y", "diabetes": "Y",
    "prolonged": "Y", "prolonged labour": "Y",
    "prolonged 2nd stage": "Y", "prolonged second stage": "Y",
    "n": "N", "no": "N",
    "not given": "N", "not administered": "N", "absent": "N",
    "not on arvs": "N", "not taking arvs": "N", "not receiving arvs": "N",
    "hbig not given": "N", "hbig not administered": "N",
    "no hypertension": "N",
    "no aph": "N", "no antepartum haemorrhage": "N",
    "no diabetes": "N",
    "not prolonged": "N", "normal labour": "N", "no prolonged labour": "N",
    "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown", "?": "Unknown",
}

# ---------------------------------------------------------------------------
# Section F1 — General examination
# ---------------------------------------------------------------------------

class SkinEnum(str, Enum):
    """Skin appearance on examination."""
    NORMAL      = "Normal"
    BRUISING    = "Bruising"
    RASH        = "Rash"
    PUSTULES    = "Pustules"
    MOTTLING    = "Mottling"
    DRY_PEELING = "Dry/Peeling/Wrinkled"

    @classmethod
    def _missing_(cls, value: object) -> "SkinEnum | None":
        return _resolve(cls, value)

_SYNONYMS["SkinEnum"] = {
    "normal": "Normal",
    "bruising": "Bruising", "bruised": "Bruising",
    "rash": "Rash",
    "pustules": "Pustules", "pustule": "Pustules",
    "mottling": "Mottling", "mottled": "Mottling",
    "dry": "Dry/Peeling/Wrinkled", "peeling": "Dry/Peeling/Wrinkled",
    "wrinkled": "Dry/Peeling/Wrinkled",
    "dry/peeling": "Dry/Peeling/Wrinkled",
    "dry peeling": "Dry/Peeling/Wrinkled",
    "dry-peeling": "Dry/Peeling/Wrinkled",
    "dry/peeling/wrinkled": "Dry/Peeling/Wrinkled",
    "dry peeling wrinkled": "Dry/Peeling/Wrinkled",
    "dry-peeling-wrinkled": "Dry/Peeling/Wrinkled",
    "dry/peeling-wrinkled": "Dry/Peeling/Wrinkled",
    "dry-peeling/wrinkled": "Dry/Peeling/Wrinkled",
}


class JaundiceEnum(str, Enum):
    """Jaundice severity: None / Mild(+) / Severe(+++)."""
    NONE   = "None"
    MILD   = "Mild"
    SEVERE = "Severe"

    @classmethod
    def _missing_(cls, value: object) -> "JaundiceEnum | None":
        return _resolve(cls, value)

_SYNONYMS["JaundiceEnum"] = {
    "none": "None", "no": "None", "absent": "None",
    "mild": "Mild", "+": "Mild", "1+": "Mild",
    "severe": "Severe", "+++": "Severe", "3+": "Severe",
}


class AppearanceEnum(str, Enum):
    """General appearance of the infant."""
    WELL       = "Well"
    SICK       = "Sick"
    DYSMORPHIC = "Dysmorphic"

    @classmethod
    def _missing_(cls, value: object) -> "AppearanceEnum | None":
        return _resolve(cls, value)

_SYNONYMS["AppearanceEnum"] = {
    "well": "Well", "normal": "Well", "healthy": "Well",
    "sick": "Sick", "ill": "Sick", "unwell": "Sick",
    "dysmorphic": "Dysmorphic",
    "well / dysmorphic": "Well", "well/dysmorphic": "Well",
}


class CryEnum(str, Enum):
    """Quality of the infant's cry."""
    NORMAL       = "Normal"
    WEAK_ABSENT  = "Weak/Absent"
    HOARSE       = "Hoarse"

    @classmethod
    def _missing_(cls, value: object) -> "CryEnum | None":
        return _resolve(cls, value)

_SYNONYMS["CryEnum"] = {
    "normal": "Normal", "strong": "Normal", "good": "Normal", "well": "Normal",
    "weak": "Weak/Absent", "feeble": "Weak/Absent",
    "absent": "Weak/Absent", "no cry": "Weak/Absent",
    "weak/absent": "Weak/Absent", "weak / absent": "Weak/Absent",
    "weak-absent": "Weak/Absent",
    "hoarse": "Hoarse",
}


class RetractionSeverityEnum(str, Enum):
    """Severity of chest retraction (xiphoid or intercostal)."""
    NONE   = "None"
    MILD   = "Mild"
    SEVERE = "Severe"

    @classmethod
    def _missing_(cls, value: object) -> "RetractionSeverityEnum | None":
        return _resolve(cls, value)

_SYNONYMS["RetractionSeverityEnum"] = {
    "none": "None", "no": "None", "absent": "None",
    "mild": "Mild", "moderate": "Mild",
    "severe": "Severe",
}


class PallorEnum(str, Enum):
    """Pallor/Anaemia severity: None / Mild(+) / Severe(+++)."""
    NONE   = "None"
    MILD   = "Mild"
    SEVERE = "Severe"

    @classmethod
    def _missing_(cls, value: object) -> "PallorEnum | None":
        return _resolve(cls, value)

_SYNONYMS["PallorEnum"] = {
    "none": "None", "no": "None", "absent": "None",
    "mild": "Mild", "+": "Mild", "1+": "Mild", "moderate": "Mild",
    "severe": "Severe", "+++": "Severe", "3+": "Severe",
}


class ToneEnum(str, Enum):
    """Neurological tone: Normal / Increased / Reduced."""
    NORMAL    = "Normal"
    INCREASED = "Increased"
    REDUCED   = "Reduced"

    @classmethod
    def _missing_(cls, value: object) -> "ToneEnum | None":
        return _resolve(cls, value)

_SYNONYMS["ToneEnum"] = {
    "normal": "Normal",
    "increased": "Increased", "high": "Increased", "hypertonic": "Increased",
    "reduced": "Reduced", "low": "Reduced", "hypotonic": "Reduced",
    "floppy": "Reduced", "decreased": "Reduced",
}


class UmbilicusEnum(str, Enum):
    """Condition of the umbilicus."""
    CLEAN     = "Clean"
    LOCAL_PUS = "Local pus"
    PUS_RED   = "Pus+Red skin"
    OTHERS    = "Others"

    @classmethod
    def _missing_(cls, value: object) -> "UmbilicusEnum | None":
        return _resolve(cls, value)

_SYNONYMS["UmbilicusEnum"] = {
    "clean": "Clean", "clear": "Clean", "normal": "Clean", "dry": "Clean",
    "local pus": "Local pus", "localpus": "Local pus", "pus": "Local pus",
    "pus + red skin": "Pus+Red skin", "pus and red skin": "Pus+Red skin",
    "pus+red skin": "Pus+Red skin", "pus + redness": "Pus+Red skin",
    "others": "Others", "other": "Others",
}


class BirthDefectsEnum(str, Enum):
    """Category of congenital birth defect recorded."""
    MAJOR_GI            = "Major GI abnormality"
    HYDROCEPHALUS       = "Hydrocephalus"
    CLEFT_LIP_PALATE    = "Cleft lip/palate"
    MICROCEPHALY        = "Microcephaly"
    NEURAL_TUBE_DEFECTS = "Neural tube defects"
    SPINA_BIFIDA        = "Spina bifida"
    LIMB_ABNORMALITIES  = "Limb abnormalities"
    BIRTH_INJURY        = "Birth injury/abnormalities"

    @classmethod
    def _missing_(cls, value: object) -> "BirthDefectsEnum | None":
        return _resolve(cls, value)

_SYNONYMS["BirthDefectsEnum"] = {
    "major gi abnormality": "Major GI abnormality",
    "major gi": "Major GI abnormality",
    "hydrocephalus": "Hydrocephalus",
    "cleft lip/palate": "Cleft lip/palate",
    "cleft lip": "Cleft lip/palate",
    "cleft palate": "Cleft lip/palate",
    "microcephaly": "Microcephaly",
    "microcephalus": "Microcephaly",
    "neural tube defects": "Neural tube defects",
    "neural tube": "Neural tube defects",
    "spina bifida": "Spina bifida",
    "limb abnormalities": "Limb abnormalities",
    "limb": "Limb abnormalities",
    "birth injury": "Birth injury/abnormalities",
    "birth injury/abnormalities": "Birth injury/abnormalities",
}


# ---------------------------------------------------------------------------
# Convenience export — maps field name -> enum class
# ---------------------------------------------------------------------------

CATEGORICAL_FIELD_MAP: dict[str, type] = {
    "sex":                              SexEnum,
    "gestation_type":                   GestationTypeEnum,
    "delivery_type":                    DeliveryTypeEnum,
    "had_cs":                           CSTypeEnum,
    "rapture_of_membrane":              ROMEnum,
    "born_where":                       BornWhereEnum,
    "anc_us_trimester":                 ANCTrimesterEnum,
    "blood_group":                      BloodGroupEnum,
    "rhesus":                           PositiveNegativeUnknownEnum,
    "given_anti_D_medication":          AntiDEnum,
    "mum_had_vdrl":                     PositiveNegativeUnknownEnum,
    "mum_pmtct_status":                 PositiveNegativeUnknownEnum,
    "mum_had_hepatitis_b":              PositiveNegativeUnknownEnum,
    "mum_on_arvs":                      YesNoUnknownEnum,
    "mum_given_HBIG_treatment":         YesNoUnknownEnum,
    "mum_had_hypertension_in_pregnancy": YesNoUnknownEnum,
    "mum_had_antepartum_haemorrhage":   YesNoUnknownEnum,
    "mum_had_diabetes":                 YesNoUnknownEnum,
    "prolonged_labour":                 YesNoUnknownEnum,
    "skin":                             SkinEnum,
    "jaundice":                         JaundiceEnum,
    "appearance":                       AppearanceEnum,
    "cry":                              CryEnum,
    "xiphoid_retraction":               RetractionSeverityEnum,
    "intercostal_retraction":           RetractionSeverityEnum,
    "pallor":                           PallorEnum,
    "tone":                             ToneEnum,
    "umbilicus":                        UmbilicusEnum,
    "birth_defect_types":               BirthDefectsEnum,
}