---
description: Analisa um teste A/B de cashback (CSV) e recomenda qual variante escalar para 100%
---

Analise o teste A/B de cashback no arquivo: $ARGUMENTS

Siga exatamente o processo descrito em `AGENTS.md` na raiz deste
repositório: rode `python scripts/analyze_ab_test.py --input <arquivo>` (crie
e ative o `.venv` e instale `requirements.txt` primeiro se ainda não
existirem), leia o relatório gerado em `reports/`, e responda em português
com a decisão recomendada, a justificativa em termos de negócio (margem
líquida, não só volume) e qualquer ressalva de qualidade de dados encontrada.
