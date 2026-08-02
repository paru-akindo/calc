import streamlit as st
import math
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

st.title("江南 修練シミュレーター（次の境地まで対応版）")

# ── 昇段に必要な修練値 ──
required_training = {
    "良民": {3: 41000, 2: 288200, 1: 497700},
    "文人": {3: 747600, 2: 1058000, 1: 1414000},
    "才女": {3: 1874000, 2: 2364000, 1: 2980000},
    "学士": {6: 3667000, 5: 4466000, 4: 5341000, 3: 6346000, 2: 7491000, 1: 8730000},
    "翰林": {6: 10120000, 5: 11680000, 4: 13350000, 3: 15200000, 2: 17180000, 1: 19340000},
    "博雅": {6: 16190000, 5: 18300000, 4: 26900000, 3: 63300000, 2: 68430000, 1: 73540000},
    "名仕": {9: 79070000, 8: 84680000, 7: 0, 6: 0, 5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
    "聖人": {9: 0, 8: 0, 7: 0, 6: 0, 5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
}

# ── 周天あたり修練速度 ──
training_speeds = {
    "良民": {3: 100, 2: 200, 1: 300},
    "文人": {3: 400, 2: 500, 1: 600},
    "才女": {3: 700, 2: 800, 1: 900},
    "学士": {6: 1000, 5: 1100, 4: 1200, 3: 1300, 2: 1400, 1: 1500},
    "翰林": {6: 1600, 5: 1700, 4: 1800, 3: 1900, 2: 2000, 1: 2100},
    "博雅": {6: 2200, 5: 2300, 4: 2400, 3: 2500, 2: 2600, 1: 2700},
    "名仕": {9: 2800, 8: 2900, 7: 3000, 6: 3100, 5: 3200, 4: 3300, 3: 3400, 2: 3500, 1: 3600},
    "聖人": {9: 3700, 8: 3800, 7: 3900, 6: 4000, 5: 4100, 4: 4200, 3: 4300, 2: 4400, 1: 4500}
}

# ── 定数 ──
CYCLE_TIME = 8
HERB_INTERVAL = 15 * 60
HERB_CYCLES = 40
BUFF_OPTIONS = {"30%": 0.30, "20%": 0.20, "10%": 0.10, "3%": 0.03}

# ── シミュレーション ──
def simulate_time(remaining, base_speed, buff):
    speed_manual = base_speed * (1 + buff)
    speed_herb = base_speed

    per_cycle = speed_manual
    herb_cycle_gain = HERB_CYCLES * speed_herb

    t = 0
    manual = 0
    herb = 0

    while remaining > 0:
        remaining -= per_cycle
        manual += per_cycle
        t += CYCLE_TIME

        if t % HERB_INTERVAL == 0:
            remaining -= herb_cycle_gain
            herb += herb_cycle_gain

    return t, manual, herb

# ── 次の境地まで（表3） ──
def simulate_until_next_stage(stage, rank, current, buff):
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    stage_list = list(required_training.keys())
    current_stage_index = stage_list.index(stage)
    next_stage = stage_list[current_stage_index + 1]

    # 計算用：自分の境地の「自分から下」だけ
    ranks = sorted(required_training[stage].keys(), reverse=True)
    start_index = ranks.index(rank)
    target_steps = [(stage, r) for r in ranks[start_index:]]

    # タイトル用：1つ後ろ＋最後に次境地
    display_steps = []
    for i, (stg_calc, rnk_calc) in enumerate(target_steps):
        if i < len(target_steps) - 1:
            # 1つ後ろの段位をタイトルにする
            stg_disp, rnk_disp = target_steps[i + 1]
        else:
            # 最後だけ次の境地の最初の段位
            next_stage_ranks = sorted(
                [r for r, v in required_training[next_stage].items() if v > 0],
                reverse=True
            )
            stg_disp, rnk_disp = next_stage, next_stage_ranks[0]

        # 計算は stg_calc, rnk_calc を使う
        base_speed = training_speeds[stg_calc][rnk_calc]
        required = required_training[stg_calc][rnk_calc]
        remaining = max(0, required - current)

        t, _, _ = simulate_time(remaining, base_speed, buff)
        reach_time = now + timedelta(seconds=t)

        display_steps.append({
            "stage": stg_disp,
            "rank": rnk_disp,
            "reach_time": reach_time.strftime("%Y-%m-%d %H:%M")
        })

        now = reach_time
        current = 0

    return display_steps

# ── 入力 ──
stage = st.selectbox("境地", list(required_training.keys()))
rank = st.selectbox("段位", sorted(training_speeds[stage].keys(), reverse=True))
current_w10k = st.number_input("現在値（万）", min_value=0)
target_w10k = st.number_input("目標値（万）", min_value=0, value=required_training[stage][rank]//10000)
item_count = st.number_input("アイテム数", min_value=0)

# ── 実行 ──
if st.button("シミュレーション開始"):
    current = current_w10k * 10000
    target = target_w10k * 10000
    remaining = max(0, target - current)
    base_speed = training_speeds[stage][rank]
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    # 表1
    rows1 = []
    for label, buff in BUFF_OPTIONS.items():
        t, m, h = simulate_time(remaining, base_speed, buff)
        finish = now + timedelta(seconds=t)
        rows1.append({
            "バフ": label,
            "到達": finish.strftime("%Y-%m-%d %H:%M"),
            "時間": f"{t//3600}h {(t%3600)//60}m",
            "自動": m//10000,
            "仙草": h//10000
        })
    st.markdown("### 次の段位まで（アイテム未使用）")
    st.table(pd.DataFrame(rows1))

    # 表3（タイトルだけ正しくずらした）
    rows3 = []
    for label, buff in BUFF_OPTIONS.items():
        steps = simulate_until_next_stage(stage, rank, current, buff)
        row = {"バフ": label}
        for s in steps:
            row[f"{s['stage']} {s['rank']}"] = s["reach_time"]
        rows3.append(row)

    st.markdown("### 次の境地まで（アイテムなし）")
    st.table(pd.DataFrame(rows3))
