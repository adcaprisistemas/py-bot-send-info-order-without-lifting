import argparse
import signal
import sys
import time

import schedule

from src.api_client import procesar_ordenes
from src.config import config
from src.logger import setup_logger

logger = setup_logger()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bot que consulta órdenes y las envía diariamente a una hora definida."
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Ejecuta el procesamiento una vez de inmediato y termina.",
    )
    return parser.parse_args()


DIAS_SEMANA = ("monday", "tuesday", "wednesday", "thursday", "friday")


def programar_ejecucion_diaria():
    for dia in DIAS_SEMANA:
        for hora in config.HORARIOS_SEMANA:
            getattr(schedule.every(), dia).at(hora).do(procesar_ordenes)
    for hora in config.HORARIOS_SABADO:
        schedule.every().saturday.at(hora).do(procesar_ordenes)
    logger.info(
        "Ejecución programada: lunes a viernes %s, sábados %s, domingos sin envíos.",
        ", ".join(config.HORARIOS_SEMANA),
        ", ".join(config.HORARIOS_SABADO),
    )


def run_forever():
    programar_ejecucion_diaria()
    logger.info("Bot en ejecución. Presione Ctrl+C para detenerlo.")

    def detener(signum, frame):
        logger.info("Señal %s recibida, deteniendo el bot.", signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, detener)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, detener)

    while True:
        try:
            schedule.run_pending()
        except Exception as exc:
            logger.error("Error en el bucle principal: %s", exc)
        time.sleep(1)


def main():
    args = parse_args()

    if not config.API_GET_URL or not config.API_POST_URL:
        logger.error(
            "Faltan variables de configuración. Revise API_GET_URL y API_POST_URL en el archivo .env"
        )
        sys.exit(1)

    if args.now or config.EJECUTAR_AL_INICIAR:
        logger.info("Ejecutando procesamiento de órdenes ahora.")
        procesar_ordenes()
        if args.now:
            return

    run_forever()


if __name__ == "__main__":
    main()
