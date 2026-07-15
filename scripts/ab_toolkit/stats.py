"""Agregação por grupo, comparação estatística pareada e decisão final.

Métrica de decisão: margem líquida diária (comissão - cashback), comparada
dia a dia (pareado por data) entre cada variante e a baseline. Uma variante
só é considerada vencedora se teste t pareado E Wilcoxon concordarem
(p < 0.05) que a margem é maior que a da baseline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from .quality import QualityReport

ALPHA = 0.05


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


@dataclass
class GroupSummary:
    group: str
    days: int
    buyers_mean: float
    commission_sum: float
    cashback_sum: float
    gmv_sum: float
    margin_sum: float
    margin_mean: float
    cashback_pct_mean: float


@dataclass
class Comparison:
    group: str
    baseline: str
    n_days: int
    mean_uplift_margin: float
    t_stat: float
    t_pvalue: float
    wilcoxon_stat: float | None
    wilcoxon_pvalue: float | None
    verdict: str  # "SIGNIFICANTLY_BETTER" | "SIGNIFICANTLY_WORSE" | "INCONCLUSIVE" | "NO_DIFFERENCE"
    estimated_extra_days_needed: int | None = None


@dataclass
class DecisionResult:
    baseline_group: str
    summaries: dict[str, GroupSummary] = field(default_factory=dict)
    comparisons: list[Comparison] = field(default_factory=list)
    winner: str | None = None
    decision_text: str = ""
    confidence_note: str = ""
    excluded_group_notes: list[str] = field(default_factory=list)


def _summarize_group(df: pd.DataFrame, group: str) -> GroupSummary:
    grp = df[df["group"] == group]
    margin = grp["commission"] - grp["cashback"]
    cashback_pct = grp["cashback"] / grp["gmv"]
    return GroupSummary(
        group=group,
        days=len(grp),
        buyers_mean=float(grp["buyers"].mean()),
        commission_sum=float(grp["commission"].sum()),
        cashback_sum=float(grp["cashback"].sum()),
        gmv_sum=float(grp["gmv"].sum()),
        margin_sum=float(margin.sum()),
        margin_mean=float(margin.mean()),
        cashback_pct_mean=float(cashback_pct.mean()),
    )


def _estimate_extra_days(diffs: np.ndarray) -> int | None:
    """Estimativa aproximada (regra de bolso) de quantos dias a mais de coleta
    seriam necessários para detectar o efeito observado com poder ~80% a
    alpha=5%, assumindo que o efeito e a variância observados se mantenham."""
    mean_diff = diffs.mean()
    sd_diff = diffs.std(ddof=1)
    if mean_diff == 0 or sd_diff == 0 or np.isnan(sd_diff):
        return None
    z_alpha2, z_beta = 1.96, 0.84
    n_needed = ((z_alpha2 + z_beta) * sd_diff / mean_diff) ** 2
    extra = int(np.ceil(n_needed)) - len(diffs)
    return max(extra, 0) if extra > 0 else None


def _compare_to_baseline(df: pd.DataFrame, group: str, baseline: str) -> Comparison:
    variant_margin = (df[df["group"] == group].set_index("date")["commission"]
                       - df[df["group"] == group].set_index("date")["cashback"])
    baseline_margin = (df[df["group"] == baseline].set_index("date")["commission"]
                        - df[df["group"] == baseline].set_index("date")["cashback"])
    common_dates = variant_margin.index.intersection(baseline_margin.index)
    variant_margin = variant_margin.loc[common_dates].sort_index()
    baseline_margin = baseline_margin.loc[common_dates].sort_index()

    diffs = (variant_margin - baseline_margin).to_numpy()

    t_stat, t_p = scipy_stats.ttest_rel(variant_margin, baseline_margin)

    if np.allclose(diffs, 0):
        w_stat, w_p = None, 1.0
    else:
        try:
            w_stat, w_p = scipy_stats.wilcoxon(variant_margin, baseline_margin)
        except ValueError:
            w_stat, w_p = None, None

    mean_uplift = float(diffs.mean())
    t_sig = t_p < ALPHA
    w_sig = (w_p is not None) and (w_p < ALPHA)

    if t_sig and w_sig:
        verdict = "SIGNIFICANTLY_BETTER" if mean_uplift > 0 else "SIGNIFICANTLY_WORSE"
        extra_days = None
    elif t_sig != w_sig:
        verdict = "INCONCLUSIVE"
        extra_days = _estimate_extra_days(diffs)
    else:
        verdict = "NO_DIFFERENCE"
        extra_days = _estimate_extra_days(diffs)

    return Comparison(
        group=group,
        baseline=baseline,
        n_days=len(common_dates),
        mean_uplift_margin=mean_uplift,
        t_stat=float(t_stat),
        t_pvalue=float(t_p),
        wilcoxon_stat=float(w_stat) if w_stat is not None else None,
        wilcoxon_pvalue=float(w_p) if w_p is not None else None,
        verdict=verdict,
        estimated_extra_days_needed=extra_days,
    )


def _descriptive_note_for_excluded_group(df: pd.DataFrame, group: str, baseline: str) -> tuple[str, bool]:
    """Comparação descritiva (sem teste de significância) entre um grupo
    excluído por bug e a baseline, para sustentar a decisão mesmo se o dado
    excluído acabar sendo real (não bug) — normalmente esses grupos têm
    margem ~R$0 por construção, o que já perde da baseline de qualquer jeito.
    Retorna (texto, grupo_excluido_e_pior_ou_igual)."""
    variant = df[df["group"] == group].set_index("date")
    base = df[df["group"] == baseline].set_index("date")
    common_dates = variant.index.intersection(base.index)
    if len(common_dates) == 0:
        return "", True
    variant_margin_mean = (variant.loc[common_dates, "commission"] - variant.loc[common_dates, "cashback"]).mean()
    base_margin_mean = (base.loc[common_dates, "commission"] - base.loc[common_dates, "cashback"]).mean()
    if variant_margin_mean < base_margin_mean:
        return (
            f"Mesmo se o dado do {group} estiver correto (não for bug), a margem líquida média observada "
            f"({_fmt_brl(variant_margin_mean)}/dia) já é menor que a da baseline {baseline} "
            f"({_fmt_brl(base_margin_mean)}/dia) — a recomendação de não escalar {group} se sustenta nas duas hipóteses."
        ), True
    return (
        f"Atenção: apesar do bug suspeito, a margem bruta média do {group} ({_fmt_brl(variant_margin_mean)}/dia) "
        f"é maior que a da baseline ({_fmt_brl(base_margin_mean)}/dia) — vale corrigir a coleta antes de descartar essa variante."
    ), False


def analyze(df: pd.DataFrame, quality: QualityReport) -> DecisionResult:
    start, end = quality.decision_window
    window_df = df[
        (df["group"].isin(quality.usable_groups))
        & (df["date"].dt.date >= start)
        & (df["date"].dt.date <= end)
    ]

    result = DecisionResult(baseline_group=quality.baseline_group)

    for group in quality.usable_groups:
        result.summaries[group] = _summarize_group(window_df, group)

    variants = [g for g in quality.usable_groups if g != quality.baseline_group]
    for group in variants:
        result.comparisons.append(_compare_to_baseline(window_df, group, quality.baseline_group))

    excluded_all_worse = True
    if quality.baseline_group:
        for group in quality.excluded_groups:
            note, is_worse = _descriptive_note_for_excluded_group(df, group, quality.baseline_group)
            if note:
                result.excluded_group_notes.append(note)
            excluded_all_worse = excluded_all_worse and is_worse

    winners = [c for c in result.comparisons if c.verdict == "SIGNIFICANTLY_BETTER"]
    losers = [c for c in result.comparisons if c.verdict == "SIGNIFICANTLY_WORSE"]
    inconclusive = [c for c in result.comparisons if c.verdict == "INCONCLUSIVE"]

    if winners:
        best = max(winners, key=lambda c: c.mean_uplift_margin)
        result.winner = best.group
        result.decision_text = (
            f"Escalar {best.group} para 100% do tráfego. Margem líquida diária "
            f"R$ {best.mean_uplift_margin:,.2f} maior que a baseline ({quality.baseline_group}), "
            f"com teste t e Wilcoxon concordando (p={best.t_pvalue:.4f} / p={best.wilcoxon_pvalue:.4f})."
        )
        if len(winners) > 1:
            others = ", ".join(c.group for c in winners if c.group != best.group)
            result.confidence_note = (
                f"Outras variantes também superaram a baseline com significância ({others}), "
                f"mas {best.group} teve o maior ganho médio de margem."
            )
    elif not variants:
        if excluded_all_worse:
            result.decision_text = (
                f"Manter {quality.baseline_group} (baseline) — não é possível validar estatisticamente as demais "
                "variantes por problemas de qualidade de dados, mas nenhuma delas se mostra melhor mesmo "
                "descritivamente (ver ressalvas). Corrigir a coleta de dados dos grupos excluídos antes de "
                "considerar escalá-los."
            )
        else:
            result.decision_text = (
                f"Sem decisão segura: {quality.baseline_group} (baseline) é a única variante estatisticamente "
                "válida, mas ao menos um grupo excluído por bug parece ter margem descritiva maior — corrigir a "
                "coleta de dados e reprocessar antes de decidir escalar qualquer variante."
            )
    elif inconclusive and not losers:
        result.decision_text = (
            f"Sem decisão estatisticamente segura ainda: manter {quality.baseline_group} rodando por enquanto. "
            "Teste t e Wilcoxon discordam para pelo menos uma variante — ver ressalvas para dias adicionais estimados."
        )
    else:
        result.decision_text = (
            f"Manter {quality.baseline_group} (baseline). Nenhuma variante superou a baseline com significância "
            "estatística na janela de decisão."
        )

    return result
