"""Testes da conversão de mL e densidade para gramas."""
import pytest

from apps.fichas.dominio.conversao import gramas_para_ml, ml_para_gramas


def test_ml_para_gramas_exemplo_do_card():
    assert ml_para_gramas(100, 1.2) == pytest.approx(120)


def test_gramas_para_ml_e_o_inverso():
    assert gramas_para_ml(120, 1.2) == pytest.approx(100)


@pytest.mark.parametrize("densidade", [None, 0, -1])
def test_densidade_invalida_levanta_erro(densidade):
    with pytest.raises(ValueError):
        ml_para_gramas(100, densidade)
    with pytest.raises(ValueError):
        gramas_para_ml(100, densidade)