# Bitácora de experimentos

Datos: sintéticos, semilla 42. Las decisiones se tomaron con las 5 ofertas de la partición **dev**. La partición **test** (5 ofertas) se evaluó **una sola vez**, al final, solo con la línea base y el sistema final (ver sección "Evaluación final").

Cada experimento cambia una sola variable respecto al anterior.

## Experimentos en dev

| ID | Fecha | Qué cambié | Hipótesis | nDCG@10 | MRR | P@10 | Recall@10 | Recall@30 | Conclusión |
|---|---|---|---|---|---|---|---|---|---|
| E-00 | 23/11/2026 | Ranking al azar (piso de referencia) | Debe ser muy bajo | 0,097 | 0,468 | 0,120 | 0,038 | 0,079 | Referencia mínima. Todo lo demás debe superarla. |
| E-01 | 23/11/2026 | Línea base BM25 (k1 = 1,5; b = 0,75, sin ajustar) | Es una línea base fuerte | 0,869 | 1,000 | 0,940 | 0,305 | 0,775 | Cumplida: supera con mucho al azar. Pero la auditoría de género falla (razón de impacto 0,613; 47,4 % de saltos de top-10). |
| E-02 | 23/11/2026 | Embeddings (MiniLM multilingüe, 128 tokens) en lugar de BM25 | Entender sinónimos mejora el ranking | 0,718 | 0,867 | 0,780 | 0,251 | 0,712 | Refutada: BM25 es mejor en estos datos. Auditoría: no favorece a un género (53,6 % / 46,4 %) pero tiene 47,6 % de saltos. |
| E-03 | 23/11/2026 | E-02 con 256 tokens en lugar de 128 | El corte a 128 tokens perdía las habilidades del final del CV | 0,540 | 0,850 | 0,760 | 0,246 | 0,652 | Refutada: con más texto el resultado empeoró. No se siguió por este camino. |
| E-04 | 23/11/2026 | BM25 con formas de género neutralizadas (ingeniera → ingeniero, etc.) | Eliminar la diferencia de palabras con género quita el sesgo de BM25 | 0,852 | 1,000 | 0,920 | 0,297 | 0,799 | Confirmada: cumple los criterios (razón 1,083; 6,7 % de saltos). Costo: −0,017 de nDCG@10 frente a E-01. |
| E-05 | 23/11/2026 | Híbrido: E-04 + embeddings con fusión de rangos RRF (k = 60) | Combinar palabras y significado mejora el ranking | 0,842 | 1,000 | 0,920 | 0,297 | 0,758 | Refutada: peor que E-04 y no pasa la auditoría (31,6 % de saltos). |

**Decisión:** el sistema final es E-04. Cumple la auditoría fijada de antemano y tiene mejor nDCG@10 que E-02, E-03 y E-05.

## Evaluación final en test (una sola corrida, 23/11/2026)

| Sistema | nDCG@10 | MRR | P@10 | Recall@10 | Recall@30 | Auditoría |
|---|---|---|---|---|---|---|
| Azar | 0,085 | 0,223 | 0,120 | 0,043 | 0,084 | — |
| BM25 (E-01) | 0,790 | 0,900 | 0,860 | 0,294 | 0,702 | No cumple (razón 0,786; 23,1 % de saltos) |
| BM25 neutro (E-04, final) | 0,791 | 0,900 | 0,880 | 0,300 | 0,709 | Cumple (razón 1,083; 0 % de saltos) |

Los embeddings y el híbrido no se evaluaron en test porque ya estaban descartados con dev.

## Notas

- Recall@10 no puede acercarse a 1: cada oferta tiene unos 30 CVs relevantes y solo se miran 10. Por eso también se reporta Recall@30.
- Los parámetros de BM25 son los estándar y no se ajustaron con ningún dato.
- Los criterios de la auditoría (razón de impacto entre 0,80 y 1,25 y saltos de top-10 de máximo 10 %) se fijaron antes de ver resultados y no se cambiaron.
- Con 5 ofertas y entre 11 y 21 pares en el top-10, las diferencias pequeñas (por ejemplo 0,790 contra 0,791) son ruido.
- Las salidas completas de cada experimento están en `results/`.
