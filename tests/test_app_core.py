import pytest
from src.app_core import cargar, analizar, auditoria, contribuciones

@pytest.fixture(scope='module')
def base():
    return cargar()

def test_ranking(base):
    datos, modelo, *_ = base
    filas, consulta, ms = analizar(datos,modelo,datos['ofertas'][0]['oferta_id'])
    assert len(filas)==400 and ms>=0
    assert filas[0]['BM25']>=filas[-1]['BM25']
    i=next(i for i,c in enumerate(datos['cvs']) if c['cv_id']==filas[0]['CV'])
    assert sum(contribuciones(modelo,i,consulta).values())==pytest.approx(filas[0]['BM25'])

def test_invalid(base):
    with pytest.raises(ValueError): analizar(base[0],base[1],'inexistente')

def test_auditoria(base):
    assert auditoria(base[0],base[1],'dev')['resumen']['pares_evaluados']==500
