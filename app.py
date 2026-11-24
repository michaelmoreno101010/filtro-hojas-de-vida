"""Filtro Hoja de Vida: demostración académica del experimento E-04."""
import csv
import io
import streamlit as st
from src.app_core import cargar, analizar, auditoria, contribuciones
from src.explicar import resaltar_html

st.set_page_config(page_title='Filtro Hoja de Vida', page_icon='📊', layout='wide')
st.markdown("""<style>
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1400px;}
[data-testid="stSidebar"] {background: #10243d;}
[data-testid="stSidebar"] :is(p, label, h1, h2, h3, span) {color: #e5eef9;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding: .65rem .5rem; border-radius: 8px;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background: #24476d;}
[data-testid="stMetric"] {background: white; border: 1px solid #dbe5ef; border-top: 3px solid #0891b2; border-radius: 12px; padding: 18px; box-shadow: 0 3px 12px #10243d09;}
[data-testid="stMetricValue"] {color: #123c60;}
[data-testid="stDataFrame"] {border: 1px solid #dbe5ef; border-radius: 10px; overflow: hidden;}
.hero {background: linear-gradient(115deg,#10243d,#174d70); color: white; padding: 28px 32px; border-radius: 16px; margin-bottom: 20px;}
.hero h1 {color: white; font-size: 2.15rem; padding: 0; margin: 8px 0;}
.hero p {color: #d4e7f6; margin: 0;}
.eyebrow {font-size: .75rem; letter-spacing: .15em; color: #80e2e7; font-weight: 700;}
mark {background: #c9f1ef !important; color: #12465a !important; border-radius: 3px;}
</style>
<div class="hero"><div class="eyebrow">ANALÍTICA DOCUMENTAL · PROTOTIPO ACADÉMICO</div><h1>Filtro Hoja de Vida</h1><p>Recuperación de información y auditoría de sesgo · BM25 neutro · E-04</p></div>""", unsafe_allow_html=True)
st.warning('Solo datos sintéticos. No utilizar para contratar, descartar ni evaluar personas reales. Una coincidencia textual no demuestra competencia.')
try:
    datos, modelo, version, generador = st.cache_resource(cargar)()
except Exception as exc:
    st.error(f'No se pudo construir el corpus sintético: {exc}')
    st.stop()
if 'latencias' not in st.session_state:
    st.session_state.latencias = []
st.sidebar.title('Filtro Hoja de Vida')
st.sidebar.caption('LABORATORIO DE ANALÍTICA')
st.sidebar.divider()
pagina = st.sidebar.radio('Módulo', ['Inicio','Ranking y explicación','Auditoría','Monitoreo'], format_func=lambda x: {'Inicio':'⌂  Inicio','Ranking y explicación':'▤  Ranking y explicación','Auditoría':'◇  Auditoría','Monitoreo':'↗  Monitoreo'}[x])
st.sidebar.divider()
st.sidebar.caption(f'E-04 · huella {version} · generador {generador}')
if pagina == 'Inicio':
    st.subheader('Panel general')
    st.caption('Conjunto de datos y alcance del experimento')
    a,b,c = st.columns(3)
    a.metric('CV sintéticos',len(datos['cvs']))
    b.metric('Ofertas sintéticas',len(datos['ofertas']))
    c.metric('Pares de gemelos',sum(x['cv_id'].endswith('_g') for x in datos['cvs']))
    st.subheader('Cómo funciona')
    st.write('Selecciona una oferta del catálogo original. BM25 compara palabras normalizadas del corpus, ordena los documentos y explica sus aportes. La auditoría compara gemelos contrafactuales.')
    st.info('El índice se reconstruye de forma determinista desde la configuración original. No se ajustan parámetros con los resultados de prueba.')
