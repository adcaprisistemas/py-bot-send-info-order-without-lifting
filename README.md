# bot_envio_alerta_info_orden_fecha_levante

Bot Python 3.12 que todos los días, a una hora definida, consulta una URL (GET) de una API para obtener órdenes y envía cada una de ellas mediante POST a otra ruta.

## Estructura del proyecto

```text
bot_envio_alerta_info_orden_fecha_levante/
├── main.py              # entrypoint: programación diaria y señales
├── src/                 # resto del código fuente
│   ├── __init__.py
│   ├── config.py        # carga de configuración desde .env
│   ├── logger.py        # logging a consola y logs/bot.log
│   └── api_client.py    # GET de órdenes y POST de cada una (con reintentos)
├── tests/               # tests con unittest (sin dependencias extra)
│   └── test_flow.py
├── logs/                # se crea automáticamente, guarda bot.log
├── .env                 # configuración y secretos (NO subir al repo)
├── .env.example
├── requirements.txt
├── run.sh               # ejecución para Linux
├── bot.service          # servicio systemd
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

Copiar `.env.example` a `.env` y completar los valores:

| Variable | Descripción |
| --- | --- |
| `API_GET_URL` | URL de la API de la cual se obtienen las órdenes (GET). |
| `API_POST_URL` | Ruta destino a la cual se envía cada orden (POST). |
| `API_TOKEN` | Token de autenticación (opcional). Si está vacío no se envía la cabecera `Authorization`. |
| `HORA_EJECUCION` | Hora de ejecución diaria en formato 24h (`HH:MM`), por ejemplo `06:00`. |
| `TIMEOUT_SEGUNDOS` | Timeout en segundos para cada petición HTTP. |
| `MAX_REINTENTOS` | Reintentos por petición ante errores de red o HTTP 429/5xx. |
| `EJECUTAR_AL_INICIAR` | `true`/`false`: ejecuta un procesamiento inmediato al iniciar el bot. |

Nunca subir `.env` al repositorio. El archivo `.env.example` no debe contener secretos reales.

## Ejecución manual

Ejecutar un único procesamiento y terminar:

```bash
python3 main.py --now
```

Ejecutar el bot de forma continua (procesa a la hora definida):

```bash
./run.sh
```

Detener con `Ctrl+C` (SIGINT) o `SIGTERM`.

## Tests

```bash
python3 -m unittest discover tests
```

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

- El bot permanece en ejecución y programa la tarea diaria a la hora indicada.
- Cada petición GET/POST cuenta con timeouts y reintentos limitados.
- Si una orden individual falla al enviarse, se registra el error y se continúa con la siguiente.
- El servicio systemd usa `Restart=always` para levantarse automáticamente si se cae o si la máquina se reinicia.
- Los errores nunca se ocultan: se registran en `logs/bot.log` y en la salida estándar.

## Troubleshooting

- `.env` no encontrado: verificar que `EnvironmentFile` en `bot.service` apunte a la ruta correcta.
- Dependencias faltantes: volver a ejecutar `pip install -r requirements.txt`.
- Rutas incorrectas: ajustar `WorkingDirectory` y `ExecStart` en `bot.service`.
- Proceso detenido: revisar `sudo journalctl -u bot.service -e` y `logs/bot.log`.
- Errores HTTP en el envío: verificar `API_POST_URL`, `API_TOKEN` y el formato esperado por el endpoint.

## Estado de validación

- Validado en Windows: sintaxis, imports, tests y arranque.
- Pendiente de validar en Linux: ejecución real como servicio systemd.
