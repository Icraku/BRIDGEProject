from utils.schema_helpers import get_true_option

def map_to_schema(structured_output: dict) -> dict:
    """
    Map structured LLM output to clean schema fields.
    """

    infant = (
        structured_output.get("A: Infant Details") or
        structured_output.get("Infant Details") or
        {}
    )

    A_B = (
        structured_output.get("A: B") or
        structured_output.get("A_B") or
        {}
    )

    symptoms = (
        structured_output.get("E: History and examination", {}).get("Symptoms", {})
        or structured_output.get("History and examination", {}).get("Symptoms & History", {})
        or {}
    )

    # SEX
    sex = None
    if "Sex" in infant:
        sex = get_true_option(infant["Sex"])
    elif infant.get("Sex_F"):
        sex = "F"
    elif infant.get("Sex_M"):
        sex = "M"
    elif infant.get("Sex_I"):
        sex = "I"

    # DELIVERY
    delivery = None
    if "Delivery" in infant:
        delivery = get_true_option(infant["Delivery"])
    else:
        for k in ["SVD", "CS", "Vacuum", "Forceps", "Breech"]:
            if infant.get(f"Delivery_{k}"):
                delivery = k
                break

    return {
        "sex": sex,
        "delivery": delivery,
        "born_outside": infant.get("Born_outside_facility_Y", False),
        "multiple_delivery": infant.get("Multiple_delivery_Y", False),
        "crackles": A_B.get("Crackles_Y", False),
        "Reduced_movement": symptoms.get("Reduced / Absent movement_Y", False),
    }