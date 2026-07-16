"""Checagens automáticas de qualidade e confiabilidade do teste A/B.

Todas as checagens são genéricas — nada aqui é específico de um parceiro ou
dataset em particular. O objetivo é que o mesmo código detecte, em qualquer
teste novo, os mesmos tipos de problema que encontramos nos 3 datasets de
referência: grupo com bug de instrumentação (cashback == comissão), mudança
de patamar de cashback no meio do teste (o "teste" para de ser um teste) e
dias de pico simultâneo em todos os grupos (evento externo, não efeito da
variante).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

BUG_EQUALITY_TOLERANCE_BRL = 1.0
BUG_EQUALITY_FRACTION_THRESHOLD = 0.90
REGIME_RELATIVE_TOLERANCE = 0.12
REGIME_MIN_CONSECUTIVE_DAYS = 2
PEAK_QUANTILE = 0.90
POPULATION_RATIO_LOW = 0.80
POPULATION_RATIO_HIGH = 1.20


@dataclass
class QualityReport:
    baseline_group: str = ""
    usable_groups: list[str] = field(default_factory=list)
    excluded_groups: dict[str, str] = field(default_factory=dict)
    decision_window: tuple[date, date] | None = None
    window_truncated: bool = False
    regime_events: list[str] = field(default_factory=list)
    simultaneous_peak_dates: list[date] = field(default_factory=list)
    missing_dates: dict[str, list[date]] = field(default_factory=dict)
    population_imbalance_notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _detect_instrumentation_bug_groups(df: pd.DataFrame) -> dict[str, str]:
    excluded = {}
    for group, grp in df.groupby("group"):
        equal_frac = float((grp["commission"] - grp["cashback"]).abs().le(BUG_EQUALITY_TOLERANCE_BRL).mean())
        if equal_frac >= BUG_EQUALITY_FRACTION_THRESHOLD:
            excluded[group] = (
                f"comissão == cashback em {equal_frac:.0%} dos dias (margem líquida ~R$0 todos os dias) "
                "— padrão típico de bug de instrumentação (coluna espelhada), excluído da decisão por margem"
            )
    return excluded


def _detect_regime_breaks(df: pd.DataFrame, groups: list[str]) -> tuple[dict[str, pd.Timestamp], list[str]]:
    """Para cada grupo, acha a primeira data em que o %cashback sai de forma
    sustentada do patamar inicial. Usado para restringir a janela de decisão
    ao período em que o teste de fato tinha braços distintos e estáveis."""
    breaks: dict[str, pd.Timestamp] = {}
    events: list[str] = []
    for group in groups:
        grp = df[df["group"] == group].sort_values("date").reset_index(drop=True)
        if len(grp) == 0:
            continue
        pct = grp["cashback"] / grp["gmv"]
        anchor_n = min(7, len(grp))
        initial_level = float(pct.iloc[:anchor_n].median())
        if initial_level == 0:
            continue
        rel_dev = (pct - initial_level).abs() / initial_level
        off_level = rel_dev > REGIME_RELATIVE_TOLERANCE

        streak = 0
        break_idx = None
        for i, flag in enumerate(off_level):
            streak = streak + 1 if flag else 0
            if streak >= REGIME_MIN_CONSECUTIVE_DAYS:
                break_idx = i - REGIME_MIN_CONSECUTIVE_DAYS + 1
                break
        if break_idx is not None:
            break_date = grp["date"].iloc[break_idx]
            new_level = float(pct.iloc[break_idx:].median())
            breaks[group] = break_date
            events.append(
                f"{group}: cashback estável em ~{initial_level:.1%} da GMV até "
                f"{grp['date'].iloc[break_idx - 1].date()}, muda a partir de "
                f"{break_date.date()} (novo patamar ~{new_level:.1%})"
            )
    return breaks, events


def _detect_simultaneous_peaks(df: pd.DataFrame, groups: list[str]) -> list[date]:
    peak_sets = []
    for group in groups:
        grp = df[df["group"] == group]
        threshold = grp["gmv"].quantile(PEAK_QUANTILE)
        peak_sets.append(set(grp.loc[grp["gmv"] >= threshold, "date"]))
    if len(peak_sets) < 2:
        return []
    common = set.intersection(*peak_sets)
    return sorted(d.date() for d in common)


def _detect_missing_dates(df: pd.DataFrame, groups: list[str]) -> dict[str, list[date]]:
    missing: dict[str, list[date]] = {}
    for group in groups:
        grp = df[df["group"] == group]
        if grp.empty:
            continue
        full_range = pd.date_range(grp["date"].min(), grp["date"].max(), freq="D")
        present = set(grp["date"])
        gaps = sorted(d.date() for d in full_range if d not in present)
        if gaps:
            missing[group] = gaps
    return missing


def _detect_population_imbalance(df: pd.DataFrame, baseline: str, groups: list[str]) -> list[str]:
    """Sinaliza quando o volume de compradores de uma variante é
    consistentemente muito diferente do baseline (fora de [0.8, 1.2]).
    Não afirma que é bug — só que a métrica de margem ABSOLUTA pode estar
    misturando "efeito do cashback" com "tamanho da fatia de tráfego", e que
    vale olhar métricas normalizadas antes de confiar só na margem em R$."""
    notes = []
    if baseline not in groups:
        return notes
    base = df[df["group"] == baseline].set_index("date")["buyers"]
    for group in groups:
        if group == baseline:
            continue
        variant = df[df["group"] == group].set_index("date")["buyers"]
        common = base.index.intersection(variant.index)
        if len(common) < 10:
            continue
        ratio = (variant.loc[common] / base.loc[common])
        mean_ratio = float(ratio.mean())
        if mean_ratio < POPULATION_RATIO_LOW or mean_ratio > POPULATION_RATIO_HIGH:
            notes.append(
                f"{group} tem em média {mean_ratio:.0%} do volume diário de compradores de {baseline} "
                f"(razão estável dia a dia) — pode ser efeito real do cashback ou diferença de alocação de "
                "tráfego entre variantes; a margem ABSOLUTA por dia favorece o grupo com mais volume "
                "independentemente da causa, então vale conferir as métricas normalizadas (margem/comprador, margem/GMV) antes de decidir só pela margem em R$."
            )
    return notes


def _select_baseline(df: pd.DataFrame, usable_groups: list[str]) -> str:
    if "Grupo 1" in usable_groups:
        return "Grupo 1"
    means = {
        g: float((df.loc[df["group"] == g, "cashback"] / df.loc[df["group"] == g, "gmv"]).mean())
        for g in usable_groups
    }
    return min(means, key=means.get)


def run_quality_checks(df: pd.DataFrame) -> QualityReport:
    report = QualityReport()

    all_groups = sorted(df["group"].unique())
    excluded = _detect_instrumentation_bug_groups(df)
    report.excluded_groups = excluded
    usable_groups = [g for g in all_groups if g not in excluded]
    report.usable_groups = usable_groups

    if len(usable_groups) < 2:
        report.warnings.append(
            "Menos de 2 grupos utilizáveis após checagens de qualidade — não é possível comparar variantes."
        )

    report.baseline_group = _select_baseline(df, usable_groups) if usable_groups else ""

    breaks, events = _detect_regime_breaks(df, usable_groups)
    report.regime_events = events
    full_start, full_end = df["date"].min(), df["date"].max()
    if breaks:
        window_end = min(breaks.values()) - pd.Timedelta(days=1)
        report.window_truncated = True
    else:
        window_end = full_end
    report.decision_window = (full_start.date(), window_end.date())

    report.simultaneous_peak_dates = _detect_simultaneous_peaks(df, usable_groups)
    report.missing_dates = _detect_missing_dates(df, all_groups)
    if report.baseline_group:
        report.population_imbalance_notes = _detect_population_imbalance(
            df, report.baseline_group, usable_groups
        )

    return report
