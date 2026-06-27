import streamlit as st
import time
from collections import defaultdict
import heapq
from copy import deepcopy

# ============================================================
# 🔼 イベント定義（共通）
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

# feed/item は全イベント共通
FEED = EVENT_DATA[EVENT_KEYS[0]]["feed"]
ITEM = EVENT_DATA[EVENT_KEYS[0]]["item"]

# ============================================================
# 共通：履歴の日本語化
# ============================================================
def convert_history(history):
    jp = []
    for ev, stage, cost, feed, item in history:
        jp.append({
            "event": EVENT_DATA[ev]["name"],
            "stage": stage,
            "cost": cost,
            "feed": feed,
            "item": item
        })
    return jp


# ============================================================
# ① オリジナル版 DP
# ============================================================
def dp_original(points, N):
    OPTIONS = []
    STAGE_MAP = {}

    for key, ev in EVENT_DATA.items():
        for stage, cost in enumerate(ev["costs"], start=1):
            feed = ev["feed"][stage - 1]
            item = ev["item"][stage - 1]
            OPTIONS.append((key, cost, feed, item))
            STAGE_MAP[cost] = stage

    def conv(hist):
        out = []
        for ev, cost, feed, item in hist:
            out.append((ev, STAGE_MAP[cost], cost, feed, item))
        return out

    event_keys = list(EVENT_DATA.keys())
    dp = [defaultdict(lambda: {"feed": -1, "item": -1, "history": []})
          for _ in range(N + 1)]

    start_key = tuple(points[k] for k in event_keys)
    dp[0][start_key] = {"feed": 0, "item": 0, "history": []}

    for i in range(N):
        for state_key, state in dp[i].items():
            feed_now = state["feed"]
            item_now = state["item"]
            hist_now = state["history"]

            current_points = dict(zip(event_keys, state_key))

            for ev, cost, feed_gain, item_gain in OPTIONS:
                if cost > current_points[ev]:
                    continue

                new_points = current_points.copy()
                new_points[ev] -= cost
                new_key = tuple(new_points[k] for k in event_keys)

                new_feed = feed_now + feed_gain
                new_item = item_now + item_gain
                new_hist = hist_now + [(ev, cost, feed_gain, item_gain)]

                old = dp[i + 1][new_key]
                if new_feed > old["feed"] or new_item > old["item"]:
                    dp[i + 1][new_key] = {
                        "feed": new_feed,
                        "item": new_item,
                        "history": new_hist
                    }

    results = []
    for i in range(N + 1):
        for st in dp[i].values():
            results.append((st["feed"], st["item"], conv(st["history"])))

    best = max(results, key=lambda x: x[0] + x[1] * 100)
    return best


# ============================================================
# ② 枝刈り強化版 DP（完全一致）
# ============================================================
def dp_pruned(points, N):
    OPTIONS = []
    STAGE_MAP = {}

    for key, ev in EVENT_DATA.items():
        for stage, cost in enumerate(ev["costs"], start=1):
            feed = ev["feed"][stage - 1]
            item = ev["item"][stage - 1]
            OPTIONS.append((key, cost, feed, item))
            STAGE_MAP[cost] = stage

    def conv(hist):
        out = []
        for ev, cost, feed, item in hist:
            out.append((ev, STAGE_MAP[cost], cost, feed, item))
        return out

    event_keys = list(EVENT_DATA.keys())
    dp = [defaultdict(lambda: {"feed": -1, "item": -1, "history": []})
          for _ in range(N + 1)]

    start_key = tuple(points[k] for k in event_keys)
    dp[0][start_key] = {"feed": 0, "item": 0, "history": []}

    for i in range(N):
        for state_key, state in dp[i].items():
            feed_now = state["feed"]
            item_now = state["item"]
            hist_now = state["history"]

            current_points = dict(zip(event_keys, state_key))

            for ev, cost, feed_gain, item_gain in OPTIONS:
                if cost > current_points[ev]:
                    continue

                new_points = current_points.copy()
                new_points[ev] -= cost
                new_key = tuple(new_points[k] for k in event_keys)

                new_feed = feed_now + feed_gain
                new_item = item_now + item_gain
                new_hist = hist_now + [(ev, cost, feed_gain, item_gain)]

                old = dp[i + 1][new_key]

                # 枝刈り
                if new_feed <= old["feed"] and new_item <= old["item"]:
                    continue

                dp[i + 1][new_key] = {
                    "feed": new_feed,
                    "item": new_item,
                    "history": new_hist
                }

    results = []
    for i in range(N + 1):
        for st in dp[i].values():
            results.append((st["feed"], st["item"], conv(st["history"])))

    best = max(results, key=lambda x: x[0] + x[1] * 100)
    return best


