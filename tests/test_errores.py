import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import generar_datos as gd  # noqa: E402
from src.errores import analizar  # noqa: E402


def test_analizar_devuelve_casos_validos(tmp_path):
    cfg = gd.cargar_json(RAIZ / "configs" / "generacion.json")
    cat = gd.cargar_json(RAIZ / "configs" / "catalogo.json")
    gd.escribir_salida(gd.generar(cfg, cat), cfg, tmp_path)
    filas = analizar(tmp_path, "dev")
    for f in filas:
        if f["tipo"] == "falso_positivo_top10":
            assert f["posicion"] <= 10 and f["relevancia"] < 2
        else:
            assert f["posicion"] > 30 and f["relevancia"] >= 2
