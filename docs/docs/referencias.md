# Referencias y matriz de antecedentes

Fecha de consulta de todas las fuentes: 22 de noviembre de 2026.

## Matriz de antecedentes

| # | Fuente | Tipo | Decisión del proyecto que respalda |
|---|--------|------|------------------------------------|
| R1 | Dastin (2018), Reuters | Prensa investigativa | Hacer una prueba contrafactual que cambie género y nombre en un mismo CV |
| R2 | NYC DCWP (2023), FAQ de la Ley Local 144 | Documento oficial | Calcular tasas de selección e impact ratio por grupo en mi reporte de auditoría |
| R3 | Contralor del Estado de NY (2025), informe 2024-N-6 | Informe oficial | Documentar con claridad la fuente de los datos y los cálculos de mi auditoría |
| R4 | Mobley v. Workday (2025), Dkt. 128 | Documento judicial | Exigir que una persona revise siempre el ranking |
| R5 | Comisión Europea, AI Act, Anexo III | Norma oficial | Declarar el sistema como educativo y de alto riesgo |
| R6 | Reimers y Gurevych (2019) + ficha del modelo en Hugging Face | Artículo + ficha técnica | Usar embeddings multilingües con licencia Apache-2.0 |
| R7 | Manning, Raghavan y Schütze (2008), cap. 8 | Libro de texto | Fijar las etiquetas de relevancia y las métricas (nDCG@10, MRR) antes de evaluar |
| R8 | Robertson y Zaragoza (2009), BM25 | Artículo de revisión | Usar BM25 como línea base |

## Notas por fuente

**R1 (Amazon).** Este caso me muestra que un modelo entrenado con hojas de vida del pasado puede aprender a penalizar a las mujeres, por ejemplo por la palabra "women's". Amazon dijo que la herramienta nunca fue usada por sus reclutadores para evaluar candidatos, aunque sí miraban sus recomendaciones; por eso cito el caso con cuidado. De aquí tomo la idea de mi prueba contrafactual: cambiar solo el género o el nombre en un mismo CV y medir cuánto se mueve su posición.

**R2 (Ley Local 144, FAQ).** El documento explica que una auditoría de sesgo debe calcular tasas de selección o de puntaje y el impact ratio por categorías de sexo, raza/etnia y combinaciones de ambas. También dice que el resumen debe publicar la fuente de los datos, y que una categoría con menos del 2 % de los datos puede excluirse. En mi proyecto adapto esa idea a un ranking: mido qué proporción de cada grupo queda en el top 10 y divido por la del grupo con mayor proporción. Mi auditoría es educativa y propia, no es una auditoría independiente como exige la ley.

**R3 (Auditoría del Contralor).** El informe evalúa cómo la ciudad de Nueva York hace cumplir la Ley Local 144 entre julio de 2023 y junio de 2025. Encontró que el sistema de quejas funcionaba mal. Además, el departamento revisó 32 empresas y halló un solo problema, mientras que los auditores, con las mismas empresas, hallaron al menos 17 posibles incumplimientos. El departamento no estuvo de acuerdo con varios hallazgos, y por eso presento esto como la posición de la auditoría y no como un hecho cerrado. Me enseña que muchas auditorías fallan por explicar mal los datos y los cálculos, así que en mi informe voy a documentar de dónde salen mis datos y cómo calculo cada cifra.

**R4 (Mobley v. Workday).** Es una demanda en curso en la que se alega que un sistema de recomendación de candidatos discrimina por edad. El tribunal aceptó de forma preliminar tramitarla como acción colectiva el 16 de mayo de 2025. Son alegaciones, no una sentencia final. Me sirve para justificar que mi sistema solo apoya y que una persona revisa y decide.

**R5 (AI Act).** El Anexo III clasifica como de alto riesgo los sistemas de IA para reclutamiento o selección, incluido analizar y filtrar solicitudes y evaluar candidatos. Mi proyecto cae en esa categoría. Por eso lo limito a uso educativo, con datos públicos o sintéticos y supervisión humana obligatoria.

