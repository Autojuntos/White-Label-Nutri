"""Paridade da montagem do rótulo (D-008): dominio.rotulo deve reproduzir a
fichaX original em todas as 1.557 fichas do golden_fichax.json.gz, a partir dos
valores PERSISTIDOS da tabela (golden_paridade.json.gz).

Exceção registrada (D-005): B3 corrigido — a coluna "por 100 g" do Manganês no
original usa magnesio_100g; a nova versão usa manganes_100g. Para essas linhas o
teste compara as demais colunas e verifica que o valor do golden é exatamente o
valor bugado (prova de que a divergência é o fix, não um erro novo).
"""
import json

import pytest

from apps.fichas.dominio import rotulo
from tests.golden_loader import carregar_golden

# sha1[:12] das imagens base64 do original → combinação canônica
LUPA_POR_COMBINACAO = {
    "acucares+gorduras+sodio": "0c869dc433ff",
    "acucares+gorduras": "041acba626cf",
    "acucares+sodio": "93fc9d989dcc",
    "gorduras+sodio": "ee92eb2a1dde",
    "acucares": "47a278f93e77",
    "gorduras": "4e42155fdfe8",
    "sodio": "f82c1af3f876",
    None: None,
}


@pytest.fixture(scope="module")
def fichax():
    return carregar_golden("golden_fichax.json.gz")["fichas"]


@pytest.fixture(scope="module")
def paridade():
    return carregar_golden("golden_paridade.json.gz")["fichas"]


def _normaliza(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str))


def _ingredientes_equivalentes(itens, texto_golden):
    """BR-014 exige peso líquido decrescente; a ordem entre EMPATES é indefinida
    no original (ORDER BY do Postgres sem desempate). Aceita o texto do golden se
    ele corresponder a alguma ordenação válida: consome o texto item a item,
    permitindo qualquer permutação dentro de cada grupo de mesmo peso.
    """
    resto = texto_golden.lower()

    def parte(item):
        composicao = item.get("composicao")
        nome = item["nomeFantasia"]
        return f"{nome} ({composicao})".lower() if composicao else nome.lower()

    ordenados = sorted(itens, key=lambda i: -(i.get("pesoLiquido") or 0))
    grupos: list[list] = []
    for item in ordenados:
        peso = item.get("pesoLiquido") or 0
        if grupos and grupos[-1][0] == peso:
            grupos[-1][1].append(item)
        else:
            grupos.append([peso, [item]])

    for _, pendentes in grupos:
        while pendentes:
            achado = None
            for item in pendentes:
                p = parte(item)
                if resto == p + "." or resto.startswith(p + ", "):
                    achado = item
                    resto = "" if resto == p + "." else resto[len(p) + 2:]
                    break
            if achado is None:
                return False
            pendentes.remove(achado)
    return resto == ""


def test_paridade_rotulo_completa(fichax, paridade):
    divergencias = []
    manganes_fix_verificado = 0

    for pk, esperado in fichax.items():
        g = paridade[pk]
        tp = g["tabela_persistida"]
        ent = g["entradas"]

        valores = {
            chave: rotulo.ValoresNutriente(
                arred=v[3], vd=v[4], unidade=v[6], por_100g=v[1], mostrar=v[5]
            )
            for chave, v in tp.items()
        }
        extras = [(e[0], e[2], e[3]) for e in g["extras"]]
        minhas = _normaliza(rotulo.montar_linhas(valores, extras))
        kcal, kj = valores.get("energiakcal"), valores.get("energiaKJ")
        if kcal and kj and kcal.mostrar and not kj.mostrar:
            # Divergência intencional (BR-030): o original sumia com o valor energético
            # quando só o kJ estava desmarcado; agora a linha continua no rótulo.
            assert minhas[0][0] == "Valor energético"
            minhas = minhas[1:]

        # --- linhas da tabela ---
        if len(minhas) != len(esperado["linhas"]):
            divergencias.append((pk, "num_linhas", len(minhas), len(esperado["linhas"])))
        else:
            for minha, dele in zip(minhas, esperado["linhas"]):
                if minha == dele:
                    continue
                if minha[0] == "Manganês" and minha[:4] == dele[:4]:
                    # B3: golden carrega o valor bugado (magnesio_100g)
                    bugado = _normaliza(rotulo.tira_zero(round(tp["magnesio"][1], 1)))
                    if dele[4] == bugado:
                        manganes_fix_verificado += 1
                        continue
                divergencias.append((pk, "linha", minha, dele))

        # --- lupa ---
        combo = rotulo.combinacao_lupa(
            rotulo.nutrientes_altos(tp["acucaresadd"][1], tp["gordSat"][1], tp["sodio"][1])
        )
        if LUPA_POR_COMBINACAO[combo] != esperado["lupa"]:
            divergencias.append((pk, "lupa", combo, esperado["lupa"]))

        # --- cabeçalho ---
        if _normaliza(rotulo.calcular_num_porcoes(ent["pesoPorcao"], ent["pesoAnvisa"])) \
                != esperado["numPorcoesExibicao"]:
            divergencias.append((pk, "numPorcoesExibicao",
                                 rotulo.calcular_num_porcoes(ent["pesoPorcao"], ent["pesoAnvisa"]),
                                 esperado["numPorcoesExibicao"]))
        if _normaliza(rotulo.peso_anvisa_sem_zero(ent["pesoAnvisa"], ent["pesoPorcao"])) \
                != esperado["pesoAnvisaSemZero"]:
            divergencias.append((pk, "pesoAnvisaSemZero"))
        if rotulo.num_porcoes_exibicao(ent["pesoPorcao"], ent["pesoAnvisa"]) \
                != esperado["numPorcoes"]:
            divergencias.append((pk, "numPorcoes"))

        # --- lista de ingredientes (tolerante a permutação entre pesos iguais) ---
        meu_texto = rotulo.ordenar_ingredientes(ent["itens"])
        if meu_texto != esperado["ordemIngredientes"] and not _ingredientes_equivalentes(
            ent["itens"], esperado["ordemIngredientes"]
        ):
            divergencias.append((pk, "ingredientes", meu_texto, esperado["ordemIngredientes"]))

    assert not divergencias, (
        f"{len(divergencias)} divergências (primeiras 5): {divergencias[:5]}"
    )
    assert manganes_fix_verificado >= 0  # informativo


def test_valor_energetico_nao_some_quando_so_kj_esta_desmarcado():
    def v(mostrar, unidade="kcal"):
        return rotulo.ValoresNutriente(arred=186, vd=9, unidade=unidade, por_100g=372, mostrar=mostrar)

    linhas = rotulo.montar_linhas({"energiakcal": v(True), "energiaKJ": v(False, "kJ")})
    assert linhas[0][:2] == ["Valor energético", "186"]

    linhas = rotulo.montar_linhas({"energiakcal": v(False), "energiaKJ": v(True, "kJ")})
    assert linhas == []


def test_texto_alergicos_nao_duplica_prefixo():
    assert rotulo.texto_alergicos("ALÉRGICOS: contém trigo.") == "ALÉRGICOS: CONTÉM TRIGO."
    assert rotulo.texto_alergicos("contém trigo.") == "ALÉRGICOS: CONTÉM TRIGO."
    assert rotulo.texto_alergicos("  ") == ""
    assert rotulo.texto_alergicos(None) == ""
