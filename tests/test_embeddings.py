"""Pruebas de la lógica de ranking con embeddings, usando un codificador falso (sin descargar modelos)."""

import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402
from src.embeddings import evaluar_embeddings  # noqa: E402
from src.linea_base import leer_csv, tokenizar  # noqa: E402


def codificador_falso(vocabulario):
    """Vector de conteo de palabras, normalizado. Sirve para probar la lógica sin un modelo real."""
    indice = {w: i for i, w in enumerate(vocabulario)}

    def codificar(textos):
        m = np.zeros((len(textos), len(vocabulario)))
        for fila, t in enumerate(textos):
            for w in tokenizar(t):
                if w in indice:
                    m[fila, indice[w]] += 1
        normas = np.linalg.norm(m, axis=1, keepdims=True)
        normas[normas == 0] = 1
        return m / normas

    return codificar


@pytest.fixture(scope="module")
def datos_dir(tmp_path_factory):
    cfg = gd.cargar_json(RAIZ / "configs" / "generacion.json")
    cat = gd.cargar_json(RAIZ / "configs" / "catalogo.json")
    destino = tmp_path_factory.mktemp("datos")
    gd.escribir_salida(gd.generar(cfg, cat), cfg, destino)
    return destino


def test_evaluar_con_codificador_falso_funciona_y_supera_al_azar(datos_dir):
    vocab = sorted({w for c in leer_csv(datos_dir / "cvs.csv") for w in tokenizar(c["texto"])})
    res = evaluar_embeddings(datos_dir, "dev", codificador_falso(vocab))
    assert len(res["filas"]) == 5  # las 5 ofertas de dev
    assert res["promedios"]["ndcg@10"] > 0.3  # el azar da ~0.1
    for fila in res["filas"]:
        assert 0.0 <= fila["ndcg@10"] <= 1.0
        assert 0.0 <= fila["mrr"] <= 1.0


def test_evaluar_es_determinista(datos_dir):
    vocab = sorted({w for c in leer_csv(datos_dir / "cvs.csv") for w in tokenizar(c["texto"])})
    a = evaluar_embeddings(datos_dir, "dev", codificador_falso(vocab))
    b = evaluar_embeddings(datos_dir, "dev", codificador_falso(vocab))
    assert a == b


def test_particion_invalida_da_error(datos_dir):
    with pytest.raises(ValueError):
        evaluar_embeddings(datos_dir, "no_existe", lambda t: np.zeros((len(t), 3)))
