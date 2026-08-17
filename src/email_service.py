import smtplib
import ssl
from email.message import EmailMessage

from src.config import config
from src.logger import setup_logger

logger = setup_logger()


def enviar_correo_html(asunto, html, destinatarios):
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = config.EMAIL_ORIGEN
    msg["To"] = ", ".join(destinatarios)
    msg.set_content(
        "Se adjunta el listado de órdenes. Si no lo visualizas, habilita el HTML en tu cliente de correo."
    )
    msg.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(
        config.SMTP_HOST, config.SMTP_PORT, timeout=config.TIMEOUT_SEGUNDOS
    ) as servidor:
        servidor.starttls(context=context)
        servidor.sendmail(config.EMAIL_ORIGEN, destinatarios, msg.as_string())

    logger.info(
        "Correo enviado a %s con asunto '%s'.", ", ".join(destinatarios), asunto
    )
