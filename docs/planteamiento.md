Título: Filtro de hojas de vida: ranking explicable con auditoría de sesgo

1. Problema
Quien recluta recibe muchas hojas de vida para una sola oferta y revisarlas una por una toma tiempo. Las herramientas automáticas de selección ya han mostrado sesgos contra grupos de personas. Este proyecto busca un ranking que ayude a priorizar la revisión y que, además, mida si trata distinto a candidatos con el mismo perfil.

2. Usuario y contexto

Usuario: una persona de reclutamiento o talento humano.
Contexto: uso educativo, con datos públicos o sintéticos.

3. Entradas y salidas

Entradas: el texto de una oferta de trabajo y un conjunto de hojas de vida (PDF o texto).
Salidas: un ranking de candidatos con puntaje de similitud, las frases del CV que más influyeron y un reporte de auditoría de sesgo.

4. Pregunta del proyecto
¿Un ranking basado en embeddings supera a uno de palabras clave (BM25/TF-IDF) en nDCG@10 sin generar diferencias de trato cuando se cambian atributos como nombre o género en un mismo CV?

5. Objetivo general
Desarrollar y evaluar un prototipo educativo que ordene hojas de vida según su ajuste a una oferta, de forma explicable y con una auditoría de sesgo.

6. Objetivos específicos 

Construir un conjunto de evaluación de al menos 10 ofertas y 30 CVs con relevancia etiquetada, antes de entrenar o ajustar nada.
Implementar una línea base (BM25/TF-IDF) y reportar nDCG@10, MRR y Recall@10.
Implementar el ranking con embeddings y compararlo con la línea base en al menos 5 experimentos controlados.
Ejecutar una prueba contrafactual (cambiar nombre y género) y reportar la variación de posición y de puntaje, con un umbral de aceptación fijado antes de ver resultados.
Entregar una app que muestre el ranking, la explicación y los límites de uso, junto con una matriz de riesgos.

7. Qué no resuelve

No decide quién es contratado ni descarta candidatos.
No infiere género, edad, origen ni otras características personales.
No evalúa entrevistas, referencias ni habilidades blandas.
No es apto para uso real en selección sin auditoría legal y supervisión humana.

8. Tipo de tarea de ML
Recuperación y ranking de información (learning to rank / búsqueda semántica), con una prueba de equidad sobre los resultados. No es clasificación, porque el objetivo es ordenar, no etiquetar.
Justificación: el reclutador necesita priorizar, y un puntaje continuo permite ordenar y explicar.

9. Alternativa no-ML 
Búsqueda por palabras clave con filtros manuales (por ejemplo "Python" y "3 años"). Es simple y transparente, pero no capta sinónimos ("analista de datos" ≈ "data analyst"). Esa debilidad es lo que el proyecto pone a prueba.

10. Resumen 
Este proyecto construye un prototipo educativo que ayuda a una persona de reclutamiento a priorizar hojas de vida frente a una oferta de trabajo. El sistema extrae el texto de cada hoja de vida, lo convierte en representaciones numéricas (embeddings) y calcula su similitud con la oferta para generar un ranking. Cada posición muestra las frases del CV que más pesaron, de modo que el puntaje sea explicable. El ranking se compara con una línea base de palabras clave (TF-IDF/BM25) usando métricas de recuperación como nDCG@10. Además, se audita el sesgo con pruebas contrafactuales: se cambian nombres o género y se mide cuánto varía la posición. El sistema nunca decide por sí solo: apoya el trabajo y una persona revisa y decide.

11. Glosario

Embedding: representación numérica de un texto que captura su significado.
Similitud coseno: medida de qué tan parecidos son dos textos a partir de sus embeddings.
BM25 / TF-IDF: métodos clásicos que puntúan por coincidencia de palabras.
Ranking: lista ordenada de candidatos por puntaje.
nDCG@k, MRR, Recall@k: métricas que miden qué tan arriba quedan los candidatos relevantes.
Prueba contrafactual: repetir el ranking cambiando solo un atributo (por ejemplo el nombre) para ver si el resultado cambia.
Fuga de datos: usar información de prueba durante el entrenamiento o la elección del modelo.
