"""Análisis de errores del sistema final (E-04: BM25 con género neutralizado).

Por oferta lista (a) falsos positivos: CVs del top-10 con relevancia < 2, y (b) relevantes
(rel >= 2) que quedan fuera del top-30. Para cada caso muestra rol, años y habilidades del CV,
para poder explicar el porqué. Todo sale de los datos; el comentario lo escribe la persona.

Uso:
    python -m src.errores --particion dev
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.linea_base import BM25, RAIZ, leer_csv, ordenar
from src.mitigacion import tokenizar_neutro


def analizar(datos: Path, particion: str) -> list[dict]:
    cvs = leer_csv(datos / "cvs.csv")
    por_id = {c["cv_id"]: c for c in cvs}
    ofertas = [o for o in leer_csv(datos / "ofertas.csv") if o["particion"] == particion]
    rel = {}
    for f in leer_csv(datos / "relevancia.csv"):
        rel.setdefault(f["oferta_id"], {})[f["cv_id"]] = int(f["relevancia"])
    ids = [c["cv_id"] for c in cvs]
    bm = BM25([tokenizar_neutro(c["texto"]) for c in cvs])

    filas = []
    for o in ofertas:
        orden = ordenar(ids, bm.puntajes(tokenizar_neutro(o["texto"])))
        r = rel[o["oferta_id"]]
        casos = [("falso_positivo_top10", c, i + 1) for i, c in enumerate(orden[:10]) if r[c] < 2]
        casos += [("relevante_fuera_top30", c, i + 1) for i, c in enumerate(orden) if i >= 30 and r[c] >= 2]
        for tipo, c, pos in casos:
            cv = por_id[c]
            filas.append(
                {
                    "oferta_id": o["oferta_id"], "oferta_rol": o["rol"], "min_anios": o["min_anios"],
                    "tipo": tipo, "cv_id": c, "posicion": pos, "relevancia": r[c],
                    "cv_rol": cv["rol"], "cv_anios": cv["anios"], "cv_calidad": cv["calidad"],
                    "cv_habilidades": cv["habilidades"],
                }
            )
    return filas


def main(argv=None) -> list[dict]:
    p = argparse.ArgumentParser(description="Análisis de errores de E-04.")
    p.add_argument("--particion", default="dev", choices=["dev", "test"])
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--resultados", default=str(RAIZ / "results"))
    a = p.parse_args(argv)
    filas = analizar(Path(a.datos), a.particion)
    out = Path(a.resultados)
    out.mkdir(parents=True, exist_ok=True)
    if filas:
        with open(out / f"errores_e04_{a.particion}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(filas)
    for tipo in ("falso_positivo_top10", "relevante_fuera_top30"):
        sel = [f for f in filas if f["tipo"] == tipo]
        print(f"\n== {tipo}: {len(sel)} casos ==")
        for f in sel[:12]:
            print(f"{f['oferta_id']} ({f['oferta_rol']}, mín {f['min_anios']} años) | {f['cv_id']} pos {f['posicion']} rel {f['relevancia']} | "
                  f"{f['cv_rol']}, {f['cv_anios']} años, calidad {f['cv_calidad']} | {f['cv_habilidades']}")
    return filas


if __name__ == "__main__":
    main()
