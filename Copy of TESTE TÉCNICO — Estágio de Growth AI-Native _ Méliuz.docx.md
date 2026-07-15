# **TESTE TÉCNICO — Estágio de Ops Integradas | Méliuz**

*Méliuz · Time de Operações Integradas*

Esse teste foi pensado pra ser justo, claro e parecido com problemas que você vai encontrar caso entre no time. Leia tudo com calma antes de começar.

**1\. Sobre a vaga**

Estamos contratando estagiário(a) de Operações Integradas — alguém que combina pensamento de growth com fluência em ferramentas de IA modernas (Claude, Claude Code, Cursor, ChatGPT, Gemini, agentes, etc.). A pessoa vai construir automações e análises que ampliam o que o time consegue fazer.

Esse teste avalia duas capacidades simultaneamente:

* **Capacidade de construção:** arquitetar uma solução reutilizável, parametrizada, robusta a dados ruins.

* **Capacidade analítica:** ler dados de teste A/B com olho crítico, identificar problemas, e tomar decisão acionável.

**2\. Contexto**

O Méliuz é uma plataforma brasileira de cashback. Nosso time roda dezenas de testes A/B por mês — variações de % de cashback por parceiro, layout de página, copy, ofertas exclusivas, segmentação. Cada teste, quando bem analisado, ajusta uma alavanca real do negócio.

Hoje a análise de cada teste leva de 2 a 4 horas e depende muito de quem está olhando — o que gera inconsistência e gargalo. Queremos automatizar isso com uma **solução reutilizável** que qualquer pessoa do time consiga rodar pra qualquer teste novo. Esse teste técnico é a primeira versão dessa solução.

**3\. A tarefa**

Construa uma **solução reutilizável** que recebe os dados de um teste A/B de cashback e retorna uma análise completa e uma decisão acionável.

A ideia é que seja fácil de reaproveitar e de acionar: uma pessoa abre uma ferramenta de IA (como Claude Code, Cursor, um GPT personalizado ou o Gemini), pede em linguagem natural pra analisar um teste novo, indica o arquivo do dataset, e recebe de volta a análise e a recomendação. Como você estrutura isso por dentro é decisão sua (instruções, scripts, prompts — a organização que achar melhor). Queremos justamente ver qual arquitetura você considera ideal para esse problema.

A mesma solução precisa processar os **3 datasets** fornecidos **sem alteração de código** — apenas indicando o novo arquivo. 

**Pergunta central:** *"Dado esse teste A/B, qual variante de cashback devemos escalar pra 100% do tráfego?"*

Ao terminar a análise, a própria solução deve registrar o teste em uma planilha do Sheets para acompanhar todos os testes rodados. Você cria a planilha e compartilha o link com acesso público. Cada linha \= um teste, com **no mínimo**: nome do teste, descrição, resultado e decisão tomada. Escrever direto no Sheets é o cenário ideal e conta como diferencial. O mínimo aceito é gerar um CSV no formato da planilha.

**4\. Inputs**

**4.1 Datasets**

Na mesma pasta do Google Drive compartilhada com este documento estão os **3 CSVs** — Parceiros A, B e C. Todos seguem o mesmo schema, mas com parceiros, períodos e número de variantes diferentes.

**4.2 Schema dos CSVs**

Todos os 3 datasets têm o **mesmo schema**:

| Coluna | Tipo | Descrição |
| :---- | :---- | :---- |
| Data | YYYY-MM-DD | Data da observação |
| Grupos de usuários | string | Variante do teste (Grupo 1, Grupo 2, Grupo 3\) |
| Parceiro | string | Parceiro do teste (A, B ou C) |
| compradores | int | Usuários únicos que compraram no dia |
| comissão | string (R$) | Comissão paga pelo parceiro ao Méliuz no dia |
| cashback | string (R$) | Cashback distribuído aos usuários no dia |
| vendas totais | string (R$) | GMV (valor total das vendas) no dia |

**5\. O que a solução deve entregar**

Para cada teste analisado:

* **Relatório dos testes A/B**: o formato é sua escolha, mas precisa ser apresentável para um gestor;

* **Resumo consolidado** e registrado em uma planilha (Google Sheets ou CSV).

**6\. Como entregar**

Responda o **email do processo** (Gupy) com o link do **seu repositório GitHub público**, contendo:

* A solução (suas instruções e scripts)

* README de como rodar

* Os relatórios dos testes A/B gerados

* O link da planilha de acompanhamento (Google Sheets ou CSV) preenchida, com acesso de leitura

Antes de enviar, garanta que o repositório está **PÚBLICO** (testa em janela anônima). Pode usar sua conta pessoal do GitHub.