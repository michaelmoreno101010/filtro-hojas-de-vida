# Ficha de datos

| Campo | Contenido |
|-------|-----------|
| Nombre | CVs y ofertas sintéticas en español (hojas_de_vida_sinteticas) |
| Fuente | Generados por `src/generar_datos.py` (código propio) |
| Fecha de generación | [COMPLETAR] |
| Semilla aleatoria | [COMPLETAR] |
| Licencia | Datos: CC BY 4.0. Código: MIT. (elegidas por el autor) |
| Formato | JSON (un archivo por CV) y CSV con metadatos |
| Tamaño | [COMPLETAR: número de CVs, número de ofertas] |
| Unidad de análisis | Un CV; y un par (oferta, CV) para la relevancia |
| Idioma | Español, con algunos términos técnicos en inglés |

## Variables
| Variable | Tipo | Descripción |
|----------|------|-------------|
| cv_id | texto | Identificador único |
| sector | categórica | Sector profesional [COMPLETAR: lista] |
| anios_experiencia | numérica | Años de experiencia |
| educacion | texto | Títulos y estudios |
| experiencia | texto | Cargos y descripciones |
| habilidades | lista | Habilidades técnicas y blandas |
| nombre | texto | Nombre ficticio (solo se usa en la prueba contrafactual) |
| genero_metadato | categórica | Solo para la auditoría; nunca entra al modelo |

## Etiquetas
Relevancia por par (oferta, CV) en escala 0 a 3, calculada con una regla definida antes de modelar. [COMPLETAR: describir la regla exacta y quién revisó la muestra]

## Datos sensibles
No hay datos de personas reales. El género es un atributo asignado por el generador, solo para auditar el sesgo. La fuente de la lista de nombres es [COMPLETAR].

## Calidad y exploración (EDA)
[COMPLETAR tras ejecutar: duplicados, faltantes, distribución por sector y por género, longitud de los CVs, riesgos de fuga detectados]

## Riesgos conocidos
- Los CVs sintéticos son más homogéneos que los reales.
- La regla de relevancia puede favorecer a los métodos basados en palabras clave si no hay suficiente variación en la redacción.
