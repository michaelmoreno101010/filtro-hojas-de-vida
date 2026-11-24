"""Pruebas de E-05 (híbrido con fusión de rangos)."""

import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402
from src.hibrido import evaluar_hibrido, fusionar  # noqa: E402
from src.linea_base import leer_csv, tokenizar  # noqa: E402


def test_fusionar_premia_al_que_esta_arriba_en_ambas_listas():
    ids = ["a", "b", "c"]
    p = fusionar(ids, [[3.0, 2.0, 1.0], [3.0, 1.0, 2.0]])
    assert p[0] > p[1] and p[0] > p[2]


def test_fusionar_valor_calculado_a_mano():
    p = fusionar(["a", "b"], [[2.0, 1.0], [1.0, 2.0]], k=60)
    assert p[0] == p[1] == 1 / 61 + 1 / 62


def test_hibrido_corre_con_codificador_falso(tmp_path):
    cfg = gd.cargar_json(RAIZ / "configs" / "generacion.json")
    cat = gd.cargar_json(RAIZ / "configs" / "catalogo.json")
    gd.escribir_salida(gd.generar(cfg, cat), cfg, tmp_path)
    vocab = {w: i for i, w in enumerate(sorted({w for c in leer_csv(tmp_path / "cvs.csv") for w in tokenizar(c["texto"])}))}

    def codificar(textos):
        m = np.zeros((len(textos), len(vocab)))
        for i, t in enumerate(textos):
            for w in tokenizar(t):
                if w in vocab:
                    m[i, vocab[w]] += 1
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1
        return m / n

    r = evaluar_hibrido(tmp_path, "dev", codificar)
    assert len(r["filas"]) == 5
    assert r["promedios"]["ndcg@10"] > 0.3
