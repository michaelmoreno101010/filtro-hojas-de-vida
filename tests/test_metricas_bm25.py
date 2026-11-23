"""Pruebas de las métricas de ranking y de la línea base BM25."""

import math
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.linea_base import BM25, ordenar, tokenizar  # noqa: E402
from src.metricas import mrr, ndcg_at_k, precision_at_k, recall_at_k  # noqa: E402


def test_ndcg_ranking_perfecto_es_uno():
    todas = [3, 3, 2, 1, 0, 0]
    assert ndcg_at_k([3, 3, 2, 1, 0, 0], todas, k=10) == pytest.approx(1.0)


def test_ndcg_peor_ranking_es_menor():
    todas = [3, 3, 2, 1, 0, 0]
    assert ndcg_at_k([0, 0, 1, 2, 3, 3], todas, k=3) < ndcg_at_k([3, 3, 2, 1, 0, 0], todas, k=3)


def test_ndcg_valor_calculado_a_mano():
    # un solo relevante (rel 3) en la posición 2: dcg = 7/log2(3); ideal = 7/log2(2) = 7
    assert ndcg_at_k([0, 3], [3, 0], k=10) == pytest.approx((7 / math.log2(3)) / 7)


def test_ndcg_sin_relevantes_es_cero():
    assert ndcg_at_k([0, 0], [0, 0], k=10) == 0.0


def test_mrr():
    assert mrr([3, 0, 0]) == 1.0
    assert mrr([0, 0, 2]) == pytest.approx(1 / 3)
    assert mrr([1, 1, 1]) == 0.0  # relevancia 1 no cuenta como relevante


def test_recall_y_precision():
    ordenadas = [3, 0, 2, 0]
    todas = [3, 2, 2, 0]  # 3 relevantes en total
    assert recall_at_k(ordenadas, todas, k=3) == pytest.approx(2 / 3)
    assert precision_at_k(ordenadas, k=2) == pytest.approx(1 / 2)


def test_tokenizar_quita_tildes_y_vacias():
    assert tokenizar("Gestión de PROYECTOS en la oficina") == ["gestion", "proyectos", "oficina"]


def test_bm25_prefiere_el_documento_que_contiene_la_consulta():
    docs = [tokenizar(t) for t in ["python y sql para analisis", "cuidado de pacientes", "contabilidad general"]]
    bm = BM25(docs)
    p = bm.puntajes(tokenizar("analisis con python"))
    assert p[0] > p[1] and p[0] > p[2]
    assert p[1] == 0.0


def test_bm25_termino_raro_pesa_mas_que_uno_comun():
    docs = [["comun", "raro"], ["comun"], ["comun"], ["comun"]]
    bm = BM25(docs)
    assert bm.idf["raro"] > bm.idf["comun"]


def test_ordenar_resuelve_empates_por_id():
    assert ordenar(["b", "a", "c"], [1.0, 1.0, 2.0]) == ["c", "a", "b"]
