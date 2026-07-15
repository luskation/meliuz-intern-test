#!/usr/bin/env python
"""CLI única para analisar um teste A/B de cashback.

Uso:
    python scripts/analyze_ab_test.py --input data/dataset_01_parceiroA.csv

Roda o pipeline completo (parsing -> qualidade -> estatística -> relatório ->
tracking) e não precisa de nenhuma alteração de código para processar um
dataset novo — só apontar --input para o arquivo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ab_toolkit import parsing, quality, stats, report, tracking


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisa um teste A/B de cashback e recomenda uma decisão.")
    parser.add_argument("--input", required=True, help="Caminho do CSV do teste A/B")
    parser.add_argument("--reports-dir", default="reports", help="Pasta onde salvar o relatório .md")
    parser.add_argument("--tracking-csv", default="tracking/testes_ab.csv", help="CSV de acompanhamento")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {input_path}", file=sys.stderr)
        return 1

    print(f"Lendo e limpando {input_path}...")
    df, parse_report = parsing.load_dataset(str(input_path))
    print(
        f"  {parse_report.linhas_brutas} linhas brutas -> {parse_report.linhas_finais} linhas válidas "
        f"(removidas: {parse_report.linhas_em_branco_removidas} em branco, "
        f"{parse_report.linhas_duplicadas_removidas} duplicadas, "
        f"{parse_report.linhas_invalidas_removidas} inválidas)"
    )

    partner = df["partner"].iloc[0] if len(df) else input_path.stem

    print("Rodando checagens de qualidade...")
    quality_report = quality.run_quality_checks(df)
    if quality_report.excluded_groups:
        print(f"  Grupo(s) excluído(s) por bug: {list(quality_report.excluded_groups)}")
    if quality_report.window_truncated:
        print(f"  Janela de decisão restrita a {quality_report.decision_window[0]} - {quality_report.decision_window[1]} (mudança de patamar detectada)")

    print("Rodando análise estatística...")
    decision = stats.analyze(df, quality_report)
    print(f"  {decision.decision_text}")

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{input_path.stem}.md"
    markdown = report.build_report(partner, str(input_path), parse_report, quality_report, decision)
    report_path.write_text(markdown, encoding="utf-8")
    print(f"Relatório salvo em {report_path}")

    row = tracking.build_tracking_row(
        partner=partner,
        dataset_path=str(input_path),
        decision=decision,
        quality_warnings=quality_report.warnings,
        report_path=str(report_path),
    )
    tracking.append_to_csv(row, args.tracking_csv)
    print(f"Linha de acompanhamento gravada em {args.tracking_csv}")

    sheets_status = tracking.maybe_append_to_google_sheets(row)
    if sheets_status:
        print(sheets_status)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
