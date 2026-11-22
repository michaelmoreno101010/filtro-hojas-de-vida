# Decisión sobre los datos

## Decisión
Se usarán hojas de vida (CVs) **sintéticas en español**, generadas con un script propio, reproducible y con semilla fija. No se usarán CVs de personas reales.

## Alternativas evaluadas
| Opción | Ventajas | Problemas |
|--------|----------|-----------|
| Resume Dataset de Kaggle (obtenido de livecareer.com) | Público, fácil de descargar | Está en inglés, solo tiene categoría de trabajo como etiqueta, no tiene atributos demográficos ni relevancia por oferta, proviene de scraping y no pude confirmar su licencia |
| Dataset de CVs sintéticos de Saldivar et al. (2025) | Diseñado para pruebas de equidad en contratación | Acceso restringido a investigadores de instituciones europeas bajo acuerdo de licencia |
| **CVs sintéticos propios (elegida)** | Permite cambiar solo el nombre o el género y dejar todo igual; sin datos personales; licencia propia; en español | Los resultados pueden no generalizarse a CVs reales |

## Razones
1. La prueba contrafactual exige controlar qué cambia entre dos CVs; solo los datos sintéticos lo permiten.
2. Se evitan problemas de privacidad y de licencia.
3. Saldivar et al. (2025) y el AI Act respaldan el uso de datos sintéticos para detectar sesgos sin procesar datos personales.

## Cómo se evita que los datos sean demasiado fáciles
- Los CVs se redactan con sinónimos, frases distintas y mezcla ocasional de español e inglés.
- La relevancia se define con una regla fijada antes de ejecutar los modelos y se revisa a mano en una muestra.

## Limitaciones declaradas
- Los CVs sintéticos son más ordenados que los reales; los resultados no se generalizan a CVs reales.
- Los nombres usados representan solo algunos grupos; la auditoría no cubre todas las formas de sesgo.
