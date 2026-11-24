# Matriz de riesgos y consideraciones éticas

## Principio rector
El sistema **solo ordena** CVs para ayudar a priorizar la lectura. **No aprueba ni rechaza a nadie.**
Toda decisión de contratación la toma una persona, que ve los CVs completos.

## Matriz de riesgos

| # | Riesgo | Probabilidad | Impacto | Evidencia en este proyecto | Mitigación | Riesgo que queda |
|---|--------|--------------|---------|----------------------------|------------|------------------|
| 1 | Sesgo de género por palabras con género ("Ingeniero/a") | Alta (sin mitigar) | Alto | BM25: razón de impacto 0,613 y 47,4 % de saltos de top-10 (E-01) | Neutralizar formas con género antes de buscar (E-04): razón 1,083 | La lista de palabras es la del generador; en CVs reales sería incompleta |
| 2 | Inestabilidad de los embeddings ante nombre y género | Media | Medio | E-02: 47,6 % de saltos de top-10; E-05 31,6 % | No usar embeddings como señal principal sin nueva auditoría | Efecto no explicado del todo |
| 3 | Sesgos que no medimos (edad, origen, nombre por clase social, foto) | Media | Alto | La auditoría solo cubre género binario | Declarar el alcance; ampliar la auditoría antes de cualquier uso real | Sin cubrir |
| 4 | Pérdida de buenos candidatos (falsos negativos) | Alta | Alto | 31 CVs relevantes fuera del top-30 en dev | Revisión humana más allá del top-10; ver el CV completo | Candidatos con vocabulario distinto |
| 5 | Sobreconfianza en el ranking ("el sistema dijo") | Media | Alto | — | La interfaz muestra la explicación y recuerda que decide una persona | Depende de la cultura de la organización |
| 6 | Datos sintéticos poco realistas; resultados no generalizables | Alta | Medio | CVs muy homogéneos | Declararlo en el informe; no afirmar rendimiento en CVs reales | Total |
| 7 | Privacidad de datos personales | Baja en este proyecto | Alto en uso real | Todos los CVs son inventados | Si se usara con datos reales: consentimiento, minimización y retención limitada (Ley 1581 de 2012 en Colombia) | — |
| 8 | Uso por una empresa sin auditar | Media | Alto | — | Auditoría periódica con gemelos; criterios fijados de antemano | — |

## Límites del trabajo
- La auditoría usa pares sintéticos (mismo CV, otro nombre y género gramatical). Un sistema puede pasarla y seguir discriminando por otras señales.
- Que la razón de impacto esté entre 0,80 y 1,25 **no prueba** que el sistema sea justo ni que cumpla la ley.
- La regla de relevancia está escrita por mí, por lo que favorece a los métodos que entienden esa regla.

## Uso permitido y no permitido
- **Permitido:** priorizar el orden de lectura, con revisión humana y auditorías periódicas.
- **No permitido:** descartar automáticamente a candidatos o decidir sin una persona.
