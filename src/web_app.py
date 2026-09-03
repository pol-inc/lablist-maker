"""抽出済み大学院データを可視化するFastAPIアプリ。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed" / "univ_portraits_R07"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


class DataError(Exception):
    """APIで利用者へ返すデータエラー。"""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    label: str
    filename: str
    relative_path: str
    description: str


DATASETS = (
    DatasetSpec(
        id="students",
        label="在籍学生",
        filename="2025_09go_H.csv",
        relative_path="graduate/2025_09go_H.csv",
        description="研究科・専攻・学年別の在籍学生数と社会人学生数",
    ),
    DatasetSpec(
        id="admissions",
        label="入学状況",
        filename="2025_09go_I.csv",
        relative_path="graduate/2025_09go_I.csv",
        description="研究科・専攻別の志願者数と入学者数",
    ),
    DatasetSpec(
        id="outcomes",
        label="卒業後状況",
        filename="2025_30go_2_1.csv",
        relative_path="outcomes/2025_30go_2_1.csv",
        description="専攻別の進学・就職などの卒業後状況",
    ),
    DatasetSpec(
        id="employment",
        label="職業・産業",
        filename="2025_30go_2_2.csv",
        relative_path="outcomes/2025_30go_2_2.csv",
        description="専攻別就職者の職業分類と産業分類",
    ),
)

DATASET_BY_ID = {dataset.id: dataset for dataset in DATASETS}

OUTCOME_COLUMNS = {
    "A大学院研究科": "大学院研究科へ進学",
    "B大学学部": "大学学部へ進学",
    "C短期大学本科": "短期大学本科へ進学",
    "D専攻科": "専攻科へ進学",
    "E別科": "別科へ進学",
    "F自営業主等": "自営業主等",
    "G無期雇用労働者": "無期雇用",
    "H有期雇用労働者": "有期雇用",
    "I臨時労働者": "臨時労働者",
    "臨床研修医(予定者を含む)": "臨床研修医",
    "専修学校・外国の学校等入学者": "専修学校・外国の学校等",
    "J(進学準備中)": "進学準備中",
    "J(就職準備中)": "就職準備中",
    "J(その他)": "その他",
    "不詳・死亡の者": "不詳・死亡",
}

ORIGIN_COLUMNS = {
    "当該": "当該大学",
    "国立": "国立大学",
    "公立": "公立大学",
    "私立": "私立大学",
    "外国": "外国の学校",
    "その他": "その他",
}


def numeric_sum(frame: pd.DataFrame, column: str) -> int:
    """空欄や記号を0として列を合計する。"""
    if column not in frame.columns:
        raise DataError("missing_column", f"必要な列がありません: {column}", 500)
    values = frame[column].str.replace(",", "", regex=False)
    return int(pd.to_numeric(values, errors="coerce").fillna(0).sum())


def columns_between(frame: pd.DataFrame, start: str, end: str) -> list[str]:
    columns = frame.columns.tolist()
    try:
        start_index = columns.index(start)
        end_index = columns.index(end)
    except ValueError as exc:
        raise DataError("missing_column", f"集計列がありません: {exc}", 500) from exc
    return columns[start_index : end_index + 1]


class VisualizationRepository:
    """CSVを読み込み、画面向けの集計結果を返す。"""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir
        self.frames: dict[str, pd.DataFrame] = {}
        for dataset in DATASETS:
            path = data_dir / dataset.relative_path
            if not path.is_file():
                raise DataError("missing_data", f"抽出済みCSVがありません: {path}", 500)
            frame = pd.read_csv(path, dtype=str, keep_default_na=False)
            self._validate_frame(dataset, frame)
            self.frames[dataset.id] = frame

    @staticmethod
    def _validate_frame(dataset: DatasetSpec, frame: pd.DataFrame) -> None:
        required = {
            "学校コード",
            "canonical_university_name",
            "canonical_graduate_school_name",
            "field_category",
            "row_level",
        }
        missing = sorted(required - set(frame.columns))
        if missing:
            raise DataError(
                "missing_column",
                f"{dataset.filename} に必要な列がありません: {', '.join(missing)}",
                500,
            )
        if frame.empty:
            raise DataError("empty_data", f"{dataset.filename} が空です", 500)

    def datasets(self) -> list[dict[str, str]]:
        return [
            {
                "id": dataset.id,
                "label": dataset.label,
                "filename": dataset.filename,
                "description": dataset.description,
            }
            for dataset in DATASETS
        ]

    def options(self, dataset_id: str) -> dict[str, Any]:
        frame = self._frame(dataset_id)
        universities = []
        for university, university_frame in frame.groupby(
            "canonical_university_name", sort=True
        ):
            graduate_schools = (
                university_frame[
                    ["canonical_graduate_school_name", "field_category"]
                ]
                .drop_duplicates()
                .sort_values(["field_category", "canonical_graduate_school_name"])
            )
            universities.append(
                {
                    "name": university,
                    "graduateSchools": [
                        {"name": row[0], "fieldCategory": row[1]}
                        for row in graduate_schools.itertuples(index=False, name=None)
                    ],
                }
            )
        return {"universities": universities}

    def chart_data(
        self,
        dataset_id: str,
        university: str | None = None,
        graduate_school: str | None = None,
    ) -> dict[str, Any]:
        frame = self._frame(dataset_id)
        filtered = frame
        if university:
            filtered = filtered.loc[
                filtered["canonical_university_name"].eq(university)
            ]
            if filtered.empty:
                raise DataError(
                    "university_not_found", f"対象大学がありません: {university}", 404
                )
        if graduate_school:
            filtered = filtered.loc[
                filtered["canonical_graduate_school_name"].eq(graduate_school)
            ]
            if filtered.empty:
                raise DataError(
                    "graduate_school_not_found",
                    f"対象研究科がありません: {graduate_school}",
                    404,
                )

        builders = {
            "students": self._students,
            "admissions": self._admissions,
            "outcomes": self._outcomes,
            "employment": self._employment,
        }
        payload = builders[dataset_id](filtered)
        spec = DATASET_BY_ID[dataset_id]
        payload.update(
            {
                "dataset": {
                    "id": spec.id,
                    "label": spec.label,
                    "filename": spec.filename,
                    "description": spec.description,
                },
                "scope": {
                    "university": university or "全大学",
                    "graduateSchool": graduate_school or "全研究科",
                },
            }
        )
        return payload

    def _frame(self, dataset_id: str) -> pd.DataFrame:
        if dataset_id not in self.frames:
            raise DataError(
                "dataset_not_found", f"対象CSVがありません: {dataset_id}", 404
            )
        return self.frames[dataset_id]

    @staticmethod
    def _common_summary(frame: pd.DataFrame) -> list[dict[str, Any]]:
        return [
            {
                "label": "大学",
                "value": int(frame["canonical_university_name"].nunique()),
                "unit": "校",
            },
            {
                "label": "研究科",
                "value": int(frame["canonical_graduate_school_name"].nunique()),
                "unit": "研究科",
            },
        ]

    def _students(self, frame: pd.DataFrame) -> dict[str, Any]:
        totals = frame.loc[frame["row_level"].eq("graduate_school_total")]

        def course_year_sum(
            course_codes: tuple[str, ...], years: tuple[int, ...], sex: str
        ) -> int:
            course_rows = totals.loc[totals["課程別"].isin(course_codes)]
            return sum(
                numeric_sum(course_rows, f"{year}年_{sex}") for year in years
            )

        # 博士前期課程は修士相当としてMに含める。表示上の最終年次を
        # 超える学生は、それぞれM2とD4へ合算する。
        buckets = [
            ("M1", (("1", "2"), (1,))),
            ("M2", (("1", "2"), (2, 3, 4, 5))),
            ("D1", (("3", "4"), (1,))),
            ("D2", (("3", "4"), (2,))),
            ("D3", (("3", "4"), (3,))),
            ("D4", (("3", "4"), (4, 5))),
            ("P1", (("5",), (1,))),
            ("P2", (("5",), (2,))),
            ("P3", (("5",), (3,))),
            ("P4", (("5",), (4,))),
            ("P5", (("5",), (5,))),
        ]
        categories = [label for label, *_parts in buckets]
        male = [
            sum(course_year_sum(codes, years, "男") for codes, years in parts)
            for _label, *parts in buckets
        ]
        female = [
            sum(course_year_sum(codes, years, "女") for codes, years in parts)
            for _label, *parts in buckets
        ]
        visible = [
            index
            for index, (male_value, female_value) in enumerate(zip(male, female))
            if male_value + female_value > 0
        ]
        categories = [categories[index] for index in visible]
        male = [male[index] for index in visible]
        female = [female[index] for index in visible]
        summary = [
            {
                "label": "学生",
                "value": numeric_sum(totals, "計_計"),
                "unit": "人",
            },
            {
                "label": "社会人",
                "value": numeric_sum(totals, "社会_計"),
                "unit": "人",
            },
            *self._common_summary(totals),
        ]
        return {
            "summary": summary,
            "charts": [
                {
                    "type": "bar",
                    "title": "学年・男女別学生数",
                    "categories": categories,
                    "series": [
                        {"name": "男", "data": male, "stack": "students"},
                        {"name": "女", "data": female, "stack": "students"},
                    ],
                }
            ],
        }

    def _admissions(self, frame: pd.DataFrame) -> dict[str, Any]:
        totals = frame.loc[frame["row_level"].eq("graduate_school_total")]
        details = frame.loc[frame["row_level"].eq("major_detail")]
        categories = list(ORIGIN_COLUMNS.values())

        def series(prefix: str) -> list[dict[str, Any]]:
            return [
                {
                    "name": "男",
                    "data": [
                        numeric_sum(details, f"{prefix}_{key}_男")
                        for key in ORIGIN_COLUMNS
                    ],
                    "stack": prefix,
                },
                {
                    "name": "女",
                    "data": [
                        numeric_sum(details, f"{prefix}_{key}_女")
                        for key in ORIGIN_COLUMNS
                    ],
                    "stack": prefix,
                },
            ]

        applicants = numeric_sum(totals, "志願_計_男") + numeric_sum(
            totals, "志願_計_女"
        )
        entrants = numeric_sum(totals, "入学_計_男") + numeric_sum(
            totals, "入学_計_女"
        )
        summary = [
            {"label": "志願者", "value": applicants, "unit": "人"},
            {"label": "入学者", "value": entrants, "unit": "人"},
            {
                "label": "入学率",
                "value": round(entrants / applicants * 100, 1) if applicants else 0,
                "unit": "%",
            },
            *self._common_summary(totals),
        ]
        return {
            "summary": summary,
            "charts": [
                {
                    "type": "bar",
                    "title": "出身区分別志願者数",
                    "categories": categories,
                    "series": series("志願"),
                },
                {
                    "type": "bar",
                    "title": "出身区分別入学者数",
                    "categories": categories,
                    "series": series("入学"),
                },
            ],
        }

    def _outcomes(self, frame: pd.DataFrame) -> dict[str, Any]:
        items = [
            {"name": label, "value": numeric_sum(frame, column)}
            for column, label in OUTCOME_COLUMNS.items()
        ]
        items = sorted(
            (item for item in items if item["value"] > 0),
            key=lambda item: item["value"],
            reverse=True,
        )
        graduates = numeric_sum(frame, "7状況別計(a)")
        employed = sum(
            numeric_sum(frame, column)
            for column in [
                "F自営業主等",
                "G無期雇用労働者",
                "H有期雇用労働者",
                "I臨時労働者",
            ]
        )
        summary = [
            {"label": "卒業者", "value": graduates, "unit": "人"},
            {"label": "就業者", "value": employed, "unit": "人"},
            *self._common_summary(frame),
        ]
        return {
            "summary": summary,
            "charts": [
                {"type": "treemap", "title": "卒業後の状況", "data": items}
            ],
        }

    def _employment(self, frame: pd.DataFrame) -> dict[str, Any]:
        profession_columns = columns_between(frame, "b-1研究者", "左記以外（職）")
        industry_columns = columns_between(frame, "A農業・林業", "左記以外（産）")

        def items(columns: list[str]) -> list[dict[str, Any]]:
            values = [
                {"name": column, "value": numeric_sum(frame, column)}
                for column in columns
            ]
            return sorted(
                (item for item in values if item["value"] > 0),
                key=lambda item: item["value"],
                reverse=True,
            )

        summary = [
            {
                "label": "就職者",
                "value": numeric_sum(frame, "職業別計"),
                "unit": "人",
            },
            *self._common_summary(frame),
        ]
        return {
            "summary": summary,
            "charts": [
                {"type": "treemap", "title": "職業別就職者数", "data": items(profession_columns)},
                {"type": "treemap", "title": "産業別就職者数", "data": items(industry_columns)},
            ],
        }


def create_app(
    data_dir: Path = DATA_DIR, frontend_dist: Path = FRONTEND_DIST
) -> FastAPI:
    repository = VisualizationRepository(data_dir)
    app = FastAPI(title="大学院データ可視化", version="0.1.0")
    app.state.repository = repository

    @app.exception_handler(DataError)
    async def data_error_handler(_request: Request, exc: DataError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "datasets": len(repository.frames)}

    @app.get("/api/datasets")
    async def datasets() -> dict[str, Any]:
        return {"datasets": repository.datasets()}

    @app.get("/api/options/{dataset_id}")
    async def options(dataset_id: str) -> dict[str, Any]:
        return repository.options(dataset_id)

    @app.get("/api/chart/{dataset_id}")
    async def chart(
        dataset_id: str,
        university: str | None = Query(default=None),
        graduate_school: str | None = Query(default=None, alias="graduateSchool"),
    ) -> dict[str, Any]:
        return repository.chart_data(dataset_id, university, graduate_school)

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        path = frontend_dist / "index.html"
        if not path.is_file():
            raise DataError(
                "missing_asset",
                "フロントエンドが未ビルドです。`npm run build` を実行してください。",
                503,
            )
        return FileResponse(path)

    @app.get("/{asset_path:path}", include_in_schema=False)
    async def frontend_asset(asset_path: str) -> FileResponse:
        path = (frontend_dist / asset_path).resolve()
        if frontend_dist.resolve() not in path.parents or not path.is_file():
            raise DataError(
                "asset_not_found", f"画面リソースがありません: {asset_path}", 404
            )
        return FileResponse(path)

    return app


def main() -> None:
    """Run the visualization application."""
    import uvicorn

    uvicorn.run("src.web_app:app", host="127.0.0.1", port=8000)


app = create_app()
