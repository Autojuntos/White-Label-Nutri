"""Testes do cadastro de ingrediente em mL com densidade."""
import pytest
from django.contrib.auth.models import User

from apps.fichas.leitura_rotulo import LeituraRotulo, montar_resultado
from apps.fichas.models import Ingrediente, Membro


@pytest.fixture
def membro(db):
    user = User.objects.create_user("laura", password="s3nh4-forte")
    return Membro.objects.create(
        usuario=user, nome="Laura", semestre="2024.1", email="l@x.com"
    )


@pytest.fixture
def logado(client, membro):
    client.force_login(membro.usuario)
    return client


def _dados(membro, **extra):
    """Dados de um ingrediente em mL: 5 g de proteína em 100 mL."""
    dados = {
        "autorIng": membro.pk, "nomeIng": "Leite", "composicao": "",
        "origemDosDados": "Marca X", "qtdeDoIngrediente": 100, "unidade": "mL",
        "numRef": 0, "dataCriacao": "10/01/2025", "proteinas": 5,
    }
    dados.update(extra)
    return dados


def test_ml_com_densidade_grava_em_gramas(logado, membro):
    logado.post("/registrarIngrediente", _dados(membro, densidade=1.2))
    ing = Ingrediente.objects.get(nomeIng="Leite")
    assert ing.unidade == "mL"
    assert ing.densidade == pytest.approx(1.2)
    assert ing.qtdeDoIngrediente == pytest.approx(120)  # 100 mL x 1,2
    assert ing.proteinas_100g == pytest.approx(5 * 100 / 120)  # BR-001 em gramas


def test_ml_sem_densidade_e_recusado(logado, membro):
    resp = logado.post("/registrarIngrediente", _dados(membro))
    assert resp.status_code == 200
    assert "Informe a densidade" in resp.content.decode()
    assert not Ingrediente.objects.exists()


@pytest.mark.parametrize("densidade", [0, -1])
def test_densidade_zero_ou_negativa_e_recusada(logado, membro, densidade):
    resp = logado.post("/registrarIngrediente", _dados(membro, densidade=densidade))
    assert "Informe a densidade" in resp.content.decode()
    assert not Ingrediente.objects.exists()


def test_em_gramas_ignora_a_densidade(logado, membro):
    logado.post("/registrarIngrediente", _dados(membro, unidade="g", densidade=1.2))
    ing = Ingrediente.objects.get(nomeIng="Leite")
    assert ing.unidade == "g"
    assert ing.densidade is None
    assert ing.qtdeDoIngrediente == pytest.approx(100)


def test_edicao_mostra_a_quantidade_em_ml(logado, membro):
    logado.post("/registrarIngrediente", _dados(membro, densidade=1.2))
    ing = Ingrediente.objects.get(nomeIng="Leite")
    resp = logado.get(f"/editarIngrediente/{ing.pk}")
    assert resp.context["form"].initial["qtdeDoIngrediente"] == pytest.approx(100)


def test_mudar_a_densidade_refaz_os_gramas(logado, membro):
    logado.post("/registrarIngrediente", _dados(membro, densidade=1.2))
    ing = Ingrediente.objects.get(nomeIng="Leite")
    logado.post(f"/editarIngrediente/{ing.pk}", _dados(membro, densidade=1.0))
    ing.refresh_from_db()
    assert ing.qtdeDoIngrediente == pytest.approx(100)  # 100 mL x 1,0
    assert ing.proteinas_100g == pytest.approx(5)


# ------------------------------------------------------- leitura por foto

def _leitura(em_ml):
    return LeituraRotulo.model_validate_json(
        '{"e_tabela_nutricional": true, "em_ml": %s, "porcao_g": 200,'
        ' "nutrientes": {"proteinas": {"por_100g": 3.2, "por_porcao": 6.4}}}'
        % ("true" if em_ml else "false")
    )


def test_leitura_em_ml_marca_a_unidade_e_nao_devolve_densidade():
    resultado = montar_resultado(_leitura(em_ml=True))
    assert resultado["campos"]["unidade"] == "mL"
    assert "densidade" not in resultado["campos"]  # a pessoa preenche
    assert any("densidade" in aviso for aviso in resultado["avisos"])


def test_leitura_em_gramas_marca_a_unidade_g():
    resultado = montar_resultado(_leitura(em_ml=False))
    assert resultado["campos"]["unidade"] == "g"