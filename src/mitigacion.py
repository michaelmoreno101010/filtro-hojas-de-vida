"""E-04: BM25 con formas de género neutralizadas (una sola variable cambia respecto a E-01).

Antes de buscar, cada forma femenina se convierte en su forma masculina ("ingeniera" -> "ingeniero")
tanto en CVs como en ofertas. Así "Ingeniero/a" de la oferta coincide igual con ambos géneros.

LIMITACIÓN (se debe decir en el informe): la lista de formas es la misma que usa el generador
sintético, así que aquí la mitigación tiene ventaja. En CVs reales habría que cubrir muchas más
palabras y la lista nunca sería completa.

Uso:
    python -m src.mitigacion --particion dev
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.auditoria import auditar
from src.linea_base import BM25, RAIZ, leer_csv, metricas_oferta, ordenar, tokenizar

FEMENINO_A_MASCULINO = {
    "desarrolladora": "desarrollador",
    "enfermera": "enfermero",
    "contadora": "contador",
    "ingeniera": "ingeniero",
    "comprometida": "comprometido",
    "orientada": "orientado",
    "motivada": "motivado",
    "egresada": "egresado",
    "encargada": "encargado",
}
COLUMNAS = ["ndcg@10", "mrr", "precision@10", "recall@10", "recall@30"]


def tokenizar_neutro(texto: str) -> list[str]:
    return [FEMENINO_A_MASCULINO.get(w, w) for w in tokenizar(texto)]


def main(argv=None) -> dict:
    p = argparse.ArgumentParser(description="E-04: BM25 con género neutralizado.")
    p.add_argument("--particion", default="dev", choices=["dev", "test"])
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--resultados", default=str(RAIZ / "results"))
    a = p.parse_args(argv)

    datos = Path(a.datos)
    cvs = leer_csv(datos / "cvs.csv")
    ofertas = [o for o in leer_csv(datos / "ofertas.csv") if o["particion"] == a.particion]
    rel = {}
    for f in leer_csv(datos / "relevancia.csv"):
        rel.setdefault(f["oferta_id"], {})[f["cv_id"]] = int(f["relevancia"])
    ids = [c["cv_id"] for c in cvs]
    modelo = BM25([tokenizar_neutro(c["texto"]) for c in cvs])
    puntajes = {o["oferta_id"]: modelo.puntajes(tokenizar_neutro(o["texto"])) for o in ofertas}

    filas = [
        {"oferta_id": o["oferta_id"], "rol": o["rol"], **metricas_oferta(ordenar(ids, puntajes[o["oferta_id"]]), rel[o["oferta_id"]])}
        for o in ofertas
    ]
    prom = {c: sum(f[c] for f in filas) / len(filas) for c in COLUMNAS}
    aud = auditar(ids, {c["cv_id"]: c["genero"] for c in cvs}, puntajes)

    out = Path(a.resultados)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"e04_bm25_neutro_{a.particion}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["oferta_id", "rol"] + COLUMNAS, lineterminator="\n")
        w.writeheader()
        for fila in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fila.items()})
    with open(out / f"e04_auditoria_{a.particion}.json", "w", encoding="utf-8") as f:
        json.dump({"particion": a.particion, **aud}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    r = aud["resumen"]
    print(f"E-04 BM25 neutro | partición: {a.particion}")
    print(f"{'':10}" + "".join(f"{c:>14}" for c in COLUMNAS))
    print(f"{'bm25neutro':10}" + "".join(f"{prom[c]:>14.3f}" for c in COLUMNAS))
    print(f"Empates {r['pct_empates']:.1%} | M mayor {r['pct_gemelo_M_con_mayor_puntaje']:.1%} | F mayor {r['pct_gemela_F_con_mayor_puntaje']:.1%}")
    print(f"Saltos top-10: {r['saltos_top']} de {r['pares_con_algun_gemelo_en_top']} ({r['pct_saltos_top']:.1%})")
    print(f"Razón de impacto F/M: {r['razon_de_impacto_F_sobre_M']:.3f}")
    print(f"¿Cumple los criterios fijados de antemano? {'SÍ' if r['cumple_criterios'] else 'NO'}")
    return {"promedios": prom, "auditoria": aud}


if __name__ == "__main__":
    main()
