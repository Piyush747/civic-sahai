from __future__ import annotations

import ssl

from app.core.config import Settings


def kafka_connection_options(settings: Settings) -> dict:
    options = {
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "security_protocol": settings.kafka_security_protocol,
    }
    if settings.kafka_sasl_username and settings.kafka_sasl_password:
        options.update(
            sasl_mechanism=settings.kafka_sasl_mechanism,
            sasl_plain_username=settings.kafka_sasl_username,
            sasl_plain_password=settings.kafka_sasl_password,
        )
    if settings.kafka_ssl_insecure:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        if settings.kafka_ssl_certfile and settings.kafka_ssl_keyfile:
            context.load_cert_chain(settings.kafka_ssl_certfile, settings.kafka_ssl_keyfile)
        options["ssl_context"] = context
    elif settings.kafka_ssl_certfile and settings.kafka_ssl_keyfile:
        options["ssl_certfile"] = settings.kafka_ssl_certfile
        options["ssl_keyfile"] = settings.kafka_ssl_keyfile
    if settings.kafka_ssl_cafile and not settings.kafka_ssl_insecure:
        options["ssl_cafile"] = settings.kafka_ssl_cafile
    return options
