## Aplicación web — Filtro Hoja de Vida

Filtro Hoja de Vida es una aplicación web desarrollada en Python y Streamlit que permite explorar los resultados del modelo BM25 con neutralización de género (E-04).

### Funcionalidades

- Exploración de 400 hojas de vida sintéticas y 10 ofertas laborales.
- Ranking de documentos mediante BM25.
- Explicabilidad mediante aportes individuales por palabra.
- Resaltado de coincidencias textuales.
- Auditoría de sesgo mediante 100 pares contrafactuales.
- Monitoreo de latencia y costo de API.
- Exportación de resultados en formato CSV.
- Interfaz gráfica interactiva.

### Instalación y ejecución

Requisitos: Python 3.13 y Git.

Crear el entorno virtual:

`python -m venv .venv`

Instalar las dependencias:

`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`

Ejecutar las pruebas automatizadas:

`.\.venv\Scripts\python.exe -m pytest -q`

Iniciar la aplicación:

`.\.venv\Scripts\python.exe -m streamlit run app.py`

Acceder desde el navegador:

http://localhost:8501

### Resultados de validación

- 54 pruebas automatizadas aprobadas.
- 100 % de empates contrafactuales en la partición dev evaluada.
- Razón de impacto F/M: 1,083.
- Saltos en el top-10: 6,7 % en la partición dev.
- Latencia media observada: 2,39 ms en dos consultas locales.
- Costo de API externa por consulta: 0 COP.

### Reproducción de experimentos

Las dependencias originales de los experimentos se conservan en `requirements-experimentos.txt`.

### Limitaciones y uso responsable

La aplicación fue desarrollada exclusivamente con fines académicos y utiliza datos sintéticos. No debe utilizarse para contratar, descartar ni evaluar personas reales. Los resultados de la auditoría no garantizan la ausencia de discriminación en escenarios reales.

### Despliegue

Aplicación desarrollada para su publicación en Streamlit Community Cloud.