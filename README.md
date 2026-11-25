# Coleta de dados públicos de municípios (IBGE)

Aplicação de terminal em Python que lista os estados brasileiros pela API do IBGE, permite escolher uma UF, abre a página de cada município no portal **Cidades e Estados** e gera uma planilha Excel pronta para consulta.

Desenvolvida como desafio técnico de estágio (QCA).

## Sumário

- [Como funciona](#como-funciona)
- [Tecnologias](#tecnologias)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Como executar](#como-executar)
- [Saída gerada](#saída-gerada)
- [Logging](#logging)
- [Testes e qualidade de código](#testes-e-qualidade-de-código)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Decisões técnicas](#decisões-técnicas)
- [Fontes utilizadas](#fontes-utilizadas)
- [Limitações conhecidas](#limitações-conhecidas)

## Como funciona

```
listar estados → escolher UF → consultar municípios → coletar no portal → exportar Excel
   (httpx)         (terminal)        (httpx)          (Playwright + BS4)      (pandas)
```

1. **API de Localidades (httpx):** obtém todos os estados e, para a UF escolhida, os municípios com código IBGE, nome, sigla da UF e região. Nada é fixo no código: estados, UFs e códigos municipais vêm sempre da API.
2. **Portal Cidades e Estados (Playwright):** abre a página de cada município em um navegador real e captura o HTML com `page.content()`.
3. **Extração (BeautifulSoup4):** lê o HTML capturado e extrai prefeito, gentílico, população estimada (com ano) e área territorial (com ano).
4. **Consolidação (pandas):** monta uma linha por município, converte os números do formato brasileiro e exporta o Excel.

Por padrão, são processados **5 municípios**, escolhidos dinamicamente (os primeiros em ordem alfabética). O limite é ajustável e nunca ultrapassa o total retornado pela API.

## Tecnologias

| Biblioteca | Papel no projeto |
|---|---|
| `httpx` | Consulta à API REST do IBGE, com timeout, novas tentativas e tratamento de erros HTTP/JSON |
| `playwright` | Navegação real no portal e captura do HTML |
| `beautifulsoup4` | Extração dos campos a partir do HTML capturado |
| `pandas` + `openpyxl` | Limpeza, tipagem, validação e exportação para Excel |
| `logging` (biblioteca padrão) | Registro das etapas, avisos e erros no terminal e em arquivo |
| `pytest` | Testes automatizados (parser, slug e URL) |
| `ruff` | Verificação de qualidade (lint) e formatação do código |

## Requisitos

- Python **3.11 ou superior** (desenvolvido e testado com Python 3.13 no Windows)
- Conexão com a internet
- Ambiente gráfico: o navegador roda com janela visível (veja [Decisões técnicas](#decisões-técnicas))

## Instalação

```bash
# 1. Clone o repositório e entre na pasta
git clone <https://github.com/mfantuness/DesafioTec_QCA.git>
cd DesafioTec_QCA

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Baixe o navegador usado pelo Playwright
playwright install chromium
```

> No PowerShell, se aparecer o erro de "execução de scripts desabilitada", rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Para desenvolvimento (testes e Ruff), instale também as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

## Como executar

Na raiz do projeto, com o ambiente virtual ativo:

```bash
python main.py
```

O programa guia o usuário pelo terminal:

1. **Escolher o estado:** é exibida a lista numerada de UFs obtida da API. Digite o **número** ou a **sigla** (por exemplo `17` ou `PE`). Entradas inválidas geram uma mensagem e o programa pergunta de novo.
2. **Ajustar o limite de municípios:** o padrão é **5**. Pressione Enter para aceitar ou digite outro valor. Se o valor for maior que o total de municípios da UF, o programa usa o total; zero, negativos e texto são recusados.
3. **Aguardar a coleta:** uma janela do Chromium abre e navega pelas páginas. Não é necessário interagir com ela.
4. **Abrir o resultado** em `output/municipios_{uf}.xlsx`.

Exemplo de execução (UF `PE`, limite `4`):

```text
23:18:04 | INFO     | ibge_api | Estados obtidos da API: 27

Estados disponíveis:
   1) Acre (AC)
   ...
  17) Pernambuco (PE)
   ...

Escolha (número ou sigla): 17
23:18:33 | INFO     | cli | UF escolhida: PE
23:18:34 | INFO     | ibge_api | Municípios encontrados para PE: 185
Quantidade de municípios [5] (máx. 185): 4
23:18:43 | INFO     | cli | Limite escolhido: 4
23:18:47 | INFO     | scraper | Coletando 1/4: Abreu e Lima
23:18:51 | INFO     | scraper | Coletando 2/4: Afogados da Ingazeira
23:18:54 | INFO     | scraper | Coletando 3/4: Afrânio
23:18:56 | INFO     | scraper | Coletando 4/4: Agrestina
23:19:00 | INFO     | exporter | Excel salvo em output\municipios_pe.xlsx
23:19:00 | INFO     | __main__ | Resumo da execução | UF=PE | processados=4 | falhas=0 | arquivo=output\municipios_pe.xlsx
Concluído. Dados salvos em output\municipios_pe.xlsx
```

> **Importante:** feche o Excel antes de rodar o programa novamente. O Windows bloqueia a sobrescrita de um arquivo aberto.

> **Uso responsável:** o programa faz uma pausa entre as requisições ao portal (1 segundo por padrão). Prefira limites pequenos; a coleta de todos os municípios do estado não é necessária.

## Saída gerada

Arquivo: `output/municipios_{uf}.xlsx` (UF em letras minúsculas), com duas abas.

### Aba `municipios`

Uma linha por município, ordenada por nome, sem duplicados (chave: `codigo_ibge`).

| Coluna | Formato |
|---|---|
| `codigo_ibge` | Texto (7 dígitos) |
| `municipio` | Texto |
| `uf` | Texto |
| `regiao` | Texto |
| `prefeito` | Texto ou vazio, se indisponível |
| `gentilico` | Texto ou vazio, se indisponível |
| `populacao_estimada` | Número inteiro |
| `ano_populacao` | Ano (inteiro) |
| `area_km2` | Número decimal |
| `ano_area` | Ano (inteiro) |
| `url_fonte` | URL da página consultada |
| `data_coleta` | Data da execução (formato ISO, `AAAA-MM-DD`) |

Trecho das primeiras colunas da execução de exemplo:

| codigo_ibge | municipio | uf | regiao |
|---|---|---|---|
| 2600054 | Abreu e Lima | PE | Nordeste |
| 2600104 | Afogados da Ingazeira | PE | Nordeste |

### Aba `resumo`

Registro da execução: UF escolhida, quantidade solicitada, municípios coletados com sucesso e com falha, e o motivo de cada falha.

### Dados ausentes

Quando um campo não está disponível na página, a célula fica **vazia**. Nenhum valor é inventado ou preenchido com valor fictício. O parser devolve `None` para o campo, registra a ausência no log e a lista de campos ausentes é considerada no resumo da coleta.

## Logging

O projeto usa o módulo `logging` da biblioteca padrão, configurado **uma única vez** em `ibge_coleta/logging_config.py` e chamado no início do `main.py`.

- **Destinos:** terminal e arquivo `logs/execucao.log` (UTF-8), com a mesma informação.
- **Formato:** `hora | nível | módulo | mensagem`, em que o módulo identifica a origem (`ibge_api`, `scraper`, `exporter`...).
- **Convenções:** cada módulo usa `logging.getLogger(__name__)` e os argumentos são passados com `%s` (e não com f-strings dentro do logger).
- **`print` e `input`** são usados apenas no menu interativo; todo o restante é registrado via `logging`.
- O excesso de mensagens internas do `httpx` é silenciado (nível `WARNING`).

| Nível | Quando é usado |
|---|---|
| `INFO` | Etapas normais: estados obtidos, UF escolhida, limite, "Coletando 3/5: Olinda", Excel salvo, resumo final |
| `WARNING` | Algo errado que não interrompe a execução: URL não encontrada (404), campo ausente |
| `ERROR` | Falha que impede uma ação: timeout, falha na API, bloqueio anti-bot em um município |
| `DEBUG` | Detalhes técnicos, como as URLs geradas |

A pasta `logs/` não é versionada (está no `.gitignore`). Para investigar uma falha, consulte `logs/execucao.log`.

## Testes e qualidade de código

```bash
pytest -q              # testes automatizados
ruff check .           # lint
ruff format --check .  # verificação de formatação
ruff format .          # aplica a formatação
```

Os testes **não dependem de rede**:

- **Parser:** usa um HTML real do portal salvo em `tests/fixtures/exemplo_recife.html` e confere os campos extraídos (prefeito, gentílico, população e área, cada um com seu ano). Também cobre HTML sem os campos, que devem vir vazios e aparecer como ausentes.
- **Scraper:** cobre a geração do slug e da URL a partir da UF e do nome do município.

A configuração do `pytest` e do `ruff` está no `pyproject.toml`.

## Estrutura do projeto

```text
Desafio_QCA/
├── main.py                    # ponto de entrada: orquestra todo o fluxo
├── ibge_coleta/
│   ├── __init__.py
│   ├── cli.py                 # menu no terminal (UF e limite)
│   ├── ibge_api.py            # Etapa A: API de Localidades (httpx)
│   ├── scraper.py             # Etapa B: navegação no portal (Playwright)
│   ├── parser.py              # Etapa C: extração dos dados (BeautifulSoup)
│   ├── exporter.py            # Etapa D: DataFrame e Excel (pandas)
│   └── logging_config.py      # configuração central de logging
├── tests/
│   ├── fixtures/
│   │   └── exemplo_recife.html
│   ├── test_parser.py
│   └── test_scraper.py
├── output/                    # planilha gerada
├── pyproject.toml             # configuração de pytest e ruff
├── requirements.txt           # dependências de execução
├── requirements-dev.txt       # dependências de desenvolvimento
└── README.md
```

## Decisões técnicas

- **Nada fixo no código.** Estados, UFs, regiões e códigos IBGE vêm da API. A lista de estados, o menu e as URLs são gerados a partir das respostas.
- **UF e região vêm do objeto do estado**, e não do caminho aninhado de cada município (`microrregiao → mesorregiao → UF → regiao`), que pode vir nulo em alguns casos.
- **Código IBGE como texto de 7 dígitos**, preservando zeros à esquerda e evitando conversão numérica indevida.
- **Ordenação sem diferenciar acentos nem maiúsculas**, para que nomes acentuados fiquem na posição esperada.
- **Tratamento de falhas na API:** timeout, novas tentativas em falhas de conexão, erro de status HTTP, JSON inválido e formato inesperado viram uma exceção própria (`ErroAPI`) com mensagem clara, registrada no log e exibida sem traceback.
- **Navegador visível por padrão (`headless=False`).** O portal usa uma verificação anti-bot (Cloudflare). Nos testes, em modo invisível a página devolvida foi a de verificação (título "Um momento…" / "Just a moment..."), enquanto com a janela visível a página real carregou normalmente. O programa **não** usa técnicas de contorno: apenas um navegador comum, com pausa entre requisições.
- **Um único navegador para toda a coleta**, reaproveitando a mesma página e encerrando sempre com `try/finally`.
- **Espera pelo conteúdo, não por tempo fixo:** o scraper aguarda o aparecimento dos indicadores da página (`div.indicador`) em vez de usar `sleep`.
- **Página de bloqueio nunca chega ao parser.** Um título de verificação anti-bot é tratado como falha daquele município.
- **Falha em um município não interrompe os demais.** 404, timeout, bloqueio ou erro inesperado são registrados no log e no resumo, e a coleta segue.
- **Extração pelo rótulo, e não pela posição.** O parser localiza cada indicador pelo texto do rótulo ("Prefeito", "Gentílico", "População estimada", "Área Territorial"), comparado sem acentos e sem diferenciar maiúsculas. Assim, mudanças na ordem dos blocos da página não quebram a extração, e "População no último censo" não é confundida com "População estimada".
- **Ano do prefeito descartado.** O portal exibe um ano ao lado do nome do prefeito; ele é removido, pois não faz parte do esquema da planilha.
- **Números no formato brasileiro** (`1.588.983`, `218,843`) são convertidos para inteiro e decimal; unidades ficam fora das células e o ano de referência fica em coluna própria.
- **Tipos anuláveis** (`Int64` do pandas) para população e anos, para suportar campos ausentes sem converter para decimal.
- **Dependências separadas:** `requirements.txt` traz apenas o necessário para executar; `pytest` e `ruff` ficam em `requirements-dev.txt`.

## Fontes utilizadas

- **API de Localidades do IBGE:** <https://servicodados.ibge.gov.br/api/docs/localidades>
  - Estados: `https://servicodados.ibge.gov.br/api/v1/localidades/estados`
  - Municípios por UF: `https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios`
- **Portal Cidades e Estados do IBGE:** <https://www.ibge.gov.br/cidades-e-estados>
  - Formato da página: `https://www.ibge.gov.br/cidades-e-estados/{uf}/{municipio}.html`

Os dados coletados pertencem ao IBGE; o ano de referência de cada valor é registrado na planilha.

## Limitações conhecidas

- **Dependência da estrutura do portal.** A extração se baseia no HTML atual da página (blocos `div.indicador` com rótulo e valor). Se o IBGE alterar a estrutura, os campos podem passar a vir vazios; nesse caso, a ausência é registrada, e o parser precisará ser ajustado.
- **Verificação anti-bot.** O portal pode bloquear acessos automatizados, e o comportamento pode variar conforme rede, horário e IP. Por isso o navegador roda visível por padrão. Se houver bloqueio, o município é registrado como falha e a coleta continua. Não há tentativa de burlar a verificação.
- **Geração da URL (slug).** A URL é montada a partir do nome do município (minúsculas, sem acentos, espaços e hífens preservados como hífen, apóstrofos removidos). Os casos com acento e espaço foram confirmados em municípios de PE. Exemplo: Lagoa d'Anta, Olho d'Água do Borges, Estrela d'Oeste, Embu-Guaçu e Arco-Íris.  Se algum município tiver URL diferente, ele aparecerá como "URL não encontrada" no log e no resumo.
- **Campos que podem não existir.** Nem todo município exibe todos os indicadores; quando um campo não está disponível, a célula fica vazia, sem valor inventado.
- **Execução interrompida (Ctrl+C).** A exportação ocorre ao final da coleta; ao interromper o programa, o que já foi coletado não é salvo.
- **Ambiente gráfico necessário** para o modo padrão (navegador visível).
- **Escopo da coleta.** Pensada para poucos municípios por execução, em respeito ao serviço público. A coleta de todos os municípios do estado não é o objetivo.
