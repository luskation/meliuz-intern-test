"""Registro de acompanhamento dos testes A/B rodados.

O mínimo aceito (e sempre funcional, sem credencial) é um CSV local em
tracking/testes_ab.csv. Se as variáveis de ambiente GOOGLE_SHEETS_ID e
GOOGLE_SHEETS_CREDENTIALS_JSON estiverem configuradas, a mesma linha também
é escrita numa planilha do Google Sheets (diferencial opcional).
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path

from .stats import DecisionResult

CSV_COLUMNS = [
    "nome_teste",
    "descricao",
    "data_analise",
    "dataset_origem",
    "grupo_baseline",
    "grupo_vencedor",
    "resultado",
    "decisao",
    "melhor_variante_testada",
    "uplift_margem_dia_brl",
    "p_valor_t",
    "p_valor_wilcoxon",
    "ressalvas",
    "link_relatorio",
]


@dataclass
class TrackingRow:
    nome_teste: str
    descricao: str
    data_analise: str
    dataset_origem: str
    grupo_baseline: str
    grupo_vencedor: str
    resultado: str
    decisao: str
    melhor_variante_testada: str
    uplift_margem_dia_brl: str
    p_valor_t: str
    p_valor_wilcoxon: str
    ressalvas: str
    link_relatorio: str

    def as_dict(self) -> dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


def build_tracking_row(
    partner: str,
    dataset_path: str,
    decision: DecisionResult,
    quality_warnings: list[str],
    report_path: str,
) -> TrackingRow:
    # Referência para uplift/p-valor: a melhor variante testada, mesmo que
    # tenha perdido da baseline — assim a planilha de histórico não fica com
    # colunas vazias só porque a baseline venceu.
    ref_cmp = decision.best_comparison
    ressalvas = "; ".join(quality_warnings) if quality_warnings else ""
    return TrackingRow(
        nome_teste=f"Cashback {partner}",
        descricao=f"Teste A/B de % de cashback — {partner} ({Path(dataset_path).name})",
        data_analise=datetime.now().strftime("%Y-%m-%d"),
        dataset_origem=str(dataset_path),
        grupo_baseline=decision.baseline_group,
        grupo_vencedor=decision.winner or "",
        resultado="vencedor definido" if decision.winner else "sem vencedor / manter baseline",
        decisao=decision.decision_text,
        melhor_variante_testada=ref_cmp.group if ref_cmp else "",
        uplift_margem_dia_brl=f"{ref_cmp.mean_uplift_margin:.2f}" if ref_cmp else "",
        p_valor_t=f"{ref_cmp.t_pvalue:.4f}" if ref_cmp else "",
        p_valor_wilcoxon=(
            f"{ref_cmp.wilcoxon_pvalue:.4f}" if ref_cmp and ref_cmp.wilcoxon_pvalue is not None else ""
        ),
        ressalvas=ressalvas,
        link_relatorio=report_path,
    )


def append_to_csv(row: TrackingRow, csv_path: str) -> None:
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow(row.as_dict())


def maybe_append_to_google_sheets(row: TrackingRow) -> str | None:
    """Escreve a linha também no Google Sheets se as credenciais estiverem
    configuradas via variável de ambiente. Retorna uma mensagem de status
    (None se a integração não estava configurada)."""
    sheet_id = os.environ.get("GOOGLE_SHEETS_ID")
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if not sheet_id or not creds_json:
        return None

    try:
        import json

        import gspread
        from google.oauth2.service_account import Credentials

        creds_dict = json.loads(creds_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1

        # Não usa append_row (a heurística de "próxima linha vazia" do gspread
        # pode deixar linhas em branco no meio). Em vez disso, lê o estado atual
        # e escreve por índice explícito, de forma determinística.
        # Nota: get_all_values() numa planilha recém-limpa (.clear()) retorna
        # [[]] (uma linha "vazia"), não [] — por isso filtramos linhas sem
        # nenhum conteúdo em vez de checar só a lista estar vazia.
        existing_rows = [r for r in sheet.get_all_values() if any(cell.strip() for cell in r)]
        if not existing_rows:
            sheet.update(range_name="A1", values=[CSV_COLUMNS])
            next_row = 2
        else:
            next_row = len(existing_rows) + 1
        sheet.update(range_name=f"A{next_row}", values=[[row.as_dict()[c] for c in CSV_COLUMNS]])
        return f"Linha adicionada ao Google Sheets (planilha {sheet_id}, linha {next_row})."
    except ImportError:
        return "GOOGLE_SHEETS_* configurado mas dependências (gspread/google-auth) não instaladas — pulei a escrita no Sheets."
    except Exception as exc:  # noqa: BLE001 - integração best-effort, não pode quebrar o pipeline
        return f"Falha ao escrever no Google Sheets: {exc}"
