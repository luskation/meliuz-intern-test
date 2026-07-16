"""Leitura e limpeza robusta do CSV de teste A/B de cashback.

Aceita o schema documentado (Data, Grupos de usuários, Parceiro, compradores,
comissão, cashback, vendas totais) com tolerância a sujeira comum: moeda em
formato pt-BR (R$ 1.234 ou R$ 1.234,56), espaços extras, linhas em branco,
linhas totalmente duplicadas e datas malformadas.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

EXPECTED_COLUMNS = {
    "data": "date",
    "grupos de usuarios": "group",
    "parceiro": "partner",
    "compradores": "buyers",
    "comissao": "commission",
    "cashback": "cashback",
    "vendas totais": "gmv",
}

CURRENCY_RE = re.compile(r"[^0-9,\.\-]")


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _normalize_col(col: str) -> str:
    return _strip_accents(col).strip().lower()


@dataclass
class ParseReport:
    """Resumo do que foi limpo durante o parsing, para transparência no relatório."""

    linhas_brutas: int = 0
    linhas_em_branco_removidas: int = 0
    linhas_duplicadas_removidas: int = 0
    linhas_duplicadas_chave_removidas: int = 0
    linhas_invalidas_removidas: int = 0
    linhas_finais: int = 0
    motivos_invalidas: list[str] = field(default_factory=list)


def _parse_currency(series: pd.Series) -> pd.Series:
    """Converte string de moeda pt-BR (R$ 1.234,56 ou R$ 1.234) para float."""
    s = series.astype(str).str.strip()
    s = s.apply(lambda v: CURRENCY_RE.sub("", v))

    def to_float(v: str) -> float:
        if v in ("", "-", "."):
            return float("nan")
        if "," in v:
            # vírgula é separador decimal; ponto (se houver) é separador de milhar
            v = v.replace(".", "").replace(",", ".")
        else:
            # sem vírgula: ponto é separador de milhar (schema observado nos datasets)
            v = v.replace(".", "")
        try:
            return float(v)
        except ValueError:
            return float("nan")

    return s.apply(to_float)


def load_dataset(path: str) -> tuple[pd.DataFrame, ParseReport]:
    """Lê o CSV do teste A/B e devolve (DataFrame limpo, relatório de parsing).

    O DataFrame de saída tem colunas: date, group, partner, buyers,
    commission, cashback, gmv — todas já no tipo correto.
    """
    report = ParseReport()

    raw = pd.read_csv(path, encoding="utf-8", skip_blank_lines=False, dtype=str)
    report.linhas_brutas = len(raw)

    raw.columns = [_normalize_col(c) for c in raw.columns]
    missing = set(EXPECTED_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(
            f"Colunas esperadas ausentes em {path}: {sorted(missing)}. "
            f"Colunas encontradas: {list(raw.columns)}"
        )
    raw = raw.rename(columns=EXPECTED_COLUMNS)
    raw = raw[list(EXPECTED_COLUMNS.values())]

    blank_mask = raw.isnull().all(axis=1) | (
        raw.apply(lambda c: c.astype(str).str.strip()).eq("").all(axis=1)
    )
    report.linhas_em_branco_removidas = int(blank_mask.sum())
    df = raw.loc[~blank_mask].copy()

    dup_mask = df.duplicated(keep="first")
    report.linhas_duplicadas_removidas = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df["group"] = df["group"].astype(str).str.strip()
    df["partner"] = df["partner"].astype(str).str.strip()
    df["buyers"] = pd.to_numeric(df["buyers"], errors="coerce")
    for col in ("commission", "cashback", "gmv"):
        df[col] = _parse_currency(df[col])

    invalid_mask = df[["date", "group", "partner", "buyers", "commission", "cashback", "gmv"]].isnull().any(
        axis=1
    )
    if invalid_mask.any():
        report.motivos_invalidas.append(
            f"{int(invalid_mask.sum())} linha(s) com data, número ou moeda ilegível após parsing"
        )
    negative_mask = (df["buyers"] < 0) | (df["commission"] < 0) | (df["cashback"] < 0) | (df["gmv"] < 0)
    if negative_mask.any():
        report.motivos_invalidas.append(f"{int(negative_mask.sum())} linha(s) com valor negativo")

    drop_mask = invalid_mask | negative_mask
    report.linhas_invalidas_removidas = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()

    df["buyers"] = df["buyers"].astype(int)

    # Duplicata de (date, group, partner) com VALORES diferentes não é pega pelo
    # dedup de linha inteira acima (linhas diferentes não batem no .duplicated()).
    # Sem isso, o set_index("date") em stats.py pareia dias errado silenciosamente.
    key_dup_mask = df.duplicated(subset=["date", "group", "partner"], keep="first")
    report.linhas_duplicadas_chave_removidas = int(key_dup_mask.sum())
    df = df.loc[~key_dup_mask].copy()

    df = df.sort_values(["group", "date"]).reset_index(drop=True)

    report.linhas_finais = len(df)
    return df, report
