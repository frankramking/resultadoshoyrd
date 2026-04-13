import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from datetime import datetime

URL = "https://loteriasdominicanas.com/"
URL_NACIONAL = "https://loteriasdominicanas.com/loteria-nacional"
URL_NUEVA_YORK = "https://loteriasdominicanas.com/nueva-york"
URL_LEIDSA = "https://loteriasdominicanas.com/leidsa"
URL_LOTEKA = "https://loteriasdominicanas.com/loteka"
URL_PRIMERA = "https://loteriasdominicanas.com/la-primera"
URL_ANGUILA = "https://loteriasdominicanas.com/anguila"
URL_LOTEDOM = "https://loteriasdominicanas.com/lotedom"
URL_KING_LOTTERY = "https://loteriasdominicanas.com/king-lottery"
URL_AMERICANAS = "https://loteriasdominicanas.com/americanas"
ARCHIVO_JSON = Path("resultados.json")
CARPETA_HISTORICOS = Path("historicos")
TIMEOUT = 20


def agregar_fecha_url(url: str, fecha: str | None) -> str:
    if not fecha:
        return url
    separador = "&" if "?" in url else "?"
    return f"{url}{separador}date={fecha}"


def descargar_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def limpiar_texto(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


def extraer_nacional(texto: str) -> dict | None:
    patron = re.compile(
        r"Nacional\s+"
        r"(\d{2}-\d{2})\s+"
        r"Juega \+ Pega \+\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+"
        r".*?"
        r"(\d{2}-\d{2})\s+"
        r"Gana Más\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+"
        r".*?"
        r"(\d{2}-\d{2})\s+"
        r"Lotería Nacional\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})",
        re.DOTALL
    )

    match = patron.search(texto)
    if not match:
        return None

    fecha_jp = match.group(1)
    fecha_gm = match.group(7)
    fecha_ln = match.group(11)

    if not (fecha_jp == fecha_gm == fecha_ln):
        print("⚠️ Las fechas no coinciden entre bloques de Nacional.")
        print(f"Juega+Pega+: {fecha_jp} | Gana Más: {fecha_gm} | Lotería Nacional: {fecha_ln}")
        return None

    data = {
        "fecha": fecha_jp,
        "juega_pega": [match.group(2), match.group(3), match.group(4), match.group(5), match.group(6)],
        "gana_mas": [match.group(8), match.group(9), match.group(10)],
        "loteria_nacional": [match.group(12), match.group(13), match.group(14)],
        "fecha_billetes_domingo": "",
        "billetes_domingo": [],
    }

    billetes = re.search(
        r"(\d{2}-\d{2})\s+Billetes Domingo\s+(\d{6})\s+(\d{6})\s+(\d{6})",
        texto,
        re.IGNORECASE,
    )

    if billetes:
        data["fecha_billetes_domingo"] = billetes.group(1)
        data["billetes_domingo"] = [billetes.group(2), billetes.group(3), billetes.group(4)]

    if len(data["juega_pega"]) != 5 or len(data["gana_mas"]) != 3 or len(data["loteria_nacional"]) != 3:
        print("⚠️ Cantidad de números incorrecta en Nacional.")
        return None

    return data


def extraer_leidsa(texto: str) -> dict | None:
    patron = re.compile(
        r"Leidsa\s+"
        r"(\d{2}-\d{2})\s+"
        r"Pega 3 Más\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+"
        r".*?"
        r"(\d{2}-\d{2})\s+"
        r"Quiniela Leidsa\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})",
        re.DOTALL
    )

    match = patron.search(texto)
    if not match:
        return None

    fecha_p3 = match.group(1)
    fecha_q = match.group(5)

    if fecha_p3 != fecha_q:
        print("⚠️ Las fechas no coinciden en Leidsa.")
        return None

    data = {
        "fecha": fecha_p3,
        "pega_3_mas": [match.group(2), match.group(3), match.group(4)],
        "quiniela_leidsa": [match.group(6), match.group(7), match.group(8)],
    }

    return data



def extraer_leidsa_completo(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"Leidsa\s+"
        r"(\d{2}-\d{2})\s+Pega 3 M\S+s\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+Quiniela Leidsa\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+Loto Pool\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+Super Kino TV\s+"
        r"((?:\d{2}\s+){19}\d{2})"
        r"\s+(\d{2}-\d{2})\s+Loto - Super Loto M\S+s\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+Super Pal\S+\s+"
        r"(\d{2})\s+(\d{2})",
        re.DOTALL
    )

    match = patron.search(texto)
    if not match:
        print("Debug Leidsa completo")
        print("No encontre el bloque completo de Leidsa.")
        return None

    return {
        "fecha": match.group(1),
        "pega_3_mas": [match.group(2), match.group(3), match.group(4)],
        "quiniela_leidsa": [match.group(6), match.group(7), match.group(8)],
        "fecha_loto_pool": match.group(9),
        "loto_pool": [match.group(10), match.group(11), match.group(12), match.group(13), match.group(14)],
        "fecha_super_kino": match.group(15),
        "super_kino_tv": match.group(16).split(),
        "fecha_loto_super_loto": match.group(17),
        "loto_super_loto_mas": [
            match.group(18),
            match.group(19),
            match.group(20),
            match.group(21),
            match.group(22),
            match.group(23),
            match.group(24),
            match.group(25),
        ],
        "fecha_super_pale": match.group(26),
        "super_pale": [match.group(27), match.group(28)],
    }


def extraer_real(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    # Quiniela Real
    qr = re.search(
        r"(\d{2}-\d{2})\s+Quiniela Real\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    # Loto Pool Real
    lp = re.search(
        r"Loter[ií]a Real\s+(\d{2}-\d{2})\s+Loto Pool\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    # Loto Real (6 números)
    lr = re.search(
        r"(\d{2}-\d{2})\s+Loto Real\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    # Loto Pool Noche (4 números)
    lpn = re.search(
        r"(\d{2}-\d{2})\s+Loto Pool Noche\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    if not qr or not lp or not lr or not lpn:
        print("⚠️ Debug Real")
        print("Quiniela Real encontrada:", bool(qr))
        print("Loto Pool Real encontrado:", bool(lp))
        print("Loto Real encontrado:", bool(lr))
        print("Loto Pool Noche encontrado:", bool(lpn))
        return None

    data = {
        "fecha": qr.group(1),
        "quiniela_real": [qr.group(2), qr.group(3), qr.group(4)],
        "loto_pool_real": [lp.group(2), lp.group(3), lp.group(4), lp.group(5)],
        "loto_real": [lr.group(2), lr.group(3), lr.group(4), lr.group(5), lr.group(6), lr.group(7)],
        "loto_pool_noche": [lpn.group(2), lpn.group(3), lpn.group(4), lpn.group(5)]
    }

    return data





def extraer_loteka(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    ql = re.search(
        r"(\d{2}-\d{2})\s+Quiniela Loteka\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    mc = re.search(
        r"(\d{2}-\d{2})\s+Mega Chances\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    ml = re.search(
        r"(\d{2}-\d{2})\s+MegaLotto\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        texto,
        re.IGNORECASE
    )

    if not ql or not mc or not ml:
        print("⚠️ Debug Loteka")
        print("Quiniela Loteka encontrada:", bool(ql))
        print("Mega Chances encontrada:", bool(mc))
        print("MegaLotto encontrada:", bool(ml))
        return None

    data = {
        "fecha": ql.group(1),
        "quiniela_loteka": [ql.group(2), ql.group(3), ql.group(4)],
        "mega_chance": [mc.group(2), mc.group(3), mc.group(4), mc.group(5), mc.group(6)],
        "megalotto": [ml.group(2), ml.group(3), ml.group(4), ml.group(5), ml.group(6), ml.group(7)]
    }

    return data



def extraer_loteka_completo(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"Loteka\s+"
        r"(\d{2}-\d{2})\s+Toca 3\s+"
        r"(\d)\s+(\d)\s+(\d)"
        r".*?"
        r"(\d{2}-\d{2})\s+Quiniela Loteka\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+Mega Chances\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+MC Repartidera\s+"
        r"(\d{2})"
        r"(?:\s+#\d+)?"
        r"\s+(\d{2}-\d{2})\s+MegaLotto\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug Loteka completo")
        print("No encontre el bloque completo de Loteka.")
        return None

    return {
        "fecha_toca_3": match.group(1),
        "toca_3": [match.group(2), match.group(3), match.group(4)],
        "fecha": match.group(5),
        "quiniela_loteka": [match.group(6), match.group(7), match.group(8)],
        "fecha_mega_chance": match.group(9),
        "mega_chance": [match.group(10), match.group(11), match.group(12), match.group(13), match.group(14)],
        "fecha_mc_repartidera": match.group(15),
        "mc_repartidera": [match.group(16)],
        "fecha_megalotto": match.group(17),
        "megalotto": [
            match.group(18),
            match.group(19),
            match.group(20),
            match.group(21),
            match.group(22),
            match.group(23),
            match.group(24),
            match.group(25),
        ],
    }


def extraer_primera(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"La Primera\s+.*?"
        r"(\d{2}-\d{2})\s+La Primera D[ií]a\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+Primera Noche\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+Loto 5\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("⚠️ Debug La Primera")
        print("No encontré La Primera Día, Primera Noche o Loto 5.")
        return None

    data = {
        "fecha_dia": match.group(1),
        "la_primera_dia": [match.group(2), match.group(3), match.group(4)],

        "fecha_noche": match.group(5),
        "primera_noche": [match.group(6), match.group(7), match.group(8)],

        "fecha_loto5": match.group(9),
        "loto_5": [
            match.group(10),
            match.group(11),
            match.group(12),
            match.group(13),
            match.group(14),
            match.group(15)
        ],
    }

    return data







def extraer_suerte(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"La Suerte\s+.*?"
        r"(\d{2}-\d{2})\s+La Suerte 12:30\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+La Suerte 18:00\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug La Suerte")
        print("No encontre La Suerte 12:30 o La Suerte 18:00.")
        return None

    data = {
        "fecha_1230": match.group(1),
        "la_suerte_1230": [match.group(2), match.group(3), match.group(4)],
        "fecha_1800": match.group(5),
        "la_suerte_1800": [match.group(6), match.group(7), match.group(8)],
    }

    return data


def extraer_primera_completo(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"La Primera\s+"
        r"(\d{2}-\d{2})\s+El Quiniel\S+n D\S+a\s+"
        r"(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+La Primera D\S+a\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+El Quiniel\S+n Noche\s+"
        r"(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+Primera Noche\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+Loto 5\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug La Primera completo")
        print("No encontre el bloque completo de La Primera.")
        return None

    return {
        "fecha_quinielon_dia": match.group(1),
        "quinielon_dia": [match.group(2)],
        "fecha_dia": match.group(3),
        "la_primera_dia": [match.group(4), match.group(5), match.group(6)],
        "fecha_quinielon_noche": match.group(7),
        "quinielon_noche": [match.group(8)],
        "fecha_noche": match.group(9),
        "primera_noche": [match.group(10), match.group(11), match.group(12)],
        "fecha_loto5": match.group(13),
        "loto_5": [
            match.group(14),
            match.group(15),
            match.group(16),
            match.group(17),
            match.group(18),
            match.group(19),
        ],
    }


def extraer_lotedom(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    def buscar(nombre: str, cantidad: int) -> tuple[str, list[str]] | None:
        patron = re.compile(
            rf"(\d{{2}}-\d{{2}})\s+{nombre}\s+"
            rf"((?:\d{{2}}\s+){{{cantidad - 1}}}\d{{2}})",
            re.IGNORECASE,
        )
        match = patron.search(texto)
        if not match:
            return None
        return match.group(1), match.group(2).split()

    patron = re.compile(
        r"LoteDom\s+.*?"
        r"(\d{2}-\d{2})\s+Quiniela LoteDom\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+El Quemaito Mayor\s+"
        r"(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug LoteDom")
        print("No encontre Quiniela LoteDom o El Quemaito Mayor.")
        return None

    data = {
        "fecha_quiniela": match.group(1),
        "quiniela_lotedom": [match.group(2), match.group(3), match.group(4)],
        "fecha_quemaito": match.group(5),
        "quemaito_mayor": [match.group(6)],
        "fecha_super_pale": "",
        "super_pale": [],
        "fecha_agarra_4": "",
        "agarra_4": [],
    }

    super_pale = buscar(r"Super Pal[ée]", 2)
    agarra_4 = buscar(r"Agarra 4", 4)

    if super_pale:
        data["fecha_super_pale"] = super_pale[0]
        data["super_pale"] = super_pale[1]

    if agarra_4:
        data["fecha_agarra_4"] = agarra_4[0]
        data["agarra_4"] = agarra_4[1]

    return data


def extraer_anguila(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    def buscar(nombre: str, cantidad: int) -> tuple[str, list[str]] | None:
        patron = re.compile(
            rf"(\d{{2}}-\d{{2}})\s+{nombre}\s+"
            rf"((?:\d{{2}}\s+){{{cantidad - 1}}}\d{{2}})",
            re.IGNORECASE,
        )
        match = patron.search(texto)
        if not match:
            return None
        return match.group(1), match.group(2).split()

    manana = buscar(r"Anguila Mañana", 3)
    cuarteta_manana = buscar(r"La Cuarteta Mañana", 4)
    medio_dia = buscar(r"Anguila Medio D[ií]a", 3)
    cuarteta_medio_dia = buscar(r"La Cuarteta Medio D[ií]a", 4)
    tarde = buscar(r"Anguila Tarde", 3)
    cuarteta_tarde = buscar(r"La Cuarteta Tarde", 4)
    noche = buscar(r"Anguila Noche", 3)
    cuarteta_noche = buscar(r"La Cuarteta Noche", 4)

    requeridos = [manana, medio_dia, tarde, noche]
    if not all(requeridos):
        print("Debug Anguila")
        print("No encontre Anguila Mañana, Medio Dia, Tarde o Noche.")
        return None

    data = {
        "fecha_manana": manana[0],
        "anguila_manana": manana[1],
        "fecha_cuarteta_manana": cuarteta_manana[0] if cuarteta_manana else "",
        "cuarteta_manana": cuarteta_manana[1] if cuarteta_manana else [],
        "fecha_medio_dia": medio_dia[0],
        "anguila_medio_dia": medio_dia[1],
        "fecha_cuarteta_medio_dia": cuarteta_medio_dia[0] if cuarteta_medio_dia else "",
        "cuarteta_medio_dia": cuarteta_medio_dia[1] if cuarteta_medio_dia else [],
        "fecha_tarde": tarde[0],
        "anguila_tarde": tarde[1],
        "fecha_cuarteta_tarde": cuarteta_tarde[0] if cuarteta_tarde else "",
        "cuarteta_tarde": cuarteta_tarde[1] if cuarteta_tarde else [],
        "fecha_noche": noche[0],
        "anguila_noche": noche[1],
        "fecha_cuarteta_noche": cuarteta_noche[0] if cuarteta_noche else "",
        "cuarteta_noche": cuarteta_noche[1] if cuarteta_noche else [],
    }

    return data


def extraer_king_lottery(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    def buscar(nombre: str, cantidad: int, digitos: int = 2) -> tuple[str, list[str]] | None:
        patron = re.compile(
            rf"(\d{{2}}-\d{{2}})\s+{nombre}\s+"
            rf"((?:\d{{{digitos}}}\s+){{{cantidad - 1}}}\d{{{digitos}}})",
            re.IGNORECASE,
        )
        match = patron.search(texto)
        if not match:
            return None
        return match.group(1), match.group(2).split()

    patron = re.compile(
        r"King Lottery\s+.*?"
        r"(\d{2}-\d{2})\s+King Lottery 12:30\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+King Lottery 7:30\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug King Lottery")
        print("No encontre King Lottery 12:30 o King Lottery 7:30.")
        return None

    data = {
        "fecha_1230": match.group(1),
        "king_1230": [match.group(2), match.group(3), match.group(4)],
        "fecha_730": match.group(5),
        "king_730": [match.group(6), match.group(7), match.group(8)],
        "fecha_pick3_dia": "",
        "pick3_dia": [],
        "fecha_pick4_dia": "",
        "pick4_dia": [],
        "fecha_philipsburg_medio_dia": "",
        "philipsburg_medio_dia": [],
        "fecha_loto_pool_medio_dia": "",
        "loto_pool_medio_dia": [],
        "fecha_pick3_noche": "",
        "pick3_noche": [],
        "fecha_pick4_noche": "",
        "pick4_noche": [],
        "fecha_philipsburg_noche": "",
        "philipsburg_noche": [],
        "fecha_loto_pool_noche": "",
        "loto_pool_noche": [],
    }

    extras = {
        "pick3_dia": buscar(r"Pick 3 D[ií]a", 3, 1),
        "pick4_dia": buscar(r"Pick 4 D[ií]a", 4, 1),
        "philipsburg_medio_dia": buscar(r"Philipsburg Medio D[ií]a", 3, 4),
        "loto_pool_medio_dia": buscar(r"Loto Pool Medio D[ií]a", 4),
        "pick3_noche": buscar(r"Pick 3 Noche", 3, 1),
        "pick4_noche": buscar(r"Pick 4 Noche", 4, 1),
        "philipsburg_noche": buscar(r"Philipsburg Noche", 3, 4),
        "loto_pool_noche": buscar(r"Loto Pool Noche", 4),
    }

    for clave, resultado in extras.items():
        if not resultado:
            continue
        data[f"fecha_{clave}"] = resultado[0]
        data[clave] = resultado[1]

    return data


def extraer_new_york(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"New York Tarde\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+New York Noche\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    fecha_tarde = re.search(
        r"(\d{2}-\d{2})\s+New York Tarde\s+"
        r"\d{2}\s+\d{2}\s+\d{2}",
        texto,
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match or not fecha_tarde:
        print("Debug New York")
        print("No encontre New York Tarde o New York Noche.")
        return None

    data = {
        "fecha_tarde": fecha_tarde.group(1),
        "new_york_tarde": [match.group(1), match.group(2), match.group(3)],
        "fecha_noche": match.group(4),
        "new_york_noche": [match.group(5), match.group(6), match.group(7)],
    }

    return data


def extraer_new_york_completo(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    patron = re.compile(
        r"Nueva York\s+"
        r"(\d{2}-\d{2})\s+Numbers Medio D[ií]a\s+"
        r"(\d)\s+(\d)\s+(\d)"
        r"\s+(\d{2}-\d{2})\s+Win 4 Medio D[ií]a\s+"
        r"(\d)\s+(\d)\s+(\d)\s+(\d)"
        r"\s+(\d{2}-\d{2})\s+Numbers Noche\s+"
        r"(\d)\s+(\d)\s+(\d)"
        r"\s+(\d{2}-\d{2})\s+Take 5 Midday\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+Win 4 Noche\s+"
        r"(\d)\s+(\d)\s+(\d)\s+(\d)"
        r"\s+(\d{2}-\d{2})\s+Take 5 Noche\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
        r"\s+(\d{2}-\d{2})\s+New York Lotto\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug New York completo")
        print("No encontre el bloque completo de Nueva York.")
        return None

    data = {
        "fecha_numbers_medio_dia": match.group(1),
        "numbers_medio_dia": [match.group(2), match.group(3), match.group(4)],
        "fecha_win4_medio_dia": match.group(5),
        "win4_medio_dia": [match.group(6), match.group(7), match.group(8), match.group(9)],
        "fecha_numbers_noche": match.group(10),
        "numbers_noche": [match.group(11), match.group(12), match.group(13)],
        "fecha_take5_midday": match.group(14),
        "take5_midday": [match.group(15), match.group(16), match.group(17), match.group(18), match.group(19)],
        "fecha_win4_noche": match.group(20),
        "win4_noche": [match.group(21), match.group(22), match.group(23), match.group(24)],
        "fecha_take5_noche": match.group(25),
        "take5_noche": [match.group(26), match.group(27), match.group(28), match.group(29), match.group(30)],
        "fecha_new_york_lotto": match.group(31),
        "new_york_lotto": [
            match.group(32),
            match.group(33),
            match.group(34),
            match.group(35),
            match.group(36),
            match.group(37),
            match.group(38),
        ],
    }

    return data


def extraer_americanas(texto: str) -> dict | None:
    texto = re.sub(r"\s+", " ", texto)

    def buscar(nombre: str, cantidad: int) -> tuple[str, list[str]] | None:
        patron = re.compile(
            rf"(\d{{2}}-\d{{2}})\s+{nombre}\s+"
            rf"((?:\d{{2}}\s+){{{cantidad - 1}}}\d{{2}})",
            re.IGNORECASE,
        )
        match = patron.search(texto)
        if not match:
            return None
        return match.group(1), match.group(2).split()

    patron = re.compile(
        r"Americanas\s+.*?"
        r"(\d{2}-\d{2})\s+Florida D[ií]a\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+Florida Noche\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+Mega Millions\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})"
        r".*?"
        r"(\d{2}-\d{2})\s+PowerBall\s+"
        r"(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\dX)",
        re.IGNORECASE
    )

    match = patron.search(texto)

    if not match:
        print("Debug Americanas")
        print("No encontre Florida, Mega Millions o PowerBall.")
        return None

    data = {
        "fecha_florida_dia": match.group(1),
        "florida_dia": [match.group(2), match.group(3), match.group(4)],
        "fecha_florida_noche": match.group(5),
        "florida_noche": [match.group(6), match.group(7), match.group(8)],
        "fecha_mega_millions": match.group(9),
        "mega_millions": [
            match.group(10),
            match.group(11),
            match.group(12),
            match.group(13),
            match.group(14),
            match.group(15),
        ],
        "fecha_powerball": match.group(16),
        "powerball": [
            match.group(17),
            match.group(18),
            match.group(19),
            match.group(20),
            match.group(21),
            match.group(22),
        ],
        "powerplay": match.group(23),
        "fecha_powerball_double_play": "",
        "powerball_double_play": [],
        "fecha_cash_4_life": "",
        "cash_4_life": [],
    }

    double_play = buscar(r"Powerball Double Play", 6)
    cash_4_life = buscar(r"Cash 4 Life", 6)

    if double_play:
        data["fecha_powerball_double_play"] = double_play[0]
        data["powerball_double_play"] = double_play[1]

    if cash_4_life:
        data["fecha_cash_4_life"] = cash_4_life[0]
        data["cash_4_life"] = cash_4_life[1]

    return data


def leer_json_existente(archivo: Path = ARCHIVO_JSON) -> dict:
    if archivo.exists():
        try:
            return json.loads(archivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"⚠️ {archivo} existe pero está dañado. Se recreará.")
    return {}


def guardar_json(data: dict, archivo: Path = ARCHIVO_JSON) -> None:
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main(fecha_consulta: str | None = None):
    archivo_salida = ARCHIVO_JSON
    if fecha_consulta:
        archivo_salida = CARPETA_HISTORICOS / f"resultados-{fecha_consulta}.json"

    print("🔄 Buscando resultados de Nacional...")
    if fecha_consulta:
        print(f"📅 Fecha solicitada: {fecha_consulta}")

    try:
        html = descargar_html(agregar_fecha_url(URL, fecha_consulta))
        texto = limpiar_texto(html)
        html_nacional = descargar_html(agregar_fecha_url(URL_NACIONAL, fecha_consulta))
        texto_nacional = limpiar_texto(html_nacional)
        html_leidsa = descargar_html(agregar_fecha_url(URL_LEIDSA, fecha_consulta))
        texto_leidsa = limpiar_texto(html_leidsa)
        html_loteka = descargar_html(agregar_fecha_url(URL_LOTEKA, fecha_consulta))
        texto_loteka = limpiar_texto(html_loteka)
        html_primera = descargar_html(agregar_fecha_url(URL_PRIMERA, fecha_consulta))
        texto_primera = limpiar_texto(html_primera)
        html_anguila = descargar_html(agregar_fecha_url(URL_ANGUILA, fecha_consulta))
        texto_anguila = limpiar_texto(html_anguila)
        html_lotedom = descargar_html(agregar_fecha_url(URL_LOTEDOM, fecha_consulta))
        texto_lotedom = limpiar_texto(html_lotedom)
        html_king_lottery = descargar_html(agregar_fecha_url(URL_KING_LOTTERY, fecha_consulta))
        texto_king_lottery = limpiar_texto(html_king_lottery)
        html_americanas = descargar_html(agregar_fecha_url(URL_AMERICANAS, fecha_consulta))
        texto_americanas = limpiar_texto(html_americanas)
        html_nueva_york = descargar_html(agregar_fecha_url(URL_NUEVA_YORK, fecha_consulta))
        texto_nueva_york = limpiar_texto(html_nueva_york)
        nacional = extraer_nacional(texto_nacional)
        leidsa = extraer_leidsa_completo(texto_leidsa)
        real = extraer_real(texto)
        loteka = extraer_loteka_completo(texto_loteka)
        primera = extraer_primera_completo(texto_primera)
        suerte = extraer_suerte(texto)
        lotedom = extraer_lotedom(texto_lotedom)
        anguila = extraer_anguila(texto_anguila)
        king_lottery = extraer_king_lottery(texto_king_lottery)
        new_york = extraer_new_york(texto)
        new_york_completo = extraer_new_york_completo(texto_nueva_york)
        americanas = extraer_americanas(texto_americanas)









        resultados_requeridos = [
            ("Nacional", nacional),
            ("Leidsa", leidsa),
            ("Lotería Real", real),
            ("Loteka", loteka),
            ("La Primera", primera),
            ("La Suerte", suerte),
            ("LoteDom", lotedom),
            ("Anguila", anguila),
            ("King Lottery", king_lottery),
            ("New York", new_york),
            ("New York completo", new_york_completo),
            ("Americanas", americanas),
        ]

        for nombre, resultado in resultados_requeridos:
            if resultado:
                continue

            print(f"❌ No pude encontrar o validar los resultados de {nombre}.")
            if not fecha_consulta:
                return

            print("⚠️ Como es una fecha histórica, voy a guardar el archivo con las demás loterías encontradas.")


        data_actual = leer_json_existente(archivo_salida)

        # 🧠 comparar con lo anterior
        nacional_anterior = data_actual.get("nacional")
        leidsa_anterior = data_actual.get("leidsa")
        real_anterior = data_actual.get("real")
        loteka_anterior = data_actual.get("loteka")
        primera_anterior = data_actual.get("primera")
        suerte_anterior = data_actual.get("suerte")
        lotedom_anterior = data_actual.get("lotedom")
        anguila_anterior = data_actual.get("anguila")
        king_lottery_anterior = data_actual.get("king_lottery")
        new_york_anterior = data_actual.get("new_york")
        new_york_completo_anterior = data_actual.get("new_york_completo")
        americanas_anterior = data_actual.get("americanas")


        sin_cambios_nacional = nacional_anterior == nacional
        sin_cambios_leidsa = leidsa_anterior == leidsa
        sin_cambios_real = real_anterior == real
        sin_cambios_loteka = loteka_anterior == loteka
        sin_cambios_primera = primera_anterior == primera
        sin_cambios_suerte = suerte_anterior == suerte
        sin_cambios_lotedom = lotedom_anterior == lotedom
        sin_cambios_anguila = anguila_anterior == anguila
        sin_cambios_king_lottery = king_lottery_anterior == king_lottery
        sin_cambios_new_york = new_york_anterior == new_york
        sin_cambios_new_york_completo = new_york_completo_anterior == new_york_completo
        sin_cambios_americanas = americanas_anterior == americanas


        if sin_cambios_nacional and sin_cambios_leidsa and sin_cambios_real and sin_cambios_loteka and sin_cambios_primera and sin_cambios_suerte and sin_cambios_lotedom and sin_cambios_anguila and sin_cambios_king_lottery and sin_cambios_new_york and sin_cambios_new_york_completo and sin_cambios_americanas:
            print("No hay cambios en Nacional, Leidsa, Real, Loteka, La Primera, La Suerte, LoteDom, Anguila, King Lottery, New York ni Americanas.")
            return


        # 🔄 si cambió, actualiza
        data_actual["actualizado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_actual["nacional"] = nacional
        data_actual["leidsa"] = leidsa
        data_actual["real"] = real
        data_actual["loteka"] = loteka
        data_actual["primera"] = primera
        data_actual["suerte"] = suerte
        data_actual["lotedom"] = lotedom
        data_actual["anguila"] = anguila
        data_actual["king_lottery"] = king_lottery
        data_actual["new_york"] = new_york
        data_actual["new_york_completo"] = new_york_completo
        data_actual["americanas"] = americanas

        guardar_json(data_actual, archivo_salida)
        print(f"💾 Guardado en {archivo_salida}")

        if nacional and not sin_cambios_nacional:
            print(f"📅 Nacional fecha: {nacional['fecha']}")
            print(f"🎯 Juega + Pega +: {nacional['juega_pega']}")
            print(f"🎯 Gana Más: {nacional['gana_mas']}")
            print(f"🎯 Lotería Nacional: {nacional['loteria_nacional']}")
            if nacional.get("billetes_domingo"):
                print(f"📅 Billetes Domingo fecha: {nacional['fecha_billetes_domingo']}")
                print(f"🎯 Billetes Domingo: {nacional['billetes_domingo']}")


        if leidsa and not sin_cambios_leidsa:
            print(f"📅 Leidsa fecha: {leidsa['fecha']}")
            print(f"🎯 Pega 3 Más: {leidsa['pega_3_mas']}")
            print(f"🎯 Quiniela Leidsa: {leidsa['quiniela_leidsa']}")
            print(f"🎯 Loto Pool: {leidsa['loto_pool']}")
            print(f"🎯 Super Kino TV: {leidsa['super_kino_tv']}")
            print(f"🎯 Loto - Super Loto Más: {leidsa['loto_super_loto_mas']}")
            print(f"🎯 Super Palé: {leidsa['super_pale']}")


        if real and not sin_cambios_real:
            print(f"📅 Real fecha: {real['fecha']}")
            print(f"🎯 Quiniela Real: {real['quiniela_real']}")
            print(f"🎯 Loto Pool Real: {real['loto_pool_real']}")
            print(f"🎯 Loto Real: {real['loto_real']}")
            print(f"🎯 Loto Pool Noche: {real['loto_pool_noche']}")

        if loteka and not sin_cambios_loteka:
            print(f"📅 Loteka fecha: {loteka['fecha']}")
            print(f"🎯 Toca 3: {loteka['toca_3']}")
            print(f"🎯 Quiniela Loteka: {loteka['quiniela_loteka']}")
            print(f"🎯 Mega Chances: {loteka['mega_chance']}")
            print(f"🎯 MC Repartidera: {loteka['mc_repartidera']}")
            print(f"🎯 MegaLotto: {loteka['megalotto']}")

        if primera and not sin_cambios_primera:
            print(f"📅 El Quinielon Dia fecha: {primera['fecha_quinielon_dia']}")
            print(f"🎯 El Quinielon Dia: {primera['quinielon_dia']}")
            print(f"📅 La Primera Dia fecha: {primera['fecha_dia']}")
            print(f"🎯 La Primera Dia: {primera['la_primera_dia']}")
            print(f"📅 El Quinielon Noche fecha: {primera['fecha_quinielon_noche']}")
            print(f"🎯 El Quinielon Noche: {primera['quinielon_noche']}")
            print(f"📅 Primera Noche fecha: {primera['fecha_noche']}")
            print(f"🎯 Primera Noche: {primera['primera_noche']}")
            print(f"📅 Loto 5 fecha: {primera['fecha_loto5']}")
            print(f"🎯 Loto 5: {primera['loto_5']}")

        if suerte and not sin_cambios_suerte:
            print(f"📅 La Suerte 12:30 fecha: {suerte['fecha_1230']}")
            print(f"🎯 La Suerte 12:30: {suerte['la_suerte_1230']}")
            print(f"📅 La Suerte 18:00 fecha: {suerte['fecha_1800']}")
            print(f"🎯 La Suerte 18:00: {suerte['la_suerte_1800']}")

        if lotedom and not sin_cambios_lotedom:
            print(f"📅 Quiniela LoteDom fecha: {lotedom['fecha_quiniela']}")
            print(f"🎯 Quiniela LoteDom: {lotedom['quiniela_lotedom']}")
            print(f"📅 El Quemaito Mayor fecha: {lotedom['fecha_quemaito']}")
            print(f"🎯 El Quemaito Mayor: {lotedom['quemaito_mayor']}")

        if anguila and not sin_cambios_anguila:
            print(f"📅 Anguila Mañana fecha: {anguila['fecha_manana']}")
            print(f"🎯 Anguila Mañana: {anguila['anguila_manana']}")
            print(f"📅 Anguila Medio Dia fecha: {anguila['fecha_medio_dia']}")
            print(f"🎯 Anguila Medio Dia: {anguila['anguila_medio_dia']}")
            print(f"📅 Anguila Tarde fecha: {anguila['fecha_tarde']}")
            print(f"🎯 Anguila Tarde: {anguila['anguila_tarde']}")
            print(f"📅 Anguila Noche fecha: {anguila['fecha_noche']}")
            print(f"🎯 Anguila Noche: {anguila['anguila_noche']}")

        if king_lottery and not sin_cambios_king_lottery:
            print(f"📅 King Lottery 12:30 fecha: {king_lottery['fecha_1230']}")
            print(f"🎯 King Lottery 12:30: {king_lottery['king_1230']}")
            print(f"📅 King Lottery 7:30 fecha: {king_lottery['fecha_730']}")
            print(f"🎯 King Lottery 7:30: {king_lottery['king_730']}")

        if new_york and not sin_cambios_new_york:
            print(f"📅 New York Tarde fecha: {new_york['fecha_tarde']}")
            print(f"🎯 New York Tarde: {new_york['new_york_tarde']}")
            print(f"📅 New York Noche fecha: {new_york['fecha_noche']}")
            print(f"🎯 New York Noche: {new_york['new_york_noche']}")

        if new_york_completo and not sin_cambios_new_york_completo:
            print(f"📅 Numbers Medio Dia fecha: {new_york_completo['fecha_numbers_medio_dia']}")
            print(f"🎯 Numbers Medio Dia: {new_york_completo['numbers_medio_dia']}")
            print(f"📅 Win 4 Medio Dia fecha: {new_york_completo['fecha_win4_medio_dia']}")
            print(f"🎯 Win 4 Medio Dia: {new_york_completo['win4_medio_dia']}")
            print(f"📅 Numbers Noche fecha: {new_york_completo['fecha_numbers_noche']}")
            print(f"🎯 Numbers Noche: {new_york_completo['numbers_noche']}")
            print(f"📅 Take 5 Midday fecha: {new_york_completo['fecha_take5_midday']}")
            print(f"🎯 Take 5 Midday: {new_york_completo['take5_midday']}")
            print(f"📅 Win 4 Noche fecha: {new_york_completo['fecha_win4_noche']}")
            print(f"🎯 Win 4 Noche: {new_york_completo['win4_noche']}")
            print(f"📅 Take 5 Noche fecha: {new_york_completo['fecha_take5_noche']}")
            print(f"🎯 Take 5 Noche: {new_york_completo['take5_noche']}")
            print(f"📅 New York Lotto fecha: {new_york_completo['fecha_new_york_lotto']}")
            print(f"🎯 New York Lotto: {new_york_completo['new_york_lotto']}")

        if americanas and not sin_cambios_americanas:
            print(f"📅 Florida Dia fecha: {americanas['fecha_florida_dia']}")
            print(f"🎯 Florida Dia: {americanas['florida_dia']}")
            print(f"📅 Florida Noche fecha: {americanas['fecha_florida_noche']}")
            print(f"🎯 Florida Noche: {americanas['florida_noche']}")
            print(f"📅 Mega Millions fecha: {americanas['fecha_mega_millions']}")
            print(f"🎯 Mega Millions: {americanas['mega_millions']}")
            print(f"📅 PowerBall fecha: {americanas['fecha_powerball']}")
            print(f"🎯 PowerBall: {americanas['powerball']} {americanas['powerplay']}")


    except requests.RequestException as e:
        print(f"❌ Error de red: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    fecha_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(fecha_arg)
