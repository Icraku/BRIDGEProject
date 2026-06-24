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

Synonym normalisation via ``@classmethod _missing_``
------------------------------------------------------
LLMs sometimes output synonyms even with enum constraints (e.g. ``"female"``
instead of ``"F"``).  Each enum overrides ``_missing_`` to map common variants
to valid members *before* Pydantic raises a ``ValidationError``.  This means
the pipeline never crashes on a reasonable synonym, it silently corrects it.

``_missing_`` is only called when the value is not already a valid enum member,
so canonical values pass through with zero overhead.

Field type in ``FIELD_TYPES``
------------------------------
All fields using these enums are now typed ``"categorical"``.
The evaluation pipeline treats categorical fields the same as str for accuracy scoring (exact or fuzzy match on the
``.value`` string).

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

class _NormEnum(str, Enum):
    """Base class providing case-insensitive synonym normalisation.

    Subclasses define a ``_SYNONYMS`` class variable mapping lowercase
    input variants to the correct member value string.
    """

    _SYNONYMS: dict[str, str] = {}

    @classmethod
    def _missing_(cls, value: object) -> "_NormEnum | None":
        if not isinstance(value, str):
            return None
        v = value.strip().lower()
        # Check synonyms first
        canonical = cls._SYNONYMS.get(v)
        if canonical:
            return cls(canonical)
        # Case-insensitive fallback over member values
        for member in cls:
            if member.value.lower() == v:
                return member
        return None


# ---------------------------------------------------------------------------
# Section A — Infant details Enums

class SexEnum(_NormEnum):
    """Sex of the infant as marked on the NAR form."""
    F = "F"
    M = "M"
    I = "I"   # Indeterminate

    _SYNONYMS = {
        "female": "F", "girl": "F", "f": "F", "Female": "F", "FEMALE": "F",
        "male": "M", "boy": "M", "m": "M", "Male": "M", "MALE": "M",
        "indeterminate": "I", "intersex": "I", "i": "I",
    }


class GestationTypeEnum(_NormEnum):
    """Used to determine gestational age."""
    US  = "US"
    LMP = "LMP"

    _SYNONYMS = {
        "us": "US", "u/s": "US", "u / s": "US", "u/ s": "US", "u /s": "US", "ultrasound": "US", "scan": "US",
        "lmp": "LMP", "last menstrual period": "LMP",
        "us lmp": "US", "lmp us": "LMP",
        "u/s lmp": "US", "lmp u/s": "LMP",
    }


class DeliveryTypeEnum(_NormEnum):
    """Mode of delivery."""
    SVD     = "SVD"
    CS      = "CS"
    VACUUM  = "Vacuum"
    FORCEPS = "Forceps"
    BREECH  = "Breech"

    _SYNONYMS = {
        "svd": "SVD", "normal": "SVD", "vaginal": "SVD", "normal vaginal": "SVD", "spontaneous": "SVD",
        "cs": "CS", "c/s": "CS", "caesarean": "CS", "cesarean": "CS", "c section": "CS", "c-section": "CS",
        "vacuum": "Vacuum", "ventouse": "Vacuum",
        "forceps": "Forceps", "instrumental": "Forceps",
        "breech": "Breech", "breach": "Breech",
    }


class CSTypeEnum(_NormEnum):
    """Type of Caesarean section."""
    EMERGENCY = "Emergency"
    ELECTIVE  = "Elective"

    _SYNONYMS = {
        "emergency": "Emergency", "emcs": "Emergency", "emergency cs": "Emergency",
        "emergency c/s": "Emergency", "emerg": "Emergency",
        "elective": "Elective", "elcs": "Elective", "elective cs": "Elective",
        "elective c/s": "Elective", "elect": "Elective",
    }


class ROMEnum(_NormEnum):
    """Rupture of membranes duration."""
    LT18    = "lt18"
    GTE18   = "gte18"
    UNKNOWN = "unknown"

    _SYNONYMS = {
        "lt18": "lt18", "<18": "lt18", "<18h": "lt18", "<18 hours": "lt18", "less than 18": "lt18", "less than 18h": "lt18",
        "gte18": "gte18", ">=18": "gte18", ">=18h": "gte18", "greater than 18": "gte18", ">=18 hours": "gte18",
        "unknown": "unknown", "unkn": "unknown", "unk": "unknown", "not known": "unknown", "n/a": "unknown",
    }


class BornWhereEnum(_NormEnum):
    """Location of birth if born before arrival."""
    HOME_OR_ROADSIDE = "Home/Roadside"
    OTHER_FACILITY = "Other facility"

    _SYNONYMS = {
        "home": "Home/Roadside", "home delivery": "Home/Roadside", "domiciliary": "Home/Roadside",
        "roadside": "Home/Roadside", "road": "Home/Roadside", "in transit": "Home/Roadside",
        "other facility": "Other facility", "other hospital": "Other facility", "facility": "Other facility",
        "clinic": "Other facility", "referred": "Other facility", "transferred": "Other facility",
    }


# ---------------------------------------------------------------------------
# Section B — Mother's details

class ANCTrimesterEnum(_NormEnum):
    """Trimester in which ANC ultrasound was performed."""
    FIRST  = "1st"
    SECOND = "2nd"
    THIRD  = "3rd"

    _SYNONYMS = {
        "1st": "1st", "first": "1st", "1": "1st", "t1": "1st",
        "2nd": "2nd", "second": "2nd", "2": "2nd", "t2": "2nd",
        "3rd": "3rd", "third": "3rd", "3": "3rd", "t3": "3rd",
    }


