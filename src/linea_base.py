"""Línea base E-01: ranking por palabras clave con BM25 (implementado desde cero).

Para cada oferta ordena los 400 CVs por su puntaje BM25 y calcula las métricas contra la
relevancia etiquetada. También calcula un ranking al azar como piso de referencia.

Uso:
    python -m src.linea_base --particion dev
    python -m src.linea_base --particion test     # solo al final del proyecto

Por defecto solo se evalúa la partición "dev" (ofertas de desarrollo). La partición "test"
se mira una sola vez, cuando todas las decisiones ya están tomadas.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

from src.metricas import mrr, ndcg_at_k, precision_at_k, recall_at_k

RAIZ = Path(__file__).resolve().parents[1]

PALABRAS_VACIAS = {
    "de", "la", "el", "en", "y", "e", "a", "con", "para", "por", "del", "los", "las", "un", "una",
    "se", "o", "al", "que", "como", "mas", "su", "sus", "es", "son", "u", "lo", "le", "sobre",
}


def tokenizar(texto: str) -> list[str]:
    """Minúsculas, sin tildes, solo letras y números, sin palabras vacías."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in PALABRAS_VACIAS]


class BM25:
    """BM25 clásico (Robertson y Zaragoza, 2009) con idf = ln(1 + (N - df + 0.5) / (df + 0.5))."""

    def __init__(self, documentos: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.n = len(documentos)
        self.tf = [Counter(d) for d in documentos]
        self.largos = [len(d) for d in documentos]
        self.largo_prom = sum(self.largos) / self.n
        df: Counter = Counter()
        for d in documentos:
            df.update(set(d))
        self.idf = {t: math.log(1 + (self.n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def puntajes(self, consulta: list[str]) -> list[float]:
        resultado = []
        terminos = set(consulta)
        for tf, largo in zip(self.tf, self.largos):
            norm = self.k1 * (1 - self.b + self.b * largo / self.largo_prom)
            s = 0.0
            for t in terminos:
                f = tf.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
            resultado.append(s)
        return resultado


def ordenar(cv_ids: list[str], puntajes: list[float]) -> list[str]:
    """Orden descendente por puntaje; los empates se resuelven por cv_id (determinista)."""
    return [c for _, c in sorted(zip([-p for p in puntajes], cv_ids))]


def metricas_oferta(orden: list[str], rel_por_cv: dict[str, int]) -> dict[str, float]:
    ordenadas = [rel_por_cv[c] for c in orden]
    todas = list(rel_por_cv.values())
    return {
        "ndcg@10": ndcg_at_k(ordenadas, todas, 10),
        "mrr": mrr(ordenadas),
        "precision@10": precision_at_k(ordenadas, 10),
        "recall@10": recall_at_k(ordenadas, todas, 10),
        "recall@30": recall_at_k(ordenadas, todas, 30),
    }


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def evaluar(datos_dir: Path, particion: str, semilla: int = 42, k1: float = 1.5, b: float = 0.75) -> dict:
    cvs = leer_csv(datos_dir / "cvs.csv")
    ofertas = [o for o in leer_csv(datos_dir / "ofertas.csv") if o["particion"] == particion]
    rel = leer_csv(datos_dir / "relevancia.csv")
    if not ofertas:
        raise ValueError(f"No hay ofertas en la partición '{particion}'")

    cv_ids = [c["cv_id"] for c in cvs]
    modelo = BM25([tokenizar(c["texto"]) for c in cvs], k1=k1, b=b)
    por_oferta: dict[str, dict[str, int]] = {}
    for fila in rel:
        por_oferta.setdefault(fila["oferta_id"], {})[fila["cv_id"]] = int(fila["relevancia"])

    filas = []
    for oferta in ofertas:
        rel_cv = por_oferta[oferta["oferta_id"]]
        orden_bm25 = ordenar(cv_ids, modelo.puntajes(tokenizar(oferta["texto"])))
        azar = list(cv_ids)
        random.Random(f"{semilla}-azar-{oferta['oferta_id']}").shuffle(azar)
        for metodo, orden in (("bm25", orden_bm25), ("azar", azar)):
            m = metricas_oferta(orden, rel_cv)
            filas.append({"oferta_id": oferta["oferta_id"], "rol": oferta["rol"], "metodo": metodo, **m})

    columnas = ["ndcg@10", "mrr", "precision@10", "recall@10", "recall@30"]
    promedios = {}
    for metodo in ("bm25", "azar"):
        sel = [f for f in filas if f["metodo"] == metodo]
        promedios[metodo] = {c: sum(f[c] for f in sel) / len(sel) for c in columnas}
    return {"filas": filas, "promedios": promedios, "columnas": columnas}


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(description="Línea base BM25 (E-01).")
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--resultados", default=str(RAIZ / "results"))
    p.add_argument("--particion", default="dev", choices=["dev", "test"])
    p.add_argument("--semilla", type=int, default=42)
    args = p.parse_args(argv)

    res = evaluar(Path(args.datos), args.particion, args.semilla)
    salida = Path(args.resultados)
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"e01_bm25_{args.particion}.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["oferta_id", "rol", "metodo"] + res["columnas"], lineterminator="\n")
        w.writeheader()
        for fila in res["filas"]:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fila.items()})

    print(f"E-01 BM25 (k1=1.5, b=0.75) | partición: {args.particion} | resultados por oferta en {ruta}")
    print(f"{'método':8}" + "".join(f"{c:>14}" for c in res["columnas"]))
    for metodo, vals in res["promedios"].items():
        print(f"{metodo:8}" + "".join(f"{vals[c]:>14.3f}" for c in res["columnas"]))
    return res


if __name__ == "__main__":
    main()
