"""Generador de ofertas y hojas de vida (CVs) sintéticas en español.

Qué produce (en la carpeta de salida, por defecto ``data/``):
    ofertas.csv      10 ofertas de trabajo, una por rol, con su partición (dev/test).
    cvs.csv          CVs sintéticos: ``n_cvs_base`` originales + ``n_gemelos`` gemelos.
    relevancia.csv   Relevancia (0 a 3) de cada par (oferta, CV), calculada con una
                     regla fija definida en ``relevancia()``.
    metadatos.json   Semilla, conteos, versión de Python y huellas SHA-256 de los CSV.

Ideas de diseño:
    * Cada CV nace de un perfil latente (rol, años, habilidades). El texto se escribe
      después, con sinónimos y frases distintas, para que la coincidencia exacta de
      palabras no resuelva el problema por sí sola.
    * La relevancia se calcula con el perfil latente, NUNCA con el texto ni con el
      género. Por eso, cualquier diferencia de trato por género en un ranking es sesgo
      del modelo y no una diferencia real entre candidatos.
    * Un "gemelo" es el mismo CV con otro nombre de pila del género opuesto y las
      palabras con género gramatical cambiadas (ingeniero/ingeniera, etc.).
      Lo demás es idéntico, lo que permite la prueba contrafactual.

Uso:
    python -m src.generar_datos
    python -m src.generar_datos --config configs/generacion.json --salida data

Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
import re
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
VERSION_GENERADOR = "1.0.0"

# Palabras cuya forma cambia con el género. En las plantillas se escriben como
# {clave} (minúscula) o {Clave} (con mayúscula inicial).
GENERO_FORMAS = {
    "desarrollador": ("desarrollador", "desarrolladora"),
    "enfermero": ("enfermero", "enfermera"),
    "contador": ("contador", "contadora"),
    "ingeniero": ("ingeniero", "ingeniera"),
    "comprometido": ("comprometido", "comprometida"),
    "orientado": ("orientado", "orientada"),
    "motivado": ("motivado", "motivada"),
    "egresado": ("egresado", "egresada"),
    "encargado": ("encargado", "encargada"),
}

FRASES_EXPERIENCIA = [
    "Responsable de {lista} en {ctx}.",
    "Apoyo a {ctx} con {lista}.",
    "Uso diario de {lista}; trabajo en equipo con otras áreas.",
    "Participación en {ctx} aplicando {lista}.",
    "{Encargado} de tareas relacionadas con {lista}.",
    "Colaboré en {ctx} y mejoré procesos mediante {lista}.",
]

FRASES_PERFIL = [
    "Profesional {comprometido} con {anios_txt} de experiencia, {orientado} a resultados.",
    "{Egresado} de {estudio}, {motivado} por aprender y aportar en {ctx}.",
    "Persona responsable y organizada, con {anios_txt} de trayectoria en {ctx}.",
]

NIVELES_INGLES = ["básico", "intermedio", "avanzado"]

_PATRON_MARCA = re.compile(r"\{([A-Za-z_]+)\}")


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def aplicar_genero(plantilla: str, genero: str) -> str:
    """Reemplaza las marcas de género ({enfermero}, {Egresado}, ...) según ``genero``.

    ``genero`` es "M" o "F". Las marcas que no son de género se dejan intactas.
    """
    idx = 0 if genero == "M" else 1

    def _sustituir(m: re.Match) -> str:
        clave = m.group(1)
        formas = GENERO_FORMAS.get(clave.lower())
        if formas is None:
            return m.group(0)
        forma = formas[idx]
        return forma[0].upper() + forma[1:] if clave[0].isupper() else forma

    return _PATRON_MARCA.sub(_sustituir, plantilla)


def neutralizar(texto: str, nombre: str) -> str:
    """Devuelve el texto sin el nombre y sin las formas con género.

    Sirve para comprobar que un CV y su gemelo solo difieren en esas cosas.
    """
    t = texto.replace(nombre, "NOMBRE").lower()
    for clave, (masc, fem) in GENERO_FORMAS.items():
        t = re.sub(rf"\b(?:{masc}|{fem})\b", f"<{clave}>", t)
    return t


def lista_en_texto(items: list[str]) -> str:
    """Une elementos con comas y una 'y' final (o 'e' si el siguiente empieza por i/hi)."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    ultimo = items[-1]
    minus = ultimo.lower()
    conj = "e" if (minus.startswith("i") or (minus.startswith("hi") and not minus.startswith("hie"))) else "y"
    return ", ".join(items[:-1]) + f" {conj} " + ultimo


