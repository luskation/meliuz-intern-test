"""Gera o relatório Markdown final — apresentável a um gestor não-técnico."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .parsing import ParseReport
from .quality import QualityReport
from .stats import DecisionResult

VERDICT_LABEL = {
    "SIGNIFICANTLY_BETTER": "✅ Vence a baseline (significativo)",
    "SIGNIFICANTLY_WORSE": "❌ Perde da baseline (significativo)",
    "INCONCLUSIVE": "⚠️ Inconclusivo (t e Wilcoxon discordam)",
    "NO_DIFFERENCE": "➖ Sem diferença estatística",
}


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _quality_section(parse: ParseReport, quality: QualityReport) -> str:
    lines = ["## Qualidade dos dados\n"]

    parsing_notes = []
    if parse.linhas_em_branco_removidas:
        parsing_notes.append(f"{parse.linhas_em_branco_removidas} linha(s) em branco removida(s)")
    if parse.linhas_duplicadas_removidas:
        parsing_notes.append(f"{parse.linhas_duplicadas_removidas} linha(s) duplicada(s) removida(s)")
    if parse.linhas_invalidas_removidas:
        parsing_notes.append(
            f"{parse.linhas_invalidas_removidas} linha(s) inválida(s) removida(s) ("
            + "; ".join(parse.motivos_invalidas) + ")"
        )
    if parsing_notes:
        lines.append("**Limpeza do CSV:** " + "; ".join(parsing_notes) + ".\n")
    else:
        lines.append("**Limpeza do CSV:** nenhuma linha ruim encontrada (sem brancos, duplicatas ou inválidas).\n")

    if quality.excluded_groups:
        lines.append("**⚠️ Grupo(s) excluído(s) da decisão por suspeita de bug de instrumentação:**\n")
        for g, reason in quality.excluded_groups.items():
            lines.append(f"- **{g}**: {reason}")
        lines.append("")
    else:
        lines.append("**Bug de instrumentação (cashback == comissão):** não detectado em nenhum grupo.\n")

    if quality.regime_events:
        lines.append("**⚠️ Mudança de patamar de cashback durante o teste (possível confundidor):**\n")
        for ev in quality.regime_events:
            lines.append(f"- {ev}")
        lines.append(
            f"\nPor isso, a decisão abaixo considera apenas a janela estável "
            f"**{quality.decision_window[0]} a {quality.decision_window[1]}**, "
            "onde todas as variantes tinham patamares de cashback distintos e constantes. "
            "O período após essa janela existe no dataset mas foi excluído da comparação estatística.\n"
        )
    else:
        lines.append("**Estabilidade de patamar de cashback:** todas as variantes mantiveram o percentual de cashback constante durante todo o teste (sem confundidor de mudança de patamar).\n")

    if quality.simultaneous_peak_dates:
        dates_str = ", ".join(str(d) for d in quality.simultaneous_peak_dates)
        lines.append(
            f"**Dias de pico simultâneo em todos os grupos:** {dates_str}. "
            "Provável evento externo (ex.: data comercial, dia de pagamento) e não efeito de variante — "
            "a comparação pareada por data já neutraliza esse efeito automaticamente.\n"
        )

    if quality.missing_dates:
        lines.append("**Datas ausentes por grupo:**\n")
        for g, dates in quality.missing_dates.items():
            preview = ", ".join(str(d) for d in dates[:5])
            suffix = f" (+{len(dates) - 5} outra(s))" if len(dates) > 5 else ""
            lines.append(f"- {g}: {preview}{suffix}")
        lines.append("")

    if quality.warnings:
        for w in quality.warnings:
            lines.append(f"> ⚠️ {w}")
        lines.append("")

    return "\n".join(lines)


def _summary_table(decision: DecisionResult) -> str:
    header = (
        "| Grupo | Dias | Compradores/dia (méd.) | Comissão total | Cashback total | "
        "GMV total | Margem total | Margem/dia (méd.) | %Cashback médio |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    rows = []
    for group, s in decision.summaries.items():
        tag = " (baseline)" if group == decision.baseline_group else ""
        rows.append(
            f"| {group}{tag} | {s.days} | {s.buyers_mean:.0f} | {_fmt_brl(s.commission_sum)} | "
            f"{_fmt_brl(s.cashback_sum)} | {_fmt_brl(s.gmv_sum)} | {_fmt_brl(s.margin_sum)} | "
            f"{_fmt_brl(s.margin_mean)} | {s.cashback_pct_mean:.2%} |"
        )
    return header + "\n".join(rows) + "\n"


def _comparison_table(decision: DecisionResult) -> str:
    header = (
        "| Variante vs. baseline | Uplift médio margem/dia | p-valor (t pareado) | "
        "p-valor (Wilcoxon) | Veredito |\n|---|---|---|---|---|\n"
    )
    rows = []
    for c in decision.comparisons:
        w_p = f"{c.wilcoxon_pvalue:.4f}" if c.wilcoxon_pvalue is not None else "n/a"
        rows.append(
            f"| {c.group} | {_fmt_brl(c.mean_uplift_margin)} | {c.t_pvalue:.4f} | {w_p} | "
            f"{VERDICT_LABEL[c.verdict]} |"
        )
    table = header + "\n".join(rows) + "\n"

    extra_notes = [
        f"- **{c.group}**: resultado inconclusivo com os dados atuais; estimativa aproximada de mais "
        f"~{c.estimated_extra_days_needed} dia(s) de coleta para decidir com confiança, mantido o efeito observado."
        for c in decision.comparisons
        if c.verdict in ("INCONCLUSIVE", "NO_DIFFERENCE") and c.estimated_extra_days_needed
    ]
    if extra_notes:
        table += "\n" + "\n".join(extra_notes) + "\n"
    return table


def build_report(
    partner: str,
    source_path: str,
    parse: ParseReport,
    quality: QualityReport,
    decision: DecisionResult,
) -> str:
    full_start = quality.decision_window[0]
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Relatório de Teste A/B de Cashback — {partner}\n",
        f"*Gerado automaticamente em {today} a partir de `{source_path}`.*\n",
        "## Decisão recomendada\n",
        f"**{decision.decision_text}**\n",
    ]
    if decision.confidence_note:
        lines.append(f"_{decision.confidence_note}_\n")
    for note in decision.excluded_group_notes:
        lines.append(f"_{note}_\n")

    lines.append(
        f"\n**Pergunta central:** qual variante de cashback devemos escalar para 100% do tráfego? "
        f"Baseline de comparação: **{decision.baseline_group}** (convenção de nomenclatura / menor % de cashback).\n"
    )

    lines.append(_quality_section(parse, quality))

    lines.append("## Resumo por grupo\n")
    lines.append(_summary_table(decision))

    if decision.comparisons:
        lines.append("\n## Comparação estatística (margem líquida diária, pareada por data)\n")
        lines.append(
            "Teste t pareado + Wilcoxon (α = 0,05) sobre `comissão − cashback` de cada dia, "
            "comparando cada variante à baseline. Uma variante só é considerada vencedora se os dois "
            "testes concordarem.\n"
        )
        lines.append(_comparison_table(decision))

    lines.append("\n## Próximos passos\n")
    if decision.winner:
        lines.append(
            f"- Escalar **{decision.winner}** para 100% do tráfego e monitorar margem líquida nas primeiras semanas pós-rollout."
        )
    if quality.excluded_groups:
        lines.append(
            "- Corrigir a coleta de dados dos grupos excluídos (ver seção de qualidade) antes de reaproveitar esse teste como referência."
        )
    if quality.window_truncated:
        lines.append(
            "- Investigar por que os grupos convergiram de patamar de cashback após a janela estável — "
            "se foi decisão de negócio, o teste já estava sendo encerrado; se não, é um problema de execução do teste."
        )
    if any(c.verdict in ("INCONCLUSIVE", "NO_DIFFERENCE") for c in decision.comparisons):
        lines.append("- Para variantes inconclusivas, considerar estender a coleta pelos dias adicionais estimados acima antes de decidir.")

    return "\n".join(lines) + "\n"
