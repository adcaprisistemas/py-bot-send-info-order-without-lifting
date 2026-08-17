from src.alerts.ordenes_sin_levante.api_client import get_session, obtener_ordenes
from src.alerts.ordenes_sin_levante.config import module_config
from src.alerts.ordenes_sin_levante.renderer import construir_tabla_html
from src.core.config import config
from src.core.email_service import enviar_correo_html
from src.core.logger import setup_logger

logger = setup_logger()


def _to_int_list(valores):
    resultado = []
    for v in valores:
        try:
            resultado.append(int(v))
        except (TypeError, ValueError):
            continue
    return resultado

def agrupar_ordenes(ordenes):
    jefes = {}
    for orden in ordenes:
        jefe = orden.get("COD_USU_JEFE")
        sectorista = orden.get("COD_USU_SECTORISTA")
        grupo_jefe = jefes.setdefault(
            jefe,
            {
                "COD_USU_JEFE": jefe,
                "CORREO_JEFE": orden.get("CORREO_JEFE", ""),
                "sectoristas": {},
            },
        )
        sectoristas = grupo_jefe["sectoristas"]
        if sectorista not in sectoristas:
            sectoristas[sectorista] = {
                "COD_USU_SECTORISTA": sectorista,
                "CORREO_SECTORISTA": orden.get("CORREO_SECTORISTA", ""),
                "ordenes": [],
            }
        sectoristas[sectorista]["ordenes"].append(orden)

    todos_sectoristas = set()
    for orden in ordenes:
        s = orden.get("COD_USU_SECTORISTA")
        if s is not None:
            todos_sectoristas.add(str(s))

    apertura_usuarios = {}
    for orden in ordenes:
        apertura = str(orden.get("COD_USU_APERTURA") or "").strip()
        if not apertura:
            continue
        if apertura in todos_sectoristas:
            continue
        if apertura not in apertura_usuarios:
            apertura_usuarios[apertura] = {
                "COD_USU_APERTURA": apertura,
                "CORREO_USU_APERTURA": orden.get("CORREO_USU_APERTURA", ""),
                "ordenes": [],
            }
        apertura_usuarios[apertura]["ordenes"].append(orden)

    resultado = []
    for grupo_jefe in jefes.values():
        grupo_jefe["sectoristas"] = list(grupo_jefe["sectoristas"].values())
        resultado.append(grupo_jefe)
    return resultado, list(apertura_usuarios.values())

def enviar_cuerpo(session, target_user_ids, ordenes):
    body = {
        "message": construir_tabla_html(ordenes),
        "title": module_config.TITULO_MENSAJE,
        "userId": module_config.USER_ID,
        "userIdsToExcludeOfNotification": [],
        "targetUserIds": list(target_user_ids),
    }
    response = session.post(
        module_config.API_POST_URL,
        json=body,
        timeout=config.TIMEOUT_SEGUNDOS,
    )
    response.raise_for_status()
    return response


def enviar_correo_a_usuario(correo, ordenes):
    destinatarios = [e.strip() for e in str(correo).split(",") if e.strip()]
    if not destinatarios:
        return
    html = construir_tabla_html(ordenes)
    enviar_correo_html(module_config.TITULO_MENSAJE, html, destinatarios)


def enviar_por_jefe(session, agrupado):
    adicionales = _to_int_list(module_config.USUARIOS_ADICIONALES_JEFE)
    exitosos = 0
    for grupo in agrupado:
        jefe = grupo["COD_USU_JEFE"]
        correo = grupo["CORREO_JEFE"]
        ordenes = []
        for sectorista in grupo["sectoristas"]:
            ordenes.extend(sectorista["ordenes"])
        try:
            enviar_cuerpo(session, [jefe] + adicionales, ordenes)
            enviar_correo_a_usuario(correo, ordenes)
            exitosos += 1
            logger.info(
                "Tabla enviada al jefe %s con %d órdenes.", jefe, len(ordenes)
            )
        except Exception as exc:
            logger.error("Error enviando tabla al jefe %s: %s", jefe, exc)
    return exitosos, len(agrupado)


