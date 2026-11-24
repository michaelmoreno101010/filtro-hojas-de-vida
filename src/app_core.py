"""Servicios de demostración exclusivamente con el corpus sintético original."""
from hashlib import sha256
from time import perf_counter
from src.generar_datos import cargar_json, generar, VERSION_GENERADOR
from src.linea_base import RAIZ, BM25, ordenar
from src.mitigacion import tokenizar_neutro
from src.explicar import contribuciones
from src.auditoria import auditar


def cargar():
    cfg = RAIZ / 'configs' / 'generacion.json'
    cat = RAIZ / 'configs' / 'catalogo.json'
    datos = generar(cargar_json(cfg), cargar_json(cat))
    modelo = BM25([tokenizar_neutro(c['texto']) for c in datos['cvs']])
    version = sha256(b''.join(p.read_bytes() for p in [cfg, cat, RAIZ/'src/generar_datos.py', RAIZ/'src/linea_base.py', RAIZ/'src/mitigacion.py'])).hexdigest()[:12]
    return datos, modelo, version, VERSION_GENERADOR


def analizar(datos, modelo, oferta_id):
    oferta = next((o for o in datos['ofertas'] if o['oferta_id'] == oferta_id), None)
    if oferta is None:
        raise ValueError('Seleccione una oferta sintética válida.')
    inicio = perf_counter()
    ids = [c['cv_id'] for c in datos['cvs']]
    consulta = tokenizar_neutro(oferta['texto'])
    puntos = modelo.puntajes(consulta)
    posiciones = {c:i for i,c in enumerate(ids)}
    filas = [{'Posición': n, 'CV': c, 'BM25': puntos[posiciones[c]]} for n,c in enumerate(ordenar(ids,puntos),1)]
    return filas, consulta, (perf_counter()-inicio)*1000


def auditoria(datos, modelo, particion):
    if particion not in ('dev','test'):
        raise ValueError('Partición inválida')
    cvs = datos['cvs']
    return auditar([c['cv_id'] for c in cvs], {c['cv_id']:c['genero'] for c in cvs}, {o['oferta_id']:modelo.puntajes(tokenizar_neutro(o['texto'])) for o in datos['ofertas'] if o['particion']==particion})