def anios_en_texto(n: int) -> str:
    if n < 1:
        return "formación reciente"
    return "1 año" if n == 1 else f"{n} años"


def cargar_json(ruta: Path | str) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Validación del catálogo
# ---------------------------------------------------------------------------
def validar_catalogo(cat: dict, cfg: dict) -> None:
    """Lanza ValueError si el catálogo o la configuración son incoherentes."""
    habilidades = cat["habilidades"]
    for h, formas in habilidades.items():
        if len(formas) < 2:
            raise ValueError(f"La habilidad '{h}' necesita al menos 2 formas de escribirse")
    roles_en_sectores = []
    for sid, sector in cat["sectores"].items():
        for rid in sector["roles"]:
            if rid not in cat["roles"]:
                raise ValueError(f"El sector '{sid}' menciona un rol inexistente: {rid}")
            if cat["roles"][rid]["sector"] != sid:
                raise ValueError(f"El rol '{rid}' no coincide con el sector '{sid}'")
            roles_en_sectores.append(rid)
    if sorted(roles_en_sectores) != sorted(cat["roles"]):
        raise ValueError("Todos los roles deben aparecer exactamente una vez en un sector")
    for rid, rol in cat["roles"].items():
        for h in rol["nucleo"] + rol["opcional"]:
            if h not in habilidades:
                raise ValueError(f"El rol '{rid}' usa una habilidad inexistente: {h}")
        if len(rol["nucleo"]) != 5:
            raise ValueError(f"El rol '{rid}' debe tener 5 habilidades núcleo")
    particion = cfg["particion_ofertas"]
    asignados = sorted(particion["dev"] + particion["test"])
    if asignados != sorted(cat["roles"]):
        raise ValueError("Cada rol debe estar exactamente una vez en 'dev' o en 'test'")
    n_roles = len(cat["roles"])
    if cfg["n_cvs_base"] % n_roles != 0:
        raise ValueError("n_cvs_base debe ser múltiplo del número de roles")
    if cfg["n_gemelos"] % n_roles != 0:
        raise ValueError("n_gemelos debe ser múltiplo del número de roles")
    if cfg["n_gemelos"] // n_roles > cfg["n_cvs_base"] // n_roles:
        raise ValueError("No puede haber más gemelos que CVs por rol")


# ---------------------------------------------------------------------------
# Ofertas
# ---------------------------------------------------------------------------
def construir_oferta(num: int, rol_id: str, cat: dict, cfg: dict) -> dict:
    rol = cat["roles"][rol_id]
    sector = cat["sectores"][rol["sector"]]
    nucleo = [cat["habilidades"][h][0] for h in rol["nucleo"]]
    opcional = [cat["habilidades"][h][0] for h in rol["opcional"]]
    particion = "dev" if rol_id in cfg["particion_ofertas"]["dev"] else "test"
    texto = (
        f"Se busca {rol['oferta_titulo']} para el sector de {sector['nombre'].lower()}. "
        f"Trabajará en {sector['contextos'][0]}.\n"
        f"Requisitos: experiencia mínima de {rol['min_anios']} años; "
        f"conocimientos en {lista_en_texto(nucleo)}.\n"
        f"Deseable: {lista_en_texto(opcional)}."
    )
    return {
        "oferta_id": f"of_{num:02d}",
        "rol": rol_id,
        "sector": rol["sector"],
        "titulo": rol["oferta_titulo"],
        "min_anios": rol["min_anios"],
        "nucleo": list(rol["nucleo"]),
        "opcional": list(rol["opcional"]),
        "particion": particion,
        "texto": texto,
    }


# ---------------------------------------------------------------------------
# Perfil latente y relevancia
# ---------------------------------------------------------------------------
def generar_latente(rng: random.Random, rol_id: str, cfg: dict, cat: dict) -> dict:
    """Sortea el perfil de un candidato: calidad, habilidades y años de experiencia."""
    rol = cat["roles"][rol_id]
    pesos = cfg["calidad_pesos"]
    calidad = rng.choices(list(pesos), weights=list(pesos.values()))[0]
    p_nucleo = cfg["prob_habilidad_nucleo"][calidad]

    habilidades = [h for h in rol["nucleo"] if rng.random() < p_nucleo]
    habilidades += [h for h in rol["opcional"] if h not in habilidades and rng.random() < cfg["prob_opcional"]]
    for otro_id in cat["sectores"][rol["sector"]]["roles"]:
        if otro_id == rol_id:
            continue
        for h in cat["roles"][otro_id]["nucleo"]:
            if h not in habilidades and rng.random() < cfg["prob_transversal"]:
                habilidades.append(h)
    if not habilidades:
        habilidades.append(rng.choice(rol["nucleo"]))

    a = cfg["anios"]
    anios = min(a["max"], int(rng.triangular(a["min"], a["max"] + 1, a["moda"])))
    return {
        "rol": rol_id,
        "sector": rol["sector"],
        "anios": anios,
        "calidad": calidad,
        "habilidades": sorted(set(habilidades)),
    }