def enviar_por_sectorista(session, agrupado):
    exitosos = 0
    total = 0
    for grupo in agrupado:
        for sectorista in grupo["sectoristas"]:
            total += 1
            codigo = sectorista["COD_USU_SECTORISTA"]
            correo = sectorista["CORREO_SECTORISTA"]
            try:
                enviar_cuerpo(session, [codigo], sectorista["ordenes"])
                enviar_correo_a_usuario(correo, sectorista["ordenes"])
                exitosos += 1
                logger.info(
                    "Tabla enviada al sectorista %s con %d órdenes.",
                    codigo,
                    len(sectorista["ordenes"]),
                )
            except Exception as exc:
                logger.error(
                    "Error enviando tabla al sectorista %s: %s", codigo, exc
                )
    return exitosos, total


def enviar_por_apertura(session, apertura_usuarios):
    exitosos = 0
    for usuario in apertura_usuarios:
        codigo = usuario["COD_USU_APERTURA"]
        correo = usuario["CORREO_USU_APERTURA"]
        try:
            enviar_cuerpo(session, [codigo], usuario["ordenes"])
            enviar_correo_a_usuario(correo, usuario["ordenes"])
            exitosos += 1
            logger.info(
                "Tabla enviada al usuario apertura %s con %d órdenes.",
                codigo,
                len(usuario["ordenes"]),
            )
        except Exception as exc:
            logger.error(
                "Error enviando tabla al usuario apertura %s: %s", codigo, exc
            )
    return exitosos, len(apertura_usuarios)


def run() -> dict:
    session = get_session()
    metricas = {"exitosos": 0, "total": 0, "errores": 0}

    try:
        ordenes = obtener_ordenes(session)
    except Exception as exc:
        logger.error(
            "Error obteniendo las órdenes desde %s: %s",
            module_config.API_GET_URL,
            exc,
        )
        metricas["errores"] += 1
        return metricas

    if not ordenes:
        logger.info("No se obtuvieron órdenes para procesar.")
        return metricas

    logger.info("Se obtuvieron %d órdenes para procesar.", len(ordenes))

    agrupado, apertura = agrupar_ordenes(ordenes)
    logger.info("Órdenes agrupadas por jefe y sectorista: %s", agrupado)
    logger.info("Usuarios apertura detectados: %d", len(apertura))

    exitosos_j, total_j = enviar_por_jefe(session, agrupado)
    logger.info(
        "Ronda 1 (jefes) finalizada: %d de %d tablas enviadas.",
        exitosos_j,
        total_j,
    )

    exitosos_s, total_s = enviar_por_sectorista(session, agrupado)
    logger.info(
        "Ronda 2 (sectoristas) finalizada: %d de %d tablas enviadas.",
        exitosos_s,
        total_s,
    )

    exitosos_a, total_a = enviar_por_apertura(session, apertura)
    logger.info(
        "Ronda 3 (apertura) finalizada: %d de %d tablas enviadas.",
        exitosos_a,
        total_a,
    )

    total_total = total_j + total_s + total_a
    total_exitosos = exitosos_j + exitosos_s + exitosos_a
    metricas["exitosos"] = total_exitosos
    metricas["total"] = total_total
    metricas["errores"] = total_total - total_exitosos
    return metricas


DIAS_SEMANA = ("monday", "tuesday", "wednesday", "thursday", "friday")


def schedule():
    from src.core.scheduler import Job

    jobs = []
    for dia in DIAS_SEMANA:
        for hora in module_config.HORARIOS_SEMANA:
            jobs.append(Job(dia, hora))
    for hora in module_config.HORARIOS_SABADO:
        jobs.append(Job("saturday", hora))
    for hora in module_config.HORARIOS_DOMINGO:
        jobs.append(Job("sunday", hora))
    return jobs
