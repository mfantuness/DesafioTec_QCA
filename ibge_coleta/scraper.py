"""Coleta HTML do portal Cidades e Estados usando Playwright."""

import logging
import time
import unicodedata
from dataclasses import dataclass

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


@dataclass
class ResultadoColeta:
    """Resultado de uma tentativa de coleta."""

    html: str | None
    url: str
    erro: str | None = None


def gerar_slug(nome: str) -> str:
    """Gera slug provável do portal; nomes difíceis precisam ser confirmados manualmente."""
    sem_acento = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    sem_acento = sem_acento.casefold().strip()
    resultado = "".join("-" if c.isspace() else c for c in sem_acento)
    resultado = "".join(c for c in resultado if c.isalnum() or c in "-")
    return "-".join(parte for parte in resultado.split("-") if parte)


def gerar_url(uf: str, municipio: str) -> str:
    """Monta a URL a partir da UF e do nome do município."""
    url = f"https://www.ibge.gov.br/cidades-e-estados/{uf.lower()}/{gerar_slug(municipio)}.html"
    logger.debug("URL gerada: %s", url)
    return url


def _pagina_bloqueada(html: str) -> bool:
    sopa = BeautifulSoup(html, "html.parser")
    titulo = sopa.title.get_text(" ", strip=True).lower() if sopa.title else ""
    return "just a moment" in titulo or "um momento" in titulo


def coletar_municipios(
    municipios: list[dict],
    headless: bool = False,
    timeout_ms: int = 30000,
    pausa_segundos: float = 1.0,
) -> list[ResultadoColeta]:
    """Coleta em um único navegador, mantendo resultado separado por município."""
    resultados: list[ResultadoColeta] = []

    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=headless)
        contexto = navegador.new_context(locale="pt-BR")
        pagina = contexto.new_page()

        try:
            for indice, municipio in enumerate(municipios, start=1):
                url = gerar_url(municipio["uf"], municipio["municipio"])
                logger.info("Coletando %s/%s: %s", indice, len(municipios), municipio["municipio"])

                try:
                    resposta = pagina.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    if resposta is not None and resposta.status == 404:
                        erro = "URL não encontrada (HTTP 404)"
                        logger.warning("URL não encontrada: %s", url)
                        resultados.append(ResultadoColeta(None, url, erro))
                    else:
                        pagina.wait_for_selector("div.indicador", timeout=timeout_ms)
                        html = pagina.content()
                        if _pagina_bloqueada(html):
                            erro = "Bloqueio anti-bot da Cloudflare"
                            logger.error("Bloqueio da Cloudflare: %s", url)
                            resultados.append(ResultadoColeta(None, url, erro))
                        else:
                            resultados.append(ResultadoColeta(html, url))
                except PlaywrightTimeoutError:
                    erro = "Timeout ao carregar a página"
                    logger.error("Timeout no município %s: %s", municipio["municipio"], url)
                    resultados.append(ResultadoColeta(None, url, erro))
                except Exception as exc:
                    erro = f"Falha ao acessar a página: {exc}"
                    logger.error("Falha no município %s: %s", municipio["municipio"], exc)
                    resultados.append(ResultadoColeta(None, url, erro))

                if indice < len(municipios) and pausa_segundos > 0:
                    time.sleep(pausa_segundos)
        finally:
            contexto.close()
            navegador.close()

    return resultados
