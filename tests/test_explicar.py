import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402
from src.explicar import explicar_oferta  # noqa: E402


@pytest.fixture(scope="module")
def datos(tmp_path_factory):
    cfg = gd.cargar_json(RAIZ / "configs" / "generacion.json")
    cat = gd.cargar_json(RAIZ / "configs" / "catalogo.json")
    d = tmp_path_factory.mktemp("d")
    gd.escribir_salida(gd.generar(cfg, cat), cfg, d)
    return d


def test_la_suma_de_aportes_es_el_puntaje(datos):
    for r in explicar_oferta(datos, "of_01", top=5):
        assert sum(r["palabras"].values()) == pytest.approx(r["puntaje"])


def test_el_top_viene_ordenado_por_puntaje(datos):
    p = [r["puntaje"] for r in explicar_oferta(datos, "of_03", top=5)]
    assert p == sorted(p, reverse=True)


def test_oferta_inexistente_da_error(datos):
    with pytest.raises(ValueError):
        explicar_oferta(datos, "of_99")
