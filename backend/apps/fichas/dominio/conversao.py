"""Conversão de unidades do ingrediente: mL e densidade para gramas.

O sistema sempre calcula em gramas (BR-001): a quantidade gravada no
ingrediente é em gramas, e a unidade mL só registra como ela foi informada.
"""


def _validar_densidade(densidade):
    if densidade is None or densidade <= 0:
        raise ValueError("A densidade deve ser maior que zero.")


def ml_para_gramas(qtde_ml: float, densidade: float) -> float:
    """Converte mL em gramas. Ex.: 100 mL com densidade 1,2 g/mL = 120 g."""
    _validar_densidade(densidade)
    return qtde_ml * densidade


def gramas_para_ml(qtde_g: float, densidade: float) -> float:
    """Inverso de ml_para_gramas. Ex.: 120 g com densidade 1,2 g/mL = 100 mL."""
    _validar_densidade(densidade)
    return qtde_g / densidade