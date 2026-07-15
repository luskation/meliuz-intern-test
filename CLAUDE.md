# CLAUDE.md

Contexto e convenções deste repositório — leia antes de mexer em qualquer coisa.

## O que é este projeto

Entrega do teste técnico de Estágio em Operações Integradas da Méliuz.
Objetivo: uma solução reutilizável que recebe os dados de um teste A/B de
cashback (CSV) e devolve uma análise completa + uma decisão acionável:
"qual variante de cashback devemos escalar pra 100% do tráfego?".

A mesma solução precisa rodar para qualquer um dos 3 datasets fornecidos
(e, no futuro, qualquer teste novo) sem alteração de código — só apontando
pro arquivo.

## Como trabalhar neste repositório

- **Branch de desenvolvimento atual:** `claude/meliuz-internship-project-w5fh8r`
  (veio pré-atribuída pelo ambiente desta sessão). **Ainda não decidido**
  se a entrega final fica aqui ou é movida pra `main` — perguntar ao
  usuário antes de mexer na branch final.
- **Commits:** mensagens descritivas em português, um commit por etapa
  lógica concluída (não um commit por arquivo isolado).
- **Nunca** rodar comandos destrutivos de git (`reset --hard`,
  `push --force`, `branch -D`, exclusão de repositório) sem confirmação
  explícita do usuário na conversa.
- **Sempre perguntar antes de decisões de produto/negócio** (ex: qual
  métrica usar, como tratar um grupo com dado suspeito). Decisões técnicas
  de implementação (ex: como parsear uma string de moeda) podem ser
  tomadas com justificativa, sem precisar perguntar.
- Ir com calma: preferir confirmar entendimento e mostrar resultado parcial
  a construir tudo de uma vez sem check-in.

## Estrutura do repositório

```
data/                    # datasets brutos fornecidos pela Méliuz (não alterar)
scripts/ab_toolkit/       # motor de análise reutilizável
  parsing.py               # leitura + limpeza robusta do CSV (moeda pt-BR, linhas ruins etc.)
  quality.py                # checagens automáticas de qualidade/confiabilidade dos dados
  stats.py                  # agregação por grupo + comparação estatística + decisão
  report.py                  # gera o relatório Markdown final (apresentável a gestor)
  tracking.py                 # grava linha no CSV de acompanhamento (e opcionalmente no Google Sheets)
scripts/analyze_ab_test.py  # CLI única: `python scripts/analyze_ab_test.py --input <arquivo.csv>`
reports/                  # relatórios .md gerados, um por teste
tracking/testes_ab.csv    # planilha de acompanhamento de todos os testes já rodados
.venv/                    # ambiente virtual Python (gitignored, não versionar)
```

## Decisões de arquitetura já tomadas (não re-discutir sem motivo)

- **Linguagem/stack:** Python 3 + pandas/numpy/scipy. Ambiente virtual em
  `.venv/`.
- **Baseline dos testes A/B:** "Grupo 1" por convenção de nome. Se não
  existir grupo com esse nome, cai pro grupo de menor % de cashback médio.
- **Métrica de decisão:** margem líquida diária (comissão − cashback),
  comparada dia a dia (pareado por data) entre cada variante e a baseline.
  Motivo: cashback maior pode trazer mais compradores/GMV, mas custa mais
  — a decisão precisa olhar lucro, não só volume.
- **Testes estatísticos:** teste t pareado + Wilcoxon (α = 0.05); uma
  variante só é considerada vencedora se os dois concordarem.
- **Checagens de qualidade automáticas:** parsing de moeda pt-BR, linhas
  em branco/duplicadas/negativas, grupo com cashback idêntico à comissão
  (bug de instrumentação), dias de pico simultâneo em todos os grupos
  (evento externo, não efeito do teste), mudança de patamar de cashback no
  meio do teste (possível confundidor).
- **Planilha de acompanhamento:** CSV local é o mínimo aceito e sempre
  funciona sem credencial. Google Sheets é diferencial opcional, ativado
  por variáveis de ambiente `GOOGLE_SHEETS_ID` e
  `GOOGLE_SHEETS_CREDENTIALS_JSON` (módulo já implementado, não conectado
  ainda de verdade).

## Status atual

- [x] Parser, checagens de qualidade, motor estatístico, relatório e
      tracking implementados e testados nos 3 datasets reais.
- [ ] README explicando como rodar o projeto.
- [ ] Camada de linguagem natural (comando/skill para agentes de IA tipo
      Claude Code/Cursor/GPT/Gemini invocarem a análise por conversa).
- [ ] Revisão dos 3 relatórios junto com o usuário.
- [ ] Decidir branch final de entrega e mover se necessário.
- [ ] (Opcional) Conectar Google Sheets de verdade.

## Como rodar (referência rápida)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # ainda não criado — ver Status atual
python scripts/analyze_ab_test.py --input data/dataset_01_parceiroA.csv
```
