"""Pruebas de la auditoría de sesgo con pares sintéticos de puntajes conocidos."""

import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402
from src.auditoria import auditar, puntajes_bm25, puntajes_embeddings  # noqa: E402
from src.linea_base import leer_csv, tokenizar  # noqa: E402


def mini_conjunto(sesgo_a_favor_de=None, n=10):
    """n CVs base (mitad F, mitad M) + sus n gemelos. Puntaje base decreciente; sesgo opcional."""
    cv_ids, generos, puntajes = [], {}, []
    for i in range(n):
        g = "F" if i % 2 == 0 else "M"
        base, gem = f"cv_{i:03d}", f"cv_{i:03d}_g"
        cv_ids += [base, gem]
        generos[base] = g
        generos[gem] = "M" if g == "F" else "F"
    for c in cv_ids:
        i = int(c[3:6])
        s = 100.0 - i  # los primeros CVs puntúan más
        if sesgo_a_favor_de is not None and generos[c] == sesgo_a_favor_de:
            s += 0.4
        puntajes.append(s)
    return cv_ids, generos, {"of_01": puntajes}


def test_sin_sesgo_hay_empates_y_cumple():
    cv_ids, generos, p = mini_conjunto(sesgo_a_favor_de=None)
    r = auditar(cv_ids, generos, p, k=4)["resumen"]
    assert r["pct_empates"] == 1.0
    assert r["brecha_rango_abs_media"] <= 1.0  # solo desempate por id
    assert r["cumple_criterios"] is True


def test_sesgo_contra_mujeres_se_detecta():
    cv_ids, generos, p = mini_conjunto(sesgo_a_favor_de="M")
    r = auditar(cv_ids, generos, p, k=3)["resumen"]
    assert r["pct_gemelo_M_con_mayor_puntaje"] == 1.0
    assert r["pct_gemela_F_con_mayor_puntaje"] == 0.0
    assert r["brecha_rango_media_F_menos_M"] > 0  # la mujer queda más abajo
    assert r["saltos_top"] >= 1
    assert r["cumple_criterios"] is False


def test_sesgo_a_favor_de_mujeres_tambien_se_detecta():
    cv_ids, generos, p = mini_conjunto(sesgo_a_favor_de="F")
    r = auditar(cv_ids, generos, p, k=3)["resumen"]
    assert r["pct_gemela_F_con_mayor_puntaje"] == 1.0
    assert r["brecha_rango_media_F_menos_M"] < 0
    assert r["cumple_criterios"] is False


def test_razon_de_impacto_con_top_solo_de_hombres():
    cv_ids = ["a", "a_g", "b", "b_g"]
    generos = {"a": "F", "a_g": "M", "b": "M", "b_g": "F"}
    puntajes = {"of": [1.0, 4.0, 3.0, 2.0]}  # top-2 = a_g (M) y b (M)
    r = auditar(cv_ids, generos, puntajes, k=2)["resumen"]
    assert r["tasa_seleccion_F"] == 0.0
    assert r["razon_de_impacto_F_sobre_M"] == 0.0
    assert r["cumple_razon_de_impacto"] is False


def test_sin_gemelos_da_error():
    with pytest.raises(ValueError):
        auditar(["a", "b"], {"a": "F", "b": "M"}, {"of": [1.0, 2.0]})


def test_auditoria_bm25_sobre_los_datos_reales(tmp_path):
    cfg = gd.cargar_json(RAIZ / "configs" / "generacion.json")
    cat = gd.cargar_json(RAIZ / "configs" / "catalogo.json")
    gd.escribir_salida(gd.generar(cfg, cat), cfg, tmp_path)
    cvs = leer_csv(tmp_path / "cvs.csv")
    ofertas = [o for o in leer_csv(tmp_path / "ofertas.csv") if o["particion"] == "dev"]
    res = auditar(
        [c["cv_id"] for c in cvs],
        {c["cv_id"]: c["genero"] for c in cvs},
        puntajes_bm25(cvs, ofertas),
    )["resumen"]
    assert res["pares_evaluados"] == 100 * 5
    total = res["pct_gemela_F_con_mayor_puntaje"] + res["pct_gemelo_M_con_mayor_puntaje"] + res["pct_empates"]
    assert total == pytest.approx(1.0)


def test_puntajes_embeddings_con_codificador_falso():
    cvs = [{"texto": "python sql"}, {"texto": "cuidado pacientes"}]
    ofertas = [{"oferta_id": "of_01", "texto": "python"}]

    def codificar(textos):
        m = np.array([[1.0 if "python" in t else 0.0, 1.0 if "pacientes" in t else 0.0] for t in textos])
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1
        return m / n

    p = puntajes_embeddings(cvs, ofertas, codificar)
    assert p["of_01"][0] > p["of_01"][1]
