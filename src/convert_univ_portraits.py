"""学校基本調査の Excel ファイルを CSV に変換する。"""

from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "univ_portraits_R07"
XLSX_DIR = DATA_DIR / "xlsx"


def convert_workbook(xlsx_path: Path) -> Path:
    """Excel の本体シートを、正規化済みヘッダを使って CSV に変換する。"""
    workbook = pd.ExcelFile(xlsx_path)
    data_sheets = [sheet for sheet in workbook.sheet_names if sheet != "凡例"]
    if len(data_sheets) != 1:
        raise ValueError(
            f"{xlsx_path}: expected exactly one data sheet, got {data_sheets}"
        )

    sheet = data_sheets[0]
    raw = pd.read_excel(xlsx_path, sheet_name=sheet, header=None, dtype=str)
    header_rows = [
        index
        for index, value in raw.iloc[:, 0].items()
        if str(value).strip() == "年度"
    ]
    if not header_rows:
        raise ValueError(f"{xlsx_path}: CSV header row not found")

    frame = pd.read_excel(
        xlsx_path,
        sheet_name=sheet,
        header=max(header_rows),
        dtype=str,
    ).dropna(axis=0, how="all")
    if frame.columns.has_duplicates:
        raise ValueError(f"{xlsx_path}: duplicate CSV headers")

    csv_path = DATA_DIR / f"{xlsx_path.stem}.csv"
    frame.to_csv(csv_path, index=False, encoding="utf-8")
    return csv_path


def main() -> None:
    xlsx_paths = sorted(XLSX_DIR.glob("*.xlsx"))
    if not xlsx_paths:
        raise FileNotFoundError(f"Excel files not found: {XLSX_DIR}")

    for xlsx_path in xlsx_paths:
        csv_path = convert_workbook(xlsx_path)
        print(f"{xlsx_path.name} -> {csv_path.name}")


if __name__ == "__main__":
    main()
