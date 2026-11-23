"""Experimentos con embeddings (E-02, E-03, ...): ranking por similitud coseno.

Cada CV y cada oferta se convierten en un vector con un modelo de sentence-transformers
(por defecto paraphrase-multilingual-MiniLM-L12-v2, licencia Apache-2.0) y los CVs se
ordenan por similitud coseno con la oferta. Se evalúa con las mismas métricas que BM25.

Uso (en Colab):
    python -m src.embeddings --id E-02 --max-seq 128 --particion dev
    python -m src.embeddings --id E-03 --max-seq 256 --particion dev

Cada experimento cambia UNA sola variable respecto al anterior y deja un CSV por oferta
y un JSON con las versiones de las librerías en results/.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from src.linea_base import leer_csv, metricas_oferta, ordenar

RAIZ = Path(__file__).resolve().parents[1]
MODELO_POR_DEFECTO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLUMNAS = ["ndcg@10", "mrr", "precision@10", "recall@10", "recall@30"]


def crear_codificador(modelo: str, max_seq: int | None) -> tuple[Callable[[Sequence[str]], np.ndarray], dict]:
    """Carga el modelo y devuelve (función que codifica textos, información de versiones)."""
    import sentence_transformers
    import torch
    from sentence_transformers import SentenceTransformer

    m = SentenceTransformer(modelo, device="cpu")
    if max_seq is not None:
        m.max_seq_length = max_seq

    def codificar(textos: Sequence[str]) -> np.ndarray:
        return np.asarray(m.encode(list(textos), normalize_embeddings=True, show_progress_bar=False, batch_size=32))

    info = {
        "modelo": modelo,
        "max_seq_length": m.max_seq_length,
        "sentence_transformers": sentence_transformers.__version__,
        "torch": torch.__version__,
    }
    return codificar, info


def evaluar_embeddings(
    datos_dir: Path,
    particion: str,
    codificar: Callable[[Sequence[str]], np.ndarray],
    preparar_texto: Callable[[str], str] = lambda t: t,
) -> dict:
    """Ordena los CVs por similitud coseno con cada oferta y calcula las métricas."""
    cvs = leer_csv(datos_dir / "cvs.csv")
    ofertas = [o for o in leer_csv(datos_dir / "ofertas.csv") if o["particion"] == particion]
    rel = leer_csv(datos_dir / "relevancia.csv")
    if not ofertas:
        raise ValueError(f"No hay ofertas en la partición '{particion}'")

    cv_ids = [c["cv_id"] for c in cvs]
    vec_cvs = codificar([preparar_texto(c["texto"]) for c in cvs])
    vec_ofertas = codificar([o["texto"] for o in ofertas])
    por_oferta: dict[str, dict[str, int]] = {}
    for fila in rel:
        por_oferta.setdefault(fila["oferta_id"], {})[fila["cv_id"]] = int(fila["relevancia"])

    filas = []
    for oferta, v in zip(ofertas, vec_ofertas):
        puntajes = (vec_cvs @ v).tolist()  # vectores normalizados: producto punto = coseno
        orden = ordenar(cv_ids, puntajes)
        m = metricas_oferta(orden, por_oferta[oferta["oferta_id"]])
        filas.append({"oferta_id": oferta["oferta_id"], "rol": oferta["rol"], **m})

    promedios = {c: sum(f[c] for f in filas) / len(filas) for c in COLUMNAS}
    return {"filas": filas, "promedios": promedios}


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(description="Ranking con embeddings.")
    p.add_argument("--id", required=True, help="Identificador del experimento, por ejemplo E-02")
    p.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    p.add_argument("--max-seq", type=int, default=None, help="Longitud máxima en tokens (por defecto la del modelo)")
    p.add_argument("--particion", default="dev", choices=["dev", "test"])
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--resultados", default=str(RAIZ / "results"))
    args = p.parse_args(argv)

    codificar, info = crear_codificador(args.modelo, args.max_seq)
    res = evaluar_embeddings(Path(args.datos), args.particion, codificar)

    salida = Path(args.resultados)
    salida.mkdir(parents=True, exist_ok=True)
    nombre = args.id.lower().replace("-", "")
    ruta = salida / f"{nombre}_embeddings_{args.particion}.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["oferta_id", "rol"] + COLUMNAS, lineterminator="\n")
        w.writeheader()
        for fila in res["filas"]:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fila.items()})
    with open(salida / f"{nombre}_embeddings_{args.particion}_meta.json", "w", encoding="utf-8") as f:
        json.dump({"id": args.id, "particion": args.particion, **info}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"{args.id} embeddings | {info} | partición: {args.particion}")
    print(f"{'':10}" + "".join(f"{c:>14}" for c in COLUMNAS))
    print(f"{'embeddings':10}" + "".join(f"{res['promedios'][c]:>14.3f}" for c in COLUMNAS))
    print(f"(resultados por oferta en {ruta})")
    return res


if __name__ == "__main__":
    main()
