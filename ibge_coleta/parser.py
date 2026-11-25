"""Extração dos dados de um município a partir do HTML do portal Cidades e Estados."""

import logging
import re
import unicodedata

from bs4 import BeautifulSoup

# rótulo normalizado no HTML -> prefixo do campo na planilha
ROTULOS = {
    "prefeito": "prefeito",
    "gentilico": "gentilico",
    "populacao estimada": "populacao",
    "area territorial": "area",
}

logger = logging.getLogger(__name__)


def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar rótulos com segurança."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def _numero_br(texto: str) -> float | None:
    """Converte '1.588.983' ou '218,843' (formato brasileiro) em número."""
    limpo = re.sub(r"[^\d.,]", "", texto or "")
    if not limpo:
        return None
    try:
        return float(limpo.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _indicadores(soup: BeautifulSoup) -> dict[str, dict]:
    """Lê todos os blocos 'div.indicador' e devolve {rotulo_normalizado: dados}."""
    resultado = {}
    for bloco in soup.select("div.indicador"):
        rotulo_tag = bloco.select_one(".ind-label")
        valor_tag = bloco.select_one("p.ind-value")
        if not rotulo_tag or not valor_tag:
            continue

        ano = None
        ano_tag = valor_tag.find("small")
        if ano_tag:
            achado = re.search(r"\d{4}", ano_tag.get_text())
            ano = int(achado.group()) if achado else None
            ano_tag.extract()

        unidade_tag = valor_tag.find(class_="indicador-unidade")
        if unidade_tag:
            unidade_tag.extract()

        valor = valor_tag.get_text(" ", strip=True)
        resultado[_normalizar(rotulo_tag.get_text(strip=True))] = {
            "valor": valor or None,
            "ano": ano,
        }
    return resultado


def parse_municipio(html: str) -> dict:
    """Extrai os campos de interesse. Campo não encontrado fica como None."""
    soup = BeautifulSoup(html, "html.parser")
    ind = _indicadores(soup)

    def pegar(rotulo: str) -> dict:
        return ind.get(rotulo, {"valor": None, "ano": None})

    pref, gent = pegar("prefeito"), pegar("gentilico")
    pop, area = pegar("populacao estimada"), pegar("area territorial")

    pop_num = _numero_br(pop["valor"])
    dados = {
        "prefeito": pref["valor"],
        "gentilico": gent["valor"],
        "populacao_estimada": int(pop_num) if pop_num is not None else None,
        "ano_populacao": pop["ano"],
        "area_km2": _numero_br(area["valor"]),
        "ano_area": area["ano"],
    }
    dados["ausentes"] = [campo for campo, v in dados.items() if v is None]
    if dados["ausentes"]:
        logger.warning("Campos ausentes no município: %s", dados["ausentes"])
    return dados
