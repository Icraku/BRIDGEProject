"""
schemas/neonatal_admission_form/categorical_enums.py
=============================================
Enum classes for every categorical field on the NAR form.

Why enums instead of ``str``
-----------------------------
When Pydantic's ``with_structured_output`` receives an enum field, it passes
the list of valid values directly into the JSON schema sent to the LLM.  The
model therefore *knows* at generation time which values are acceptable and is
much less likely to hallucinate variants like ``"male"`` instead of ``"M"``.


``_missing_`` is only called when the value is not already a valid enum member,
so canonical values pass through with zero overhead.

Field type in ``FIELD_TYPES``
------------------------------
All fields using these enums are typed as``"categorical"``.
The evaluation pipeline treats categorical fields the same as str for accuracy scoring

Adding new valid values
-----------------------
If a new valid clinical value is encountered in the future,
add it as a member of the relevant enum here.  Do NOT add it to the
hallucination detector allowlist — the allowlist is only for fields that
remain ``str``.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Helper base class; all enums inherit from this so _missing_ is DRY

_SYNONYMS: dict[str, dict[str, str]] = {}


def _resolve(cls: type, value: object) -> object:
    """Look up *value* in the synonym registry for *cls*.

    Returns a valid enum member on success, or ``None`` on failure
    (which causes Python to re-raise ValueError, which Pydantic catches
    and converts to a None field value).
    """
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    canonical = _SYNONYMS.get(cls.__name__, {}).get(v)
    if canonical:
        try:
            return cls(canonical)
        except ValueError:
            return None
    # Case-insensitive fallback over member values
    for member in cls:
        if member.value.lower() == v:
            return member
    return None


# ---------------------------------------------------------------------------
# Section A — Infant details Enums

class SexEnum(str, Enum):
    """Sex of the infant as marked on the NAR form."""
    F = "F"
    M = "M"
    I = "I"   # Indeterminate
    
    @classmethod
    def _missing_(cls, value: object) -> "SexEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "female": "F", "girl": "F", "f": "F", "Female": "F", "FEMALE": "F",
        "male": "M", "boy": "M", "m": "M", "Male": "M", "MALE": "M",
        "indeterminate": "I", "intersex": "I", "i": "I",
    }


class GestationTypeEnum(str, Enum):
    """Used to determine gestational age."""
    US  = "US"
    LMP = "LMP"

    @classmethod
    def _missing_(cls, value: object) -> "GestationTypeEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "us": "US", "u/s": "US", "u / s": "US", "u/ s": "US", "u /s": "US", "ultrasound": "US", "scan": "US",
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

    _SYNONYMS = {
        "svd": "SVD", "normal": "SVD", "vaginal": "SVD", "normal vaginal": "SVD", "spontaneous": "SVD",
        "cs": "CS", "c/s": "CS", "caesarean": "CS", "cesarean": "CS", "c section": "CS", "c-section": "CS",
        "vacuum": "Vacuum", "ventouse": "Vacuum",
        "forceps": "Forceps", "instrumental": "Forceps",
        "breech": "Breech", "breach": "Breech",
    }


class CSTypeEnum(str, Enum):
    """Type of Caesarean section."""
    EMERGENCY = "Emergency"
    ELECTIVE  = "Elective"

    @classmethod
    def _missing_(cls, value: object) -> "CSTypeEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "emergency": "Emergency", "emcs": "Emergency", "emergency cs": "Emergency",
        "emergency c/s": "Emergency", "emerg": "Emergency",
        "elective": "Elective", "elcs": "Elective", "elective cs": "Elective",
        "elective c/s": "Elective", "elect": "Elective",
    }


class ROMEnum(str, Enum):
    """Rupture of membranes duration."""
    LT18    = "lt18"
    GTE18   = "gte18"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "ROMEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "lt18": "lt18", "<18": "lt18", "<18h": "lt18", "<18 hours": "lt18", "less than 18": "lt18", "less than 18h": "lt18",
        "gte18": "gte18", ">=18": "gte18", ">=18h": "gte18", "greater than 18": "gte18", ">=18 hours": "gte18",
        "unknown": "unknown", "unkn": "unknown", "unk": "unknown", "not known": "unknown", "n/a": "unknown",
    }


class BornWhereEnum(str, Enum):
    """Location of birth if born before arrival."""
    HOME_OR_ROADSIDE = "Home/Roadside"
    OTHER_FACILITY = "Other facility"

    @classmethod
    def _missing_(cls, value: object) -> "BornWhereEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "home": "Home/Roadside", "home delivery": "Home/Roadside", "domiciliary": "Home/Roadside",
        "roadside": "Home/Roadside", "road": "Home/Roadside", "in transit": "Home/Roadside",
        "other facility": "Other facility", "other hospital": "Other facility", "facility": "Other facility",
        "clinic": "Other facility", "referred": "Other facility", "transferred": "Other facility",
    }


# ---------------------------------------------------------------------------
# Section B — Mother's details

class ANCTrimesterEnum(str, Enum):
    """Trimester in which ANC ultrasound was performed."""
    FIRST  = "1st"
    SECOND = "2nd"
    THIRD  = "3rd"

    @classmethod
    def _missing_(cls, value: object) -> "ANCTrimesterEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
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

    _SYNONYMS = {
        "a": "A", "a+": "A", "a-": "A",
        "b": "B", "b+": "B", "b-": "B",
        "ab": "AB", "ab+": "AB", "ab-": "AB",
        "o": "O", "o+": "O", "o-": "O",
        "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown", "?": "Unknown",
    }


class RhesusEnum(str, Enum):
    """Rhesus blood group status."""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    UNKNOWN  = "Unknown"

    @classmethod
    def _missing_(cls, value: object) -> "RhesusEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "positive": "Positive", "pos": "Positive", "+": "Positive", "rh+": "Positive", "rhesus positive": "Positive",
        "negative": "Negative", "neg": "Negative", "-": "Negative", "rh-": "Negative", "rhesus negative": "Negative",
        "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown",
    }


class AntiDEnum(str, Enum):
    """Whether Anti-D medication was given."""
    Y       = "Y"
    N       = "N"

    @classmethod
    def _missing_(cls, value: object) -> "AntiDEnum | None":
        return _resolve(cls, value)


    _SYNONYMS = {
        "y": "Y", "yes": "Y", "given": "Y",
        "n": "N", "no": "N", "not given": "N",
    }


# ---------------------------------------------------------------------------
# Section F1 — General examination

class SkinEnum(str, Enum):
    """Skin appearance on examination."""
    NORMAL          = "Normal"
    BRUISING        = "Bruising"
    RASH            = "Rash"
    PUSTULES        = "Pustules"
    MOTTLING        = "Mottling"
    DRY_PEELING     = "Dry/Peeling/Wrinkled"

    @classmethod
    def _missing_(cls, value: object) -> "SkinEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
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
    """Severity of jaundice on examination."""
    NONE     = "None"
    MILD     = "Mild"      # +
    SEVERE   = "Severe"    # +++

    @classmethod
    def _missing_(cls, value: object) -> "JaundiceEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "none": "None", "no": "None", "absent": "None",
        "mild": "Mild", "+": "Mild", "1+": "Mild",
        "severe": "Severe", "+++": "Severe", "3+": "Severe",
    }


class AppearanceEnum(str, Enum):
    """General appearance of the infant."""
    WELL        = "Well"
    SICK        = "Sick"
    DYSMORPHIC  = "Dysmorphic"

    @classmethod
    def _missing_(cls, value: object) -> "AppearanceEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "well": "Well", "normal": "Well", "healthy": "Well",
        "sick": "Sick", "ill": "Sick", "unwell": "Sick",
        "dysmorphic": "Dysmorphic",
    }


class CryEnum(str, Enum):
    """Quality of the infant's cry."""
    NORMAL = "Normal"
    WEAK_OR_ABSENT   = "Weak/Absent"
    HOARSE = "Hoarse"

    @classmethod
    def _missing_(cls, value: object) -> "CryEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "normal": "Normal", "strong": "Normal", "good": "Normal", "well": "Normal",
        "weak": "Weak/Absent", "feeble": "Weak/Absent", "absent": "Weak/Absent", "no cry": "Weak/Absent",
        "weak/absent": "Weak/Absent", "weak / absent": "Weak/Absent", "weak-absent": "Weak/Absent",
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

    _SYNONYMS = {
        "none": "None", "no": "None", "absent": "None",
        "mild": "Mild", "moderate": "Mild",
        "severe": "Severe",
    }


