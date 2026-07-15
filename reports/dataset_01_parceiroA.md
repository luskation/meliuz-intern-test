# Relatório de Teste A/B de Cashback — Parceiro A

*Gerado automaticamente em 2026-07-15 a partir de `data\dataset_01_parceiroA.csv`.*

## Decisão recomendada

**Manter Grupo 1 (baseline). Nenhuma variante superou a baseline com significância estatística na janela de decisão.**


**Pergunta central:** qual variante de cashback devemos escalar para 100% do tráfego? Baseline de comparação: **Grupo 1** (convenção de nomenclatura / menor % de cashback).

## Qualidade dos dados

**Limpeza do CSV:** nenhuma linha ruim encontrada (sem brancos, duplicatas ou inválidas).

**Bug de instrumentação (cashback == comissão):** não detectado em nenhum grupo.

**⚠️ Mudança de patamar de cashback durante o teste (possível confundidor):**

- Grupo 1: cashback estável em ~3.1% da GMV até 2011-02-22, muda a partir de 2011-02-23 (novo patamar ~5.0%)
- Grupo 2: cashback estável em ~5.5% da GMV até 2011-03-10, muda a partir de 2011-03-11 (novo patamar ~5.0%)
- Grupo 3: cashback estável em ~8.0% da GMV até 2011-02-22, muda a partir de 2011-02-23 (novo patamar ~5.0%)

Por isso, a decisão abaixo considera apenas a janela estável **2011-01-01 a 2011-02-22**, onde todas as variantes tinham patamares de cashback distintos e constantes. O período após essa janela existe no dataset mas foi excluído da comparação estatística.

**Dias de pico simultâneo em todos os grupos:** 2011-01-08, 2011-01-11, 2011-01-13, 2011-01-14, 2011-03-12. Provável evento externo (ex.: data comercial, dia de pagamento) e não efeito de variante — a comparação pareada por data já neutraliza esse efeito automaticamente.

## Resumo por grupo

| Grupo | Dias | Compradores/dia (méd.) | Comissão total | Cashback total | GMV total | Margem total | Margem/dia (méd.) | %Cashback médio |
|---|---|---|---|---|---|---|---|---|
| Grupo 1 (baseline) | 53 | 118 | R$ 396.687,00 | R$ 109.417,00 | R$ 3.606.278,00 | R$ 287.270,00 | R$ 5.420,19 | 3.03% |
| Grupo 2 | 53 | 139 | R$ 491.740,00 | R$ 245.880,00 | R$ 4.470.338,00 | R$ 245.860,00 | R$ 4.638,87 | 5.50% |
| Grupo 3 | 53 | 151 | R$ 535.226,00 | R$ 387.822,00 | R$ 4.865.459,00 | R$ 147.404,00 | R$ 2.781,21 | 7.97% |


## Comparação estatística (margem líquida diária, pareada por data)

Teste t pareado + Wilcoxon (α = 0,05) sobre `comissão − cashback` de cada dia, comparando cada variante à baseline. Uma variante só é considerada vencedora se os dois testes concordarem.

| Variante vs. baseline | Uplift médio margem/dia | p-valor (t pareado) | p-valor (Wilcoxon) | Veredito |
|---|---|---|---|---|
| Grupo 2 | R$ -781,32 | 0.0000 | 0.0000 | ❌ Perde da baseline (significativo) |
| Grupo 3 | R$ -2.638,98 | 0.0000 | 0.0000 | ❌ Perde da baseline (significativo) |


## Próximos passos

- Investigar por que os grupos convergiram de patamar de cashback após a janela estável — se foi decisão de negócio, o teste já estava sendo encerrado; se não, é um problema de execução do teste.
