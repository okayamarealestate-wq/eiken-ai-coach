import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

APP_TITLE = "英検AIコーチ Ver.2"
DATA_DIR = Path("data")
LOG_FILE = DATA_DIR / "study_log.csv"
SETTINGS_FILE = DATA_DIR / "settings.json"

LOG_COLUMNS = [
    "date",
    "planned_vocab",
    "planned_reading",
    "planned_writing",
    "planned_listening",
    "actual_vocab",
    "actual_reading",
    "actual_writing",
    "actual_listening",
    "grammar_minutes",
    "total_minutes",
    "understanding",
    "mood",
    "school_busy",
    "writing_text",
    "reflection",
]

RESOURCE_OPTIONS = {
    "英検2級": {
        "文法": [
            "大岩のいちばんはじめの英文法【超基礎文法編】",
            "改訂版 大学入試 肘井学の ゼロから英文法が面白いほどわかる本",
            "Evergreen English Grammar 31 Lessons（旧Forest系）",
            "高校の学校配布文法問題集",
            "Next Stage / Vintage などの4択文法問題集",
        ],
        "ボキャブラリー": [
            "英検2級 でる順パス単 5訂版",
            "ランク順英検2級英単語1750 改訂版",
            "英検2級 文で覚える単熟語 4訂版",
            "mikan（英検2級）",
            "英検2級 でる順パス単 クイックチェック",
        ],
        "英作文": [
            "最短合格！ 英検2級 英作文問題完全制覇",
            "英検2級ライティング大特訓",
            "7日間完成 英検2級 予想問題ドリル",
            "学校配布の英作文プリント・ノート",
            "このアプリの英作文フィードバック機能",
        ],
        "長文": [
            "2026年度版 英検2級 過去6回全問題集",
            "英検2級 文で覚える単熟語 4訂版",
            "英検分野別ターゲット 英検2級リーディング問題",
            "最短合格！ 英検2級 リーディング問題完全制覇",
            "高校英語の教科書長文",
        ],
        "リスニング": [
            "NHK高校講座 英語",
            "VOA Learning English",
            "ELLLO (English Listening Lesson Library Online)",
            "BBC Learning English YouTube",
            "EnglishClass101 YouTube",
        ],
    },
    "英検準1級": {
        "文法": [
            "大岩のいちばんはじめの英文法【超基礎文法編】",
            "改訂版 大学入試 肘井学の ゼロから英文法が面白いほどわかる本",
            "Evergreen English Grammar 31 Lessons（旧Forest系）",
            "高校の学校配布文法問題集",
            "Next Stage / Vintage などの4択文法問題集",
        ],
        "ボキャブラリー": [
            "英検準1級 でる順パス単 5訂版",
            "ランク順英検準1級英単語1900 新装版",
            "英検準1級 文で覚える単熟語 4訂版",
            "英検準1級 でる順パス単 クイックチェック",
            "mikan（英検準1級語彙の復習用）",
        ],
        "英作文": [
            "最短合格！ 英検準1級 要約＆英作文完全制覇",
            "最短合格！ 英検準1級 英作文問題 完全制覇",
            "改訂版 英検準1級ライティング大特訓",
            "大学入試 英作文ハイパートレーニング 自由英作文編 Plus",
            "英検合格のための要約問題 予想問題集（1級・準1級・2級対応）",
        ],
        "長文": [
            "2026年度版 英検準1級 過去6回全問題集",
            "英検準1級 文で覚える単熟語 4訂版",
            "英検分野別ターゲット 英検準1級リーディング問題",
            "最短合格！ 英検準1級 リーディング問題 完全制覇",
            "英文解釈の技術70 / Code 70 系の精読教材",
        ],
        "リスニング": [
            "VOA Learning English",
            "ELLLO (English Listening Lesson Library Online)",
            "TED-Ed",
            "BBC Learning English YouTube",
            "EnglishClass101 YouTube",
        ],
    },
}

