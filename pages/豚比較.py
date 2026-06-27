import streamlit as st
import random
import time
from collections import defaultdict
from copy import deepcopy

# ============================================================
# イベント定義
# ============================================================
EVENT_DATA = {
    "shousen": {
        "name": "商戦",
        "costs": [8170, 81625, 163250, 653000],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    },
    "puzzle": {
        "name": "海上パズル",
        "costs": [550, 1175, 2350, 9400],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    },
    "nankai": {
        "name": "南海航路",
        "costs": [1, 4, 7, 28],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    },
    "hana": {
        "name": "花咲く春",
        "costs": [210, 850, 1700, 6800],
        "feed":  [20, 200, 400, 1600],
        "item":  [1, 1, 2, 2]
    }
}

EVENT_KEYS = list(EVENT_DATA.keys())
FEED = EVENT_DATA[EVENT_KEYS[0]]["feed"]
ITEM = EVENT_DATA[EVENT_KEYS[0]]["item"]

# ============================================================
# オリジナルDP（完全一致用）
# ============================================================
def dp_original(points, N):
    OPTIONS = []
    for key, ev in EVENT_DATA.items():
        for stage, cost in enumerate(ev["costs"], start=1):
            OPTIONS.append((key, cost, ev["feed"][stage-1], ev["item"][stage-1]))

    event_keys = list(EVENT_DATA.keys())
    dp = [defaultdict(lambda: {"feed": -1, "item": -1}) for _ in range(N + 1)]

    start_key = tuple(points[k] for k in event_keys)
    dp[0][start_key] = {"feed": 0, "item": 0}

    for i in range(N):
        for state_key, state in dp[i].items():
            feed_now = state["feed"]
            item_now = state["item"]
            current_points = dict(zip(event_keys, state_key))

            for ev, cost, feed_gain, item_gain in OPTIONS:
                if cost > current_points[ev]:
                    continue

                new_points = current_points.copy()
                new_points[ev] -= cost
                new_key = tuple(new_points[k] for k in event_keys)

                new_feed = feed_now + feed_gain
                new_item = item_now + item_gain

                old = dp[i + 1][new_key]
                if new_feed > old["feed"] or new_item > old["item"]:
                    dp[i + 1][new_key] = {"feed": new_feed, "item": new_item}

    results = []
    for i in range(N + 1):
        for st in dp[i].values():
            results.append((st["feed"], st["item"]))

    best_mix  = max(results, key=lambda x: x[0] + x[1] * 100)
    best_feed = max(results, key=lambda x: (x[0], x[1]))
    best_item = max(results, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# 高速オリジナルDP（完全一致・Pareto枝刈り）
# ============================================================
def dp_fast_original(points, N):
    OPTIONS = []
    for ev in EVENT_KEYS:
        for stage, cost in enumerate(EVENT_DATA[ev]["costs"], start=1):
            OPTIONS.append((ev, stage, cost))

    dp = [defaultdict(list) for _ in range(N + 1)]
    dp[0][tuple(points[k] for k in EVENT_KEYS)] = [(0, 0)]

    for i in range(N):
        for state_key, states in dp[i].items():
            rem_now = dict(zip(EVENT_KEYS, state_key))

            for feed_now, item_now in states:
                for ev, stage, cost in OPTIONS:
                    if rem_now[ev] < cost:
                        continue

                    new_rem = rem_now.copy()
                    new_rem[ev] -= cost
                    new_key = tuple(new_rem[k] for k in EVENT_KEYS)

                    new_feed = feed_now + FEED[stage-1]
                    new_item = item_now + ITEM[stage-1]

                    dp[i+1][new_key].append((new_feed, new_item))

        # 各ポイント残量ごとに Pareto 最適化
        for key in dp[i+1]:
            arr = dp[i+1][key]
            arr.sort(key=lambda x: (x[0], x[1]), reverse=True)
            pruned = []
            for f, it in arr:
                if any(pf >= f and pit >= it for pf, pit in pruned):
                    continue
                pruned.append((f, it))
            dp[i+1][key] = pruned

    # 全状態から最適解を取る
    all_states = []
    for states in dp[N].values():
        all_states.extend(states)

    best_mix  = max(all_states, key=lambda x: x[0] + x[1] * 100)
    best_feed = max(all_states, key=lambda x: (x[0], x[1]))
    best_item = max(all_states, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# Streamlit UI
# ============================================================
st.title("🐷 完全一致版 高速オリジナルDP × 10回検証")

count = st.number_input("残り育成回数（最大10）", min_value=1, max_value=10, value=10)

if st.button("10回テスト実行"):
    st.write("### 🚀 実行中…")

    results = []
    success_mix = 0
    success_feed = 0
    success_item = 0

    for t in range(10):
        random_points = {}
        for ev in EVENT_KEYS:
            stage2 = EVENT_DATA[ev]["costs"][1]
            stage4 = EVENT_DATA[ev]["costs"][3]
            random_points[ev] = random.randint(stage2, stage4 * 2)

        # オリジナル
        t0 = time.perf_counter()
        o_mix, o_feed, o_item = dp_original(random_points, count)
        t1 = time.perf_counter()

        # 高速版
        t2 = time.perf_counter()
        f_mix, f_feed, f_item = dp_fast_original(random_points, count)
        t3 = time.perf_counter()

        ok_mix  = (o_mix  == f_mix)
        ok_feed = (o_feed == f_feed)
        ok_item = (o_item == f_item)

        if ok_mix:  success_mix  += 1
        if ok_feed: success_feed += 1
        if ok_item: success_item += 1

        results.append({
            "test": t + 1,
            "points": random_points,
            "mix_orig": o_mix,
            "mix_fast": f_mix,
            "mix_match": ok_mix,
            "feed_orig": o_feed,
            "feed_fast": f_feed,
            "feed_match": ok_feed,
            "item_orig": o_item,
            "item_fast": f_item,
            "item_match": ok_item,
            "time_orig_ms": (t1 - t0) * 1000,
            "time_fast_ms": (t3 - t2) * 1000,
        })

    st.write("### 🔍 結果一覧")
    st.table(results)

    st.write(f"### 🎉 一致率（10回中）")
    st.write(f"- 複合スコア（mix）：{success_mix} / 10")
    st.write(f"- 餌軸（feed）：{success_feed} / 10")
    st.write(f"- アイテム軸（item）：{success_item} / 10")
