# Relatório de Teste A/B de Cashback — Parceiro B

*Gerado automaticamente em 2026-07-15 a partir de `data/dataset_02_parceiroB.csv`.*

## Decisão recomendada

**Manter Grupo 1 (baseline) com confiança: todas as 2 variante(s) testada(s) perderam da baseline com significância estatística (p < 0.05 em teste t e Wilcoxon) — não é apenas 'sem evidência de ganho', é evidência de que escalar qualquer uma delas reduziria a margem.**


**Pergunta central:** qual variante de cashback devemos escalar para 100% do tráfego? Baseline de comparação: **Grupo 1** (convenção de nomenclatura / menor % de cashback).

## Qualidade dos dados

**Limpeza do CSV:** nenhuma linha ruim encontrada (sem brancos, duplicatas ou inválidas).

**Bug de instrumentação (cashback == comissão):** não detectado em nenhum grupo.

**Estabilidade de patamar de cashback:** todas as variantes mantiveram o percentual de cashback constante durante todo o teste (sem confundidor de mudança de patamar).

**Dias de pico simultâneo em todos os grupos:** 2011-05-15, 2011-05-22. Provável evento externo (ex.: data comercial, dia de pagamento) e não efeito de variante — a comparação pareada por data já neutraliza esse efeito automaticamente.

**⚠️ Diferença de volume de compradores entre grupos:**

- Grupo 2 tem em média 68% do volume diário de compradores de Grupo 1 (razão estável dia a dia) — pode ser efeito real do cashback ou diferença de alocação de tráfego entre variantes; a margem ABSOLUTA por dia favorece o grupo com mais volume independentemente da causa, então vale conferir as métricas normalizadas (margem/comprador, margem/GMV) antes de decidir só pela margem em R$.
- Grupo 3 tem em média 64% do volume diário de compradores de Grupo 1 (razão estável dia a dia) — pode ser efeito real do cashback ou diferença de alocação de tráfego entre variantes; a margem ABSOLUTA por dia favorece o grupo com mais volume independentemente da causa, então vale conferir as métricas normalizadas (margem/comprador, margem/GMV) antes de decidir só pela margem em R$.

## Resumo por grupo

| Grupo | Dias | Compradores/dia (méd.) | Comissão total | Cashback total | GMV total | Margem total | Margem/dia (méd.) | %Cashback médio |
|---|---|---|---|---|---|---|---|---|
| Grupo 1 (baseline) | 61 | 131 | R$ 450.321,00 | R$ 163.751,00 | R$ 4.093.818,00 | R$ 286.570,00 | R$ 4.697,87 | 4.00% |
| Grupo 2 | 61 | 89 | R$ 314.935,00 | R$ 171.778,00 | R$ 2.863.019,00 | R$ 143.157,00 | R$ 2.346,84 | 6.00% |
| Grupo 3 | 61 | 82 | R$ 289.290,00 | R$ 236.697,00 | R$ 2.629.963,00 | R$ 52.593,00 | R$ 862,18 | 9.00% |


**Métricas normalizadas (checagem de sensibilidade):** a margem total em R$ favorece grupos com mais volume — se os grupos não têm o mesmo tamanho de tráfego, isso pode enviesar a comparação em R$ absolutos mesmo sem nenhum efeito real do cashback. As métricas abaixo (por comprador e como % da GMV) não dependem do tamanho do grupo e servem para confirmar que a decisão não é só um artefato de volume.

| Grupo | Margem por comprador | Margem como % da GMV |
|---|---|---|
| Grupo 1 (baseline) | R$ 35,87 | 7.00% |
| Grupo 2 | R$ 26,26 | 5.00% |
| Grupo 3 | R$ 10,46 | 2.00% |


## Comparação estatística (margem líquida diária, pareada por data)

Teste t pareado + Wilcoxon (α = 0,05) sobre `comissão − cashback` de cada dia, comparando cada variante à baseline. Uma variante só é considerada vencedora se os dois testes concordarem.

| Variante vs. baseline | Uplift médio margem/dia | p-valor (t pareado) | p-valor (Wilcoxon) | Veredito |
|---|---|---|---|---|
| Grupo 2 | R$ -2.351,03 | 0.0000 | 0.0000 | ❌ Perde da baseline (significativo) |
| Grupo 3 | R$ -3.835,69 | 0.0000 | 0.0000 | ❌ Perde da baseline (significativo) |


## Limitações da análise

- **Autocorrelação temporal:** os dias não são independentes entre si (efeito dia-da-semana, sazonalidade) — o teste t e o Wilcoxon assumem observações pareadas independentes, o que é uma simplificação comum, mas vale ter em mente ao interpretar o p-valor como probabilidade exata.
- **Dados agregados por dia, não por usuário:** não é possível medir variância entre usuários dentro do mesmo dia, nem detectar heterogeneidade de efeito por segmento.
- **Múltiplas comparações:** quando há mais de uma variante, cada uma é comparada à baseline a α = 0,05 sem correção (ex.: Bonferroni) — com mais variantes, a chance de um falso positivo isolado sobe.


## Próximos passos

- Confirmar junto ao time de instrumentação se a alocação de tráfego entre variantes foi igualitária; se não foi por desenho, considerar a métrica normalizada (margem/comprador) como critério principal em vez da margem absoluta.
