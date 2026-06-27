import streamlit as st
import random
import time
from collections import defaultdict
from copy import deepcopy
import heapq

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
# ① オリジナル DP（mix / feed / item の3軸で返す）
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

    # mix 最大
    best_mix = max(results, key=lambda x: x[0] + x[1] * 100)

    # feed 軸（feed → item）
    best_feed = max(results, key=lambda x: (x[0], x[1]))

    # item 軸（item → feed）
    best_item = max(results, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# ② 段階縮約DP（完全一致版）
# ============================================================
def dp_fast(points, N):
    OPTIONS = []
    for ev in EVENT_KEYS:
        for stage, cost in enumerate(EVENT_DATA[ev]["costs"], start=1):
            OPTIONS.append((ev, stage, cost))

    dp = [[] for _ in range(N + 1)]
    dp[0] = [(0, 0, deepcopy(points))]

    for i in range(N):
        next_states = []

        for feed_now, item_now, rem_now in dp[i]:
            for ev, stage, cost in OPTIONS:
                if rem_now[ev] < cost:
                    continue

                new_rem = rem_now.copy()
                new_rem[ev] -= cost

                feed_gain = FEED[stage - 1]
                item_gain = ITEM[stage - 1]

                next_states.append((
                    feed_now + feed_gain,
                    item_now + item_gain,
                    new_rem
                ))

        # 枝刈り
        pruned = []
        next_states.sort(key=lambda x: (x[0], x[1]), reverse=True)

        for f, it, rem in next_states:
            dominated = False
            for pf, pit, _ in pruned:
                if pf >= f and pit >= it:
                    dominated = True
                    break
            if not dominated:
                pruned.append((f, it, rem))

        dp[i + 1] = pruned

    results = []
    for states in dp:
        for f, it, rem in states:
            results.append((f, it))

    best_mix = max(results, key=lambda x: x[0] + x[1] * 100)
    best_feed = max(results, key=lambda x: (x[0], x[1]))
    best_item = max(results, key=lambda x: (x[1], x[0]))

    return best_mix, best_feed, best_item


# ============================================================
# Streamlit UI
# ============================================================
st.title("🐷 DP 自動検証ツール（10回ランダムテスト × 3評価軸）")

count = st.number_input("残り育成回数（最大10）", min_value=1, max_value=10, value=5)

if st.button("10回テスト実行"):
    st.write("### 🚀 実行中…")

    results = []
    success_mix = 0
    success_feed = 0
    success_item = 0

    for t in range(10):
        # ランダムポイント生成（段階2〜段階4×2）
        random_points = {}
        for ev in EVENT_KEYS:
            stage2 = EVENT_DATA[ev]["costs"][1]
            stage4 = EVENT_DATA[ev]["costs"][3]
            random_points[ev] = random.randint(stage2, stage4 * 2)

        # オリジナル
        o_mix, o_feed, o_item = dp_original(random_points, count)

        # 高速版
        f_mix, f_feed, f_item = dp_fast(random_points, count)

        ok_mix = (o_mix == f_mix)
        ok_feed = (o_feed == f_feed)
        ok_item = (o_item == f_item)

        if ok_mix: success_mix += 1
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
            "item_match": ok_item
        })

    st.write("### 🔍 結果一覧")
    st.table(results)

    st.write(f"### 🎉 一致率（10回中）")
    st.write(f"- 複合スコア（mix）：{success_mix} / 10")
    st.write(f"- 餌軸（feed）：{success_feed} / 10")
    st.write(f"- アイテム軸（item）：{success_item} / 10")
