"""Testes unitários do cálculo de energia (BR-003) considerando os tipos de fibra."""
import pytest

from apps.fichas.dominio.calculo import EntradaCalculo, ItemReceita, calcular


def _criar_entrada(tipo_fibra: str, fibras: float = 10.0, carboidratos: float = 30.0,
                   proteinas: float = 10.0, gorduras: float = 5.0) -> EntradaCalculo:
    """Helper que monta uma entrada de teste para 100 g de receita."""
    return EntradaCalculo(
        peso_total=100.0,
        peso_porcao=100.0,
        peso_anvisa=100.0,
        itens=[
            ItemReceita(
                peso_liquido=100.0,
                ing_100g={
                    "proteinas": proteinas,
                    "carboidratos": carboidratos,
                    "fibras": fibras,
                    "gordTotais": gorduras,
                },
                tipo_fibra=tipo_fibra,
            )
        ],
    )


def test_energia_fibra_soluvel():
    """Fibra solúvel: 2 kcal/g.
    Cálculo à mão:
    - Proteínas: 10 * 4 = 40 kcal
    - Carboidratos disponíveis: (30 - 10) * 4 = 80 kcal
    - Fibra solúvel: 10 * 2 = 20 kcal
    - Gorduras: 5 * 9 = 45 kcal
    - Total: 40 + 80 + 20 + 45 = 185 kcal (e 185 * 4.184 = 774.04 kJ)
    """
    entrada = _criar_entrada(tipo_fibra="soluvel")
    r = calcular(entrada)
    assert r.total["energiakcal"] == pytest.approx(185.0)
    assert r.total["energiaKJ"] == pytest.approx(774.04)


def test_energia_polidextrose():
    """Polidextrose: 1 kcal/g.
    Cálculo à mão:
    - Proteínas: 10 * 4 = 40 kcal
    - Carboidratos disponíveis: (30 - 10) * 4 = 80 kcal
    - Polidextrose: 10 * 1 = 10 kcal
    - Gorduras: 5 * 9 = 45 kcal
    - Total: 40 + 80 + 10 + 45 = 175 kcal (e 175 * 4.184 = 732.2 kJ)
    """
    entrada = _criar_entrada(tipo_fibra="polidextrose")
    r = calcular(entrada)
    assert r.total["energiakcal"] == pytest.approx(175.0)
    assert r.total["energiaKJ"] == pytest.approx(732.2)


def test_energia_fibra_insoluvel():
    """Fibra insolúvel: 0 kcal/g.
    Cálculo à mão:
    - Proteínas: 10 * 4 = 40 kcal
    - Carboidratos disponíveis: (30 - 10) * 4 = 80 kcal
    - Fibra insolúvel: 10 * 0 = 0 kcal
    - Gorduras: 5 * 9 = 45 kcal
    - Total: 40 + 80 + 0 + 45 = 165 kcal (e 165 * 4.184 = 690.36 kJ)
    """
    entrada = _criar_entrada(tipo_fibra="insoluvel")
    r = calcular(entrada)
    assert r.total["energiakcal"] == pytest.approx(165.0)
    assert r.total["energiaKJ"] == pytest.approx(690.36)


def test_energia_fibra_nao_informado():
    """Fibra não informada: conta nos carboidratos a 4 kcal/g (cálculo antigo).
    Cálculo à mão:
    - Proteínas: 10 * 4 = 40 kcal
    - Carboidratos totais (fibra não subtrai): 30 * 4 = 120 kcal
    - Gorduras: 5 * 9 = 45 kcal
    - Total: 40 + 120 + 45 = 205 kcal (e 205 * 4.184 = 857.72 kJ)
    """
    entrada = _criar_entrada(tipo_fibra="nao_informado")
    r = calcular(entrada)
    assert r.total["energiakcal"] == pytest.approx(205.0)
    assert r.total["energiaKJ"] == pytest.approx(857.72)


def test_energia_receita_mista():
    """Receita mista: um ingrediente com fibra solúvel e outro não informado.
    Item 1 (solúvel): 100 g, 5 g prot, 20 g carb, 5 g fibra solúvel, 2 g gord.
      -> 5*4 + (20-5)*4 + 5*2 + 2*9 = 20 + 60 + 10 + 18 = 108 kcal
    Item 2 (não informado): 100 g, 5 g prot, 25 g carb, 3 g fibra, 1 g gord.
      -> 5*4 + 25*4 + 1*9 = 20 + 100 + 9 = 129 kcal
    Total da receita: 108 + 129 = 237 kcal.
    """
    entrada = EntradaCalculo(
        peso_total=200.0,
        peso_porcao=100.0,
        peso_anvisa=100.0,
        itens=[
            ItemReceita(
                peso_liquido=100.0,
                ing_100g={"proteinas": 5.0, "carboidratos": 20.0, "fibras": 5.0, "gordTotais": 2.0},
                tipo_fibra="soluvel",
            ),
            ItemReceita(
                peso_liquido=100.0,
                ing_100g={"proteinas": 5.0, "carboidratos": 25.0, "fibras": 3.0, "gordTotais": 1.0},
                tipo_fibra="nao_informado",
            ),
        ],
    )
    r = calcular(entrada)
    assert r.total["energiakcal"] == pytest.approx(237.0)
    assert r.total["energiaKJ"] == pytest.approx(237.0 * 4.184)