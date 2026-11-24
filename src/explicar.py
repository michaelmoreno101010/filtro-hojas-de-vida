"""Explicación por palabra del ranking final (E-04: BM25 con género neutralizado).

El puntaje BM25 de un CV es la suma de la contribución de cada palabra de la oferta que
aparece en él. Este módulo descompone ese puntaje: para cada CV del top-N muestra qué
palabras lo subieron y cuánto aportó cada una. La suma de las contribuciones es EXACTAMENTE
el puntaje (hay una prueba que lo verifica).

La explicación describe cómo funciona el método; no dice si la persona es buena candidata.
La decisión la toma siempre una persona leyendo el CV completo.

Uso:
    python -m src.explicar --oferta of_01 --top 5
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.linea_base import BM25, RAIZ, leer_csv, ordenar
from src.mitigacion import tokenizar_neutro


def contribuciones(modelo: BM25, indice_cv: int, consulta: list[str]) -> dict[str, float]:
    """Aporte de cada palabra de la consulta al puntaje del CV ``indice_cv`` (mismas fórmulas que BM25)."""
    tf = modelo.tf[indice_cv]
    norm = modelo.k1 * (1 - modelo.b + modelo.b * modelo.largos[indice_cv] / modelo.largo_prom)
    salida = {}
    for t in set(consulta):
        f = tf.get(t, 0)
        if f:
            salida[t] = modelo.idf[t] * f * (modelo.k1 + 1) / (f + norm)
    return dict(sorted(salida.items(), key=lambda x: (-x[1], x[0])))


def explicar_oferta(datos: Path, oferta_id: str, top: int = 5) -> list[dict]:
    cvs = leer_csv(datos / "cvs.csv")
    oferta = next((o for o in leer_csv(datos / "ofertas.csv") if o["oferta_id"] == oferta_id), None)
    if oferta is None:
        raise ValueError(f"No existe la oferta '{oferta_id}'")
    ids = [c["cv_id"] for c in cvs]
    modelo = BM25([tokenizar_neutro(c["texto"]) for c in cvs])
    consulta = tokenizar_neutro(oferta["texto"])
    puntajes = modelo.puntajes(consulta)
    orden = ordenar(ids, puntajes)
    resultado = []
    for pos, cv_id in enumerate(orden[:top], start=1):
        i = ids.index(cv_id)
        resultado.append(
            {"posicion": pos, "cv_id": cv_id, "puntaje": puntajes[i], "palabras": contribuciones(modelo, i, consulta)}
        )
    return resultado


def main(argv=None) -> list[dict]:
    p = argparse.ArgumentParser(description="Explicación por palabra del ranking E-04.")
    p.add_argument("--oferta", required=True, help="Por ejemplo of_01")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--datos", default=str(RAIZ / "data"))
    a = p.parse_args(argv)
    res = explicar_oferta(Path(a.datos), a.oferta, a.top)
    print(f"Explicación del top-{a.top} para {a.oferta} (BM25 con género neutralizado)")
    for r in res:
        print(f"\n#{r['posicion']} {r['cv_id']}  puntaje {r['puntaje']:.2f}")
        for palabra, aporte in list(r["palabras"].items())[:6]:
            print(f"    {palabra:<22} +{aporte:.2f}")
    print("\nRecuerda: esto explica el puntaje, no decide por nadie. La decisión es de una persona.")
    return res


if __name__ == "__main__":
    main()
