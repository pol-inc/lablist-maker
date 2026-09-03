"""可視化対象となる国公立大学院の理系データを抽出する。"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIERS_DIR = PROJECT_ROOT / "data" / "tiers"
SOURCE_DIR = PROJECT_ROOT / "data" / "univ_portraits_R07"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "univ_portraits_R07"

EXPECTED_TIER_NAMES = 33
EXPECTED_UNIVERSITIES = 32
EXPECTED_AVAILABLE = 23
EXPECTED_UNAVAILABLE = 9

SOURCE_SPECS = {
    "2025_09go_H.csv": {
        "group": "09",
        "output_dir": "graduate",
        "school_name": "大学名",
        "graduate_school": "研究科名",
    },
    "2025_09go_I.csv": {
        "group": "09",
        "output_dir": "graduate",
        "school_name": "大学名",
        "graduate_school": "研究科名",
    },
    "2025_30go_2_1.csv": {
        "group": "30",
        "output_dir": "outcomes",
        "school_name": "学校名",
        "graduate_school": "学部・研究科名",
    },
    "2025_30go_2_2.csv": {
        "group": "30",
        "output_dir": "outcomes",
        "school_name": "学校名",
        "graduate_school": "学部・研究科名",
    },
}

FIELD_CATEGORY_BY_SOURCE_NAME = {
    # 理学・数学
    "数理学府": "理学・数学",
    "理学府": "理学・数学",
    "理学研究科": "理学・数学",
    "理学院": "理学・数学",
    "多元数理科学研究科": "理学・数学",
    "数理科学研究科": "理学・数学",
    "理学系研究科": "理学・数学",
    "総合化学院": "理学・数学",
    # 工学
    "工学府": "工学",
    "総合理工学府": "工学",
    "工学研究科": "工学",
    "工芸科学研究科": "工学",
    "工学院": "工学",
    "基礎工学研究科": "工学",
    "工学系研究科": "工学",
    "物質理工学院": "工学",
    "理工学研究科": "工学",
    "総合理工学研究科": "工学",
    # 情報
    "システム情報科学府": "情報",
    "情報工学府": "情報",
    "情報学研究科": "情報",
    "情報科学研究科": "情報",
    "情報科学院": "情報",
    "情報理工学系研究科": "情報",
    "情報理工学院": "情報",
    "情報理工学研究科": "情報",
    "情報システム学研究科": "情報",
    # 農学・水産
    "生物資源環境科学府": "農学・水産",
    "農学研究科": "農学・水産",
    "水産科学院": "農学・水産",
    "国際食資源学院": "農学・水産",
    "農学院": "農学・水産",
    "生命農学研究科": "農学・水産",
    "農学生命科学研究科": "農学・水産",
    "農学府": "農学・水産",
    "連合農学研究科": "農学・水産",
    "農学部・農学研究科": "農学・水産",
    # 生命科学
    "システム生命科学府": "生命科学",
    "生命体工学研究科": "生命科学",
    "生命科学研究科": "生命科学",
    "生命科学院": "生命科学",
    "生命科学院（４年制）": "生命科学",
    "生命機能研究科": "生命科学",
    "生命理工学院": "生命科学",
    "生命理工学研究科": "生命科学",
    "生物システム応用科学府": "生命科学",
    "生物システム応用科学府一貫制博士": "生命科学",
    "生物システム応用科学府博士前期": "生命科学",
    "生物システム応用科学府博士後期": "生命科学",
    # 環境・エネルギー
    "エネルギー科学研究科": "環境・エネルギー",
    "地球環境学舎": "環境・エネルギー",
    "環境科学院": "環境・エネルギー",
    "環境学研究科": "環境・エネルギー",
    "地域レジリエンス学環": "環境・エネルギー",
    "環境科学研究科": "環境・エネルギー",
    "環境・社会理工学院": "環境・エネルギー",
    # 医歯薬・保健・獣医
    "医学系学府": "医歯薬・保健・獣医",
    "医学系学府（保健学）": "医歯薬・保健・獣医",
    "医学系学府（医学）": "医歯薬・保健・獣医",
    "医学系学府（医療経営・管理学）": "医歯薬・保健・獣医",
    "歯学府": "医歯薬・保健・獣医",
    "歯学府（口腔科学）": "医歯薬・保健・獣医",
    "歯学府（歯学）": "医歯薬・保健・獣医",
    "薬学府": "医歯薬・保健・獣医",
    "薬学府（創薬科学）": "医歯薬・保健・獣医",
    "薬学府（臨床薬学）": "医歯薬・保健・獣医",
    "医学研究科": "医歯薬・保健・獣医",
    "薬学研究科": "医歯薬・保健・獣医",
    "保健科学院": "医歯薬・保健・獣医",
    "医学研究科（修業年限４年）": "医歯薬・保健・獣医",
    "医学院": "医歯薬・保健・獣医",
    "医学院（修業年限４年）": "医歯薬・保健・獣医",
    "医理工学院": "医歯薬・保健・獣医",
    "国際感染症学院（４年制）": "医歯薬・保健・獣医",
    "歯学院（修業年限４年）": "医歯薬・保健・獣医",
    "獣医学院": "医歯薬・保健・獣医",
    "創薬科学研究科": "医歯薬・保健・獣医",
    "医学系研究科": "医歯薬・保健・獣医",
    "大学院医学系研究科": "医歯薬・保健・獣医",
    "歯学研究科": "医歯薬・保健・獣医",
    "連合小児発達学研究科": "医歯薬・保健・獣医",
    "大阪大学・金沢大学・浜松医科大学・千葉大学・福井大学連合小児発達学研究科": "医歯薬・保健・獣医",
    "医農融合公衆衛生学環": "医歯薬・保健・獣医",
    "薬学系研究科": "医歯薬・保健・獣医",
    "薬学系研究科（４年制）": "医歯薬・保健・獣医",
    "保健衛生学研究科": "医歯薬・保健・獣医",
    "医歯学総合研究科": "医歯薬・保健・獣医",
    "医歯学総合研究科（４年制）": "医歯薬・保健・獣医",
    "医学系研究科（修業年限４年）": "医歯薬・保健・獣医",
    "医工学研究科": "医歯薬・保健・獣医",
    "歯学研究科（修業年限４年）": "医歯薬・保健・獣医",
    "薬学研究科（４年制）": "医歯薬・保健・獣医",
    "薬学部・薬学研究科": "医歯薬・保健・獣医",
    # 学際
    "マス・フォア・イノベーション連係学府": "学際",
    "人文情報連係学府": "学際",
    "地球社会統合科学府": "学際",
    "統合新領域学府": "学際",
    "芸術工学府": "学際",
    "先端科学技術研究科": "学際",
    "学際情報学教育部（府）": "学際",
    "学際情報学教育部": "学際",
    "新領域創成科学研究科": "学際",
    "先進学際科学府": "学際",
    "社会理工学研究科": "学際",
}

EXCLUDED_GRADUATE_SCHOOL_NAMES = {
    "いずれの研究科にも所属しない聴講生・研究生等",
    "人文科学府",
    "人間環境学府",
    "人間環境学府（心理学）",
    "法務学府",
    "法学府",
    "経済学府",
    "経済学院",
    "産業マネジメント専攻",
    "アジア・アフリカ地域研究研究科",
    "人間・環境学研究科",
    "公共政策教育部",
    "教育学研究科",
    "文学研究科",
    "法学研究科",
    "経営管理教育部",
    "経済学研究科",
    "総合生存学館",
    "公共政策学教育部",
    "国際広報メディア・観光学院",
    "教育学院",
    "文学院",
    "人文学研究科",
    "国際開発研究科",
    "教育発達科学研究科",
    "人間科学研究科",
    "国際公共政策研究科",
    "言語文化研究科",
    "高等司法研究科",
    "人文社会科学研究科",
    "法文学研究科",
    "人文社会系研究科",
    "法学政治学研究科",
    "総合文化研究科",
    "国際文化研究科",
    "教育情報学教育部",
    "法制理論研究",
    "総合教育科学",
}

CANONICAL_NAME_OVERRIDES = {
    ("九州大学", "医学系学府（保健学）"): "医学系学府",
    ("九州大学", "医学系学府（医学）"): "医学系学府",
    ("九州大学", "医学系学府（医療経営・管理学）"): "医学系学府",
    ("九州大学", "歯学府（口腔科学）"): "歯学府",
    ("九州大学", "歯学府（歯学）"): "歯学府",
    ("九州大学", "薬学府（創薬科学）"): "薬学府",
    ("九州大学", "薬学府（臨床薬学）"): "薬学府",
    ("北海道大学", "医学研究科（修業年限４年）"): "医学院",
    ("北海道大学", "医学院（修業年限４年）"): "医学院",
    ("北海道大学", "生命科学院（４年制）"): "生命科学院",
    ("名古屋大学", "大学院医学系研究科"): "医学系研究科",
    ("名古屋大学", "情報科学研究科"): "情報学研究科",
    (
        "大阪大学",
        "大阪大学・金沢大学・浜松医科大学・千葉大学・福井大学連合小児発達学研究科",
    ): "連合小児発達学研究科",
    ("奈良先端科学技術大学院大学", "情報科学研究科"): "先端科学技術研究科",
    ("東京大学", "学際情報学教育部（府）"): "学際情報学教育部",
    ("東京大学", "薬学系研究科（４年制）"): "薬学系研究科",
    ("東京科学大学", "医歯学総合研究科（４年制）"): "医歯学総合研究科",
    ("東京科学大学", "生命理工学研究科"): "生命理工学院",
    ("東京農工大学", "生物システム応用科学府一貫制博士"): "生物システム応用科学府",
    ("東京農工大学", "生物システム応用科学府博士前期"): "生物システム応用科学府",
    ("東京農工大学", "生物システム応用科学府博士後期"): "生物システム応用科学府",
    ("東北大学", "医学系研究科（修業年限４年）"): "医学系研究科",
    ("東北大学", "歯学研究科（修業年限４年）"): "歯学研究科",
    ("東北大学", "薬学研究科（４年制）"): "薬学研究科",
    ("東北大学", "薬学部・薬学研究科"): "薬学研究科",
    ("東北大学", "農学部・農学研究科"): "農学研究科",
    ("電気通信大学", "情報システム学研究科"): "情報理工学研究科",
}

INDIVIDUAL_DECISION_REASONS = {
    "人文情報連係学府": "人文知とデータ科学を連係する文理融合組織として学際に採用",
    "地球社会統合科学府": "地球科学を含む文理融合組織として学際に採用",
    "統合新領域学府": "応用科学を中心とする融合組織として学際に採用",
    "芸術工学府": "工学とデザインを横断する融合組織として学際に採用",
    "先端科学技術研究科": "情報・バイオ・物質科学を横断する融合組織として学際に採用",
    "環境学研究科": "環境科学を主題とする融合組織として環境・エネルギーに採用",
    "医農融合公衆衛生学環": "医学と農学を横断する公衆衛生組織として医歯薬・保健・獣医に採用",
    "地域レジリエンス学環": "防災・環境を主題とする融合組織として環境・エネルギーに採用",
    "学際情報学教育部（府）": "情報学を中心とする文理融合組織として学際に採用",
    "学際情報学教育部": "情報学を中心とする文理融合組織として学際に採用",
    "新領域創成科学研究科": "自然科学と応用科学を横断する組織として学際に採用",
    "先進学際科学府": "工学・農学を横断する融合組織として学際に採用",
    "環境・社会理工学院": "環境工学を中心とする融合組織として環境・エネルギーに採用",
    "社会理工学研究科": "理工学を基盤とする旧組織として学際に採用",
    "人間環境学府": "文理混在で研究科単位では理系に限定できないため対象外",
    "人間環境学府（心理学）": "心理学単独の区分は今回の理系範囲に含めないため対象外",
    "人間・環境学研究科": "文理混在で研究科単位では理系に限定できないため対象外",
    "総合文化研究科": "文理混在で研究科単位では理系に限定できないため対象外",
    "総合生存学館": "分野横断型だが理系中心の研究科とは判定できないため対象外",
}

METADATA_COLUMNS = [
    "canonical_university_name",
    "canonical_graduate_school_name",
    "field_category",
    "row_level",
    "source_file",
]


def normalize_university_name(name: str) -> str:
    """大学院を表す末尾の文字列だけを除去する。"""
    return name.removesuffix("大学院")


def read_tier_rows() -> pd.DataFrame:
    frames = []
    for path in sorted(TIERS_DIR.glob("*.csv")):
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        frame = frame.loc[frame["大学/大学院名"].ne("")].copy()
        frame["tier_source"] = path.name
        frames.append(frame[["大学TIer", "大学/大学院名", "tier_source"]])
    if not frames:
        raise FileNotFoundError(f"Tier CSV files not found: {TIERS_DIR}")
    return pd.concat(frames, ignore_index=True)


def build_university_master() -> pd.DataFrame:
    """tiersとR07を突合した対象校マスタを作る。"""
    tier_rows = read_tier_rows()
    distinct_tier_names = tier_rows["大学/大学院名"].nunique()
    if distinct_tier_names != EXPECTED_TIER_NAMES:
        raise ValueError(
            f"Expected {EXPECTED_TIER_NAMES} tier names, got {distinct_tier_names}"
        )

    tier_rows["normalized_university_name"] = tier_rows[
        "大学/大学院名"
    ].map(normalize_university_name)
    grouped = (
        tier_rows.groupby("normalized_university_name", sort=True)
        .agg(
            tier=("大学TIer", lambda values: "|".join(sorted(set(values)))),
            tier_source=("tier_source", lambda values: "|".join(sorted(set(values)))),
            tier_university_name=(
                "大学/大学院名",
                lambda values: "|".join(sorted(set(values))),
            ),
        )
        .reset_index()
    )
    if len(grouped) != EXPECTED_UNIVERSITIES:
        raise ValueError(
            f"Expected {EXPECTED_UNIVERSITIES} normalized universities, got {len(grouped)}"
        )

    school_lookup_source = pd.read_csv(
        SOURCE_DIR / "2025_09go_H.csv", dtype=str, keep_default_na=False
    )[["学校コード", "大学名"]].drop_duplicates()
    duplicates = school_lookup_source["大学名"].duplicated(keep=False)
    if duplicates.any():
        names = sorted(school_lookup_source.loc[duplicates, "大学名"].unique())
        raise ValueError(f"University names map to multiple school codes: {names}")

    master = grouped.merge(
        school_lookup_source,
        how="left",
        left_on="normalized_university_name",
        right_on="大学名",
        validate="one_to_one",
    )
    master["school_code"] = master["学校コード"].fillna("")
    available_mask = master["school_code"].ne("")
    master["availability"] = available_mask.map(
        {True: "available", False: "unavailable"}
    )
    master["exclusion_reason"] = master["availability"].map(
        lambda value: "" if value == "available" else "R07一括データ未収録"
    )
    master = master[
        [
            "tier",
            "tier_source",
            "tier_university_name",
            "normalized_university_name",
            "school_code",
            "availability",
            "exclusion_reason",
        ]
    ]

    counts = master["availability"].value_counts().to_dict()
    if counts.get("available", 0) != EXPECTED_AVAILABLE:
        raise ValueError(
            f"Expected {EXPECTED_AVAILABLE} available universities, got {counts}"
        )
    if counts.get("unavailable", 0) != EXPECTED_UNAVAILABLE:
        raise ValueError(
            f"Expected {EXPECTED_UNAVAILABLE} unavailable universities, got {counts}"
        )
    return master


def source_candidates(
    university_master: pd.DataFrame, source_group: str
) -> pd.DataFrame:
    """入力群に存在する対象校の研究科候補を列挙する。"""
    source_file = "2025_09go_H.csv" if source_group == "09" else "2025_30go_2_1.csv"
    spec = SOURCE_SPECS[source_file]
    frame = pd.read_csv(SOURCE_DIR / source_file, dtype=str, keep_default_na=False)
    if source_group == "30":
        frame = frame.loc[frame["学校種別"].eq("2")]

    available = university_master.loc[
        university_master["availability"].eq("available"),
        ["school_code", "normalized_university_name"],
    ]
    frame = frame.loc[frame["学校コード"].isin(set(available["school_code"]))]
    candidates = frame[
        ["学校コード", spec["school_name"], spec["graduate_school"]]
    ].drop_duplicates()
    candidates.columns = [
        "school_code",
        "university_name",
        "source_graduate_school_name",
    ]
    candidates["source_group"] = source_group
    return candidates.sort_values(
        ["university_name", "source_graduate_school_name"]
    ).reset_index(drop=True)


def build_graduate_school_master(university_master: pd.DataFrame) -> pd.DataFrame:
    """研究科候補に明示済みの採否、正規名、分野を付与する。"""
    overlap = set(FIELD_CATEGORY_BY_SOURCE_NAME) & EXCLUDED_GRADUATE_SCHOOL_NAMES
    if overlap:
        raise ValueError(f"Graduate school decisions overlap: {sorted(overlap)}")

    candidates = pd.concat(
        [
            source_candidates(university_master, "09"),
            source_candidates(university_master, "30"),
        ],
        ignore_index=True,
    )
    decided_names = set(FIELD_CATEGORY_BY_SOURCE_NAME) | EXCLUDED_GRADUATE_SCHOOL_NAMES
    unknown = sorted(set(candidates["source_graduate_school_name"]) - decided_names)
    if unknown:
        raise ValueError(f"Graduate school decisions are missing: {unknown}")

    def classify(row: pd.Series) -> pd.Series:
        source_name = row["source_graduate_school_name"]
        included = source_name in FIELD_CATEGORY_BY_SOURCE_NAME
        category = FIELD_CATEGORY_BY_SOURCE_NAME.get(source_name, "")
        canonical_name = CANONICAL_NAME_OVERRIDES.get(
            (row["university_name"], source_name), source_name
        )
        if source_name in INDIVIDUAL_DECISION_REASONS:
            reason = INDIVIDUAL_DECISION_REASONS[source_name]
        elif included:
            reason = f"理系研究科として採用（{category}）"
        elif source_name == "いずれの研究科にも所属しない聴講生・研究生等":
            reason = "研究科ではない集計区分のため対象外"
        else:
            reason = "人文・社会科学系のため対象外"
        return pd.Series(
            {
                "canonical_graduate_school_name": canonical_name,
                "field_category": category,
                "included": "true" if included else "false",
                "decision_reason": reason,
            }
        )

    decisions = candidates.apply(classify, axis=1)
    master = pd.concat([candidates, decisions], axis=1)
    master = master[
        [
            "school_code",
            "university_name",
            "canonical_graduate_school_name",
            "source_group",
            "source_graduate_school_name",
            "field_category",
            "included",
            "decision_reason",
        ]
    ]
    key_columns = ["school_code", "source_group", "source_graduate_school_name"]
    if master.duplicated(key_columns).any():
        raise ValueError("Graduate school master contains duplicate source keys")
    included = master["included"].eq("true")
    if master.loc[included, ["field_category", "decision_reason"]].eq("").any().any():
        raise ValueError("Included graduate schools require category and reason")
    return master


def extract_source(
    source_file: str,
    university_master: pd.DataFrame,
    graduate_school_master: pd.DataFrame,
) -> pd.DataFrame:
    """1つの入力CSVから可視化対象行を抽出する。"""
    spec = SOURCE_SPECS[source_file]
    source = pd.read_csv(SOURCE_DIR / source_file, dtype=str, keep_default_na=False)
    original_columns = source.columns.tolist()
    if set(original_columns) & set(METADATA_COLUMNS):
        raise ValueError(f"Metadata columns already exist in {source_file}")

    if spec["group"] == "30":
        source = source.loc[source["学校種別"].eq("2")].copy()

    available = university_master.loc[
        university_master["availability"].eq("available"),
        ["school_code", "normalized_university_name"],
    ].rename(columns={"normalized_university_name": "canonical_university_name"})
    source = source.merge(
        available,
        how="inner",
        left_on="学校コード",
        right_on="school_code",
        validate="many_to_one",
    ).drop(columns="school_code")

    decisions = graduate_school_master.loc[
        graduate_school_master["source_group"].eq(spec["group"]),
        [
            "school_code",
            "source_graduate_school_name",
            "canonical_graduate_school_name",
            "field_category",
            "included",
        ],
    ]
    source = source.merge(
        decisions,
        how="left",
        left_on=["学校コード", spec["graduate_school"]],
        right_on=["school_code", "source_graduate_school_name"],
        validate="many_to_one",
    )
    unmatched = source["included"].isna()
    if unmatched.any():
        values = source.loc[
            unmatched, [spec["school_name"], spec["graduate_school"]]
        ].drop_duplicates()
        raise ValueError(
            f"Unmatched graduate schools in {source_file}: {values.to_dict('records')}"
        )

    source = source.loc[source["included"].eq("true")].copy()
    if spec["group"] == "09":
        total_rows = source["専攻"].eq("計") & source["符号"].eq("9999")
        source["row_level"] = total_rows.map(
            {True: "graduate_school_total", False: "major_detail"}
        )
    else:
        source["row_level"] = "major_detail"
    source["source_file"] = source_file

    source = source.drop(
        columns=[
            "school_code",
            "source_graduate_school_name",
            "included",
        ]
    )
    source = source[original_columns + METADATA_COLUMNS]
    if source.columns.tolist()[: len(original_columns)] != original_columns:
        raise ValueError(f"Original column order changed in {source_file}")
    return source


def validate_outputs(
    outputs: dict[str, pd.DataFrame],
    university_master: pd.DataFrame,
    graduate_school_master: pd.DataFrame,
) -> None:
    """計画で定めた抽出結果の不変条件を検証する。"""
    available_codes = set(
        university_master.loc[
            university_master["availability"].eq("available"), "school_code"
        ]
    )
    valid_categories = {
        "理学・数学",
        "工学",
        "情報",
        "農学・水産",
        "生命科学",
        "環境・エネルギー",
        "医歯薬・保健・獣医",
        "学際",
    }
    for source_file, output in outputs.items():
        source_rows = len(
            pd.read_csv(SOURCE_DIR / source_file, dtype=str, keep_default_na=False)
        )
        if len(output) > source_rows:
            raise ValueError(f"Output has more rows than source: {source_file}")
        if output.empty:
            raise ValueError(f"Output is empty: {source_file}")
        if not set(output["学校コード"]).issubset(available_codes):
            raise ValueError(f"Unavailable university found: {source_file}")
        if not set(output["field_category"]).issubset(valid_categories):
            raise ValueError(f"Unknown field category found: {source_file}")
        if output[METADATA_COLUMNS].eq("").any().any():
            raise ValueError(f"Empty metadata found: {source_file}")

    if not set(outputs) == set(SOURCE_SPECS):
        raise ValueError("Output files do not match the configured source files")
    if not graduate_school_master["included"].isin(["true", "false"]).all():
        raise ValueError("Graduate school master has invalid included values")


def write_outputs(
    university_master: pd.DataFrame,
    graduate_school_master: pd.DataFrame,
    outputs: dict[str, pd.DataFrame],
) -> None:
    """検証済みのマスタと抽出データを書き出す。"""
    (OUTPUT_DIR / "graduate").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "outcomes").mkdir(parents=True, exist_ok=True)
    university_master.to_csv(
        OUTPUT_DIR / "target_universities.csv", index=False, encoding="utf-8"
    )
    graduate_school_master.to_csv(
        OUTPUT_DIR / "target_graduate_schools.csv", index=False, encoding="utf-8"
    )
    for source_file, frame in outputs.items():
        output_dir = OUTPUT_DIR / SOURCE_SPECS[source_file]["output_dir"]
        frame.to_csv(output_dir / source_file, index=False, encoding="utf-8")

    stale_outputs = [
        OUTPUT_DIR / "graduate" / "2025_09go_4.csv",
        OUTPUT_DIR / "graduate" / "2025_09go_5.csv",
        OUTPUT_DIR / "graduate" / "2025_09go_8.csv",
        OUTPUT_DIR / "graduate" / "2025_09go_S.csv",
        OUTPUT_DIR / "outcomes" / "2025_30go_2_1_bekkei.csv",
    ]
    for stale_path in stale_outputs:
        if stale_path.exists():
            stale_path.unlink()


def main() -> None:
    university_master = build_university_master()
    graduate_school_master = build_graduate_school_master(university_master)
    outputs = {
        source_file: extract_source(
            source_file, university_master, graduate_school_master
        )
        for source_file in SOURCE_SPECS
    }
    validate_outputs(outputs, university_master, graduate_school_master)
    write_outputs(university_master, graduate_school_master, outputs)

    available = university_master["availability"].eq("available").sum()
    included = graduate_school_master["included"].eq("true").sum()
    print(f"対象校: {available}/{len(university_master)}校")
    print(f"採用研究科表記: {included}/{len(graduate_school_master)}件")
    for source_file, output in outputs.items():
        print(f"{source_file}: {len(output)}行")


if __name__ == "__main__":
    main()
