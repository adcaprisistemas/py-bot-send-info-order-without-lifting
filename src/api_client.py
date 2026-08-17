from datetime import datetime
from html import escape

from src.config import config
from src.email_service import enviar_correo_html
from src.logger import setup_logger

logger = setup_logger()


def get_session():
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()

    retry = Retry(
        total=config.MAX_REINTENTOS,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"Content-Type": "application/json"})

    if config.API_TOKEN:
        session.headers.update({"Authorization": f"Bearer {config.API_TOKEN}"})

    return session


def obtener_ordenes(session):
    response = session.get(config.API_GET_URL, timeout=config.TIMEOUT_SEGUNDOS)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
    return data.get("data", []) if isinstance(data, dict) else []


def enviar_orden(session, orden):
    response = session.post(
        config.API_POST_URL, json=orden, timeout=config.TIMEOUT_SEGUNDOS
    )
    response.raise_for_status()
    return response


def agrupar_ordenes(ordenes):
    jefes = {}
    for orden in ordenes:
        jefe = orden.get("COD_USU_JEFE")
        sectorista = orden.get("COD_USU_SECTORISTA")
        grupo_jefe = jefes.setdefault(
            jefe, {"COD_USU_JEFE": jefe, "sectoristas": {}}
        )
        sectoristas = grupo_jefe["sectoristas"]
        if sectorista not in sectoristas:
            sectoristas[sectorista] = {
                "COD_USU_SECTORISTA": sectorista,
                "ordenes": [],
            }
        sectoristas[sectorista]["ordenes"].append(orden)

    resultado = []
    for grupo_jefe in jefes.values():
        grupo_jefe["sectoristas"] = list(grupo_jefe["sectoristas"].values())
        resultado.append(grupo_jefe)
    return resultado



CAMPOS_TABLA = [
    "ORDEN_COMPUESTO",
    "CODIGO_DESPACHO",
    "REFERENCIA",
    "NOMBRE_CLIENTE",
    "N_DECLARACION",
    "FECHA_NUMERACION",
    "FECHA_LLEGADA",
    "FECHA_TERMINO_DESCARGA",
    "FECHA_AUTORIZACION",
    "FECHA_RETIRO_MERCANCIA",
    "FECHA_LEVANTE",
]

ETIQUETAS_COLUMNAS = {
    "ORDEN_COMPUESTO": "Orden",
    "CODIGO_DESPACHO": "Tipo Despacho",
    "COD_ADUANA": "Aduana",
    "COD_REGIMEN": "Régimen",
    "ANIO": "Año",
    "NUME_ORDEN": "N° Orden",
    "REFERENCIA": "Referencia",
    "NOMBRE_CLIENTE": "Cliente",
    "N_DECLARACION": "N° Declaración",
    "FECHA_NUMERACION": "Fecha Numeración",
    "FECHA_LLEGADA": "Fecha Llegada",
    "FECHA_TERMINO_DESCARGA": "Término Descarga",
    "FECHA_AUTORIZACION": "Autorización",
    "FECHA_RETIRO_MERCANCIA": "Retiro Mercancía",
    "FECHA_LEVANTE": "Fecha Levante",
}


def valor_celda(orden, campo):
    if campo == "ORDEN_COMPUESTO":
        partes = [
            orden.get("COD_ADUANA"),
            orden.get("COD_REGIMEN"),
            orden.get("ANIO"),
            orden.get("NUME_ORDEN"),
        ]
        partes = [str(p) for p in partes if p is not None and str(p).strip()]
        return "-".join(partes)
    valor = orden.get(campo)
    if valor is None:
        return ""
    texto = str(valor)
    if texto.startswith("0000-00-00") or texto.startswith("00/00/0000"):
        return ""
    return texto


def parsear_fecha(fecha_str):
    if not fecha_str:
        return None
    texto = str(fecha_str).strip()
    if texto.startswith("0000-00-00") or texto.startswith("00/00/0000"):
        return None
    formatos = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
    )
    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def dias_transcurridos(fecha_str):
    fecha = parsear_fecha(fecha_str)
    if fecha is None:
        return None
    return (datetime.now() - fecha).days


def fila_en_rojo(orden):
    despacho = str(orden.get("CODIGO_DESPACHO", "") or "").strip()
    if despacho == "1-0":
        dias = dias_transcurridos(orden.get("FECHA_TERMINO_DESCARGA"))
    elif despacho == "0-0":
        dias = dias_transcurridos(orden.get("FECHA_NUMERACION"))
    else:
        return False
    return dias is not None and dias >= 15


CAMPOS_FECHA = {
    "FECHA_NUMERACION",
    "FECHA_LLEGADA",
    "FECHA_TERMINO_DESCARGA",
    "FECHA_AUTORIZACION",
    "FECHA_RETIRO_MERCANCIA",
    "FECHA_LEVANTE",
}


