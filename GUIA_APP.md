# Filtro Hoja de Vida — ejecución local
Desde la carpeta raíz, con Python 3.11 o 3.12, ejecutar en PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-app.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Abrir http://localhost:8501. No se necesitan los embeddings para esta aplicación.
Seleccionar una oferta sintética, analizar, inspeccionar aportes y reproducir auditoría. En monitoreo se muestran tiempos reales de la sesión. El costo API es cero; no incluye infraestructura. El índice BM25 se reconstruye desde los JSON originales y se identifica mediante una huella de código/configuración. No se admiten CV reales. La interfaz no se ha ejecutado en el entorno de preparación porque Streamlit no está instalado; validar localmente antes de entregar.

Actualizar el README y las secciones del informe que indican ausencia de interfaz una vez verificada. Añadir a la declaración de IA el apoyo de ChatGPT en la interfaz, servicios y pruebas; documentar la verificación propia.
