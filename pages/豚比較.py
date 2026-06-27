import streamlit as st
import random
import time
from copy import deepcopy

# ============================================================
# イベント定義
# ============================================================
EVENT_DATA = {
    "shousen": {
        "costs": [8170, 81625, 163250, 653000],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    },
    "puzzle": {
        "costs": [550, 1175, 2350, 9400],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    },
    "nankai": {
        "costs": [1, 4, 7, 28],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    },
    "hana": {
        "costs": [210, 850, 1700, 6800],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    }
}

EVENT_KEYS = list(EVENT_DATA.keys())
FEED = EVENT_DATA["shousen"]["feed"]
ITEM = EVENT_DATA["shousen"]["item"]

# ============================================================
# オリジナルDP（完全一致基準）
# ============================================================
def dp_original(points, N):
    OPTIONS = []
    for ev, evd in EVENT_DATA.items():
        for stage, cost in enumerate(evd["costs"], start=1):
            OPTIONS.append((ev, cost, evd["feed"][stage-1], evd["item"][stage-1]))

    dp = [{} for _ in range(N+1)]
    dp[0][tuple(points[k] for k in EVENT_KEYS)] = (0, 0)

    for i in range(N):
        for key, (f_now, it_now) in dp[i].items():
            rem = dict(zip(EVENT_KEYS, key))
            for ev, cost, f_gain, it_gain in OPTIONS:
                if rem[ev] < cost:
                    continue
                new_rem = rem.copy()
                new_rem[ev] -= cost
                new_key = tuple(new_rem[k] for k in EVENT_KEYS)
                new_state = (f_now + f_gain, it_now + it_gain)

                if new_key not in dp[i+1]:
                    dp[i+1][new_key] = new_state
                else:
                    old = dp[i+1][new_key]
                    if new_state[0] > old[0] or new_state[1] > old[1]:
                        dp[i+1][new_key] = new_state

    all_states = dp[N].values()
    best_mix  = max(all_states, key=lambda x: x[0] + x[1]*100)
    best_feed = max(all_states, key=lambda x: (x[0], x[1]))
    best_item = max(all_states, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# レベル3：最大最適化DP（完全一致 × 超高速）
# ============================================================
def dp_fast3(points, N):
    OPTIONS = []
    # イベント順固定（高速化）
    for ev in ["nankai", "puzzle", "hana", "shousen"]:
        evd = EVENT_DATA[ev]
        for stage, cost in enumerate(evd["costs"], start=1):
            OPTIONS.append((ev, cost, evd["feed"][stage-1], evd["item"][stage-1]))

    dp = {}
    dp[tuple(points[k] for k in EVENT_KEYS)] = (0, 0)

    for _ in range(N):
        next_dp = {}
        for key, (f_now, it_now) in dp.items():
            rem = dict(zip(EVENT_KEYS, key))
            for ev, cost, f_gain, it_gain in OPTIONS:
                if rem[ev] < cost:
                    continue

                new_rem = rem.copy()
                new_rem[ev] -= cost
                new_key = (
                    new_rem["shousen"],
                    new_rem["puzzle"],
                    new_rem["nankai"],
                    new_rem["hana"]
                )

                new_state = (f_now + f_gain, it_now + it_gain)

                if new_key not in next_dp:
                    next_dp[new_key] = new_state
                else:
                    old = next_dp[new_key]
                    if new_state[0] > old[0] or new_state[1] > old[1]:
                        next_dp[new_key] = new_state

        dp = next_dp

    all_states = dp.values()
    best_mix  = max(all_states, key=lambda x: x[0] + x[1]*100)
    best_feed = max(all_states, key=lambda x: (x[0], x[1]))
    best_item = max(all_states, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# Streamlit UI
# ============================================================
st.title("🐷 レベル3：完全一致 × 超高速DP（10回検証）")

count = st.number_input("残り育成回数（最大10）", min_value=1, max_value=10, value=10)

if st.button("10回テスト実行"):
    st.write("### 🚀 実行中…")

    results = []
    ok_mix = ok_feed = ok_item = 0

    for t in range(10):
        random_points = {}
        for ev in EVENT_KEYS:
            stage2 = EVENT_DATA[ev]["costs"][1]
            stage4 = EVENT_DATA[ev]["costs"][3]
            random_points[ev] = random.randint(stage2, stage4 * 2)

        # original
        t0 = time.perf_counter()
        o_mix, o_feed, o_item = dp_original(random_points, count)
        t1 = time.perf_counter()

        # fast3
        t2 = time.perf_counter()
        f_mix, f_feed, f_item = dp_fast3(random_points, count)
        t3 = time.perf_counter()

        ok_mix  += (o_mix  == f_mix)
        ok_feed += (o_feed == f_feed)
        ok_item += (o_item == f_item)

        results.append({
            "test": t+1,
            "points": random_points,
            "orig_mix": o_mix,
            "fast3_mix": f_mix,
            "mix_match": o_mix == f_mix,
            "orig_feed": o_feed,
            "fast3_feed": f_feed,
            "feed_match": o_feed == f_feed,
            "orig_item": o_item,
            "fast3_item": f_item,
            "item_match": o_item == f_item,
            "time_orig_ms": (t1 - t0) * 1000,
            "time_fast3_ms": (t3 - t2) * 1000,
        })

    st.write("### 🔍 結果一覧")
    st.table(results)

    st.write("### 🎉 一致率（10回中）")
    st.write(f"- mix：{ok_mix} / 10")
    st.write(f"- feed：{ok_feed} / 10")
    st.write(f"- item：{ok_item} / 10")