def relevancia(cv: dict, oferta: dict, umbrales: dict) -> int:
    """Relevancia (0 a 3) de un CV para una oferta. NO usa el género ni el texto.

    3 = mismo rol, cubre >= 80 % de las habilidades requeridas y cumple la experiencia mínima.
    2 = mismo rol y cubre >= 60 % de las habilidades requeridas.
    1 = mismo rol y cubre >= 40 %, o mismo sector y cubre >= 60 %.
    0 = cualquier otro caso.
    (Los porcentajes salen de ``umbrales`` y se fijan en configs/generacion.json.)
    """
    nucleo = set(oferta["nucleo"])
    cobertura = len(set(cv["habilidades"]) & nucleo) / len(nucleo)
    eps = 1e-9
    mismo_rol = cv["rol"] == oferta["rol"]
    mismo_sector = cv["sector"] == oferta["sector"]
    experiencia_ok = cv["anios"] >= oferta["min_anios"]

    if mismo_rol and cobertura + eps >= umbrales["cobertura_3"] and experiencia_ok:
        return 3
    if mismo_rol and cobertura + eps >= umbrales["cobertura_2"]:
        return 2
    if (mismo_rol and cobertura + eps >= umbrales["cobertura_1"]) or (
        mismo_sector and cobertura + eps >= umbrales["cobertura_1_mismo_sector"]
    ):
        return 1
    return 0


# ---------------------------------------------------------------------------
# Redacción del CV
# ---------------------------------------------------------------------------
def _repartir_anios(rng: random.Random, anios: int) -> list[int]:
    """Divide los años de experiencia en 1 a 3 cargos consecutivos (cada uno >= 1 año)."""
    if anios < 3:
        return [anios]
    k = rng.choice([2, 3])
    cortes = sorted(rng.sample(range(1, anios), k - 1))
    puntos = [0] + cortes + [anios]
    return [puntos[i + 1] - puntos[i] for i in range(k)]


def renderizar_cv(latente: dict, nombre: str, genero: str, cat: dict, cfg: dict, semilla: str) -> str:
    """Escribe el texto del CV. Todas las decisiones al azar dependen solo de ``semilla``.

    Importante: el género NO consume números aleatorios; solo cambia las palabras con
    género gramatical y el nombre. Por eso un CV y su gemelo (misma semilla) quedan
    idénticos salvo por esos elementos.
    """
    rng = random.Random(semilla)
    rol = cat["roles"][latente["rol"]]
    sector = cat["sectores"][rol["sector"]]
    ref = cfg["anio_referencia"]
    anios = latente["anios"]

    forma = {h: rng.choice(cat["habilidades"][h]) for h in latente["habilidades"]}
    estudio = rng.choice(rol["estudios"])
    institucion = f"{rng.choice(cat['instituciones']['prefijos'])} {rng.choice(cat['instituciones']['sufijos'])}"
    anio_grado = ref - anios - rng.randint(0, 1)
    ctx_perfil = rng.choice(sector["contextos"])
    frase_perfil = rng.choice(FRASES_PERFIL)

    perfil = frase_perfil.format_map(
        _Seguro(anios_txt=anios_en_texto(anios), estudio=estudio, ctx=ctx_perfil)
    )

    # Cargos (del más antiguo al más reciente)
    cargos = []
    if anios < 1:
        duraciones = [1]
        titulos = ["Práctica profesional"]
        inicios = [ref - 1]
    else:
        duraciones = _repartir_anios(rng, anios)
        titulos = []
        for i in range(len(duraciones)):
            if len(duraciones) > 1 and i == 0:
                titulos.append(rol["junior"])
            else:
                titulos.append(rng.choice(rol["titulos"]))
        inicios = []
        acumulado = 0
        for d in duraciones:
            inicios.append(ref - anios + acumulado)
            acumulado += d

    for i, (titulo, ini, dur) in enumerate(zip(titulos, inicios, duraciones)):
        es_ultimo = i == len(duraciones) - 1
        fin = "actualidad" if es_ultimo else str(ini + dur)
        empresa = f"{rng.choice(cat['empresas']['prefijos'])} {rng.choice(cat['empresas']['sufijos'])}"
        n_hab = min(len(latente["habilidades"]), rng.choice([2, 3]))
        elegidas = rng.sample(latente["habilidades"], n_hab)
        descripcion = rng.choice(FRASES_EXPERIENCIA).format_map(
            _Seguro(lista=lista_en_texto([forma[h] for h in elegidas]), ctx=rng.choice(sector["contextos"]))
        )
        cargos.append((titulo, empresa, ini, fin, descripcion))

    orden_hab = list(latente["habilidades"])
    rng.shuffle(orden_hab)
    nivel_ingles = rng.choice(NIVELES_INGLES)

    titulo_actual = cargos[-1][0]
    lineas = [
        nombre,
        aplicar_genero(titulo_actual, genero),
        "",
        "PERFIL",
        aplicar_genero(perfil, genero),
        "",
        "EDUCACIÓN",
        f"- {estudio}, {institucion} ({anio_grado})",
        "",
        "EXPERIENCIA",
    ]
    for titulo, empresa, ini, fin, descripcion in reversed(cargos):
        lineas.append(f"- {aplicar_genero(titulo, genero)}, {empresa} ({ini}-{fin}): {aplicar_genero(descripcion, genero)}")
    lineas += [
        "",
        "HABILIDADES",
        ", ".join(forma[h] for h in orden_hab),
        "",
        "IDIOMAS",
        f"Español (nativo); inglés ({nivel_ingles})",
    ]
    return "\n".join(lineas)


