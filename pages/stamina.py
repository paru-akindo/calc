# app.py
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

JST = ZoneInfo("Asia/Tokyo")
CSV_PATH = "events.csv"

st.set_page_config(page_title="体力回復予測", layout="centered")
st.title("体力回復予測（単体版）")

# --- ヘルパー ---
def load_events_from_csv(path):
    events = []
    try:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("event_name") or row.get("name")
                if not name:
                    continue
                max_stamina = row.get("max_stamina")
                recovery = row.get("recovery_minutes")
                events.append({
                    "name": name,
                    "max_stamina": int(max_stamina) if max_stamina else None,
                    "recovery_minutes": float(recovery) if recovery else 0.0,
                })
    except FileNotFoundError:
        return []
    return events

def calc_recovery_local(event_info, current):
    max_stamina = event_info["max_stamina"]
    t = event_info["recovery_minutes"]
    if max_stamina is None:
        raise ValueError("This event has no max stamina")
    if current > max_stamina:
        raise ValueError("Current stamina exceeds max")
    need = max_stamina - current
    now = datetime.now(JST)
    if need <= 0:
        time_str = f"{now.month}/{now.day} {now.strftime('%H:%M')}"
        return {"need": 0, "min": time_str, "max": time_str}
    min_minutes = (need - 1) * t
    max_minutes = need * t
    min_time = now + timedelta(minutes=min_minutes)
    max_time = now + timedelta(minutes=max_minutes)
    min_str = f"{min_time.month}/{min_time.day} {min_time.strftime('%H:%M')}"
    max_str = f"{max_time.month}/{max_time.day} {max_time.strftime('%H:%M')}"
    return {"need": need, "min": min_str, "max": max_str}

def format_range(min_str, max_str):
    if not min_str or not max_str:
        return ""
    min_parts = str(min_str).split(" ")
    max_parts = str(max_str).split(" ")
    min_date, min_time = (min_parts[0], min_parts[1]) if len(min_parts) >= 2 else (min_parts[0], "")
    max_date, max_time = (max_parts[0], max_parts[1]) if len(max_parts) >= 2 else (max_parts[0], "")
    if min_date == max_date:
        return f"{min_date} {min_time}〜{max_time}"
    return f"{min_str} 〜 {max_str}"

# --- データ読み込み ---
events = load_events_from_csv(CSV_PATH)

if not events:
    st.warning("events.csv が見つかりません。プロジェクトルートに events.csv を置いてください。")
    st.stop()

names = [e["name"] for e in events]

# --- UI（単一表示） ---
selected = st.selectbox("イベントを選択", ["（選択しない）"] + names, index=0)

# スライダーの max は選択イベントの max_stamina を使う（選択なしは 100）
selected_max = next((e["max_stamina"] for e in events if e["name"] == selected), 100)
current = st.slider("現在体力", min_value=0, max_value=selected_max if selected_max is not None else 100, value=0)

if st.button("計算する"):
    if selected == "（選択しない）":
        st.info("イベントを選んでください。")
    else:
        ev = next((e for e in events if e["name"] == selected), None)
        if not ev:
            st.error("選択されたイベント情報が見つかりません。")
        else:
            try:
                res = calc_recovery_local(ev, current)
                st.markdown(f"**必要回復数：{res['need']}**")
                st.markdown(f"**全回復予想：{format_range(res['min'], res['max'])}**")
            except Exception as ex:
                st.error(f"計算エラー: {ex}")
