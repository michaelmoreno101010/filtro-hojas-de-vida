"""E-05: híbrido = BM25 neutro (E-04) + embeddings (E-02) combinados con fusión de rangos (RRF).

RRF: puntaje = suma sobre los dos rankings de 1/(60 + posición). Es la única variable nueva
respecto a E-04 (se agrega la señal de embeddings). Constante 60 fijada de antemano.

Uso (en Colab):
    python -m src.hibrido --particion dev
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.auditoria import auditar, puntajes_embeddings
from src.linea_base import BM25, RAIZ, leer_csv, metricas_oferta, ordenar
from src.mitigacion import COLUMNAS, tokenizar_neutro

RRF_K = 60


def fusionar(ids: list[str], lista_puntajes: list[list[float]], k: int = RRF_K) -> list[float]:
    """Fusión de rangos recíprocos. Devuelve un puntaje por CV, alineado con ``ids``."""
    total = {c: 0.0 for c in ids}
    for puntajes in lista_puntajes:
        for pos, c in enumerate(ordenar(ids, puntajes), start=1):
            total[c] += 1.0 / (k + pos)
    return [total[c] for c in ids]


def evaluar_hibrido(datos: Path, particion: str, codificar) -> dict:
    cvs = leer_csv(datos / "cvs.csv")
    ofertas = [o for o in leer_csv(datos / "ofertas.csv") if o["particion"] == particion]
    rel = {}
    for f in leer_csv(datos / "relevancia.csv"):
        rel.setdefault(f["oferta_id"], {})[f["cv_id"]] = int(f["relevancia"])
    ids = [c["cv_id"] for c in cvs]
    bm = BM25([tokenizar_neutro(c["texto"]) for c in cvs])
    emb = puntajes_embeddings(cvs, ofertas, codificar)
    puntajes = {
        o["oferta_id"]: fusionar(ids, [bm.puntajes(tokenizar_neutro(o["texto"])), emb[o["oferta_id"]]])
        for o in ofertas
    }
    filas = [
        {"oferta_id": o["oferta_id"], "rol": o["rol"], **metricas_oferta(ordenar(ids, puntajes[o["oferta_id"]]), rel[o["oferta_id"]])}
        for o in ofertas
    ]
    prom = {c: sum(f[c] for f in filas) / len(filas) for c in COLUMNAS}
    aud = auditar(ids, {c["cv_id"]: c["genero"] for c in cvs}, puntajes)
    return {"filas": filas, "promedios": prom, "auditoria": aud}


def main(argv=None) -> dict:
    p = argparse.ArgumentParser(description="E-05: híbrido BM25 neutro + embeddings.")
    p.add_argument("--particion", default="dev", choices=["dev", "test"])
    p.add_argument("--max-seq", type=int, default=128)
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--resultados", default=str(RAIZ / "results"))
    a = p.parse_args(argv)

    from src.embeddings import MODELO_POR_DEFECTO, crear_codificador

    codificar, info = crear_codificador(MODELO_POR_DEFECTO, a.max_seq)
    res = evaluar_hibrido(Path(a.datos), a.particion, codificar)

    out = Path(a.resultados)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"e05_hibrido_{a.particion}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["oferta_id", "rol"] + COLUMNAS, lineterminator="\n")
        w.writeheader()
        for fila in res["filas"]:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fila.items()})
    with open(out / f"e05_auditoria_{a.particion}.json", "w", encoding="utf-8") as f:
        json.dump({"info": info, "rrf_k": RRF_K, "particion": a.particion, **res["auditoria"]}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    r = res["auditoria"]["resumen"]
    print(f"E-05 híbrido (RRF k={RRF_K}) | {info} | partición: {a.particion}")
    print(f"{'':10}" + "".join(f"{c:>14}" for c in COLUMNAS))
    print(f"{'hibrido':10}" + "".join(f"{res['promedios'][c]:>14.3f}" for c in COLUMNAS))
    print(f"Empates {r['pct_empates']:.1%} | M mayor {r['pct_gemelo_M_con_mayor_puntaje']:.1%} | F mayor {r['pct_gemela_F_con_mayor_puntaje']:.1%}")
    print(f"Saltos top-10: {r['saltos_top']} de {r['pares_con_algun_gemelo_en_top']} ({r['pct_saltos_top']:.1%})")
    razon = r["razon_de_impacto_F_sobre_M"]
    print(f"Razón de impacto F/M: {'n/a' if razon is None else f'{razon:.3f}'}")
    print(f"¿Cumple los criterios fijados de antemano? {'SÍ' if r['cumple_criterios'] else 'NO'}")
    return res


if __name__ == "__main__":
    main()