class BloodGroupEnum(_NormEnum):
    """ABO blood group."""
    A       = "A"
    B       = "B"
    AB      = "AB"
    O       = "O"
    UNKNOWN = "Unknown"

    _SYNONYMS = {
        "a": "A", "a+": "A", "a-": "A",
        "b": "B", "b+": "B", "b-": "B",
        "ab": "AB", "ab+": "AB", "ab-": "AB",
        "o": "O", "o+": "O", "o-": "O",
        "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown", "?": "Unknown",
    }


class RhesusEnum(_NormEnum):
    """Rhesus blood group status."""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    UNKNOWN  = "Unknown"

    _SYNONYMS = {
        "positive": "Positive", "pos": "Positive", "+": "Positive", "rh+": "Positive", "rhesus positive": "Positive",
        "negative": "Negative", "neg": "Negative", "-": "Negative", "rh-": "Negative", "rhesus negative": "Negative",
        "unknown": "Unknown", "unkn": "Unknown", "unk": "Unknown",
    }


class AntiDEnum(_NormEnum):
    """Whether Anti-D medication was given."""
    Y       = "Y"
    N       = "N"

    _SYNONYMS = {
        "y": "Y", "yes": "Y", "given": "Y",
        "n": "N", "no": "N", "not given": "N",
    }


# ---------------------------------------------------------------------------
# Section F1 — General examination

class SkinEnum(_NormEnum):
    """Skin appearance on examination."""
    NORMAL          = "Normal"
    BRUISING        = "Bruising"
    RASH            = "Rash"
    PUSTULES        = "Pustules"
    MOTTLING        = "Mottling"
    DRY_PEELING     = "Dry/Peeling/Wrinkled"

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


class JaundiceEnum(_NormEnum):
    """Severity of jaundice on examination."""
    NONE     = "None"
    MILD     = "Mild"      # +
    SEVERE   = "Severe"    # +++

    _SYNONYMS = {
        "none": "None", "no": "None", "absent": "None",
        "mild": "Mild", "+": "Mild", "1+": "Mild",
        "severe": "Severe", "+++": "Severe", "3+": "Severe",
    }


class AppearanceEnum(_NormEnum):
    """General appearance of the infant."""
    WELL        = "Well"
    SICK        = "Sick"
    DYSMORPHIC  = "Dysmorphic"

    _SYNONYMS = {
        "well": "Well", "normal": "Well", "healthy": "Well",
        "sick": "Sick", "ill": "Sick", "unwell": "Sick",
        "dysmorphic": "Dysmorphic",
    }


class CryEnum(_NormEnum):
    """Quality of the infant's cry."""
    NORMAL = "Normal"
    WEAK_OR_ABSENT   = "Weak/Absent"
    HOARSE = "Hoarse"

    _SYNONYMS = {
        "normal": "Normal", "strong": "Normal", "good": "Normal", "well": "Normal",
        "weak": "Weak/Absent", "feeble": "Weak/Absent", "absent": "Weak/Absent", "no cry": "Weak/Absent",
        "weak/absent": "Weak/Absent", "weak / absent": "Weak/Absent", "weak-absent": "Weak/Absent",
        "hoarse": "Hoarse",
    }


class RetractionSeverityEnum(_NormEnum):
    """Severity of chest retraction (xiphoid or intercostal)."""
    NONE   = "None"
    MILD   = "Mild"
    SEVERE = "Severe"

    _SYNONYMS = {
        "none": "None", "no": "None", "absent": "None",
        "mild": "Mild", "moderate": "Mild",
        "severe": "Severe",
    }


class PallorEnum(_NormEnum):
    """Severity of pallor / anaemia."""
    NONE   = "None"
    MILD   = "Mild"    # +
    SEVERE = "Severe"  # +++

    _SYNONYMS = {
        "none": "None", "no": "None", "absent": "None",
        "mild": "Mild", "+": "Mild", "1+": "Mild", "moderate": "Mild",
        "severe": "Severe", "+++": "Severe", "3+": "Severe",
    }


class ToneEnum(_NormEnum):
    """Neurological tone of the infant."""
    NORMAL    = "Normal"
    INCREASED = "Increased"
    REDUCED   = "Reduced"

    _SYNONYMS = {
        "normal": "Normal",
        "increased": "Increased", "high": "Increased", "hypertonic": "Increased",
        "reduced": "Reduced", "low": "Reduced", "hypotonic": "Reduced",
        "floppy": "Reduced", "decreased": "Reduced",
    }


class UmbilicusEnum(_NormEnum):
    """Condition of the umbilicus."""
    CLEAN       = "Clean"
    LOCAL_PUS   = "Local pus"
    PUS_RED     = "Pus+Red skin"
    OTHERS      = "Others"

    _SYNONYMS = {
        "clean": "Clean", "clear": "Clean", "normal": "Clean", "dry": "Clean",
        "local pus": "Local pus", "localpus": "Local pus", "pus": "Local pus",
        "pus + red skin": "Pus+Red skin", "pus and red skin": "Pus+Red skin",
        "pus+red skin": "Pus+Red skin", "pus + redness": "Pus+Red skin", "pus with redness": "Pus+Red skin",
        "others": "Others", "other": "Others",
    }

class BirthDefectsEnum(_NormEnum):
    """Category of congenital birth defect recorded."""
    MAJOR_GI_ABNORMALITY = "Major gi abnormality",
    HYDROCEPHALUS = "Hydrocephalus",
    CLEFT_LIP_OR_PALATED = "Clef lip/palated",
    MICROCEPHALY = "Microcephalus",
    NEURAL_TUBE_DEFECTS = "Neural tube defects",
    SPINA_BIFIDA = "Spina bifida",
    LIMB_ABNORMALITIES = "Limb abnormalities",
    BIRTH_INJURY_OR_ABNORMALITIES = "Birth injury or abnormalities",

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

CATEGORICAL_FIELD_MAP: dict[str, type[_NormEnum]] = {
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