**R6 (Sentence-BERT y ficha del modelo).** Sentence-BERT es el método en que se basan los modelos de embeddings de oraciones. La ficha del modelo indica que soporta unos 50 idiomas, produce vectores de 384 dimensiones y tiene licencia Apache-2.0. Lo elegí porque mis CVs están en español y la licencia me permite usarlo en el proyecto.

**R7 (Manning et al., capítulo 8).** El capítulo trata cómo evaluar sistemas de recuperación: colecciones de prueba, medidas para resultados ordenados y cómo juzgar la relevancia. De aquí saco que primero debo definir qué CVs son relevantes para cada oferta y recién después comparar métodos. Mis métricas principales serán nDCG@10 y MRR, y también reportaré Recall@10, porque miden qué tan arriba quedan los candidatos relevantes.

**R8 (Robertson y Zaragoza, BM25).** BM25 es la función de puntuación más conocida del marco de relevancia probabilística. Es una línea base simple y fuerte, así que mis embeddings tienen que superarla para justificar su uso. Como BM25 tiene parámetros que se pueden ajustar, los voy a ajustar solo con la partición de validación y nunca con la de prueba.

## Referencias completas

R1. Dastin, J. (10 de octubre de 2018). *Amazon scraps secret AI recruiting tool that showed bias against women*. Reuters.
URL: https://www.reuters.com/article/us-amazon-com-jobs-automation-insight/amazon-scraps-secret-ai-recruiting-tool-that-showed-bias-against-women-idUSKCN1MK08G
Consultado: 22/11/2026.

R2. NYC Department of Consumer and Worker Protection (29 de junio de 2023). *Automated Employment Decision Tools: Frequently Asked Questions*.
URL: https://www.nyc.gov/assets/dca/downloads/pdf/about/DCWP-AEDT-FAQ.pdf
Consultado: 22/11/2026.

R3. Office of the New York State Comptroller, Division of State Government Accountability (diciembre de 2025). *Department of Consumer and Worker Protection: Enforcement of Local Law 144 – Automated Employment Decision Tools* (Report 2024-N-6).
URL: https://www.osc.ny.gov/files/state-agencies/audits/pdf/sga-2026-24n6.pdf
Consultado: 22/11/2026.

R4. United States District Court, Northern District of California (16 de mayo de 2025). *Mobley v. Workday, Inc.*, Case No. 3:23-cv-00770-RFL, Order Granting Preliminary Collective Certification (Dkt. 128).
URL: https://www.govinfo.gov/content/pkg/USCOURTS-cand-3_23-cv-00770/pdf/USCOURTS-cand-3_23-cv-00770-1.pdf
Consultado: 22/11/2026.

R5. European Commission, AI Act Service Desk. *Annex III: High-risk AI systems* (Reglamento (UE) 2024/1689).
URL: https://ai-act-service-desk.ec.europa.eu/en/ai-act/annex-3
Consultado: 22/11/2026.

R6a. Reimers, N. y Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. Proceedings of EMNLP 2019. Association for Computational Linguistics.
URL: http://arxiv.org/abs/1908.10084
Consultado: 22/11/2026.

R6b. sentence-transformers (s. f.). *paraphrase-multilingual-MiniLM-L12-v2* [ficha del modelo]. Hugging Face.
URL: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Consultado: 22/11/2026.

R7. Manning, C. D., Raghavan, P. y Schütze, H. (2008). *Introduction to Information Retrieval*, capítulo 8: "Evaluation in information retrieval". Cambridge University Press.
URL: https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-in-information-retrieval-1.html
Consultado: 22/11/2026.

R8. Robertson, S. y Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389. DOI: 10.1561/1500000019.
URL: https://doi.org/10.1561/1500000019
Consultado: 22/11/2026.
