import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# -----------------------------
# 設定値（江南版）
# -----------------------------
required_training = {
    "学士": {6: 3667000, 5: 4466000, 4: 5341000, 3: 6346000, 2: 7491000, 1: 8730000},
    "翰林": {6: 10120000, 5: 11680000, 4: 13350000, 3: 15200000, 2: 17180000, 1: 19340000},
}

training_speeds = {
    "学士": {6: 1000, 5: 1100, 4: 1200, 3: 1300, 2: 1400, 1: 1500},
    "翰林": {6: 1600, 5: 1700, 4: 1800, 3: 1900, 2: 2000, 1: 2100},
}

CYCLE_TIME = 8
HERB_INTERVAL = 900
HERB_CYCLES = 40

# -----------------------------
# simulate_time のデバッグ版
# -----------------------------
def simulate_time_debug(remaining, base_speed, buff):
    speed_manual = base_speed * (1 + buff)
    speed_herb = base_speed

    per_cycle = speed_manual
    herb_cycle_gain = HERB_CYCLES * speed_herb

    t = 0
    manual = 0
    herb = 0
    next_herb_time = HERB_INTERVAL

    logs = []

    while remaining > 0:
        before = remaining

        # 周天
        remaining -= per_cycle
        manual += per_cycle
        t += CYCLE_TIME

        log = {
            "t": t,
            "before": before,
            "after_manual": remaining,
            "manual_gain": per_cycle,
            "herb_gain": 0,
            "herb_trigger": False,
        }

        # 仙草発動（複数回発動の可能性あり）
        while t >= next_herb_time:
            remaining -= herb_cycle_gain
            herb += herb_cycle_gain
            log["herb_gain"] += herb_cycle_gain
            log["herb_trigger"] = True
            next_herb_time += HERB_INTERVAL

        log["after_herb"] = remaining
        logs.append(log)

    return t, manual, herb, logs


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("江南 修練シミュレーター（デバッグ版）")

stage = st.selectbox("境地", ["学士"])
rank = st.selectbox("段位", [1, 2, 3, 4, 5, 6])
current_w10k = st.number_input("現在値（万）", value=0)
target_stage = st.selectbox("目標境地", ["翰林"])
target_rank = st.selectbox("目標段位", [6, 5, 4, 3, 2, 1])
buff = st.selectbox("バフ", [0.30, 0.20, 0.10, 0.03])

if st.button("デバッグ実行"):
    current = current_w10k * 10000
    target = required_training[target_stage][target_rank]
    remaining = max(0, target - current)

    base_speed = training_speeds[stage][rank]

    st.write(f"### 計算条件")
    st.write(f"- 現在：{stage} {rank}")
    st.write(f"- 速度：{base_speed}")
    st.write(f"- 目標：{target_stage} {target_rank}")
    st.write(f"- 必要値：{remaining:,}")
    st.write(f"- バフ：{buff*100:.0f}%")

    t, m, h, logs = simulate_time_debug(remaining, base_speed, buff)

    st.write(f"### 結果")
    st.write(f"- 総時間：{t//3600}h {(t%3600)//60}m {t%60}s")
    st.write(f"- 手動：{m:,}")
    st.write(f"- 仙草：{h:,}")

    df = pd.DataFrame(logs)
    st.write("### デバッグログ（周天ごとの状態）")
    st.dataframe(df)
