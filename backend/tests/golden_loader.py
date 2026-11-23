"""Carregador único dos arquivos golden (backend/tests/golden/*.json.gz).

Os golden são o histórico do sistema antigo e NUNCA são editados. Quando o texto
de um rótulo muda de propósito, a mudança entra em RENOMEACOES e é aplicada aqui,
ao carregar, só no texto do rótulo. Nenhum valor numérico é alterado.
"""
import gzip
import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# Renomeações intencionais de rótulos: texto antigo (no golden) -> texto novo.
# "Fibra Alimentar" -> "Fibras Alimentares": mudança pedida pela NutriJR em 16/11.
RENOMEACOES = {"Fibra Alimentar": "Fibras Alimentares"}


def _renomear_linhas(golden):
    """Troca só o texto do rótulo (posição 0) das linhas do registro de nutrientes.

    Linhas com mais de 3 posições vêm do registro; as de 3 posições são nutrientes
    extras digitados à mão e ficam como estão.
    """
    fichas = golden.get("fichas")
    if not isinstance(fichas, dict):
        return golden
    for ficha in fichas.values():
        for linha in ficha.get("linhas", []) if isinstance(ficha, dict) else []:
            if len(linha) > 3 and linha[0] in RENOMEACOES:
                linha[0] = RENOMEACOES[linha[0]]
    return golden


def carregar_golden(nome):
    """Lê `golden/<nome>` (ex.: "golden_fichax.json.gz") e devolve o JSON completo."""
    with gzip.open(GOLDEN_DIR / nome, "rt", encoding="utf-8") as f:
        return _renomear_linhas(json.load(f))
