import signal
import sys
import time
from dataclasses import dataclass

import schedule

from src.alerts import discover_alerts
from src.core.logger import setup_logger

logger = setup_logger()


@dataclass(frozen=True)
class Job:
    day: str
    time: str
    enviar_correo: bool = True

    def register(self, scheduler, callback):
        getattr(scheduler.every(), self.day).at(self.time).do(
            callback, enviar_correo=self.enviar_correo
        )


def programar_todos():
    alertas = discover_alerts()
    if not alertas:
        logger.warning("No se encontraron módulos de alerta en src/alerts/")
        return []
    programacion = []
    for alerta in alertas:
        logger.info(
            "Módulo '%s': programando %d ejecuciones.",
            alerta["name"],
            len(alerta["jobs"]),
        )
        for job in alerta["jobs"]:
            job.register(schedule, alerta["run"])
            programacion.append((alerta["name"], job.day, job.time))
    return programacion


def run_forever():
    programar_todos()
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
