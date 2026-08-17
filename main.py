import argparse
import sys

from src.alerts import discover_alerts, get_alert
from src.core.config import config
from src.core.logger import setup_logger
from src.core.scheduler import run_forever

logger = setup_logger()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bot modular de alertas. Ejecuta los módulos en src/alerts/."
    )
    parser.add_argument(
        "--now",
        nargs="?",
        const="__all__",
        default=None,
        help="Ejecuta los módulos inmediatamente y termina. Opcional: nombre de un módulo específico.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista los módulos detectados y termina.",
    )
    return parser.parse_args()


def ejecutar_now(nombre):
    alertas = discover_alerts()
    if nombre == "__all__":
        objetivos = alertas
    else:
        alerta = get_alert(nombre)
        if alerta is None:
            logger.error("No existe el módulo '%s'.", nombre)
            sys.exit(1)
        objetivos = [alerta]

    for alerta in objetivos:
        logger.info("Ejecutando módulo '%s' ahora.", alerta["name"])
        try:
            alerta["run"]()
        except Exception as exc:
            logger.error("Error ejecutando '%s': %s", alerta["name"], exc)


def main():
    args = parse_args()

    if args.list:
        alertas = discover_alerts()
        if not alertas:
            print("No se encontraron módulos en src/alerts/")
            return
        print("Módulos disponibles:")
        for alerta in alertas:
            print(f"  - {alerta['name']}")
        return

    if args.now is not None:
        ejecutar_now(args.now)
        return

    if config.EJECUTAR_AL_INICIAR:
        ejecutar_now("__all__")

    run_forever()


if __name__ == "__main__":
    main()