def construir_tabla_html(ordenes):
    estilo_tabla = "border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 11px;"
    estilo_th = "background-color: #87CEEB; color: #003366; border: 1px solid #5a9bd5; padding: 8px 10px; text-align: center;"
    estilo_td = "border: 1px solid #bcd7e8; padding: 6px 10px;"
    estilo_fila_par = "border: 1px solid #bcd7e8; padding: 6px 10px; background-color: #f2f9fc;"
    ancho_cliente = "min-width: 220px; "
    nowrap_orden = "white-space: nowrap; "
    centrado_fecha = "text-align: center; "

    def estilo_campo(campo, base):
        extra = ""
        if campo == "NOMBRE_CLIENTE":
            extra += ancho_cliente
        if campo == "ORDEN_COMPUESTO":
            extra += nowrap_orden
        if campo in CAMPOS_FECHA or campo == "CODIGO_DESPACHO":
            extra += centrado_fecha
        return extra + base

    encabezados = "".join(
        f"<th style='{estilo_campo(campo, estilo_th)}'>"
        f"{escape(ETIQUETAS_COLUMNAS.get(campo, campo))}</th>"
        for campo in CAMPOS_TABLA
    )
    filas = []
    ordenes_ordenadas = sorted(
        ordenes,
        key=lambda o: parsear_fecha(o.get("FECHA_NUMERACION")) or datetime.min,
    )
    for indice, orden in enumerate(ordenes_ordenadas):
        estilo_celda = estilo_fila_par if indice % 2 == 1 else estilo_td
        if fila_en_rojo(orden):
            estilo_celda = estilo_td + " background-color: #ff4d4d;"
        celdas = "".join(
            f"<td style='{estilo_campo(campo, estilo_celda)}'>"
            f"{escape(valor_celda(orden, campo))}</td>"
            for campo in CAMPOS_TABLA
        )
        filas.append(f"<tr>{celdas}</tr>")
    return (
        f"<table style='{estilo_tabla}'>"
        f"<thead><tr>{encabezados}</tr></thead>"
        f"<tbody>{''.join(filas)}</tbody>"
        "</table>"
    )


TITULO_MENSAJE = "ORDENES DE DEPOSITO SIN LEVANTE AUTORIZADO (NO SE ENCUENTRAN LEGAJADAS O EN ABANDONO LEGAL)"
USER_ID = "1"
# USUARIOS_ADICIONALES_JEFE = [3, 887]
USUARIOS_ADICIONALES_JEFE = []


def enviar_cuerpo(session, target_user_ids, ordenes):
    body = {
        "message": construir_tabla_html(ordenes),
        "title": TITULO_MENSAJE,
        "userId": USER_ID,
        "userIdsToExcludeOfNotification": [],
        "targetUserIds": list(target_user_ids),
    }
    response = session.post(
        config.API_POST_URL,
        json=body,
        timeout=config.TIMEOUT_SEGUNDOS,
    )
    response.raise_for_status()
    return response


def enviar_por_jefe(session, agrupado):
    exitosos = 0
    for grupo in agrupado:
        # jefe = grupo["COD_USU_JEFE"]
        jefe = 3
        ordenes = []
        for sectorista in grupo["sectoristas"]:
            ordenes.extend(sectorista["ordenes"])
        try:
            enviar_cuerpo(session, [jefe] + USUARIOS_ADICIONALES_JEFE, ordenes)
            exitosos += 1
            logger.info(
                "Tabla enviada al jefe %s con %d órdenes.", jefe, len(ordenes)
            )
        except Exception as exc:
            logger.error("Error enviando tabla al jefe %s: %s", jefe, exc)
    return exitosos, len(agrupado)


def enviar_por_trabajador(session, agrupado):
    exitosos = 0
    total = 0
    for grupo in agrupado:
        for sectorista in grupo["sectoristas"]:
            total += 1
            codigo = sectorista["COD_USU_SECTORISTA"]
            try:
                enviar_cuerpo(session, [codigo], sectorista["ordenes"])
                exitosos += 1
                logger.info(
                    "Tabla enviada al trabajador %s con %d órdenes.",
                    codigo,
                    len(sectorista["ordenes"]),
                )
            except Exception as exc:
                logger.error("Error enviando tabla al trabajador %s: %s", codigo, exc)
    return exitosos, total


def procesar_ordenes():
    session = get_session()

    try:
        ordenes = obtener_ordenes(session)
    except Exception as exc:
        logger.error("Error obteniendo las órdenes desde %s: %s", config.API_GET_URL, exc)
        return

    if not ordenes:
        logger.info("No se obtuvieron órdenes para procesar.")
        return
    
    if len(ordenes) == 0:
        logger.info("No se encontraron ordenes.")
        return

    logger.info("Se obtuvieron %d órdenes para procesar.", len(ordenes))

    agrupado = agrupar_ordenes(ordenes)
    logger.info("Órdenes agrupadas por jefe y sectorista: %s", agrupado)

    exitosos, total = enviar_por_jefe(session, agrupado)
    logger.info("Ronda 1 (jefes) finalizada: %d de %d tablas enviadas.", exitosos, total)

    # exitosos, total = enviar_por_trabajador(session, agrupado)
    # logger.info(
    #     "Ronda 2 (trabajadores) finalizada: %d de %d tablas enviadas.",
    #     exitosos,
    #     total,
    # )

    try:
        html_completo = construir_tabla_html(ordenes)
        enviar_correo_html(TITULO_MENSAJE, html_completo, config.EMAIL_DESTINOS)
        logger.info(
            "Correo con el listado completo enviado a %s.",
            ", ".join(config.EMAIL_DESTINOS),
        )
    except Exception as exc:
        logger.error("Error enviando el correo con el listado completo: %s", exc)
