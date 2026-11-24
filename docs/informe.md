# Filtro de hojas de vida: ranking explicable y auditoría de sesgo

Proyecto 26 del taller de aprendizaje automático.

## 1. Problema y alcance

Un equipo de selección recibe muchas hojas de vida para una misma oferta y no alcanza a leerlas todas con el mismo cuidado. Este proyecto construye un sistema que **ordena** las hojas de vida según su cercanía con la oferta, para ayudar a decidir cuáles leer primero. El sistema **no aprueba ni rechaza a nadie**: la decisión siempre la toma una persona.

Además del ranking, el proyecto responde dos preguntas:

1. ¿Puede explicarse por qué una hoja de vida quedó arriba?
2. ¿Trata igual a una mujer y a un hombre con la misma hoja de vida?

Para la segunda pregunta se hizo una auditoría con "gemelos": la misma hoja de vida con otro nombre y las palabras con género gramatical cambiadas (por ejemplo, "ingeniera" por "ingeniero").

## 2. Datos

Se usaron datos **sintéticos en español**, generados con un programa propio (`src/generar_datos.py`, semilla 42). La razón es que permiten controlar el género de cada hoja de vida y crear gemelos exactos, no hay datos personales reales y no hay problemas de licencia. El costo es que **los resultados no se pueden generalizar a hojas de vida reales**.

- 10 ofertas de 10 roles distintos y 400 hojas de vida (300 base y 100 gemelos), con 200 mujeres y 200 hombres.
- 4000 pares oferta–hoja de vida con relevancia de 0 a 3, calculada solo a partir del perfil oculto (rol, años y habilidades). **Nunca** depende del texto ni del género.
- Se considera "relevante" una relevancia de 2 o más.
- Las ofertas se separaron por roles: 5 de desarrollo (para tomar decisiones) y 5 de prueba, que se evaluaron **una sola vez**, al final.

Limitaciones: las hojas de vida son más homogéneas que las reales, y la regla de relevancia la escribí yo, por lo que puede favorecer a los métodos que la "entienden". Detalles en `docs/ficha_datos.md` y `docs/decision_datos.md`.

## 3. Declaración de uso de IA

Usé un asistente de IA (Claude) como apoyo para algunos aspecto de el proyecto. La declaración completa está en `docs/declaracion_ia.md`. Las cifras de este informe salen de las ejecuciones que hice yo mismo y están guardadas en `results/`.

## 4. Método

Todos los sistemas ordenan las 400 hojas de vida para cada oferta y se evalúan con las mismas métricas.

- **Línea base (E-01):** BM25 escrito desde cero (k1 = 1,5; b = 0,75), con palabras sin tildes ni palabras vacías. Compara las palabras de la oferta con las de cada hoja de vida.
- **Embeddings (E-02, E-03):** modelo `paraphrase-multilingual-MiniLM-L12-v2` (licencia Apache-2.0). Cada texto se convierte en un vector y se ordena por similitud coseno.
- **BM25 con género neutralizado (E-04):** igual que E-01, pero antes de buscar cada forma femenina se convierte en la masculina ("ingeniera" → "ingeniero") en ofertas y hojas de vida.
- **Híbrido (E-05):** combina los rankings de E-04 y E-02 con fusión de rangos recíprocos (RRF, constante 60).

**Métricas:** nDCG@10 (la principal), MRR, Precision@10, Recall@10 y Recall@30. Como hay unos 30 CVs relevantes por oferta, el Recall@10 no puede pasar de ≈0,33.

**Reproducibilidad:** semilla 42, datos deterministas con hash sha256, versiones fijadas y 47 pruebas automáticas (`pytest`).

## 5. Experimentos

Cada experimento cambia una sola variable respecto al anterior. Los resultados de E-01 a E-05 se midieron en las ofertas de **desarrollo**; la partición de prueba se usó una sola vez al final.

| ID | Qué cambia | nDCG@10 (dev) | Razón de impacto F/M (dev) | Cumple auditoría |
|---|---|---|---|---|
| E-01 | BM25 | 0,869 | 0,613 | No |
| E-02 | Embeddings, 128 tokens | 0,718 | 0,852 | No (47,6 % de saltos) |
| E-03 | Embeddings, 256 tokens | 0,540 | no se auditó | Hipótesis refutada |
| E-04 | BM25 con género neutralizado | 0,852 | 1,083 | Sí |
| E-05 | Híbrido RRF | 0,842 | 1,174 | No (31,6 % de saltos) |

