# Filtro de hojas de vida: ranking explicable y auditoría de sesgo

Proyecto 26 del taller de aprendizaje automático. Trabajo individual.

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

Usé un asistente de IA (Claude) como apoyo para diseñar el proyecto, escribir el código y redactar documentos. La declaración completa está en `docs/declaracion_ia.md`. Las cifras de este informe salen de las ejecuciones que hice yo mismo y están guardadas en `results/`.