class PallorEnum(str, Enum):
    """Severity of pallor / anaemia."""
    NONE   = "None"
    MILD   = "Mild"    # +
    SEVERE = "Severe"  # +++

    @classmethod
    def _missing_(cls, value: object) -> "PallorEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "none": "None", "no": "None", "absent": "None",
        "mild": "Mild", "+": "Mild", "1+": "Mild", "moderate": "Mild",
        "severe": "Severe", "+++": "Severe", "3+": "Severe",
    }


class ToneEnum(str, Enum):
    """Neurological tone of the infant."""
    NORMAL    = "Normal"
    INCREASED = "Increased"
    REDUCED   = "Reduced"

    @classmethod
    def _missing_(cls, value: object) -> "ToneEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "normal": "Normal",
        "increased": "Increased", "high": "Increased", "hypertonic": "Increased",
        "reduced": "Reduced", "low": "Reduced", "hypotonic": "Reduced",
        "floppy": "Reduced", "decreased": "Reduced",
    }


class UmbilicusEnum(str, Enum):
    """Condition of the umbilicus."""
    CLEAN       = "Clean"
    LOCAL_PUS   = "Local pus"
    PUS_RED     = "Pus+Red skin"
    OTHERS      = "Others"

    @classmethod
    def _missing_(cls, value: object) -> "UmbilicusEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "clean": "Clean", "clear": "Clean", "normal": "Clean", "dry": "Clean",
        "local pus": "Local pus", "localpus": "Local pus", "pus": "Local pus",
        "pus + red skin": "Pus+Red skin", "pus and red skin": "Pus+Red skin",
        "pus+red skin": "Pus+Red skin", "pus + redness": "Pus+Red skin", "pus with redness": "Pus+Red skin",
        "others": "Others", "other": "Others",
    }