**Hallazgos:**
- BM25 superó a los embeddings en estos datos (0,869 contra 0,718). Una posible razón, que no comprobé, es que las hojas de vida sintéticas repiten términos muy concretos, lo que favorece a la búsqueda por palabras.
- E-03: pensé que el modelo perdía las habilidades escritas al final del CV por el límite de 128 tokens. Con 256 tokens el nDCG@10 **empeoró** (de 0,718 a 0,540), así que la hipótesis quedó refutada.
- E-04 bajó el nDCG@10 de 0,869 a 0,852 en dev (−0,017) y corrigió el sesgo de BM25.
- E-05 no mejoró: el híbrido (0,842) quedó por debajo de E-04 y no pasó la auditoría. Los embeddings aportaron ruido.

**Decisión:** el sistema final es **E-04**, porque cumple la auditoría y tiene mejor nDCG@10 que el híbrido.

## 6. Resultados en la partición de prueba (una sola corrida)

| Sistema | nDCG@10 | MRR | Precision@10 | Recall@10 | Recall@30 |
|---|---|---|---|---|---|
| Azar | 0,085 | 0,223 | 0,120 | 0,043 | 0,084 |
| BM25 (E-01) | 0,790 | 0,900 | 0,860 | 0,294 | 0,702 |
| **BM25 neutro (E-04, final)** | **0,791** | 0,900 | 0,880 | 0,300 | 0,709 |

Los embeddings y el híbrido **no se evaluaron en `test`** porque se descartaron con los datos de desarrollo. La diferencia entre E-01 y E-04 (0,001) es ruido, porque hay solo 5 ofertas. Lo que sí se puede decir es que el sistema final supera con claridad al azar y que la neutralización de género no empeoró la calidad en `test`.

## 7. Auditoría de sesgo de género

**Criterios fijados antes de ver resultados:** razón de impacto F/M en el top-10 entre 0,80 y 1,25, y saltos de top-10 en como máximo el 10 % de los pares con algún gemelo en el top.

| Sistema | Partición | Gemelo M mejor | Empates | Saltos de top-10 | Razón F/M | Cumple |
|---|---|---|---|---|---|---|
| BM25 (E-01) | dev | 7,8 % | 92,2 % | 47,4 % | 0,613 | No |
| Embeddings (E-02) | dev | 46,4 % | 0 % | 47,6 % | 0,852 | No |
| Híbrido (E-05) | dev | 46,6 % | 0 % | 31,6 % | 1,174 | No |
| BM25 neutro (E-04) | dev | 0 % | 100 % | 6,7 % | 1,083 | Sí |
| BM25 (E-01) | test | 6,0 % | 94,0 % | 23,1 % | 0,786 | No |
| **BM25 neutro (E-04)** | **test** | **0 %** | **100 %** | **0 %** | **1,083** | **Sí** |

**Causa del sesgo en BM25:** el título de la oferta dice "Ingeniero/a", y el tokenizador convierte eso en "ingeniero". Esa palabra coincide con el CV del hombre ("ingeniero") pero no con el de la mujer ("ingeniera"). Todas las diferencias favorecieron al hombre y ninguna a la mujer.

**Embeddings:** no favorecen a un género (53,6 % mujeres y 46,4 % hombres), pero el nombre y las palabras con género mueven mucho las posiciones (19 posiciones de diferencia absoluta media). Es inestabilidad y no una dirección clara, pero igual incumple el criterio.

**Cuidado con la razón de 1,083:** con 100 % de empates, la razón no la define el género sino el desempate por `cv_id` en el borde del top-10. Por eso se repite en dev y en test.

**Advertencias:** la auditoría solo cubre género binario, usa pares sintéticos y tiene pocos casos (11 a 21 pares en el top-10). Pasarla **no prueba** que el sistema sea justo.
## 8. Análisis de errores (E-04, dev)

- **Pocos falsos positivos:** 4 casos en el top-10, que son 2 CVs contados dos veces por su gemelo. Uno es un contador con 12 años que menciona "auditoría" pero no cumple el núcleo del cargo (relevancia 0); otro es un ingeniero civil de calidad baja (relevancia 1).
- **Lo que más falla son los relevantes perdidos:** 31 casos fuera del top-30, sobre todo en analista de datos y enfermería. Son CVs que sí tienen las habilidades requeridas pero quedan abajo. Mi hipótesis, que no comprobé con un experimento, es que BM25 solo cuenta palabras exactas, así que los CVs que expresan la misma habilidad con otras palabras o en listas largas puntúan menos.
- Un analista de datos con 12 años y relevancia 3 (cv_209) queda en la posición 47 de 400.
- Esto coincide con el límite del Recall@10 (≈0,33): solo caben 10 CVs y hay unos 30 relevantes por oferta.