RESOURCE_NOTES = {
    "文法": {
        "大岩のいちばんはじめの英文法【超基礎文法編】": "文法がやや苦手な高校生の入り口に最適。",
        "改訂版 大学入試 肘井学の ゼロから英文法が面白いほどわかる本": "用語から丁寧に理解したいときに向く。",
        "Evergreen English Grammar 31 Lessons（旧Forest系）": "学校英語の標準書として長く使える。",
        "高校の学校配布文法問題集": "定期テスト対策と直結しやすい。",
        "Next Stage / Vintage などの4択文法問題集": "理解の後に定着確認するための演習向き。",
    },
    "ボキャブラリー": {
        "英検2級 でる順パス単 5訂版": "2級の最初の1冊として最有力。",
        "ランク順英検2級英単語1750 改訂版": "ランク順で回しやすく、補助教材に便利。",
        "英検2級 文で覚える単熟語 4訂版": "長文と語彙を一緒に鍛えられる。",
        "mikan（英検2級）": "スキマ時間の復習向き。",
        "英検2級 でる順パス単 クイックチェック": "定着確認用。",
        "英検準1級 でる順パス単 5訂版": "準1級の語彙対策の中心。",
        "ランク順英検準1級英単語1900 新装版": "語彙の幅を広げやすい。",
        "英検準1級 文で覚える単熟語 4訂版": "社会テーマ長文に慣れやすい。",
        "英検準1級 でる順パス単 クイックチェック": "確認テスト向き。",
        "mikan（英検準1級語彙の復習用）": "紙単語帳の補助に最適。",
    },
    "英作文": {
        "最短合格！ 英検2級 英作文問題完全制覇": "2級の型作りに強い。",
        "英検2級ライティング大特訓": "短時間で練習を回しやすい。",
        "7日間完成 英検2級 予想問題ドリル": "短期仕上げ向き。",
        "学校配布の英作文プリント・ノート": "学校課題と両立しやすい。",
        "このアプリの英作文フィードバック機能": "毎日の軽い添削向き。",
        "最短合格！ 英検準1級 要約＆英作文完全制覇": "要約と英作文を一体で対策できる。",
        "最短合格！ 英検準1級 英作文問題 完全制覇": "意見論述の型作りに強い。",
        "改訂版 英検準1級ライティング大特訓": "書く本数を増やしたい時に便利。",
        "大学入試 英作文ハイパートレーニング 自由英作文編 Plus": "論理展開を鍛えられる。",
        "英検合格のための要約問題 予想問題集（1級・準1級・2級対応）": "要約だけ補強したい時向き。",
    },
    "長文": {
        "2026年度版 英検2級 過去6回全問題集": "2級実戦の中心。",
        "英検2級 文で覚える単熟語 4訂版": "語彙と読解を同時に強化。",
        "英検分野別ターゲット 英検2級リーディング問題": "分野別練習向き。",
        "最短合格！ 英検2級 リーディング問題完全制覇": "形式慣れに使いやすい。",
        "高校英語の教科書長文": "学校との両立に有効。",
        "2026年度版 英検準1級 過去6回全問題集": "準1級実戦の中心。",
        "英検準1級 文で覚える単熟語 4訂版": "語彙と読解耐性を上げられる。",
        "英検分野別ターゲット 英検準1級リーディング問題": "弱点分野を補いやすい。",
        "最短合格！ 英検準1級 リーディング問題 完全制覇": "設問形式に慣れやすい。",
        "英文解釈の技術70 / Code 70 系の精読教材": "精読補強用。",
    },
    "リスニング": {
        "NHK高校講座 英語": "無料で高校生が入りやすい。",
        "VOA Learning English": "無料でややゆっくりした学習者向け音声。",
        "ELLLO (English Listening Lesson Library Online)": "無料でスクリプトとクイズ付き。",
        "BBC Learning English YouTube": "無料動画が豊富。",
        "EnglishClass101 YouTube": "短い動画で回しやすい。",
        "TED-Ed": "知的テーマで準1級に近い話題に慣れやすい。",
    },
}

DEFAULT_SELECTED_RESOURCES_BY_STAGE = {
    "英検2級": {
        "文法": "大岩のいちばんはじめの英文法【超基礎文法編】",
        "ボキャブラリー": "英検2級 でる順パス単 5訂版",
        "英作文": "最短合格！ 英検2級 英作文問題完全制覇",
        "長文": "2026年度版 英検2級 過去6回全問題集",
        "リスニング": "NHK高校講座 英語",
    },
    "英検準1級": {
        "文法": "大岩のいちばんはじめの英文法【超基礎文法編】",
        "ボキャブラリー": "英検準1級 でる順パス単 5訂版",
        "英作文": "最短合格！ 英検準1級 要約＆英作文完全制覇",
        "長文": "2026年度版 英検準1級 過去6回全問題集",
        "リスニング": "VOA Learning English",
    },
}

COACH_PERSONALITIES = {
    "やさしい": "今日も一歩ずつで大丈夫。ちゃんと伸びているよ。",
    "熱血": "今日の積み上げが未来を変える！もう一歩いこう！",
    "クール": "優先順位を絞って、確実に進めましょう。",
    "フレンドリー": "いい感じ！今日もサクッと積んでいこう。",
    "お姉さん/お兄さん風": "焦らなくて大丈夫。今日やる分を積めばちゃんと伸びるよ。",
}

RANKS = [
    (0, "Starter"),
    (150, "Bronze"),
    (350, "Silver"),
    (700, "Gold"),
    (1100, "Platinum"),
    (1600, "Diamond"),
    (2300, "Master"),
]

BADGES = {
    "3日連続": "3日連続ログイン達成！",
    "7日連続": "7日連続の継続！すごい！",
    "30日連続": "30日連続！習慣化の達人！",
    "計画超え": "今日の計画を超えて達成！",
    "英作文5本": "英作文5本達成！",
    "単語1000": "累計単語1000語突破！",
}

GRAMMAR_KEYWORDS = [
    ("I am agree", "I agree を使いましょう。am は不要です。"),
    ("He go", "He goes のように三単現の s を確認しましょう。"),
    ("She go", "She goes のように三単現の s を確認しましょう。"),
    ("people is", "people は通常 are を使います。"),
    ("There have", "There is / There are の形を確認しましょう。"),
    ("more easier", "比較級の二重使用です。easier のみで十分です。"),
    ("discuss about", "discuss は about なしで使えることが多いです。"),
]

WRITING_TOPICS = [
    "Do you think high school students should study abroad?",
    "Should school uniforms be mandatory?",
    "Is it a good idea for teenagers to use AI for learning?",
    "Should students volunteer in their community?",
    "Do the advantages of social media outweigh the disadvantages?",
    "Should more classes be taught online?",
]

DEFAULT_SETTINGS = {
    "student_name": "娘さん",
    "target_exam": "英検2級",
    "target_exam_date": "2026-10-04",
    "current_level": "英検準2級",
    "learning_stage": "英検2級",
    "weekday_minutes": 55,
    "weekend_minutes": 90,
    "busy_day": "木曜日",
    "school_exam_months": [6, 11, 2],
    "reading_goal_per_day": 1,
    "writing_goal_per_day": 1,
    "last_exam_result": "未受験",
    "last_exam_score": "",
    "last_exam_date": "",
    "selected_resources": DEFAULT_SELECTED_RESOURCES_BY_STAGE["英検2級"],
    "coach_name": "Mia",
    "coach_gender": "女性",
    "coach_personality": "やさしい",
    "coach_image_url": "",
}