elif pagina == 'Ranking y explicación':
    st.subheader('Explorador de ranking')
    st.caption('Selecciona una vacante sintética para consultar la relevancia textual.')
    ofertas = {o['oferta_id']:o for o in datos['ofertas']}
    oid = st.selectbox('Oferta sintética', list(ofertas), format_func=lambda x: f"{x} — {ofertas[x]['titulo']}")
    st.write(ofertas[oid]['texto'])
    top = st.slider('Documentos visibles', 5, 30, 10)
    if st.button('Analizar oferta', type='primary'):
        try:
            filas, consulta, ms = analizar(datos, modelo, oid)
            st.session_state.ultimo = (oid, filas, consulta, ms)
            st.session_state.latencias.append(ms)
        except ValueError as exc:
            st.error(str(exc))
    if 'ultimo' in st.session_state and st.session_state.ultimo[0] == oid:
        _, filas, consulta, ms = st.session_state.ultimo
        st.metric('Latencia del ranking (ms)', f'{ms:.2f}')
        st.caption('BM25 es un puntaje sin unidad, no un porcentaje ni probabilidad.')
        st.dataframe(filas[:top], hide_index=True, use_container_width=True)
        import pandas as pd
        st.subheader('Puntuaciones por posición')
        st.bar_chart(pd.DataFrame(filas[:top]).assign(Documento=lambda df: df['Posición'].map(lambda n: f'{n:02d}') + ' · ' + df['CV']), x='Documento', y='BM25', color='#167c9c')
        cv_id = st.selectbox('Documento para explicar', [r['CV'] for r in filas])
        i = next(i for i,c in enumerate(datos['cvs']) if c['cv_id']==cv_id)
        aportes = contribuciones(modelo,i,consulta)
        st.subheader('Aportes por palabra')
        st.dataframe([{'Palabra':k,'Aporte BM25':v} for k,v in aportes.items()], hide_index=True, use_container_width=True)
        st.write(f'Suma de aportes: {sum(aportes.values()):.6f}')
        st.markdown(resaltar_html(datos['cvs'][i]['texto'],set(aportes)), unsafe_allow_html=True)
        out = io.StringIO(); w = csv.DictWriter(out,fieldnames=['Posición','CV','BM25']); w.writeheader(); w.writerows(filas)
        st.download_button('Descargar ranking sintético CSV',out.getvalue(), 'ranking_sintetico.csv','text/csv')
elif pagina == 'Auditoría':
    st.subheader('Auditoría contrafactual')
    st.caption('Comparación de pares sintéticos bajo el protocolo original.')
    particion = st.selectbox('Partición original', ['dev','test'])
    st.caption('Reproducción descriptiva del protocolo original; no se usa para seleccionar ni reajustar el modelo.')
    if st.button('Reproducir auditoría'):
        st.session_state.audit = (particion, auditoria(datos,modelo,particion))
    if 'audit' in st.session_state and st.session_state.audit[0]==particion:
        res=st.session_state.audit[1]; r=res['resumen']; a,b,c=st.columns(3)
        a.metric('Empates',f"{r['pct_empates']:.1%}"); b.metric('Saltos top-10',f"{r['pct_saltos_top']:.1%}"); c.metric('Impacto F/M', 'No definido' if r['razon_de_impacto_F_sobre_M'] is None else f"{r['razon_de_impacto_F_sobre_M']:.3f}")
        st.write('Criterios originales: impacto entre 0,80 y 1,25; saltos ≤ 10 %. Resultado:', 'Cumple' if r['cumple_criterios'] else 'No cumple')
        st.dataframe(res['por_oferta'],hide_index=True)
        st.warning('Auditoría binaria y sintética; no demuestra ausencia de discriminación. El desempate por ID puede afectar el top-10.')
else:
    st.subheader('Seguimiento de la sesión')
    lat=st.session_state.latencias
    a,b,c=st.columns(3); a.metric('Consultas',len(lat)); b.metric('Latencia media (ms)',f'{sum(lat)/len(lat):.2f}' if lat else 'Sin datos'); c.metric('Costo API por consulta','0 COP')
    st.caption('No hay API externa. El costo de equipo, electricidad y alojamiento no está medido. La latencia excluye carga inicial y renderizado.')
    if lat:
        import pandas as pd
        st.line_chart(pd.DataFrame({'Consulta': range(1, len(lat)+1), 'Latencia (ms)': lat}), x='Consulta', y='Latencia (ms)', color='#167c9c')
    st.write('Plan: revisar latencia y errores por versión; comparar distribución de puntajes y vocabulario ante cambios del corpus; repetir auditoría y métricas con un conjunto nuevo independiente antes de aprobar cambios. BM25 requiere reconstruir el índice, no entrenar una red neuronal.')
    st.write('No se almacenan datos personales ni se admiten archivos externos. Los tiempos se conservan solo durante la sesión.')

st.divider()
st.caption('Filtro Hoja de Vida · E-04 · Uso exclusivamente académico')
