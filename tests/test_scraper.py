"""Testes dos helpers de URL do scraper."""

import pytest

from ibge_coleta.scraper import gerar_slug, gerar_url


def test_gerar_slug_acentos_espaco_e_apostrofo():
    """Confirma a hipótese de slug; o formato real deve ser testado no portal."""
    assert gerar_slug("São José dos Campos") == "sao-jose-dos-campos"
    assert gerar_slug("Santa Bárbara d'Oeste") == "santa-barbara-doeste"


def test_gerar_url():
    """Confirma o formato provável usado pelo portal; validar também municípios reais difíceis."""
    assert gerar_url("PE", "Recife") == "https://www.ibge.gov.br/cidades-e-estados/pe/recife.html"


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("Embu-Guaçu", "embu-guacu"),
        ("Arco-Íris", "arco-iris"),
        ("Lagoa d'Anta", "lagoa-danta"),
        ("Estrela d'Oeste", "estrela-doeste"),
        ("Olho d'Água do Borges", "olho-dagua-do-borges"),
    ],
)
def test_gerar_slug_casos_confirmados_no_portal(nome, esperado):
    assert gerar_slug(nome) == esperado
