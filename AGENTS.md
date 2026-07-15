# Instruções para agentes de IA (Claude Code, Cursor, GPT, Gemini, etc.)

Este repositório contém uma ferramenta de análise de teste A/B de cashback do
Méliuz. Se o usuário pedir, em linguagem natural, para "analisar um teste
A/B", "ver qual variante escalar", "rodar o teste do parceiro X" ou algo
equivalente, apontando para um arquivo `.csv`, siga este processo:

## 1. Rodar a análise

Execute a CLI do projeto — não reimplemente a lógica de análise manualmente,
ela já existe e é testada:

```bash
python scripts/analyze_ab_test.py --input <caminho_do_csv>
```

Se `.venv` não existir ainda no repositório, crie e instale as dependências
primeiro:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); em Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Ler o resultado

O comando gera dois artefatos:
- `reports/<nome_do_arquivo>.md` — relatório completo (qualidade dos dados, comparação estatística, decisão);
- uma nova linha em `tracking/testes_ab.csv` — registro do teste.

Leia o `.md` gerado.

## 3. Responder ao usuário em linguagem natural

Não apenas cole o relatório inteiro. Traduza para uma resposta objetiva,
em português, cobrindo:
- **A decisão recomendada** (qual grupo escalar para 100%, ou manter a baseline) e por quê, em termos de negócio (margem líquida, não só volume);
- **Ressalvas relevantes** encontradas na checagem de qualidade (grupo excluído por bug, janela de teste restrita por mudança de patamar de cashback, etc.) — se existirem, são tão importantes quanto a decisão em si;
- Ofereça abrir o relatório completo (`reports/<arquivo>.md`) se o usuário quiser os números e p-valores.

## Regras importantes

- **Nunca hardcode** nomes de parceiro, número de grupos ou datas — a ferramenta já é genérica e detecta isso a partir do CSV. Se o dataset tiver um schema diferente do esperado (colunas `Data, Grupos de usuários, Parceiro, compradores, comissão, cashback, vendas totais`), o script falha com uma mensagem clara — reporte esse erro ao usuário em vez de tentar adivinhar o schema.
- **Não decida sozinho questões de negócio** que a ferramenta sinaliza como ambíguas (ex: grupo com dado suspeito, janela de teste instável) — repasse a ressalva do relatório ao usuário, não a esconda para simplificar a resposta.
- Se o usuário pedir para analisar um CSV fora da pasta `data/`, funciona normalmente — o `--input` aceita qualquer caminho.
