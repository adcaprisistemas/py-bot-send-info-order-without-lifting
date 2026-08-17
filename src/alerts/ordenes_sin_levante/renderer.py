from datetime import datetime
from html import escape


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

CAMPOS_FECHA = {
    "FECHA_NUMERACION",
    "FECHA_LLEGADA",
    "FECHA_TERMINO_DESCARGA",
    "FECHA_AUTORIZACION",
    "FECHA_RETIRO_MERCANCIA",
    "FECHA_LEVANTE",
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