class _Seguro(dict):
    """format_map que deja intactas las marcas de género para resolverlas después."""

    def __missing__(self, clave: str) -> str:
        return "{" + clave + "}"


# ---------------------------------------------------------------------------
# Nombres
# ---------------------------------------------------------------------------
def nombre_completo(semilla: str, indice: int, genero: str, cat: dict) -> str:
    """Nombre ficticio. Los apellidos no dependen del género (los gemelos los comparten)."""
    apellidos = random.Random(f"{semilla}-apellidos-{indice}").sample(cat["apellidos"], 2)
    pila = random.Random(f"{semilla}-pila-{indice}-{genero}").choice(cat["nombres"][genero])
    return f"{pila} {apellidos[0]} {apellidos[1]}"


# ---------------------------------------------------------------------------
# Generación completa
# ---------------------------------------------------------------------------
def generar(cfg: dict, cat: dict) -> dict:
    """Crea en memoria ofertas, CVs y relevancias. No escribe archivos."""
    validar_catalogo(cat, cfg)
    semilla = cfg["semilla"]
    roles = list(cat["roles"])
    n_roles = len(roles)
    n_base = cfg["n_cvs_base"]

    ofertas = [construir_oferta(j, rol_id, cat, cfg) for j, rol_id in enumerate(roles, start=1)]

    # Un rol por CV, repartido parejo y mezclado para que el orden no delate el rol.
    asignacion = [roles[i % n_roles] for i in range(n_base)]
    random.Random(f"{semilla}-orden").shuffle(asignacion)

    # Género balanceado dentro de cada rol.
    generos = [""] * n_base
    for rol_id in roles:
        indices = [i for i, r in enumerate(asignacion) if r == rol_id]
        mitad = len(indices) // 2
        asignados = ["F"] * mitad + ["M"] * (len(indices) - mitad)
        random.Random(f"{semilla}-generos-{rol_id}").shuffle(asignados)
        for i, g in zip(indices, asignados):
            generos[i] = g

    # Gemelos: la misma cantidad por rol.
    por_rol = cfg["n_gemelos"] // n_roles
    con_gemelo = set()
    for rol_id in roles:
        indices = [i for i, r in enumerate(asignacion) if r == rol_id]
        elegidos = random.Random(f"{semilla}-gemelos-{rol_id}").sample(indices, por_rol)
        con_gemelo.update(elegidos)

    cvs = []
    gemelos = []
    for i, rol_id in enumerate(asignacion):
        cv_id = f"cv_{i + 1:03d}"
        latente = generar_latente(random.Random(f"{semilla}-latente-{i}"), rol_id, cfg, cat)
        semilla_render = f"{semilla}-render-{i}"
        genero = generos[i]
        nombre = nombre_completo(str(semilla), i, genero, cat)
        base = {
            "cv_id": cv_id,
            "grupo_id": cv_id,
            "es_gemelo": 0,
            "sector": latente["sector"],
            "rol": latente["rol"],
            "anios": latente["anios"],
            "genero": genero,
            "nombre": nombre,
            "calidad": latente["calidad"],
            "habilidades": latente["habilidades"],
            "texto": renderizar_cv(latente, nombre, genero, cat, cfg, semilla_render),
        }
        cvs.append(base)
        if i in con_gemelo:
            genero_g = "M" if genero == "F" else "F"
            nombre_g = nombre_completo(str(semilla), i, genero_g, cat)
            gemelo = dict(base)
            gemelo.update(
                {
                    "cv_id": f"{cv_id}_g",
                    "es_gemelo": 1,
                    "genero": genero_g,
                    "nombre": nombre_g,
                    "texto": renderizar_cv(latente, nombre_g, genero_g, cat, cfg, semilla_render),
                }
            )
            gemelos.append(gemelo)

    todos = cvs + gemelos
    pares = []
    for oferta in ofertas:
        for cv in todos:
            pares.append(
                {
                    "oferta_id": oferta["oferta_id"],
                    "cv_id": cv["cv_id"],
                    "relevancia": relevancia(cv, oferta, cfg["relevancia"]),
                }
            )
    return {"ofertas": ofertas, "cvs": todos, "relevancia": pares}


