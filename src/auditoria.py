"""Auditoría de sesgo de género con pares contrafactuales ("gemelos").

Cada gemelo es el mismo CV que su original, con otro nombre de pila y las palabras con
género gramatical cambiadas (ver src/generar_datos.py). Como la relevancia NO depende del
género, un sistema justo debería tratar igual a los dos. Lo que mide esta auditoría:

  1. Diferencia de puntaje y de posición entre la gemela (F) y el gemelo (M).
  2. "Saltos" de top-10: pares donde uno de los dos entra al top-10 y el otro no.
  3. Razón de impacto: tasa de selección en el top-10 de mujeres dividida por la de hombres
     (misma idea que el "impact ratio" de la auditoría de la Ley Local 144 de Nueva York).

CRITERIOS DE ACEPTACIÓN (fijados ANTES de ver cualquier resultado; no se cambian después):
  * razón de impacto en el top-10 entre 0.80 y 1.25, Y
  * saltos de top-10 en como máximo el 10 % de los pares con algún gemelo en el top-10.

Uso:
    python -m src.auditoria --metodo bm25 --particion dev
    python -m src.auditoria --metodo embeddings --max-seq 128 --particion dev
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.linea_base import BM25, RAIZ, leer_csv, ordenar, tokenizar

K = 10
RAZON_MIN = 0.80
RAZON_MAX = 1.25
SALTOS_MAX = 0.10
TOLERANCIA = 1e-9


def auditar(
    cv_ids: list[str],
    generos: dict[str, str],
    puntajes_por_oferta: dict[str, list[float]],
    k: int = K,
) -> dict:
    """Calcula las métricas de auditoría. ``puntajes_por_oferta[oferta]`` va alineado con ``cv_ids``."""
    ids = set(cv_ids)
    pares = [(c[:-2], c) for c in cv_ids if c.endswith("_g") and c[:-2] in ids]
    if not pares:
        raise ValueError("No hay pares de gemelos para auditar")

    n_f = sum(1 for c in cv_ids if generos[c] == "F")
    n_m = sum(1 for c in cv_ids if generos[c] == "M")

    mejor_f = mejor_m = empate = 0
    brechas_rango, brechas_puntaje = [], []
    pares_con_top = saltos = 0
    top_f = top_m = 0
    por_oferta = []

    for oferta, puntajes in puntajes_por_oferta.items():
        orden = ordenar(cv_ids, puntajes)
        rango = {c: i + 1 for i, c in enumerate(orden)}
        puntaje = dict(zip(cv_ids, puntajes))
        top = set(orden[:k])
        amplitud = (max(puntajes) - min(puntajes)) or 1.0

        o_mejor_f = o_mejor_m = o_empate = o_saltos = o_con_top = 0
        for a, b in pares:
            f, m = (a, b) if generos[a] == "F" else (b, a)
            dif = puntaje[f] - puntaje[m]
            if abs(dif) <= TOLERANCIA:
                empate += 1
                o_empate += 1
            elif dif > 0:
                mejor_f += 1
                o_mejor_f += 1
            else:
                mejor_m += 1
                o_mejor_m += 1
            brechas_rango.append(rango[f] - rango[m])
            brechas_puntaje.append(abs(dif) / amplitud)
            if f in top or m in top:
                pares_con_top += 1
                o_con_top += 1
                if (f in top) != (m in top):
                    saltos += 1
                    o_saltos += 1

        o_f = sum(1 for c in orden[:k] if generos[c] == "F")
        o_m = k - o_f
        top_f += o_f
        top_m += o_m
        por_oferta.append(
            {
                "oferta_id": oferta,
                "pares_gemelo_F_mejor": o_mejor_f,
                "pares_gemelo_M_mejor": o_mejor_m,
                "pares_empate": o_empate,
                "pares_con_algun_gemelo_en_top": o_con_top,
                "saltos_top": o_saltos,
                "mujeres_en_top": o_f,
                "hombres_en_top": o_m,
            }
        )

    total = len(brechas_rango)
    tasa_f = top_f / (n_f * len(puntajes_por_oferta))
    tasa_m = top_m / (n_m * len(puntajes_por_oferta))
    razon = (tasa_f / tasa_m) if tasa_m > 0 else None
    pct_saltos = (saltos / pares_con_top) if pares_con_top else 0.0
    cumple_razon = razon is not None and RAZON_MIN <= razon <= RAZON_MAX
    cumple_saltos = pct_saltos <= SALTOS_MAX

    resumen = {
        "k": k,
        "ofertas": len(puntajes_por_oferta),
        "pares_evaluados": total,
        "pct_gemela_F_con_mayor_puntaje": mejor_f / total,
        "pct_gemelo_M_con_mayor_puntaje": mejor_m / total,
        "pct_empates": empate / total,
        "brecha_rango_media_F_menos_M": sum(brechas_rango) / total,
        "brecha_rango_abs_media": sum(abs(x) for x in brechas_rango) / total,
        "brecha_puntaje_norm_abs_media": sum(brechas_puntaje) / total,
        "pares_con_algun_gemelo_en_top": pares_con_top,
        "saltos_top": saltos,
        "pct_saltos_top": pct_saltos,
        "tasa_seleccion_F": tasa_f,
        "tasa_seleccion_M": tasa_m,
        "razon_de_impacto_F_sobre_M": razon,
        "cumple_razon_de_impacto": cumple_razon,
        "cumple_saltos": cumple_saltos,
        "cumple_criterios": cumple_razon and cumple_saltos,
    }
    return {"resumen": resumen, "por_oferta": por_oferta}


def puntajes_bm25(cvs: list[dict], ofertas: list[dict]) -> dict[str, list[float]]:
    modelo = BM25([tokenizar(c["texto"]) for c in cvs])
    return {o["oferta_id"]: modelo.puntajes(tokenizar(o["texto"])) for o in ofertas}


def puntajes_embeddings(cvs: list[dict], ofertas: list[dict], codificar) -> dict[str, list[float]]:
    vec_cvs = codificar([c["texto"] for c in cvs])
    vec_of = codificar([o["texto"] for o in ofertas])
    return {o["oferta_id"]: (vec_cvs @ v).tolist() for o, v in zip(ofertas, vec_of)}


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(description="Auditoría de sesgo de género con gemelos.")
    p.add_argument("--metodo", required=True, choices=["bm25", "embeddings"])
    p.add_argument("--max-seq", type=int, default=None)
    p.add_argument("--modelo", default=None)
    p.add_argument("--particion", default="dev", choices=["dev", "test"])
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--resultados", default=str(RAIZ / "results"))
    args = p.parse_args(argv)

    datos = Path(args.datos)
    cvs = leer_csv(datos / "cvs.csv")
    ofertas = [o for o in leer_csv(datos / "ofertas.csv") if o["particion"] == args.particion]
    info = {"metodo": args.metodo}
    if args.metodo == "bm25":
        puntajes = puntajes_bm25(cvs, ofertas)
    else:
        from src.embeddings import MODELO_POR_DEFECTO, crear_codificador

        codificar, info_modelo = crear_codificador(args.modelo or MODELO_POR_DEFECTO, args.max_seq)
        info.update(info_modelo)
        puntajes = puntajes_embeddings(cvs, ofertas, codificar)

    res = auditar([c["cv_id"] for c in cvs], {c["cv_id"]: c["genero"] for c in cvs}, puntajes)

    salida = Path(args.resultados)
    salida.mkdir(parents=True, exist_ok=True)
    etiqueta = args.metodo if args.max_seq is None else f"{args.metodo}{args.max_seq}"
    with open(salida / f"auditoria_{etiqueta}_{args.particion}.json", "w", encoding="utf-8") as f:
        json.dump({"info": info, "particion": args.particion, **res}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(salida / f"auditoria_{etiqueta}_{args.particion}_por_oferta.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res["por_oferta"][0]), lineterminator="\n")
        w.writeheader()
        w.writerows(res["por_oferta"])

    r = res["resumen"]
    print(f"AUDITORÍA {info} | partición: {args.particion} | pares gemelos x ofertas: {r['pares_evaluados']}")
    print(f"  Gemela (F) con mayor puntaje: {r['pct_gemela_F_con_mayor_puntaje']:.1%} | gemelo (M): {r['pct_gemelo_M_con_mayor_puntaje']:.1%} | empates: {r['pct_empates']:.1%}")
    print(f"  Brecha de posición media (F - M): {r['brecha_rango_media_F_menos_M']:+.2f} | absoluta media: {r['brecha_rango_abs_media']:.2f}")
    print(f"  Brecha de puntaje normalizada (abs, media): {r['brecha_puntaje_norm_abs_media']:.4f}")
    print(f"  Saltos de top-{r['k']}: {r['saltos_top']} de {r['pares_con_algun_gemelo_en_top']} pares con algún gemelo en el top ({r['pct_saltos_top']:.1%})")
    razon = r["razon_de_impacto_F_sobre_M"]
    print(f"  Razón de impacto (F/M) en top-{r['k']}: {'n/a' if razon is None else f'{razon:.3f}'} (aceptable: {RAZON_MIN} a {RAZON_MAX})")
    print(f"  ¿Cumple los criterios fijados de antemano? {'SÍ' if r['cumple_criterios'] else 'NO'}")
    return res


if __name__ == "__main__":
    main()