## 9. Explicabilidad

El sistema final (BM25 con género neutralizado) es explicable por construcción: el puntaje de cada hoja de vida es la suma de la contribución de cada palabra de la oferta que aparece en ella, ponderada por qué tan rara es esa palabra en el conjunto. El módulo `src/explicar.py` descompone ese puntaje y muestra, para cada CV del top, las palabras que más lo subieron y cuánto aportó cada una. Una prueba automática verifica que la suma de los aportes es exactamente el puntaje.

Ejemplo de uso: `python -m src.explicar --oferta of_01 --top 5`. [PEGA AQUÍ 1 CV DE LA SALIDA QUE TE DIO COLAB, con sus palabras y aportes, y escribe una línea con tus palabras sobre qué te dice.]

**Qué explica y qué no:** la explicación dice qué palabras coincidieron, no si la persona es buena candidata. Una palabra puede aparecer sin que la persona sepa usar esa habilidad, y un buen candidato puede usar otras palabras y quedar abajo (ver sección 8). Los embeddings no permiten esta descomposición de forma directa, y es una razón más para elegir BM25 neutro.

**Lo que NO se hizo:** no se construyó una interfaz gráfica; la explicación se obtiene por línea de comandos. Es una limitación y trabajo futuro.

**Uso previsto:** la persona reclutadora ve el ranking con sus explicaciones y lee los CVs completos. La decisión es siempre suya.
## 10. Limitaciones y riesgos

- **Datos sintéticos:** los resultados no se pueden generalizar a hojas de vida reales, que son más variadas, tienen errores y distintos formatos.
- **La regla de relevancia es mía:** se calcula a partir de rol, años y habilidades, y puede favorecer a los métodos que entienden esa regla.
- **La neutralización usa la lista del generador:** en CVs reales habría muchas más palabras con género y la lista nunca sería completa.
- **La auditoría es limitada:** cubre solo género binario, con pares sintéticos y entre 11 y 21 pares en el top-10. No cubre edad, origen, nombre ni otras señales. Pasarla no prueba que el sistema sea justo.
- **Pocas ofertas:** 5 en desarrollo y 5 en prueba, por lo que diferencias de centésimas son ruido.
- **Se pierden CVs relevantes:** 31 casos en dev quedaron fuera del top-30 por usar otro vocabulario.
- **Sin interfaz gráfica: la explicación solo se obtiene por línea de comandos (ver sección 9).

La matriz completa de riesgos y las consideraciones éticas están en `docs/riesgos_y_etica.md`.

## 11. Conclusiones

1. En estos datos sintéticos, BM25 (nDCG@10 de 0,869 en dev) superó a los embeddings (0,718) y al híbrido (0,842 con el modelo usado).
2. BM25 simple **sí discrimina por género**, por una causa concreta y comprobada: los títulos "Ingeniero/a" solo coinciden con el CV masculino. Incumple los criterios en dev y en test.
3. Neutralizar las formas con género corrige el problema con un costo pequeño: −0,017 de nDCG@10 en dev y ninguno en test (0,791 contra 0,790).
4. Los embeddings no favorecen a un género, pero el nombre y el género gramatical cambian mucho las posiciones, por lo que tampoco pasan la auditoría.
5. Mi hipótesis de que el límite de 128 tokens perdía información fue refutada por E-03.
6. El resultado no prueba que el sistema sea justo ni sirva con CVs reales. Este sistema solo ordena y **la decisión siempre la toma una persona**.

**Trabajo futuro:** mostrar la explicación por palabra al usuario, probar con hojas de vida reales anonimizadas y con consentimiento, ampliar la auditoría a más atributos y más ofertas.

## 12. Referencias y documentos

Las referencias completas, con lo que se tomó de cada una, están en `docs/referencias.md`. Otros documentos del repositorio:

- `docs/planteamiento.md`: planteamiento del problema.
- `docs/decision_datos.md` y `docs/ficha_datos.md`: decisión y descripción de los datos.
- `docs/bitacora_experimentos.md`: registro de experimentos.
- `docs/riesgos_y_etica.md`: matriz de riesgos y ética.
- `docs/declaracion_ia.md`: declaración de uso de IA.
- `results/`: todos los resultados que sustentan las cifras de este informe.
