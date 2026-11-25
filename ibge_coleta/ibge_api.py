"""Consulta à API de Localidades do IBGE (Etapa A)."""

import logging
import unicodedata

import httpx

logger = logging.getLogger(__name__)
BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"


class ErroAPI(Exception):
    """Falha ao consultar ou interpretar a resposta da API do IBGE."""


def criar_cliente() -> httpx.Client:
    """Cliente com timeout e até 2 novas tentativas em falhas de conexão."""
    return httpx.Client(
        timeout=15.0,
        transport=httpx.HTTPTransport(retries=2),
        headers={"Accept": "application/json"},
    )


def _chave_ordenacao(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()


def _get_json(cliente: httpx.Client, url: str) -> list:
    try:
        logger.debug("Consultando API: %s", url)
        resposta = cliente.get(url)
        resposta.raise_for_status()
        dados = resposta.json()
    except httpx.TimeoutException as e:
        logger.error("Timeout na API: %s", url)
        raise ErroAPI("Tempo esgotado ao consultar %s" % url) from e
    except httpx.HTTPStatusError as e:
        logger.error("API respondeu HTTP %s em %s", e.response.status_code, url)
        raise ErroAPI("A API respondeu %s em %s" % (e.response.status_code, url)) from e
    except httpx.HTTPError as e:
        logger.error("Falha de conexão na API: %s", url)
        raise ErroAPI("Falha de conexão com %s: %s" % (url, e)) from e
    except ValueError as e:
        logger.error("Resposta não é JSON válido: %s", url)
        raise ErroAPI("Resposta inválida (não é JSON) de %s" % url) from e

    if not isinstance(dados, list) or not dados:
        logger.error("Resposta vazia ou inválida da API: %s", url)
        raise ErroAPI("Resposta vazia ou em formato inesperado de %s" % url)
    return dados


def listar_estados(cliente: httpx.Client) -> list[dict]:
    """Todas as UFs devolvidas pela API, ordenadas por nome."""
    dados = _get_json(cliente, f"{BASE_URL}/estados")
    try:
        estados = [
            {"sigla": item["sigla"], "nome": item["nome"], "regiao": item["regiao"]["nome"]}
            for item in dados
        ]
    except (KeyError, TypeError) as e:
        logger.error("Estrutura inesperada na lista de estados")
        raise ErroAPI("Estrutura inesperada na lista de estados") from e
    logger.info("Estados obtidos da API: %s", len(estados))
    return sorted(estados, key=lambda e: _chave_ordenacao(e["nome"]))


def listar_municipios(cliente: httpx.Client, estado: dict) -> list[dict]:
    """Municípios da UF escolhida, ordenados por nome."""
    dados = _get_json(cliente, f"{BASE_URL}/estados/{estado['sigla']}/municipios")
    try:
        municipios = [
            {
                "codigo_ibge": str(item["id"]).zfill(7),
                "municipio": item["nome"],
                "uf": estado["sigla"],
                "regiao": estado["regiao"],
            }
            for item in dados
        ]
    except (KeyError, TypeError) as e:
        logger.error("Estrutura inesperada na lista de municípios")
        raise ErroAPI("Estrutura inesperada na lista de municípios") from e
    logger.info("Municípios encontrados para %s: %s", estado["sigla"], len(municipios))
    return sorted(municipios, key=lambda m: _chave_ordenacao(m["municipio"]))
