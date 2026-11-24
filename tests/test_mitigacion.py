"""Pruebas de E-04 (BM25 con género neutralizado)."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402
from src.mitigacion import FEMENINO_A_MASCULINO, main, tokenizar_neutro  # noqa: E402


def test_femenino_y_masculino_dan_los_mismos_tokens():
    assert tokenizar_neutro("Ingeniera comprometida") == tokenizar_neutro("Ingeniero comprometido")


def test_la_lista_cubre_todas_las_formas_del_generador():
    fem = {f for _, f in gd.GENERO_FORMAS.values()}
    assert fem == set(FEMENINO_A_MASCULINO)


def test_e04_elimina_el_sesgo_de_puntaje(tmp_path):
    cfg = gd.cargar_json(RAIZ / "configs" / "generacion.json")
    cat = gd.cargar_json(RAIZ / "configs" / "catalogo.json")
    datos = tmp_path / "d"
    gd.escribir_salida(gd.generar(cfg, cat), cfg, datos)
    r = main(["--datos", str(datos), "--resultados", str(tmp_path / "r")])
    assert r["auditoria"]["resumen"]["pct_empates"] > 0.99
