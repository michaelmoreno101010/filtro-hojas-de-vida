# Ficha de datos

| Campo | Contenido |
|---|---|
| Nombre | CVs y ofertas sintéticas en español (hojas_de_vida_sinteticas) |
| Fuente | Generados por `src/generar_datos.py` (código propio, versión 1.0.0) |
| Fecha de generación | 23/11/2026 |
| Semilla aleatoria | 42 |
| Licencia | Datos: CC BY 4.0. Código: MIT. (elegidas por el autor) |
| Formato | CSV: `ofertas.csv`, `cvs.csv`, `relevancia.csv`, más `metadatos.json` con versiones y hashes |
| Tamaño | 400 CVs (300 base + 100 gemelos), 10 ofertas, 4000 pares oferta–CV |
| Unidad de análisis | Un CV; y un par (oferta, CV) para la relevancia |
| Idioma | Español, con algunos términos técnicos en inglés |

## Variables (`cvs.csv`)

| Variable | Tipo | Descripción |
|---|---|---|
| cv_id | texto | Identificador único (los gemelos terminan en `_g`) |
| grupo_id | texto | Identificador del grupo; el CV y su gemelo comparten el mismo |
| es_gemelo | 0/1 | 1 si es el gemelo contrafactual de otro CV |
| sector | categórica | tic, educacion_comunicacion, salud, finanzas, ingenieria (80 CVs cada uno) |
| rol | categórica | 10 roles, 40 CVs cada uno |
| anios | numérica | Años de experiencia (de 0 a 15) |
| genero | categórica | F o M; solo para la auditoría, **nunca entra al modelo** |
| nombre | texto | Nombre ficticio (nombre de pila y dos apellidos de listas propias) |
| calidad | categórica | alta (156), media (132), baja (112); controla cuántas habilidades del cargo aparecen |
| habilidades | lista | Habilidades del perfil oculto (separadas por `|`) |
| texto | texto | CV completo redactado a partir del perfil oculto |

## Etiquetas

Relevancia por par (oferta, CV) en escala 0 a 3, calculada con una regla definida antes de modelar, solo a partir del perfil oculto (rol, sector, años y habilidades), **nunca del texto ni del género**:

- **3:** mismo rol, cubre al menos el 80 % de las habilidades requeridas de la oferta y cumple los años mínimos.
- **2:** mismo rol y cubre al menos el 60 % de las habilidades requeridas.
- **1:** mismo rol y cubre al menos el 40 %, o mismo sector y cubre al menos el 60 %.
- **0:** cualquier otro caso.

Distribución de los 4000 pares: nivel 0: 3590; nivel 1: 108; nivel 2: 105; nivel 3: 197. Se considera "relevante" una relevancia de 2 o más (unos 30 CVs por oferta).

Los umbrales están en `configs/generacion.json` y se fijaron antes de ejecutar cualquier modelo. El autor escribió la regla y las ofertas; no hubo un segundo anotador.

**Revisión manual de una muestra:** [COMPLETAR TÚ: revisé unos 20 pares de `relevancia.csv` contra el texto del CV. En X de 20 la etiqueta coincidía con lo que se lee en el CV. Casos que no coincidían y por qué: ...]

## Datos sensibles

No hay datos de personas reales. Todos los nombres son inventados: el nombre de pila sale de una lista propia por género y los apellidos de una lista propia de 30 apellidos comunes. El género es un atributo asignado por el generador, solo para auditar el sesgo. Los apellidos no dependen del género, así que cada gemelo comparte los apellidos de su original.

## Gemelos contrafactuales

100 CVs son gemelos: el mismo CV con otro nombre de pila y las palabras con género cambiadas (por ejemplo, "ingeniera" por "ingeniero"). Hay 10 por rol. Como la relevancia no depende del género, un CV y su gemelo tienen siempre la misma relevancia. Esto permite medir si un sistema los trata igual.

## Calidad y exploración (EDA)

- **Duplicados:** los 400 textos son distintos entre sí.
- **Balance:** 200 CVs de cada género; 80 por sector; 40 por rol.
- **Longitud:** entre 58 y 137 palabras por CV (mediana 96).
- **Años de experiencia:** de 0 a 15.
- **Faltantes:** no hay, porque los datos se generan completos.
- **Fuga de información:** la relevancia no se calcula a partir del texto ni del género. El género se guarda en una columna aparte que los modelos no leen. Aun así, los CVs se redactan desde el mismo perfil que define la relevancia, por lo que un método de palabras clave tiene una ventaja estructural (ver riesgos).
- **Reproducibilidad:** `metadatos.json` guarda la semilla, la versión de Python y el hash sha256 de cada archivo.

## Riesgos conocidos

- Los CVs sintéticos son más homogéneos y cortos que los reales; los resultados no se pueden generalizar a CVs reales.
- La regla de relevancia es del autor y puede favorecer a los métodos que entienden esa regla.
- Los CVs se redactan con plantillas y sinónimos controlados, lo que puede favorecer a los métodos basados en palabras.
- El género solo toma dos valores (F y M) y solo se asigna con nombres y gramática; no se cubren otros atributos como edad u origen.