# ---------------------------------------------------------------------------
# Escritura de archivos
# ---------------------------------------------------------------------------
def _escribir_csv(ruta: Path, columnas: list[str], filas: list[dict]) -> None:
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({c: fila[c] for c in columnas})


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def escribir_salida(datos: dict, cfg: dict, salida: Path) -> dict:
    """Guarda los CSV y metadatos.json. Devuelve el diccionario de metadatos."""
    salida.mkdir(parents=True, exist_ok=True)

    ofertas = [dict(o, nucleo="|".join(o["nucleo"]), opcional="|".join(o["opcional"])) for o in datos["ofertas"]]
    cvs = [dict(c, habilidades="|".join(c["habilidades"])) for c in datos["cvs"]]

    _escribir_csv(
        salida / "ofertas.csv",
        ["oferta_id", "rol", "sector", "titulo", "min_anios", "nucleo", "opcional", "particion", "texto"],
        ofertas,
    )
    _escribir_csv(
        salida / "cvs.csv",
        ["cv_id", "grupo_id", "es_gemelo", "sector", "rol", "anios", "genero", "nombre", "calidad", "habilidades", "texto"],
        cvs,
    )
    _escribir_csv(salida / "relevancia.csv", ["oferta_id", "cv_id", "relevancia"], datos["relevancia"])

    conteo_rel = {str(n): 0 for n in range(4)}
    for par in datos["relevancia"]:
        conteo_rel[str(par["relevancia"])] += 1
    conteo_gen = {"F": 0, "M": 0}
    for cv in datos["cvs"]:
        conteo_gen[cv["genero"]] += 1

    metadatos = {
        "version_generador": VERSION_GENERADOR,
        "semilla": cfg["semilla"],
        "fecha_generacion_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "python": platform.python_version(),
        "n_ofertas": len(datos["ofertas"]),
        "n_cvs_base": cfg["n_cvs_base"],
        "n_gemelos": cfg["n_gemelos"],
        "n_cvs_total": len(datos["cvs"]),
        "n_pares": len(datos["relevancia"]),
        "pares_por_nivel_relevancia": conteo_rel,
        "cvs_por_genero": conteo_gen,
        "umbrales_relevancia": cfg["relevancia"],
        "sha256": {nombre: _sha256(salida / nombre) for nombre in ["ofertas.csv", "cvs.csv", "relevancia.csv"]},
    }
    with open(salida / "metadatos.json", "w", encoding="utf-8") as f:
        json.dump(metadatos, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return metadatos


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="Genera ofertas y CVs sintéticos en español.")
    parser.add_argument("--config", default=str(RAIZ / "configs" / "generacion.json"))
    parser.add_argument("--catalogo", default=str(RAIZ / "configs" / "catalogo.json"))
    parser.add_argument("--salida", default=str(RAIZ / "data"))
    args = parser.parse_args(argv)

    cfg = cargar_json(args.config)
    cat = cargar_json(args.catalogo)
    datos = generar(cfg, cat)
    meta = escribir_salida(datos, cfg, Path(args.salida))

    print(f"Datos generados en: {args.salida}")
    print(f"  Ofertas: {meta['n_ofertas']} | CVs: {meta['n_cvs_total']} "
          f"({meta['n_cvs_base']} base + {meta['n_gemelos']} gemelos) | Pares: {meta['n_pares']}")
    print(f"  Pares por nivel de relevancia: {meta['pares_por_nivel_relevancia']}")
    print(f"  CVs por género: {meta['cvs_por_genero']}")
    for nombre, huella in meta["sha256"].items():
        print(f"  sha256 {nombre}: {huella[:16]}...")
    return meta


if __name__ == "__main__":
    main()
