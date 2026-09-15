from datetime import datetime, timezone


def agora_utc():
    """UTC, sem fuso no banco para preservar compatibilidade com os registros existentes."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
