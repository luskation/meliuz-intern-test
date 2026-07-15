# Relatório de Teste A/B de Cashback — Parceiro C

*Gerado automaticamente em 2026-07-15 a partir de `data\dataset_03_parceiroC.csv`.*

## Decisão recomendada

**Manter Grupo 1 (baseline) — não é possível validar estatisticamente as demais variantes por problemas de qualidade de dados, mas nenhuma delas se mostra melhor mesmo descritivamente (ver ressalvas). Corrigir a coleta de dados dos grupos excluídos antes de considerar escalá-los.**

_Mesmo se o dado do Grupo 2 estiver correto (não for bug), a margem líquida média observada (R$ 0,00/dia) já é menor que a da baseline Grupo 1 (R$ 772,64/dia) — a recomendação de não escalar Grupo 2 se sustenta nas duas hipóteses._


**Pergunta central:** qual variante de cashback devemos escalar para 100% do tráfego? Baseline de comparação: **Grupo 1** (convenção de nomenclatura / menor % de cashback).

## Qualidade dos dados

**Limpeza do CSV:** nenhuma linha ruim encontrada (sem brancos, duplicatas ou inválidas).

**⚠️ Grupo(s) excluído(s) da decisão por suspeita de bug de instrumentação:**

- **Grupo 2**: comissão == cashback em 100% dos dias (margem líquida ~R$0 todos os dias) — padrão típico de bug de instrumentação (coluna espelhada), excluído da decisão por margem

**Estabilidade de patamar de cashback:** todas as variantes mantiveram o percentual de cashback constante durante todo o teste (sem confundidor de mudança de patamar).

> ⚠️ Menos de 2 grupos utilizáveis após checagens de qualidade — não é possível comparar variantes.

## Resumo por grupo

| Grupo | Dias | Compradores/dia (méd.) | Comissão total | Cashback total | GMV total | Margem total | Margem/dia (méd.) | %Cashback médio |
|---|---|---|---|---|---|---|---|---|
| Grupo 1 (baseline) | 45 | 101 | R$ 121.693,00 | R$ 86.924,00 | R$ 1.738.460,00 | R$ 34.769,00 | R$ 772,64 | 5.00% |


## Próximos passos

- Corrigir a coleta de dados dos grupos excluídos (ver seção de qualidade) antes de reaproveitar esse teste como referência.
