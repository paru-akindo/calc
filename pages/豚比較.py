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
# オリジナルDP（完全一致基準）
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
# fast1：軽量最適化（枝刈り O(n²→n)）
# ============================================================
def dp_fast1(points, N):
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

        # Pareto 最適化（O(n)）
        for key in dp[i+1]:
            arr = dp[i+1][key]
            arr.sort(key=lambda x: (x[0], x[1]), reverse=True)
            pruned = []
            best_item = -1
            for f, it in arr:
                if it > best_item:
                    pruned.append((f, it))
                    best_item = it
            dp[i+1][key] = pruned

    all_states = []
    for states in dp[N].values():
        all_states.extend(states)

    best_mix  = max(all_states, key=lambda x: x[0] + x[1] * 100)
    best_feed = max(all_states, key=lambda x: (x[0], x[1]))
    best_item = max(all_states, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# fast2：中量最適化（fast1 + イベント順固定 + 辞書キー削減）
# ============================================================
def dp_fast2(points, N):
    OPTIONS = []
    # イベント順固定（高速化）
    for ev in ["nankai", "puzzle", "hana", "shousen"]:
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
                    new_key = (
                        new_rem["shousen"],
                        new_rem["puzzle"],
                        new_rem["nankai"],
                        new_rem["hana"]
                    )

                    new_feed = feed_now + FEED[stage-1]
                    new_item = item_now + ITEM[stage-1]

                    dp[i+1][new_key].append((new_feed, new_item))

        # Pareto 最適化（O(n)）
        for key in dp[i+1]:
            arr = dp[i+1][key]
            arr.sort(key=lambda x: (x[0], x[1]), reverse=True)
            pruned = []
            best_item = -1
            for f, it in arr:
                if it > best_item:
                    pruned.append((f, it))
                    best_item = it
            dp[i+1][key] = pruned

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
st.title("🐷 original / fast1 / fast2 比較検証ツール（10回ランダムテスト）")

count = st.number_input("残り育成回数（最大10）", min_value=1, max_value=10, value=10)

if st.button("10回テスト実行"):
    st.write("### 🚀 実行中…")

    results = []
    ok1_mix = ok1_feed = ok1_item = 0
    ok2_mix = ok2_feed = ok2_item = 0

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

        # fast1
        t2 = time.perf_counter()
        f1_mix, f1_feed, f1_item = dp_fast1(random_points, count)
        t3 = time.perf_counter()

        # fast2
        t4 = time.perf_counter()
        f2_mix, f2_feed, f2_item = dp_fast2(random_points, count)
        t5 = time.perf_counter()

        # 一致判定
        m1 = (o_mix == f1_mix)
        f1 = (o_feed == f1_feed)
        i1 = (o_item == f1_item)

        m2 = (o_mix == f2_mix)
        f2 = (o_feed == f2_feed)
        i2 = (o_item == f2_item)

        ok1_mix += m1
        ok1_feed += f1
        ok1_item += i1

        ok2_mix += m2
        ok2_feed += f2
        ok2_item += i2

        results.append({
            "test": t+1,
            "points": random_points,

            "orig_mix": o_mix,
            "fast1_mix": f1_mix,
            "fast2_mix": f2_mix,
            "mix1_match": m1,
            "mix2_match": m2,

            "orig_feed": o_feed,
            "fast1_feed": f1_feed,
            "fast2_feed": f2_feed,
            "feed1_match": f1,
            "feed2_match": f2,

            "orig_item": o_item,
            "fast1_item": f1_item,
            "fast2_item": f2_item,
            "item1_match": i1,
            "item2_match": i2,

            "time_orig_ms": (t1 - t0) * 1000,
            "time_fast1_ms": (t3 - t2) * 1000,
            "time_fast2_ms": (t5 - t4) * 1000,
        })

    st.write("### 🔍 結果一覧")
    st.table(results)

    st.write("### 🎉 一致率（10回中）")
    st.write(f"- fast1（軽量） mix/feed/item：{ok1_mix}/{ok1_feed}/{ok1_item}")
    st.write(f"- fast2（中量） mix/feed/item：{ok2_mix}/{ok2_feed}/{ok2_item}")
