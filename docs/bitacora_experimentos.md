# Bitácora de experimentos

Datos: sintéticos, semilla 42. Partición de evaluación: ofertas "dev" (5 ofertas). La partición "test" no se ha mirado.

| ID | Fecha | Qué cambié | Hipótesis | nDCG@10 | MRR | P@10 | Recall@10 | Recall@30 | Conclusión |
|----|-------|-----------|-----------|---------|-----|------|-----------|-----------|------------|
| E-00 | 23/11/2026 | Ranking al azar (piso de referencia) | Debe ser muy bajo | [de tu salida] | [..] | [..] | [..] | [..] | Referencia mínima |
| E-01 | 23/11/2026 | Línea base BM25 (k1=1.5, b=0.75, sin ajustar) | Es una línea base fuerte | [de tu salida] | [..] | [..] | [..] | [..] | [escríbela tú con lo que veas] |

## Notas
- Recall@10 no puede acercarse a 1: cada oferta tiene unos 30 CVs relevantes y solo se miran 10. Por eso también se reporta Recall@30.
- Los parámetros de BM25 son los estándar y no se ajustaron con ningún dato.
