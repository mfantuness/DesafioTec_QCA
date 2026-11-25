"""Menu interativo no terminal."""

import logging

logger = logging.getLogger(__name__)


def escolher_estado(estados: list[dict]) -> dict:
    print("\nEstados disponíveis:")
    for i, estado in enumerate(estados, start=1):
        print(f"  {i:>2}) {estado['nome']} ({estado['sigla']})")

    while True:
        entrada = input("\nEscolha (número ou sigla): ").strip()
        if entrada.isdigit() and 1 <= int(entrada) <= len(estados):
            estado = estados[int(entrada) - 1]
            logger.info("UF escolhida: %s", estado["sigla"])
            return estado
        for estado in estados:
            if estado["sigla"].lower() == entrada.lower():
                logger.info("UF escolhida: %s", estado["sigla"])
                return estado
        print(
            f"Opção inválida: '{entrada}'. Digite um número de 1 a {len(estados)} ou uma sigla (ex.: PE)."
        )


def pedir_limite(total: int, padrao: int = 5) -> int:
    padrao = min(padrao, total)
    while True:
        entrada = input(f"Quantidade de municípios [{padrao}] (máx. {total}): ").strip()
        if not entrada:
            logger.info("Limite escolhido: %s", padrao)
            return padrao
        if entrada.isdigit() and int(entrada) > 0:
            quantidade = int(entrada)
            if quantidade > total:
                print(f"A UF tem só {total} municípios; usando {total}.")
                return total
            logger.info("Limite escolhido: %s", quantidade)
            return quantidade
        print("Informe um número inteiro maior que zero.")
