import importlib
from pathlib import Path

from src.core.logger import setup_logger

logger = setup_logger()

ALERTS_DIR = Path(__file__).resolve().parent


def discover_alerts():
    alertas = []
    for module_dir in ALERTS_DIR.iterdir():
        if not module_dir.is_dir():
            continue
        if module_dir.name.startswith("_") or module_dir.name.startswith("."):
            continue
        module_file = module_dir / "module.py"
        if not module_file.exists():
            continue
        try:
            mod = importlib.import_module(f"src.alerts.{module_dir.name}.module")
            run_fn = getattr(mod, "run", None)
            schedule_fn = getattr(mod, "schedule", None) #CRONOGRAMA
            if run_fn is None or schedule_fn is None:
                logger.warning(
                    "Módulo '%s' no expone run() y/o schedule(). Se omite.",
                    module_dir.name,
                )
                continue
            alertas.append(
                {
                    "name": module_dir.name,
                    "run": run_fn,
                    "jobs": schedule_fn(),
                }
            )
        except Exception as exc:
            logger.error(
                "Error cargando el módulo '%s': %s", module_dir.name, exc
            )
    return alertas


def get_alert(name):
    for alerta in discover_alerts():
        if alerta["name"] == name:
            return alerta
    return None
