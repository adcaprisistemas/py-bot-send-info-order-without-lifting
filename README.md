# bot_envio_alerta_info_orden_fecha_levante

Bot Python 3.12 con arquitectura modular. Cada alerta es un módulo autocontenido bajo `src/alerts/` y se descubre automáticamente. El bot orquesta todos los módulos desde un único entrypoint (`main.py`).

## Estructura del proyecto

```text
bot_envio_alerta_info_orden_fecha_levante/
├── main.py                                # entrypoint único: orquesta todos los módulos
├── src/
│   ├── core/                              # núcleo compartido por todos los módulos
│   │   ├── __init__.py
│   │   ├── config.py                      # config global (SMTP, HTTP, logging)
│   │   ├── logger.py                      # logger base
│   │   ├── email_service.py               # SMTP genérico
│   │   ├── http_client.py                 # requests.Session con reintentos
│   │   └── scheduler.py                   # orquestador de horarios
│   └── alerts/                            # módulos de alerta (descubrimiento automático)
│       ├── __init__.py
│       └── ordenes_sin_levante/           # módulo de órdenes sin levante
│           ├── __init__.py
│           ├── config.py                  # config con prefijo LEVANTE_
│           ├── api_client.py              # GET de órdenes
│           ├── grouping.py                # agrupación por jefe/sectorista
│           ├── renderer.py                # tabla HTML
│           └── module.py                  # run() y schedule()
├── tests/
│   ├── core/
│   │   └── test_discovery.py
│   └── alerts/
│       └── ordenes_sin_levante/
│           └── test_flow.py
├── logs/                                  # se crea automáticamente, guarda bot.log
├── .env                                   # configuración y secretos (NO subir al repo)
├── .env.example
├── requirements.txt
├── run.sh                                 # ejecución para Linux
├── bot.service                            # servicio systemd
└── README.md
```

## Requisitos

- Python 3.12
- Linux (destino) / Windows (desarrollo)
- Dependencias en `requirements.txt`

## Instalación

```bash
cd /ruta/al/proyecto/bot_envio_alerta_info_orden_fecha_levante
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Copiar `.env.example` a `.env` y completar los valores. El archivo se divide en dos secciones:

### Globales (compartidas por todos los módulos)

| Variable | Descripción |
| --- | --- |
| `LOG_LEVEL` | Nivel de logging (`INFO`, `DEBUG`, etc). |
| `SMTP_HOST` | Host SMTP para envío de correos. |
| `SMTP_PORT` | Puerto SMTP (587 por defecto). |
| `SMTP_USER` | Usuario SMTP. |
| `SMTP_PASSWORD` | Contraseña SMTP. |
| `EMAIL_ORIGEN` | Dirección de origen de los correos. |
| `EMAIL_DESTINO` | Destinatarios por defecto (separados por coma). |
| `TIMEOUT_SEGUNDOS` | Timeout HTTP en segundos. |
| `MAX_REINTENTOS` | Reintentos HTTP ante errores 5xx/429. |
| `EJECUTAR_AL_INICIAR` | `true`/`false`: ejecuta todos los módulos al iniciar. |

### Por módulo (prefijo del módulo)

Todas las variables del módulo `ordenes_sin_levante` usan el prefijo `LEVANTE_`:

| Variable | Descripción |
| --- | --- |
| `LEVANTE_API_GET_URL` | URL de la API para obtener órdenes. |
| `LEVANTE_API_POST_URL` | URL destino para enviar cada tabla. |
| `LEVANTE_API_TOKEN` | Token Bearer (opcional). |
| `LEVANTE_TITULO_MENSAJE` | Título del mensaje enviado por la API. |
| `LEVANTE_USER_ID` | ID de usuario emisor. |
| `LEVANTE_USUARIOS_ADICIONALES_JEFE` | IDs adicionales para notificar al jefe. |
| `LEVANTE_HORARIOS_SEMANA` | Horarios lunes a viernes (`HH:MM` separadas por coma). |
| `LEVANTE_HORARIOS_SABADO` | Horarios sábados. |
| `LEVANTE_HORARIOS_DOMINGO` | Horarios domingos (vacío por defecto). |

Nunca subir `.env` al repositorio.

## Ejecución manual

Listar módulos detectados:

```bash
python3 main.py --list
```

Ejecutar todos los módulos una vez y terminar:

```bash
python3 main.py --now
```

Ejecutar un módulo específico:

```bash
python3 main.py --now ordenes_sin_levante
```

Ejecutar el bot de forma continua (procesa a las horas definidas):

```bash
./run.sh
```

Detener con `Ctrl+C` (SIGINT) o `SIGTERM`.

## Tests

```bash
python3 -m unittest discover tests
```

## Cómo agregar un nuevo módulo de alerta

No se toca `main.py`. Solo crear una carpeta bajo `src/alerts/`:

```
src/alerts/mi_nueva_alerta/
├── __init__.py
├── config.py        # module_config con prefijo propio
├── ...              # lógica específica
└── module.py        # expone run() y schedule()
```

El `module.py` debe exponer dos funciones:

```python
# src/alerts/mi_nueva_alerta/module.py
def run() -> dict:
    """Ejecuta el procesamiento. Retorna métricas: {exitosos, total, errores}."""
    ...

def schedule() -> list:
    """Declara los horarios. Cada item debe ser un Job(day, time)."""
    from src.core.scheduler import Job
    return [Job("monday", "08:00"), Job("wednesday", "08:00")]
```

Y agregar sus variables al `.env` con su prefijo propio:

```
MI_NUEVA_ALERTA_API_GET_URL=https://...
MI_NUEVA_ALERTA_HORARIOS_SEMANA=08:00
```

Al iniciar el bot, el módulo se descubre automáticamente.

## systemd

Instalar el servicio (después de ajustar las rutas en `bot.service`):

```bash
sudo cp bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bot.service
sudo systemctl start bot.service
```

## Estado

```bash
sudo systemctl status bot.service
```

## Logs

```bash
sudo journalctl -u bot.service -f
tail -f logs/bot.log
```

## Reinicio

```bash
sudo systemctl restart bot.service
```

## Detención

```bash
sudo systemctl stop bot.service
```

## Comportamiento y robustez

- El bot permanece en ejecución y programa cada módulo a sus horarios.
- Cada petición HTTP usa timeouts y reintentos limitados.
- Si una orden falla al enviarse, se registra el error y se continúa.
- El servicio systemd usa `Restart=always`.
- Los errores nunca se ocultan: se registran en `logs/bot.log` y stdout.

## Troubleshooting

- `.env` no encontrado: verificar que `EnvironmentFile` en `bot.service` apunte a la ruta correcta.
- Dependencias faltantes: volver a ejecutar `pip install -r requirements.txt`.
- Rutas incorrectas: ajustar `WorkingDirectory` y `ExecStart` en `bot.service`.
- Proceso detenido: revisar `sudo journalctl -u bot.service -e` y `logs/bot.log`.
- Errores HTTP: verificar las URLs y el token del módulo correspondiente.
- Módulo no detectado: verificar que exista `module.py` con `run()` y `schedule()`.

## Estado de validación

- Validado en Windows: sintaxis, imports, tests y arranque.
- Pendiente de validar en Linux: ejecución real como servicio systemd.
