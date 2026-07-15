# Relatório de Teste A/B de Cashback — Parceiro B

*Gerado automaticamente em 2026-07-15 a partir de `data\dataset_02_parceiroB.csv`.*

## Decisão recomendada

**Manter Grupo 1 (baseline). Nenhuma variante superou a baseline com significância estatística na janela de decisão.**


**Pergunta central:** qual variante de cashback devemos escalar para 100% do tráfego? Baseline de comparação: **Grupo 1** (convenção de nomenclatura / menor % de cashback).

## Qualidade dos dados

**Limpeza do CSV:** nenhuma linha ruim encontrada (sem brancos, duplicatas ou inválidas).

**Bug de instrumentação (cashback == comissão):** não detectado em nenhum grupo.

**Estabilidade de patamar de cashback:** todas as variantes mantiveram o percentual de cashback constante durante todo o teste (sem confundidor de mudança de patamar).

**Dias de pico simultâneo em todos os grupos:** 2011-05-15, 2011-05-22. Provável evento externo (ex.: data comercial, dia de pagamento) e não efeito de variante — a comparação pareada por data já neutraliza esse efeito automaticamente.

## Resumo por grupo

| Grupo | Dias | Compradores/dia (méd.) | Comissão total | Cashback total | GMV total | Margem total | Margem/dia (méd.) | %Cashback médio |
|---|---|---|---|---|---|---|---|---|
| Grupo 1 (baseline) | 61 | 131 | R$ 450.321,00 | R$ 163.751,00 | R$ 4.093.818,00 | R$ 286.570,00 | R$ 4.697,87 | 4.00% |
| Grupo 2 | 61 | 89 | R$ 314.935,00 | R$ 171.778,00 | R$ 2.863.019,00 | R$ 143.157,00 | R$ 2.346,84 | 6.00% |
| Grupo 3 | 61 | 82 | R$ 289.290,00 | R$ 236.697,00 | R$ 2.629.963,00 | R$ 52.593,00 | R$ 862,18 | 9.00% |


## Comparação estatística (margem líquida diária, pareada por data)

Teste t pareado + Wilcoxon (α = 0,05) sobre `comissão − cashback` de cada dia, comparando cada variante à baseline. Uma variante só é considerada vencedora se os dois testes concordarem.

| Variante vs. baseline | Uplift médio margem/dia | p-valor (t pareado) | p-valor (Wilcoxon) | Veredito |
|---|---|---|---|---|
| Grupo 2 | R$ -2.351,03 | 0.0000 | 0.0000 | ❌ Perde da baseline (significativo) |
| Grupo 3 | R$ -3.835,69 | 0.0000 | 0.0000 | ❌ Perde da baseline (significativo) |


## Próximos passos

