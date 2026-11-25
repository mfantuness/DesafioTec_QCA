"""Testes do parser com HTML real e casos mínimos."""

from pathlib import Path

from ibge_coleta.parser import parse_municipio

FIXTURE = Path(__file__).parent / "fixtures" / "exemplo_recife.html"


def test_parser_recife():
    dados = parse_municipio(FIXTURE.read_text(encoding="utf-8"))

    assert dados["prefeito"] == "JOÃO HENRIQUE DE ANDRADE LIMA CAMPOS"
    assert dados["gentilico"] == "recifense"
    assert dados["populacao_estimada"] == 1588983
    assert dados["ano_populacao"] == 2026
    assert dados["area_km2"] == 218.843
    assert dados["ano_area"] == 2025
    assert dados["ausentes"] == []


def test_campos_ausentes():
    dados = parse_municipio("<html><body><p>Sem indicadores</p></body></html>")

    assert dados["prefeito"] is None
    assert dados["gentilico"] is None
    assert dados["populacao_estimada"] is None
    assert dados["ano_populacao"] is None
    assert dados["area_km2"] is None
    assert dados["ano_area"] is None
    assert set(dados["ausentes"])


def test_censo_nao_confunde_com_estimativa():
    html = """
    <div class="indicador">
      <div class="ind-label"><p>População no último censo</p></div>
      <p class="ind-value">1.488.920 pessoas<small>[2022]</small></p>
    </div>
    """
    dados = parse_municipio(html)

    assert dados["populacao_estimada"] is None
    assert dados["ano_populacao"] is None
