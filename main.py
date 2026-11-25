"""Orquestra a coleta da API, portal e exportação Excel."""

import logging
from datetime import date

from ibge_coleta.cli import escolher_estado, pedir_limite
from ibge_coleta.exporter import exportar_excel
from ibge_coleta.ibge_api import ErroAPI, criar_cliente, listar_estados, listar_municipios
from ibge_coleta.logging_config import configurar_logging
from ibge_coleta.parser import parse_municipio
from ibge_coleta.scraper import coletar_municipios

logger = logging.getLogger(__name__)


def main() -> None:
    """Executa o fluxo interativo completo."""
    configurar_logging()

    cliente = criar_cliente()
    erros: dict[str, str] = {}
    ausentes: dict[str, list[str]] = {}

    try:
        estados = listar_estados(cliente)
        estado = escolher_estado(estados)
        uf = estado["sigla"]
        municipios = listar_municipios(cliente, estado)

        quantidade = pedir_limite(len(municipios))
        selecionados = municipios[:quantidade]
        resultados = coletar_municipios(selecionados)

        linhas = []
        data_coleta = date.today().isoformat()

        for municipio, resultado in zip(selecionados, resultados):
            if resultado.erro:
                erros[municipio["municipio"]] = resultado.erro
                continue

            if not resultado.html:
                erros[municipio["municipio"]] = "HTML vazio"
                continue

            dados = parse_municipio(resultado.html)
            linha = {
                **municipio,
                **dados,
                "url_fonte": resultado.url,
                "data_coleta": data_coleta,
            }
            linha.pop("ausentes", None)
            linhas.append(linha)

            if dados["ausentes"]:
                ausentes[municipio["municipio"]] = dados["ausentes"]
                logger.warning("Prefeito ou outro campo ausente em %s", municipio["municipio"])

        resumo = {
            "uf": uf,
            "solicitada": quantidade,
            "sucesso": len(linhas),
            "falhas": len(erros),
            "erros": erros,
            "ausentes": ausentes,
        }
        caminho = exportar_excel(uf, linhas, resumo)

        logger.info(
            "Resumo da execução | UF=%s | processados=%s | falhas=%s | arquivo=%s",
            uf,
            len(linhas),
            len(erros),
            caminho,
        )
        print(f"Concluído. Dados salvos em {caminho}")
    except ErroAPI as exc:
        logger.error("Falha na API do IBGE: %s", exc)
        print(f"Não foi possível concluir: {exc}")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()