SHEET_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@dataclass
class Phase:
    name: str
    focus: str


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(
            json.dumps(DEFAULT_SETTINGS, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if not LOG_FILE.exists():
        pd.DataFrame(columns=LOG_COLUMNS).to_csv(LOG_FILE, index=False)


def _get_sheet_mode() -> str:
    try:
        if "gcp_service_account" in st.secrets and "spreadsheet" in st.secrets:
            return "sheets"
    except Exception:
        pass
    return "local"


def _get_gspread_client() -> Optional["gspread.Client"]:
    if gspread is None or Credentials is None:
        return None
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SHEET_SCOPES
        )
        return gspread.authorize(creds)
    except Exception:
        return None


def _get_spreadsheet():
    client = _get_gspread_client()
    if client is None:
        return None
    try:
        spreadsheet_name = st.secrets["spreadsheet"]["name"]
        return client.open(spreadsheet_name)
    except Exception:
        return None


def _get_or_create_worksheet(sheet, title: str, headers: List[str]):
    try:
        ws = sheet.worksheet(title)
    except Exception:
        ws = sheet.add_worksheet(title=title, rows=1000, cols=max(len(headers), 10))
        ws.append_row(headers)
    values = ws.get_all_values()
    if not values:
        ws.append_row(headers)
    elif values[0] != headers:
        ws.clear()
        ws.append_row(headers)
    return ws


def _load_settings_from_sheets() -> Dict:
    sheet = _get_spreadsheet()
    if sheet is None:
        raise RuntimeError("Google Sheets に接続できません。")
    ws = _get_or_create_worksheet(sheet, "settings", ["key", "value"])
    records = ws.get_all_records()
    if not records:
        for k, v in DEFAULT_SETTINGS.items():
            ws.append_row([k, json.dumps(v, ensure_ascii=False)])
        return DEFAULT_SETTINGS.copy()
    settings = DEFAULT_SETTINGS.copy()
    for row in records:
        key = row.get("key")
        raw = row.get("value")
        if not key:
            continue
        try:
            settings[key] = json.loads(raw)
        except Exception:
            settings[key] = raw
    return settings


def _save_settings_to_sheets(settings: Dict) -> None:
    sheet = _get_spreadsheet()
    if sheet is None:
        raise RuntimeError("Google Sheets に接続できません。")
    ws = _get_or_create_worksheet(sheet, "settings", ["key", "value"])
    ws.clear()
    ws.append_row(["key", "value"])
    for k, v in settings.items():
        ws.append_row([k, json.dumps(v, ensure_ascii=False)])


def _load_log_from_sheets() -> pd.DataFrame:
    sheet = _get_spreadsheet()
    if sheet is None:
        raise RuntimeError("Google Sheets に接続できません。")
    ws = _get_or_create_worksheet(sheet, "study_log", LOG_COLUMNS)
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=LOG_COLUMNS)
    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def _save_log_row_to_sheets(row: Dict) -> None:
    sheet = _get_spreadsheet()
    if sheet is None:
        raise RuntimeError("Google Sheets に接続できません。")
    ws = _get_or_create_worksheet(sheet, "study_log", LOG_COLUMNS)
    records = ws.get_all_records()
    df = pd.DataFrame(records) if records else pd.DataFrame(columns=LOG_COLUMNS)
    row_df = pd.DataFrame([row])
    row_df["date"] = pd.to_datetime(row_df["date"])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date"] != row_df.loc[0, "date"]]
    df = pd.concat([df, row_df], ignore_index=True).sort_values("date")
    export = df.copy()
    export["date"] = export["date"].dt.strftime("%Y-%m-%d")
    ws.clear()
    ws.append_row(LOG_COLUMNS)
    for _, rec in export.iterrows():
        ws.append_row([rec.get(col, "") for col in LOG_COLUMNS])


def load_settings() -> Dict:
    ensure_data_files()
    mode = _get_sheet_mode()
    if mode == "sheets":
        settings = _load_settings_from_sheets()
    else:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    settings.setdefault("learning_stage", "英検2級")
    settings.setdefault(
        "selected_resources",
        DEFAULT_SELECTED_RESOURCES_BY_STAGE[settings["learning_stage"]],
    )
    settings.setdefault("coach_name", "Mia")
    settings.setdefault("coach_gender", "女性")
    settings.setdefault("coach_personality", "やさしい")
    settings.setdefault("coach_image_url", "")
    return settings


def save_settings(settings: Dict) -> None:
    if _get_sheet_mode() == "sheets":
        _save_settings_to_sheets(settings)
    else:
        SETTINGS_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def load_log() -> pd.DataFrame:
    ensure_data_files()
    if _get_sheet_mode() == "sheets":
        return _load_log_from_sheets()
    df = pd.read_csv(LOG_FILE)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def save_log_row(row: Dict) -> None:
    if _get_sheet_mode() == "sheets":
        _save_log_row_to_sheets(row)
        return
    df = load_log()
    row_df = pd.DataFrame([row])
    row_df["date"] = pd.to_datetime(row_df["date"])
    if not df.empty and row_df.loc[0, "date"] in set(df["date"]):
        df = df[df["date"] != row_df.loc[0, "date"]]
    df = pd.concat([df, row_df], ignore_index=True).sort_values("date")
    df.to_csv(LOG_FILE, index=False)


def get_phase(today: date, target_exam_date: date, stage: str) -> Phase:
    delta_days = (target_exam_date - today).days
    if stage == "英検2級":
        if delta_days > 120:
            return Phase("2級基礎期", "文法の立て直し・基本語彙・短めの長文")
        return Phase("2級仕上げ期", "過去問・英作文の型・時間配分")
    if delta_days > 120:
        return Phase("準1級土台期", "準1級語彙・社会テーマ長文・要約の土台")
    return Phase("準1級仕上げ期", "過去問・要約・英作文・時間配分")