class BirthDefectsEnum(str, Enum):
    """Category of congenital birth defect recorded."""
    MAJOR_GI_ABNORMALITY = "Major gi abnormality",
    HYDROCEPHALUS = "Hydrocephalus",
    CLEFT_LIP_OR_PALATED = "Clef lip/palated",
    MICROCEPHALY = "Microcephalus",
    NEURAL_TUBE_DEFECTS = "Neural tube defects",
    SPINA_BIFIDA = "Spina bifida",
    LIMB_ABNORMALITIES = "Limb abnormalities",
    BIRTH_INJURY_OR_ABNORMALITIES = "Birth injury or abnormalities",

    @classmethod
    def _missing_(cls, value: object) -> "BirthDefectsEnum | None":
        return _resolve(cls, value)

    _SYNONYMS = {
        "major gi abnormality": "Major GI abnormality", "gi abnormality": "Major GI abnormality",
        "gastrointestinal abnormality": "Major GI abnormality", "gut abnormality": "Major GI abnormality",
        "intestinal abnormality": "Major GI abnormality",
        "hydrocephalus": "Hydrocephalus", "hydrocephaly": "Hydrocephalus",
        "cleft lip/palate": "Cleft lip/palate", "cleft lip and palate": "Cleft lip/palate",  "cleft lip palate": "Cleft lip/palate",
        "cleft lip": "Cleft lip/palate", "cleft palate": "Cleft lip/palate",
        "palate": "Cleft lip/palate", "cleft": "Cleft lip/palate",
        "microcephaly": "Microcephaly", "microcephalus": "Microcephaly", "small head": "Microcephaly",
    }


# ---------------------------------------------------------------------------
# Maps field name to enum class for evaluation and normaliser

CATEGORICAL_FIELD_MAP: dict[str, type[str, Enum]] = {
    "sex":                    SexEnum,
    "gestation_type":         GestationTypeEnum,
    "delivery_type":          DeliveryTypeEnum,
    "had_cs":                 CSTypeEnum,
    "rapture_of_membrane":    ROMEnum,
    "born_where":             BornWhereEnum,
    "anc_us_trimester":       ANCTrimesterEnum,
    "blood_group":            BloodGroupEnum,
    "rhesus":                 RhesusEnum,
    "given_anti_D_medication": AntiDEnum,
    "skin":                   SkinEnum,
    "jaundice":               JaundiceEnum,
    "appearance":             AppearanceEnum,
    "cry":                    CryEnum,
    "chest_indrawing":        RetractionSeverityEnum,
    "xiphoid_retraction":     RetractionSeverityEnum,
    "intercostal_retraction": RetractionSeverityEnum,
    "pallor":                 PallorEnum,
    "tone":                   ToneEnum,
    "umbilicus":              UmbilicusEnum,
    "has_birth_defects":      BirthDefectsEnum,
}