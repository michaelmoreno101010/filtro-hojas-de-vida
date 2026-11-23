"""Métricas de ranking.

Todas reciben la lista de relevancias (0 a 3) de los CVs EN EL ORDEN en que el sistema los
puso (el primero es el que el sistema considera mejor). Un CV cuenta como "relevante" si su
relevancia es >= 2 (umbral fijado antes de modelar).
"""

from __future__ import annotations

import math

UMBRAL_RELEVANTE = 2


def dcg(rels: list[int], k: int) -> float:
    """Ganancia acumulada con descuento: sum((2^rel - 1) / log2(posicion + 1))."""
    return sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(rels[:k]))


def ndcg_at_k(rels_ordenadas: list[int], todas_rels: list[int], k: int = 10) -> float:
    """nDCG@k: qué tan cerca está el ranking del ranking ideal (1.0 = perfecto)."""
    ideal = dcg(sorted(todas_rels, reverse=True), k)
    return 0.0 if ideal == 0 else dcg(rels_ordenadas, k) / ideal


def mrr(rels_ordenadas: list[int], umbral: int = UMBRAL_RELEVANTE) -> float:
    """Inverso de la posición del primer relevante (1.0 si el primero ya es relevante)."""
    for i, r in enumerate(rels_ordenadas):
        if r >= umbral:
            return 1.0 / (i + 1)
    return 0.0


def recall_at_k(rels_ordenadas: list[int], todas_rels: list[int], k: int, umbral: int = UMBRAL_RELEVANTE) -> float:
    """Fracción de los relevantes que aparecen en las primeras k posiciones."""
    total = sum(1 for r in todas_rels if r >= umbral)
    if total == 0:
        return 0.0
    return sum(1 for r in rels_ordenadas[:k] if r >= umbral) / total


def precision_at_k(rels_ordenadas: list[int], k: int, umbral: int = UMBRAL_RELEVANTE) -> float:
    """Fracción de las primeras k posiciones que son relevantes."""
    return sum(1 for r in rels_ordenadas[:k] if r >= umbral) / k