def calculate_stage_weights(stage: str, phase_name: str) -> Dict[str, float]:
    if stage == "英検2級":
        if phase_name == "2級基礎期":
            return {
                "vocab": 0.24,
                "grammar": 0.28,
                "reading": 0.18,
                "writing": 0.12,
                "listening": 0.18,
            }
        return {
            "vocab": 0.22,
            "grammar": 0.16,
            "reading": 0.22,
            "writing": 0.18,
            "listening": 0.22,
        }
    if phase_name == "準1級土台期":
        return {
            "vocab": 0.30,
            "grammar": 0.08,
            "reading": 0.24,
            "writing": 0.20,
            "listening": 0.18,
        }
    return {
        "vocab": 0.20,
        "grammar": 0.06,
        "reading": 0.24,
        "writing": 0.25,
        "listening": 0.25,
    }


def build_daily_plan(settings: Dict, today: date) -> Dict:
    stage = settings.get("learning_stage", "英検2級")
    target_exam_date = datetime.strptime(
        settings["target_exam_date"], "%Y-%m-%d"
    ).date()
    phase = get_phase(today, target_exam_date, stage)
    is_weekend = today.weekday() >= 5
    total_minutes = (
        settings["weekend_minutes"] if is_weekend else settings["weekday_minutes"]
    )
    today_name = [
        "月曜日",
        "火曜日",
        "水曜日",
        "木曜日",
        "金曜日",
        "土曜日",
        "日曜日",
    ][today.weekday()]

    if today_name == settings["busy_day"]:
        total_minutes = max(35, total_minutes - 20)
    if today.month in settings["school_exam_months"]:
        total_minutes = max(40, total_minutes - 10)

    weights = calculate_stage_weights(stage, phase.name)
    minutes = {k: max(5, round(total_minutes * v)) for k, v in weights.items()}
    vocab_words = max(
        25, round(minutes["vocab"] * (2.1 if stage == "英検2級" else 2.3))
    )
    if is_weekend:
        vocab_words += 10

    if stage == "英検2級":
        writing_sets = 1
        reading_sets = 1 if not is_weekend else 2
        mission = "文法の穴を埋めつつ、2級の型に慣れる日"
    else:
        writing_sets = 1 if phase.name == "準1級土台期" else 2
        reading_sets = 1 if not is_weekend else 2
        mission = (
            "語彙・要約・社会テーマ長文を伸ばす日"
            if phase.name == "準1級土台期"
            else "本番形式で仕上げる日"
        )

    return {
        "stage": stage,
        "phase": phase.name,
        "focus": phase.focus,
        "mission": mission,
        "total_minutes": total_minutes,
        "vocab_words": vocab_words,
        "grammar_minutes": minutes["grammar"],
        "reading_sets": reading_sets,
        "writing_sets": writing_sets,
        "listening_minutes": minutes["listening"],
    }


def summarize_progress(df: pd.DataFrame, days: int = 7) -> Dict[str, float]:
    if df.empty:
        return {
            "vocab": 0,
            "reading": 0,
            "writing": 0,
            "listening": 0,
            "minutes": 0,
            "understanding": 0,
        }
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=days - 1)
    recent = df[df["date"] >= cutoff]
    if recent.empty:
        return {
            "vocab": 0,
            "reading": 0,
            "writing": 0,
            "listening": 0,
            "minutes": 0,
            "understanding": 0,
        }
    return {
        "vocab": float(recent["actual_vocab"].fillna(0).sum()),
        "reading": float(recent["actual_reading"].fillna(0).sum()),
        "writing": float(recent["actual_writing"].fillna(0).sum()),
        "listening": float(recent["actual_listening"].fillna(0).sum()),
        "minutes": float(recent["total_minutes"].fillna(0).sum()),
        "understanding": float(
            recent["understanding"].fillna(0).mean() if len(recent) else 0
        ),
    }


