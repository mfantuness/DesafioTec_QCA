"""Consolidação em pandas e exportação para Excel."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

COLUNAS = [
    "codigo_ibge",
    "municipio",
    "uf",
    "regiao",
    "prefeito",
    "gentilico",
    "populacao_estimada",
    "ano_populacao",
    "area_km2",
    "ano_area",
    "url_fonte",
    "data_coleta",
]


def criar_dataframe(linhas: list[dict]) -> pd.DataFrame:
    """Cria o DataFrame com tipos e coluna vazios padronizados."""
    dataframe = pd.DataFrame(linhas)
    for coluna in COLUNAS:
        if coluna not in dataframe.columns:
            dataframe[coluna] = pd.NA

    dataframe = dataframe[COLUNAS].copy()
    dataframe["codigo_ibge"] = dataframe["codigo_ibge"].astype("string")
    for coluna in ("populacao_estimada", "ano_populacao", "ano_area"):
        dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors="coerce").astype("Int64")
    dataframe["area_km2"] = pd.to_numeric(dataframe["area_km2"], errors="coerce").astype("float")

    dataframe = dataframe.drop_duplicates(subset="codigo_ibge")
    dataframe = dataframe.sort_values("municipio", key=lambda serie: serie.str.lower()).reset_index(
        drop=True
    )
    return dataframe


def exportar_excel(
    uf: str,
    linhas: list[dict],
    resumo: dict | None = None,
) -> str:
    """Salva dados e resumo opcional em output/municipios_{uf}.xlsx."""
    pasta = Path("output")
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"municipios_{uf.lower()}.xlsx"

    dataframe = criar_dataframe(linhas)
    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        dataframe.to_excel(escritor, sheet_name="municipios", index=False)
        if resumo:
            resumo_linhas = []
            resumo_linhas.append({"campo": "UF escolhida", "valor": resumo.get("uf", "")})
            resumo_linhas.append(
                {"campo": "Quantidade solicitada", "valor": resumo.get("solicitada", "")}
            )
            resumo_linhas.append(
                {"campo": "Coletada com sucesso", "valor": resumo.get("sucesso", "")}
            )
            resumo_linhas.append({"campo": "Coletada com falha", "valor": resumo.get("falhas", "")})
            for municipio, motivo in resumo.get("erros", {}).items():
                resumo_linhas.append(
                    {"campo": "Município com erro", "valor": municipio, "motivo": motivo}
                )
            for municipio, ausentes in resumo.get("ausentes", {}).items():
                resumo_linhas.append(
                    {"campo": "Campos ausentes", "valor": municipio, "motivo": ", ".join(ausentes)}
                )
            pd.DataFrame(resumo_linhas).to_excel(escritor, sheet_name="resumo", index=False)

    logger.info("Excel salvo em %s", caminho)
    return str(caminho)
