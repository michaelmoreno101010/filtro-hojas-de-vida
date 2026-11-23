"""Pruebas del generador de datos sintéticos.

Se ejecutan con:  python -m pytest -q
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return gd.cargar_json(RAIZ / "configs" / "generacion.json")


@pytest.fixture(scope="module")
def cat():
    return gd.cargar_json(RAIZ / "configs" / "catalogo.json")


@pytest.fixture(scope="module")
def datos(cfg, cat):
    return gd.generar(cfg, cat)


def test_conteos(datos, cfg):
    assert len(datos["ofertas"]) == 10
    assert len(datos["cvs"]) == cfg["n_cvs_base"] + cfg["n_gemelos"]
    assert len(datos["relevancia"]) == 10 * len(datos["cvs"])


def test_determinismo(cfg, cat):
    """Misma semilla, mismos datos."""
    a = gd.generar(cfg, cat)
    b = gd.generar(cfg, cat)
    assert a == b


def test_semilla_distinta_cambia_datos(cfg, cat):
    otra = dict(cfg, semilla=cfg["semilla"] + 1)
    a = gd.generar(cfg, cat)
    b = gd.generar(otra, cat)
    assert [c["texto"] for c in a["cvs"]] != [c["texto"] for c in b["cvs"]]


def test_ids_unicos(datos):
    ids = [c["cv_id"] for c in datos["cvs"]]
    assert len(ids) == len(set(ids))


def test_genero_balanceado_por_rol(datos):
    """Cada rol tiene casi la misma cantidad de mujeres y de hombres (CVs base)."""
    por_rol = {}
    for cv in datos["cvs"]:
        if cv["es_gemelo"] == 0:
            por_rol.setdefault(cv["rol"], Counter())[cv["genero"]] += 1
    for rol, conteo in por_rol.items():
        assert abs(conteo["F"] - conteo["M"]) <= 1, rol


def test_roles_repartidos_parejo(datos):
    conteo = Counter(c["rol"] for c in datos["cvs"] if c["es_gemelo"] == 0)
    assert set(conteo.values()) == {30}


def test_gemelos_solo_difieren_en_nombre_y_genero(datos):
    por_id = {c["cv_id"]: c for c in datos["cvs"]}
    gemelos = [c for c in datos["cvs"] if c["es_gemelo"] == 1]
    assert len(gemelos) == 100
    for g in gemelos:
        base = por_id[g["grupo_id"]]
        assert g["cv_id"] == base["cv_id"] + "_g"
        assert g["genero"] != base["genero"]
        assert g["nombre"] != base["nombre"]
        assert g["habilidades"] == base["habilidades"]
        assert g["anios"] == base["anios"]
        assert g["rol"] == base["rol"]
        assert gd.neutralizar(g["texto"], g["nombre"]) == gd.neutralizar(base["texto"], base["nombre"])


def test_gemelos_tienen_misma_relevancia(datos):
    """La relevancia NO depende del género: un CV y su gemelo valen lo mismo."""
    rel = {(p["oferta_id"], p["cv_id"]): p["relevancia"] for p in datos["relevancia"]}
    for cv in datos["cvs"]:
        if cv["es_gemelo"] == 1:
            for oferta in datos["ofertas"]:
                assert rel[(oferta["oferta_id"], cv["cv_id"])] == rel[(oferta["oferta_id"], cv["grupo_id"])]


def test_gemelos_balanceados_por_rol(datos):
    conteo = Counter(c["rol"] for c in datos["cvs"] if c["es_gemelo"] == 1)
    assert set(conteo.values()) == {10}


def test_relevancia_regla_basica(cfg):
    oferta = {
        "rol": "r1",
        "sector": "s1",
        "min_anios": 2,
        "nucleo": ["a", "b", "c", "d", "e"],
    }
    u = cfg["relevancia"]
    perfecto = {"rol": "r1", "sector": "s1", "anios": 5, "habilidades": ["a", "b", "c", "d", "e"]}
    assert gd.relevancia(perfecto, oferta, u) == 3
    sin_experiencia = dict(perfecto, anios=1)
    assert gd.relevancia(sin_experiencia, oferta, u) == 2  # cumple habilidades pero no la experiencia
    cuatro = dict(perfecto, habilidades=["a", "b", "c", "d"])
    assert gd.relevancia(cuatro, oferta, u) == 3  # 80 %
    tres = dict(perfecto, habilidades=["a", "b", "c"])
    assert gd.relevancia(tres, oferta, u) == 2  # 60 %
    dos = dict(perfecto, habilidades=["a", "b"])
    assert gd.relevancia(dos, oferta, u) == 1  # 40 %
    una = dict(perfecto, habilidades=["a"])
    assert gd.relevancia(una, oferta, u) == 0
    otro_rol_mismo_sector = {"rol": "r2", "sector": "s1", "anios": 9, "habilidades": ["a", "b", "c"]}
    assert gd.relevancia(otro_rol_mismo_sector, oferta, u) == 1  # 60 % en el mismo sector
    otro_rol_menos = {"rol": "r2", "sector": "s1", "anios": 9, "habilidades": ["a", "b"]}
    assert gd.relevancia(otro_rol_menos, oferta, u) == 0
    otro_sector = {"rol": "r3", "sector": "s2", "anios": 9, "habilidades": ["a", "b", "c", "d", "e"]}
    assert gd.relevancia(otro_sector, oferta, u) == 0


def test_hay_los_cuatro_niveles_de_relevancia(datos):
    niveles = {p["relevancia"] for p in datos["relevancia"]}
    assert niveles == {0, 1, 2, 3}


def test_cada_oferta_tiene_candidatos_relevantes(datos):
    """Sin relevantes no se pueden calcular nDCG, MRR ni Recall."""
    for oferta in datos["ofertas"]:
        rels = [p["relevancia"] for p in datos["relevancia"] if p["oferta_id"] == oferta["oferta_id"]]
        assert sum(1 for r in rels if r >= 2) >= 10, oferta["oferta_id"]


def test_texto_no_contiene_la_etiqueta_ni_marcas_sin_resolver(datos):
    for cv in datos["cvs"]:
        assert "{" not in cv["texto"] and "}" not in cv["texto"], cv["cv_id"]
        assert "relevancia" not in cv["texto"].lower()
        assert cv["calidad"] not in cv["texto"].split()  # la calidad es un dato interno


def test_los_cvs_usan_sinonimos(datos, cat):
    """La forma exacta que usa la oferta no debe aparecer en todos los CVs que tienen la habilidad."""
    cv_con_habilidad = [c for c in datos["cvs"] if "sql" in c["habilidades"] and c["es_gemelo"] == 0]
    assert len(cv_con_habilidad) > 10
    forma_oferta = cat["habilidades"]["sql"][0].lower()
    con_forma_exacta = sum(1 for c in cv_con_habilidad if forma_oferta in c["texto"].lower())
    assert con_forma_exacta < len(cv_con_habilidad)


def test_particion_de_ofertas(datos, cfg):
    dev = {o["rol"] for o in datos["ofertas"] if o["particion"] == "dev"}
    test = {o["rol"] for o in datos["ofertas"] if o["particion"] == "test"}
    assert dev == set(cfg["particion_ofertas"]["dev"])
    assert test == set(cfg["particion_ofertas"]["test"])
    assert not dev & test


def test_aplicar_genero():
    assert gd.aplicar_genero("{Ingeniero} civil y {comprometido}", "M") == "Ingeniero civil y comprometido"
    assert gd.aplicar_genero("{Ingeniero} civil y {comprometido}", "F") == "Ingeniera civil y comprometida"
    assert gd.aplicar_genero("Docente {otra}", "F") == "Docente {otra}"


def test_lista_en_texto():
    assert gd.lista_en_texto(["a"]) == "a"
    assert gd.lista_en_texto(["a", "b"]) == "a y b"
    assert gd.lista_en_texto(["a", "b", "c"]) == "a, b y c"
    assert gd.lista_en_texto(["a", "inglés"]) == "a e inglés"


def test_catalogo_incoherente_se_rechaza(cfg, cat):
    mal = json.loads(json.dumps(cat))
    mal["roles"]["analista_datos"]["nucleo"][0] = "habilidad_que_no_existe"
    with pytest.raises(ValueError):
        gd.validar_catalogo(mal, cfg)


def test_escritura_de_archivos(tmp_path, cfg, cat):
    datos = gd.generar(cfg, cat)
    meta = gd.escribir_salida(datos, cfg, tmp_path)
    for nombre in ["ofertas.csv", "cvs.csv", "relevancia.csv", "metadatos.json"]:
        assert (tmp_path / nombre).exists(), nombre
    with open(tmp_path / "cvs.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 400
    assert "\n" in filas[0]["texto"]  # los saltos de línea sobreviven al CSV
    assert meta["n_cvs_total"] == 400
    assert set(meta["sha256"]) == {"ofertas.csv", "cvs.csv", "relevancia.csv"}


def test_archivos_identicos_con_misma_semilla(tmp_path, cfg, cat):
    """Los CSV salen byte a byte iguales; así cualquiera puede reproducir tu dataset."""
    a, b = tmp_path / "a", tmp_path / "b"
    gd.escribir_salida(gd.generar(cfg, cat), cfg, a)
    gd.escribir_salida(gd.generar(cfg, cat), cfg, b)
    for nombre in ["ofertas.csv", "cvs.csv", "relevancia.csv"]:
        assert (a / nombre).read_bytes() == (b / nombre).read_bytes()