def calc_streak(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    dates = sorted(set(pd.to_datetime(df["date"]).dt.date.tolist()))
    date_set = set(dates)
    streak = 0
    current = date.today()
    while current in date_set:
        streak += 1
        current -= timedelta(days=1)
    return streak


def calc_total_points(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    points = 0
    for _, row in df.iterrows():
        points += int(row.get("actual_vocab", 0) // 5)
        points += int(row.get("actual_reading", 0) * 20)
        points += int(row.get("actual_writing", 0) * 25)
        points += int(row.get("actual_listening", 0) // 3)
        points += int(row.get("grammar_minutes", 0) // 5)
        if row.get("total_minutes", 0) >= 60:
            points += 10
        if row.get("understanding", 0) >= 4:
            points += 5
        if row.get("actual_vocab", 0) > row.get("planned_vocab", 0):
            points += 10
    return points


def get_rank(points: int) -> Tuple[str, int, int]:
    current_rank = RANKS[0][1]
    floor = 0
    next_threshold = RANKS[1][0]
    for i, (threshold, rank_name) in enumerate(RANKS):
        if points >= threshold:
            current_rank = rank_name
            floor = threshold
            next_threshold = RANKS[i + 1][0] if i + 1 < len(RANKS) else threshold
    return current_rank, floor, next_threshold


def collect_badges(df: pd.DataFrame) -> List[str]:
    badges: List[str] = []
    streak = calc_streak(df)
    if streak >= 3:
        badges.append(BADGES["3日連続"])
    if streak >= 7:
        badges.append(BADGES["7日連続"])
    if streak >= 30:
        badges.append(BADGES["30日連続"])
    if not df.empty:
        latest = df.sort_values("date").iloc[-1]
        if latest.get("actual_vocab", 0) > latest.get("planned_vocab", 0):
            badges.append(BADGES["計画超え"])
        if df["actual_writing"].fillna(0).sum() >= 5:
            badges.append(BADGES["英作文5本"])
        if df["actual_vocab"].fillna(0).sum() >= 1000:
            badges.append(BADGES["単語1000"])
    return badges


def praise_message(df: pd.DataFrame) -> str:
    if df.empty:
        return "今日の1回目のログを入れて、最初のスターターランクを進めよう！"

    latest = df.sort_values("date").iloc[-1]
    messages: List[str] = []

    if latest.get("actual_vocab", 0) > latest.get("planned_vocab", 0):
        messages.append("計画より多く単語を進められたね。かなりえらい！")
    if latest.get("total_minutes", 0) >= latest.get(
        "planned_listening", 0
    ) + latest.get("grammar_minutes", 0) + 20:
        messages.append("予定を上回る学習時間！集中力がすごい！")
    if latest.get("understanding", 0) >= 4:
        messages.append("理解度も高い日です。この感覚を明日もつなげよう。")

    streak = calc_streak(df)
    if streak >= 2:
        messages.append(f"{streak}日連続で継続中。この積み重ねが本当に強いです。")
    if not messages:
        messages.append("今日も記録できたのが大きな前進です。継続できていて良い流れです。")

    return "

".join(messages)


def coach_comment(settings: Dict, plan: Dict, df: pd.DataFrame) -> str:
    name = settings.get("coach_name", "Mia")
    personality = settings.get("coach_personality", "やさしい")
    stage = settings.get("learning_stage", "英検2級")
    streak = calc_streak(df)
    praise = praise_message(df)

    if personality == "熱血":
        opener = f"{name}です！"
        style = "今日の積み上げが未来を変える！ここで一歩上積みしよう！"
    elif personality == "クール":
        opener = f"{name}です。"
        style = "今日は優先順位を絞って、淡々と積み上げましょう。"
    elif personality == "フレンドリー":
        opener = f"{name}だよ！"
        style = "今日もいい感じで進めよう。"
    elif personality == "お姉さん/お兄さん風":
        opener = f"{name}だよ。"
        style = "焦らなくて大丈夫。今日やる分を積めばちゃんと伸びるよ。"
    else:
        opener = f"{name}です。"
        style = "今日も一歩ずつで大丈夫です。"

    mission = f"今日は {plan['mission']}"
    stage_line = (
        "2級では文法と型を安定させるのが大事。"
        if stage == "英検2級"
        else "準1級では語彙・要約・長文への耐性を伸ばすのが大事。"
    )
    streak_line = (
        f"いま {streak}日連続です。"
        if streak > 0
        else "まずは今日の1日目を作りましょう。"
    )

    return (
        f"{opener} {style}

{mission}

{stage_line}

{streak_line}

{praise}"
    )


def coach_bubble_html(settings: Dict, message: str) -> str:
    name = settings.get("coach_name", "Mia")
    personality = settings.get("coach_personality", "やさしい")
    bubble_color = {
        "やさしい": "#F7E8FF",
        "熱血": "#FFE7E0",
        "クール": "#E8F0FF",
        "フレンドリー": "#E8FFF1",
        "お姉さん/お兄さん風": "#FFF6E5",
    }.get(personality, "#F7E8FF")
    border_color = {
        "やさしい": "#C084FC",
        "熱血": "#FB7185",
        "クール": "#60A5FA",
        "フレンドリー": "#34D399",
        "お姉さん/お兄さん風": "#F59E0B",
    }.get(personality, "#C084FC")
    escaped = message.replace("
", "<br>")

    return f"""
    <div style='display:flex; align-items:flex-start; gap:12px; margin:8px 0 18px 0;'>
      <div style='width:54px; height:54px; border-radius:50%; background:#f3f4f6; display:flex; align-items:center; justify-content:center; font-size:26px; border:2px solid {border_color};'>🧑‍🏫</div>
      <div style='position:relative; background:{bubble_color}; border:2px solid {border_color}; border-radius:18px; padding:14px 16px; max-width:100%; box-shadow:0 2px 6px rgba(0,0,0,0.05);'>
        <div style='font-weight:700; margin-bottom:6px;'>{name} コーチ</div>
        <div style='line-height:1.7;'>{escaped}</div>
      </div>
    </div>
    """


def generate_feedback(df: pd.DataFrame, settings: Dict) -> str:
    if df.empty:
        return "まだ学習ログがありません。まずは3日分記録してみましょう。"

    stage = settings.get("learning_stage", "英検2級")
    recent = summarize_progress(df, 7)
    msg: List[str] = []

    if stage == "英検2級":
        msg.append("今は2級ステージなので、文法と基本語彙の安定が最優先です。")
    else:
        msg.append("今は準1級ステージなので、語彙・要約・社会テーマ読解を厚めに進めます。")

    if recent["vocab"] >= (180 if stage == "英検2級" else 230):
        msg.append("単語は順調です。")
    else:
        msg.append("単語がやや不足です。毎日20〜30語の固定から戻しましょう。")

    if recent["writing"] >= (4 if stage == "英検2級" else 6):
        msg.append("英作文の本数は確保できています。")
    else:
        msg.append("英作文は週3〜6本を目標に戻しましょう。")

    if recent["minutes"] < settings["weekday_minutes"] * 5:
        msg.append(
            "他科目が忙しい週は、単語10分＋リスニング5分だけでも継続すると流れが切れません。"
        )
    if recent["understanding"] and recent["understanding"] < 3:
        msg.append(
            "理解度が低めなので、新しい教材を増やすより復習比率を上げるのが有効です。"
        )

    return "

".join(msg)


def simple_writing_feedback(text: str) -> Dict[str, List[str]]:
    text = (text or "").strip()
    if not text:
        return {
            "score": ["0/10"],
            "strengths": ["まだ英文がありません。"],
            "suggestions": ["80語以上を目標に書いてみましょう。"],
            "grammar": [],
        }

    words = text.replace("
", " ").split()
    word_count = len(words)
    strengths: List[str] = []
    suggestions: List[str] = []
    grammar: List[str] = []

    if word_count >= 80:
        strengths.append(f"語数は {word_count} 語で十分です。")
    else:
        suggestions.append(
            f"語数が {word_count} 語です。まずは80語以上を目指しましょう。"
        )

    lowered = text.lower()
    if any(
        x in lowered
        for x in ["first", "second", "for these reasons", "however", "therefore"]
    ):
        strengths.append("構成の型を意識できています。")
    else:
        suggestions.append("First / Second / For these reasons を入れると安定します。")

    for bad, tip in GRAMMAR_KEYWORDS:
        if bad.lower() in lowered:
            grammar.append(f"{bad} → {tip}")

    if not grammar:
        grammar.append("目立つ典型ミスは見当たりません。")

    score = 5
    if word_count >= 80:
        score += 2
    if len(grammar) == 1:
        score += 1
    if any(x in lowered for x in ["first", "second", "for these reasons"]):
        score += 1
    score = min(10, score)

    if not strengths:
        strengths.append("立場を述べて理由を書く形に近づいています。")
    if not suggestions:
        suggestions.append("次は具体例を1つ入れて説得力を上げましょう。")

    return {
        "score": [f"{score}/10"],
        "strengths": strengths,
        "suggestions": suggestions,
        "grammar": grammar,
    }


def maybe_promote_stage(settings: Dict, result_status: str) -> Tuple[Dict, str]:
    current_stage = settings.get("learning_stage", "英検2級")
    if current_stage == "英検2級" and result_status == "合格":
        settings["learning_stage"] = "英検準1級"
        settings["target_exam"] = "英検準1級"
        settings["current_level"] = "英検2級"
        settings["selected_resources"] = DEFAULT_SELECTED_RESOURCES_BY_STAGE[
            "英検準1級"
        ].copy()
        return settings, "2級合格が入力されたので、教材を準1級モードに自動切替しました。"
    return settings, "現在の学習ステージを維持します。"


def apply_weakness_adjustment(settings: Dict, weak_areas: List[str]) -> None:
    stage = settings.get("learning_stage", "英検2級")
    selected = DEFAULT_SELECTED_RESOURCES_BY_STAGE[stage].copy()

    if "文法" in weak_areas:
        selected["文法"] = "改訂版 大学入試 肘井学の ゼロから英文法が面白いほどわかる本"
    if "語彙" in weak_areas:
        selected["ボキャブラリー"] = (
            "ランク順英検2級英単語1750 改訂版"
            if stage == "英検2級"
            else "ランク順英検準1級英単語1900 新装版"
        )
    if "長文" in weak_areas:
        selected["長文"] = (
            "英検分野別ターゲット 英検2級リーディング問題"
            if stage == "英検2級"
            else "英検分野別ターゲット 英検準1級リーディング問題"
        )
    if "英作文" in weak_areas:
        selected["英作文"] = (
            "英検2級ライティング大特訓"
            if stage == "英検2級"
            else "改訂版 英検準1級ライティング大特訓"
        )
    if "リスニング" in weak_areas:
        selected["リスニング"] = "ELLLO (English Listening Lesson Library Online)"

    settings["selected_resources"] = selected


def plan_recommendation_text(plan: Dict, settings: Dict) -> str:
    target_exam_date = datetime.strptime(
        settings["target_exam_date"], "%Y-%m-%d"
    ).date()
    days_left = (target_exam_date - date.today()).days
    selected = settings.get(
        "selected_resources",
        DEFAULT_SELECTED_RESOURCES_BY_STAGE[settings.get("learning_stage", "英検2級")],
    )

    items = [
        f"学習ステージ: {settings.get('learning_stage', '英検2級')}",
        f"フェーズ: {plan['phase']}",
        f"今日の重点: {plan['focus']}",
        f"今日のミッション: {plan['mission']}",
        f"試験まで残り: {days_left}日",
        f"単語: {plan['vocab_words']}語",
        f"文法: {plan['grammar_minutes']}分",
        f"長文: {plan['reading_sets']}題",
        f"英作文: {plan['writing_sets']}題",
        f"リスニング: {plan['listening_minutes']}分",
        "使用教材: " + " / ".join([f"{k}={v}" for k, v in selected.items()]),
    ]
    return "
".join([f"- {x}" for x in items])


def make_line_chart(df: pd.DataFrame, column: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(df["date"], df[column])
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)


def weekly_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = df.copy()
    temp["week"] = temp["date"].dt.to_period("W").astype(str)
    return temp.groupby("week", as_index=False).agg(
        actual_vocab=("actual_vocab", "sum"),
        actual_reading=("actual_reading", "sum"),
        actual_writing=("actual_writing", "sum"),
        actual_listening=("actual_listening", "sum"),
        total_minutes=("total_minutes", "sum"),
        understanding=("understanding", "mean"),
    )


st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption(
    "Google Sheets保存、2級→準1級の自動切替、ゲーム要素、キャラクターコーチ、吹き出しUIに対応した家庭用英検学習ダッシュボード"
)

ensure_data_files()
settings = load_settings()
df = load_log()
plan = build_daily_plan(settings, date.today())
points = calc_total_points(df)
rank_name, rank_floor, next_threshold = get_rank(points)
streak = calc_streak(df)
badges = collect_badges(df)
mode_label = "Google Sheets" if _get_sheet_mode() == "sheets" else "ローカルCSV"

with st.sidebar:
    st.header("保存先")
    st.caption(f"現在の保存先: {mode_label}")
    if _get_sheet_mode() == "local":
        st.info("st.secrets に Google Sheets の認証情報が入ると自動で Sheets 保存に切り替わります。")

    st.header("コーチ設定")
    coach_name = st.text_input("コーチの名前", value=settings.get("coach_name", "Mia"))
    coach_gender = st.selectbox(
        "コーチの性別",
        ["女性", "男性", "その他/未設定"],
        index=["女性", "男性", "その他/未設定"].index(
            settings.get("coach_gender", "女性")
        ),
    )
    coach_personality = st.selectbox(
        "コーチの性格",
        list(COACH_PERSONALITIES.keys()),
        index=list(COACH_PERSONALITIES.keys()).index(
            settings.get("coach_personality", "やさしい")
        ),
    )
    coach_image_url = st.text_input(
        "コーチ写真URL",
        value=settings.get("coach_image_url", ""),
        help="好きな画像URLを設定できます",
    )
    st.caption(COACH_PERSONALITIES[coach_personality])

    st.header("基本設定")
    student_name = st.text_input("生徒名", value=settings["student_name"])
    target_exam_date = st.date_input(
        "目標受験日",
        value=datetime.strptime(settings["target_exam_date"], "%Y-%m-%d").date(),
    )
    current_level = st.selectbox(
        "現在の級",
        ["英検3級", "英検準2級", "英検2級"],
        index=["英検3級", "英検準2級", "英検2級"].index(
            settings["current_level"]
        ),
    )
    weekday_minutes = st.slider(
        "平日の学習時間（分）", 30, 120, int(settings["weekday_minutes"])
    )
    weekend_minutes = st.slider(
        "週末の学習時間（分）", 45, 180, int(settings["weekend_minutes"])
    )
    busy_day = st.selectbox(
        "忙しい曜日",
        ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"],
        index=[
            "月曜日",
            "火曜日",
            "水曜日",
            "木曜日",
            "金曜日",
            "土曜日",
            "日曜日",
        ].index(settings["busy_day"]),
    )

    st.header("教材選択")
    learning_stage = settings.get("learning_stage", "英検2級")
    st.selectbox(
        "現在の学習ステージ",
        ["英検2級", "英検準1級"],
        index=["英検2級", "英検準1級"].index(learning_stage),
        disabled=True,
    )
    selected_resources = settings.get(
        "selected_resources",
        DEFAULT_SELECTED_RESOURCES_BY_STAGE[learning_stage],
    ).copy()
    for category, options in RESOURCE_OPTIONS[learning_stage].items():
        current_value = selected_resources.get(category, options[0])
        selected_resources[category] = st.selectbox(
            category,
            options,
            index=options.index(current_value) if current_value in options else 0,
        )
        st.caption(RESOURCE_NOTES[category][selected_resources[category]])

    if st.button("設定を保存", use_container_width=True):
        settings.update(
            {
                "coach_name": coach_name,
                "coach_gender": coach_gender,
                "coach_personality": coach_personality,
                "coach_image_url": coach_image_url,
                "student_name": student_name,
                "target_exam_date": target_exam_date.strftime("%Y-%m-%d"),
                "current_level": current_level,
                "weekday_minutes": weekday_minutes,
                "weekend_minutes": weekend_minutes,
                "busy_day": busy_day,
                "selected_resources": selected_resources,
            }
        )
        save_settings(settings)
        st.success("設定を保存しました")
        st.rerun()

st.subheader(f"{settings['student_name']}さんの学習ダッシュボード")
st.caption(f"保存先: {mode_label}")
coach_col1, coach_col2 = st.columns([1, 4])
with coach_col1:
    if settings.get("coach_image_url"):
        st.image(settings.get("coach_image_url"), use_container_width=True)
    else:
        st.markdown("## 🧑‍🏫")
with coach_col2:
    st.markdown(f"### {settings.get('coach_name', 'Mia')} コーチ")
    st.caption(
        f"性別: {settings.get('coach_gender', '女性')} / 性格: {settings.get('coach_personality', 'やさしい')}"
    )
    st.markdown(
        coach_bubble_html(settings, coach_comment(settings, plan, df)),
        unsafe_allow_html=True,
    )

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("学習ステージ", settings.get("learning_stage", "英検2級"))
col2.metric("ランク", rank_name)
col3.metric("ポイント", points)
col4.metric("連続日数", f"{streak}日")
col5.metric("今日の単語", f"{plan['vocab_words']}語")

if next_threshold > rank_floor:
    progress_ratio = min(1.0, (points - rank_floor) / (next_threshold - rank_floor))
    st.progress(progress_ratio, text=f"次のランクまで {max(0, next_threshold - points)} pt")

st.success(praise_message(df))
st.info(plan_recommendation_text(plan, settings))

if badges:
    st.markdown("### 獲得バッジ")
    for badge in badges:
        st.write(f"🏅 {badge}")

with st.expander("教材候補一覧", expanded=False):
    stage_for_view = settings.get("learning_stage", "英検2級")
    for category, options in RESOURCE_OPTIONS[stage_for_view].items():
        st.markdown(f"**{category}**")
        for item in options:
            mark = (
                "✅ "
                if settings.get(
                    "selected_resources",
                    DEFAULT_SELECTED_RESOURCES_BY_STAGE[stage_for_view],
                ).get(category)
                == item
                else "- "
            )
            st.write(f"{mark}{item}")
            st.caption(RESOURCE_NOTES[category][item])

with st.expander("Google Sheets 接続手順", expanded=False):
    st.markdown(
        """
1. Google Cloud でサービスアカウントを作成し、JSONキーを取得します。  
2. Google Sheets を作成し、サービスアカウントのメールアドレスを編集権限で共有します。  
3. Streamlit Community Cloud の App settings → Secrets に次を登録します。  

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"

[spreadsheet]
name = "EikenCoachData"
```

4. 保存後にアプリを再起動すると、自動で Google Sheets 保存に切り替わります。
        """
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["今日の計画", "ログ入力", "進捗", "英作文フィードバック", "試験結果"]
)

with tab1:
    st.markdown("### 今日やること")
    st.write(f"- 単語: {plan['vocab_words']}語")
    st.write(f"- 文法: {plan['grammar_minutes']}分")
    st.write(f"- 長文: {plan['reading_sets']}題")
    st.write(f"- 英作文: {plan['writing_sets']}題")
    st.write(f"- リスニング: {plan['listening_minutes']}分")
    st.markdown("### 今日の英作文テーマ")
    st.write(WRITING_TOPICS[date.today().toordinal() % len(WRITING_TOPICS)])
    st.markdown("### コーチからのひとこと")
    st.markdown(
        coach_bubble_html(settings, generate_feedback(df, settings)),
        unsafe_allow_html=True,
    )

with tab2:
    st.markdown("### 実施ログ入力")
    log_date = st.date_input("日付", value=date.today())
    c1, c2, c3, c4 = st.columns(4)
    actual_vocab = c1.number_input("単語数", 0, 300, int(plan["vocab_words"]))
    actual_reading = c2.number_input("長文題数", 0, 10, int(plan["reading_sets"]))
    actual_writing = c3.number_input("英作文本数", 0, 10, int(plan["writing_sets"]))
    actual_listening = c4.number_input(
        "リスニング分", 0, 180, int(plan["listening_minutes"])
    )

    c5, c6, c7, c8 = st.columns(4)
    grammar_minutes = c5.number_input(
        "文法分", 0, 180, int(plan["grammar_minutes"])
    )
    total_minutes = c6.number_input(
        "総学習時間（分）", 0, 300, int(plan["total_minutes"])
    )
    understanding = c7.slider("理解度", 1, 5, 3)
    mood = c8.selectbox("気分", ["😊", "🙂", "😐", "😣", "😫"])

    school_busy = st.selectbox("学校の忙しさ", ["低い", "普通", "高い"], index=1)
    writing_text = st.text_area("今日の英作文（任意）", height=160)
    reflection = st.text_area("振り返りメモ", height=100)

    if st.button("ログを保存", type="primary", use_container_width=True):
        save_log_row(
            {
                "date": pd.Timestamp(log_date),
                "planned_vocab": plan["vocab_words"],
                "planned_reading": plan["reading_sets"],
                "planned_writing": plan["writing_sets"],
                "planned_listening": plan["listening_minutes"],
                "actual_vocab": actual_vocab,
                "actual_reading": actual_reading,
                "actual_writing": actual_writing,
                "actual_listening": actual_listening,
                "grammar_minutes": grammar_minutes,
                "total_minutes": total_minutes,
                "understanding": understanding,
                "mood": mood,
                "school_busy": school_busy,
                "writing_text": writing_text,
                "reflection": reflection,
            }
        )
        st.success("ログを保存しました。ポイントと連続日数が更新されます。")
        st.rerun()

with tab3:
    st.markdown("### 進捗ダッシュボード")
    if df.empty:
        st.write("まだログがありません。")
    else:
        recent7 = summarize_progress(df, 7)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("7日間の総学習時間", f"{int(recent7['minutes'])}分")
        m2.metric("7日間の単語", f"{int(recent7['vocab'])}語")
        m3.metric("7日間の長文", f"{int(recent7['reading'])}題")
        m4.metric("7日間の英作文", f"{int(recent7['writing'])}本")

        st.markdown("### AIコーチのフィードバック")
        st.markdown(
            coach_bubble_html(settings, generate_feedback(df, settings)),
            unsafe_allow_html=True,
        )

        display_df = df.sort_values("date", ascending=False).copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(display_df, use_container_width=True)

        chart_df = df.sort_values("date")
        make_line_chart(chart_df, "actual_vocab", "単語数の推移")
        make_line_chart(chart_df, "total_minutes", "学習時間の推移")
        make_line_chart(chart_df, "understanding", "理解度の推移")

        st.markdown("### 週次まとめ")
        st.dataframe(weekly_summary_table(df), use_container_width=True)

with tab4:
    st.markdown("### 英作文フィードバック")
    essay = st.text_area("英文を入力してください", height=220)
    if st.button("フィードバックを実行", use_container_width=True):
        result = simple_writing_feedback(essay)
        st.metric("簡易スコア", result["score"][0])

        st.markdown("**良い点**")
        for x in result["strengths"]:
            st.write(f"- {x}")

        st.markdown("**改善点**")
        for x in result["suggestions"]:
            st.write(f"- {x}")

        st.markdown("**文法・表現チェック**")
        for x in result["grammar"]:
            st.write(f"- {x}")

with tab5:
    st.markdown("### 試験結果入力")
    st.write(
        "2級に合格したら、ここで結果を入力すると教材が準1級モードに自動で切り替わります。"
    )
    exam_date_input = st.date_input("受験日", value=date.today(), key="exam_date_input")
    result_status = st.selectbox(
        "結果", ["未受験", "合格", "不合格"], key="result_status"
    )
    exam_score_input = st.text_input(
        "スコア・メモ（任意）", value="", key="exam_score_input"
    )
    weak_area = st.multiselect(
        "不合格だった場合の弱点（任意）",
        ["文法", "語彙", "長文", "英作文", "リスニング"],
        key="weak_area",
    )

    if st.button("試験結果を保存して教材を更新", type="primary", use_container_width=True):
        settings["last_exam_result"] = result_status
        settings["last_exam_score"] = exam_score_input
        settings["last_exam_date"] = exam_date_input.strftime("%Y-%m-%d")
        settings, message = maybe_promote_stage(settings, result_status)

        if result_status == "不合格" and weak_area:
            apply_weakness_adjustment(settings, weak_area)
            message += " 不合格時の弱点に合わせて教材も調整しました。"

        save_settings(settings)
        st.success(message)
        st.rerun()

st.divider()
st.caption(
    "使い方: ①Google Sheets を設定すると公開版でもログが残る → ②コーチを設定 → ③2級モードで学習 → ④合格なら準1級モードへ自動切替。"
)
