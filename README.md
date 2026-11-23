# Filtro de hojas de vida con auditoría de sesgo

Prototipo educativo de Machine Learning (proyecto 26 del taller): ordena hojas de vida según su ajuste a una oferta de trabajo, con ranking explicable y auditoría de sesgo. **No decide nada por sí solo: una persona siempre revisa y decide.**

## Estado
- [x] Planteamiento y referencias (`docs/`)
- [x] Generador de datos sintéticos en español (`src/generar_datos.py`)
- [ ] Línea base BM25 / TF-IDF
- [ ] Ranking con embeddings
- [ ] Auditoría de sesgo contrafactual
- [ ] Aplicación (Streamlit)

!git clone https://github.com/michaelmoreno101010/filtro-hojas-de-vida.git
%cd filtro-hojas-de-vida
!pip install -q pytest
!python -m pytest -q
!python -m src.generar_datos
```

## Datos
Los CVs y ofertas son **sintéticos** (inventados por el autor, sin personas reales). La decisión y sus limitaciones están en `docs/decision_datos.md`; la descripción de las variables, en `docs/ficha_datos.md`.

## Estructura
```
configs/   catálogo de habilidades y parámetros de generación
src/       código
tests/     pruebas automáticas
notebooks/ cuadernos de exploración
docs/      planteamiento, referencias, decisiones, fichas
data/      datos generados (se regeneran con el script)
results/   figuras y tablas de resultados
```
