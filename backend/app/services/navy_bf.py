import math


def bf_percent_male(height_cm: float, waist_cm: float, neck_cm: float) -> float:
    return 495 / (
        1.0324
        - 0.19077 * math.log10(waist_cm - neck_cm)
        + 0.15456 * math.log10(height_cm)
    ) - 450


def bf_percent_female(
    height_cm: float, waist_cm: float, neck_cm: float, hip_cm: float
) -> float:
    return 495 / (
        1.29579
        - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm)
        + 0.22100 * math.log10(height_cm)
    ) - 450


def calc_bf(
    sexo: str,
    altura_cm: float,
    cintura_cm: float,
    pescoco_cm: float,
    quadril_cm: float | None,
) -> float:
    sexo = sexo.upper()
    if sexo == "M":
        return bf_percent_male(altura_cm, cintura_cm, pescoco_cm)
    if sexo == "F":
        if quadril_cm is None:
            raise ValueError("quadril_cm is required for female")
        return bf_percent_female(altura_cm, cintura_cm, pescoco_cm, quadril_cm)
    raise ValueError("sexo must be M or F")