# ============================================================
# ③ 完全一致版 段階縮約DP（高速）
# ============================================================
def dp_fast(points, N):
    # DP状態: (feed, item, remaining_points, history)
    dp = [[] for _ in range(N + 1)]
    dp[0] = [(0, 0, deepcopy(points), [])]

    for i in range(N):
        next_states = []

        for feed_now, item_now, rem_now, hist_now in dp[i]:
            for stage in range(1, 5):
                feed_gain = FEED[stage - 1]
                item_gain = ITEM[stage - 1]

                for ev, cost in [(e, EVENT_DATA[e]["costs"][stage - 1]) for e in EVENT_KEYS]:
                    if rem_now[ev] < cost:
                        continue

                    new_rem = rem_now.copy()
                    new_rem[ev] -= cost

                    new_feed = feed_now + feed_gain
                    new_item = item_now + item_gain
                    new_hist = hist_now + [(ev, stage, cost, feed_gain, item_gain)]

                    next_states.append((new_feed, new_item, new_rem, new_hist))

        # 枝刈り
        pruned = []
        next_states.sort(key=lambda x: (x[0], x[1]), reverse=True)

        for f, it, rem, h in next_states:
            dominated = False
            for pf, pit, _, _ in pruned:
                if pf >= f and pit >= it:
                    dominated = True
                    break
            if not dominated:
                pruned.append((f, it, rem, h))

        dp[i + 1] = pruned

    results = []
    for states in dp:
        for f, it, rem, h in states:
            results.append((f, it, h))

    best = max(results, key=lambda x: x[0] + x[1] * 100)
    return best


# ============================================================
# Streamlit UI
# ============================================================
st.title("🐷 DP 性能比較ツール（オリジナル / 枝刈り / 段階縮約）")

points = {}
for key, ev in EVENT_DATA.items():
    points[key] = st.number_input(f"{ev['name']}ポイント", min_value=0, value=0, step=100)

count = st.number_input("残り育成回数（最大10）", min_value=1, max_value=10, value=5)

if st.button("比較実行"):
    st.write("### 🚀 実行中…")

    # ① オリジナル
    t0 = time.perf_counter()
    o_feed, o_item, o_hist = dp_original(points, count)
    t1 = time.perf_counter()

    # ② 枝刈り
    t2 = time.perf_counter()
    p_feed, p_item, p_hist = dp_pruned(points, count)
    t3 = time.perf_counter()

    # ③ 段階縮約
    t4 = time.perf_counter()
    f_feed, f_item, f_hist = dp_fast(points, count)
    t5 = time.perf_counter()

    # 結果表示
    st.subheader("① オリジナル版")
    st.write(f"餌:{o_feed} / アイテム:{o_item} / 時間:{(t1-t0)*1000:.2f}ms")
    st.write(o_hist)

    st.subheader("② 枝刈り版")
    st.write(f"餌:{p_feed} / アイテム:{p_item} / 時間:{(t3-t2)*1000:.2f}ms")
    st.write(p_hist)

    st.subheader("③ 段階縮約DP（高速）")
    st.write(f"餌:{f_feed} / アイテム:{f_item} / 時間:{(t5-t4)*1000:.2f}ms")
    st.write(f_hist)

    # 一致チェック
    st.subheader("🔍 一致チェック")

    def eq(a, b):
        return a == b

    st.write(f"オリジナル vs 枝刈り → {'OK' if eq((o_feed,o_item,o_hist),(p_feed,p_item,p_hist)) else 'NG'}")
    st.write(f"オリジナル vs 段階縮約 → {'OK' if eq((o_feed,o_item,o_hist),(f_feed,f_item,f_hist)) else 'NG'}")
