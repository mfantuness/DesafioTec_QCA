"""Configuração central de logs da aplicação."""

import logging
from pathlib import Path


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Configura saída no terminal e no arquivo logs/execucao.log."""
    pasta_logs = Path("logs")
    pasta_logs.mkdir(parents=True, exist_ok=True)

    logger_raiz = logging.getLogger()
    logger_raiz.setLevel(nivel)

    formato = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(formato, datefmt="%H:%M:%S")

    for handler in logger_raiz.handlers[:]:
        logger_raiz.removeHandler(handler)

    handler_terminal = logging.StreamHandler()
    handler_terminal.setFormatter(formatter)
    logger_raiz.addHandler(handler_terminal)

    handler_arquivo = logging.FileHandler(pasta_logs / "execucao.log", encoding="utf-8")
    handler_arquivo.setFormatter(formatter)
    logger_raiz.addHandler(handler_arquivo)

    logging.getLogger("httpx").setLevel(logging.WARNING)
