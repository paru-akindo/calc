# main_routes_only.py
import streamlit as st
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import re
import requests
from io import StringIO
from copy import deepcopy
from math import prod

st.set_page_config(page_title="ルート解析（簡易表示）", layout="wide")

# --------------------
# 設定: ITEMS はスプレッドシートの品目列ヘッダと一致させること
# --------------------
ITEMS = [
    ("鳳梨",100),("魚肉",100),("酒",100),("水稲",100),("木材",100),("ヤシ",100),
    ("海鮮",200),("絹糸",200),("水晶",200),("茶葉",200),("鉄鉱",200),
    ("香料",300),("玉器",300),("白銀",300),("皮革",300),
    ("真珠",500),("燕の巣",500),("陶器",500),
    ("象牙",1000),("鹿茸",1000)
]

# --------------------
# スプレッドシート設定（公開CSV）
# --------------------
SPREADSHEET_ID = "1ft5FlwM5kaZK7B4vLQg2m1WYe5nWNb0udw5isFwDWy0"
GID = "0"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={GID}"

# --------------------
# ヘルパー: 厳格整数テキスト入力（再利用のため残すが UI では使わない）
# --------------------
def numeric_input_optional_strict(label: str, key: str, placeholder: str = "", allow_commas: bool = True, min_value: Optional[int] = None, max_value: Optional[int] = None):
    invalid_flag = f"{key}_invalid"
    if invalid_flag not in st.session_state:
        st.session_state[invalid_flag] = False

    raw = st.text_input(label, value="", placeholder=placeholder, key=key)

    s = (raw or "").strip()
    if s == "":
        st.session_state[invalid_flag] = False
        return None

    if allow_commas:
        s = s.replace(",", "")
    s = s.translate(str.maketrans("０１２３４５６７８９－＋．，", "0123456789-+.,"))
    if not re.fullmatch(r"\d+", s):
        st.error(f"「{label}」は整数の半角数字のみで入力してください。入力値: {raw}")
        st.session_state[invalid_flag] = True
        return None

    try:
        val = int(s)
    except Exception:
        st.error(f"「{label}」の数値変換に失敗しました。入力: {raw}")
        st.session_state[invalid_flag] = True
        return None

    if min_value is not None and val < min_value:
        st.error(f"「{label}」は {min_value} 以上で入力してください。")
        st.session_state[invalid_flag] = True
        return None
    if max_value is not None and val > max_value:
        st.error(f"「{label}」は {max_value} 以下で入力してください。")
        st.session_state[invalid_flag] = True
        return None

    st.session_state[invalid_flag] = False
    return val

# --------------------
# CSV 取得: 行=港 or 行=品目 を自動判定して price_matrix を作る
# --------------------
@st.cache_data(ttl=60)
def fetch_price_matrix_from_csv_auto(url: str):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    s = r.content.decode("utf-8")
    df = pd.read_csv(StringIO(s))

    if df.shape[1] < 2:
        raise ValueError("スプレッドシートに品目列/港列が見つかりません。")

    items_names = [name for name, _ in ITEMS]
    first_col_name = df.columns[0]
    first_col_values = df[first_col_name].astype(str).tolist()

    any_first_col_is_item = any(v in items_names for v in first_col_values)
    if any_first_col_is_item:
        # 行=品目, 列=港 の形式 -> 転置して行=港に合わせる
        df_items = df.set_index(df.columns[0])
        df_t = df_items.transpose().reset_index()
        port_col = df_t.columns[0]
        ports = df_t[port_col].astype(str).tolist()
        price_matrix = {name: {} for name, _ in ITEMS}
        for name, _ in ITEMS:
            if name in df_t.columns:
                for idx, p in enumerate(ports):
                    raw = df_t.at[idx, name]
                    try:
                        price_matrix[name][p] = int(raw)
                    except Exception:
                        price_matrix[name][p] = 0
            else:
                for p in ports:
                    price_matrix[name][p] = 0
        return ports, price_matrix
    else:
        # 行=港, 列=品目 の形式
        port_col = df.columns[0]
        ports = df[port_col].astype(str).tolist()
        price_matrix = {name: {} for name, _ in ITEMS}
        for name, _ in ITEMS:
            if name in df.columns:
                for idx, p in enumerate(ports):
                    raw = df.at[idx, name]
                    try:
                        price_matrix[name][p] = int(raw)
                    except Exception:
                        price_matrix[name][p] = 0
            else:
                for p in ports:
                    price_matrix[name][p] = 0
        return ports, price_matrix

# --------------------
# 既存の解析ロジック（そのまま利用）
# --------------------
def greedy_plan_for_destination_general(current_port: str, dest_port: str, cash: int, stock: Optional[Dict[str,int]], price_matrix: Dict[str,Dict[str,int]]):
    cash = int(cash) if cash is not None else 0
    candidates = []
    for item, base in ITEMS:
        avail = float('inf') if stock is None else stock.get(item, 0)
        if avail <= 0:
            continue
        buy = price_matrix[item].get(current_port, 0)
        sell = price_matrix[item].get(dest_port, 0)
        unit_profit = sell - buy
        if unit_profit <= 0 or buy <= 0:
            continue
        candidates.append((item, buy, sell, unit_profit, avail))
    candidates.sort(key=lambda x: x[3], reverse=True)

    remaining_cash = cash
    plan = []
    for item, buy, sell, unit_profit, avail in candidates:
        if buy <= 0:
            continue
        max_by_cash = remaining_cash // buy if remaining_cash >= buy else 0
        qty = min(avail if avail != float('inf') else max_by_cash, max_by_cash)
        if qty <= 0:
            continue
        plan.append((item, int(qty), int(buy), int(sell), int(unit_profit)))
        remaining_cash -= qty * buy
        if remaining_cash <= 0:
            break

    total_cost = sum(q * b for _, q, b, _, _ in plan)
    total_profit = sum(q * up for _, q, _, _, up in plan)
    remaining_cash_after_sell = cash + total_profit
    return plan, int(total_cost), int(total_profit), int(remaining_cash_after_sell)

def evaluate_with_lookahead(current_port: str, dest_port: str, cash: int, stock: Dict[str,int], price_matrix: Dict[str,Dict[str,int]], second_k: Optional[int] = None):
    first_plan, first_cost, first_profit, cash_after_sell = greedy_plan_for_destination_general(current_port, dest_port, cash, stock, price_matrix)

    example_item = next(iter(price_matrix))
    ports_list = list(price_matrix[example_item].keys())
    second_candidates = [p for p in ports_list if p != dest_port]

    if second_k is not None and second_k < len(second_candidates):
        scores = []
        for s in second_candidates:
            score = 0
            for item, _ in ITEMS:
                buy = price_matrix[item].get(dest_port, 0)
                sell = price_matrix[item].get(s, 0)
                if buy > 0:
                    unit = sell - buy
                    if unit > 0:
                        score += unit
            scores.append((s, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        second_candidates = [s for s,_ in scores[:second_k]]

    best_second_profit = 0
    best_second_plan = []
    best_second_dest = None
    for s in second_candidates:
        plan2, cost2, profit2, cash_after2 = greedy_plan_for_destination_general(dest_port, s, cash_after_sell, None, price_matrix)
        if profit2 > best_second_profit:
            best_second_profit = profit2
            best_second_plan = plan2
            best_second_dest = s

    total_profit = first_profit + best_second_profit
    return {
        "total_profit": int(total_profit),
        "first_profit": int(first_profit),
        "second_best_profit": int(best_second_profit),
        "first_plan": first_plan,
        "second_plan": best_second_plan,
        "second_dest": best_second_dest,
        "cash_after_first_sell": int(cash_after_sell)
    }

def greedy_one_item_for_destination(current_port: str, dest_port: str, cash: int, price_matrix: Dict[str,Dict[str,int]]):
    cash = int(max(1, cash))
    best_item = None
    best_rate = -1.0
    best_buy = 0
    best_sell = 0

    for item, _ in ITEMS:
        buy = price_matrix[item].get(current_port, 0)
        sell = price_matrix[item].get(dest_port, 0)
        if buy <= 0:
            continue
        unit_profit = sell - buy
        if unit_profit <= 0:
            continue
        rate = unit_profit / float(buy)
        if rate > best_rate:
            best_rate = rate
            best_item = item
            best_buy = buy
            best_sell = sell

    if best_item is None:
        return None, 0, 0, 0, 0, cash

    qty = cash // best_buy if best_buy > 0 else 0
    if qty <= 0:
        return best_item, best_buy, best_sell, 0, 0, cash

    step_profit = qty * (best_sell - best_buy)
    cash_after = cash + step_profit
    return best_item, best_buy, best_sell, int(qty), int(step_profit), int(cash_after)

def compute_single_step_multipliers_oneitem(price_matrix: Dict[str,Dict[str,int]], from_ports: List[str], to_ports: List[str], cash: int):
    mapping = {}
    candidates = []
    for p in from_ports:
        mapping.setdefault(p, {})
        for q in to_ports:
            if p == q:
                continue
            item, buy, sell, qty, profit, cash_after = greedy_one_item_for_destination(p, q, cash, price_matrix)
            multiplier = float(cash_after) / float(max(1, cash))
            mapping[p][q] = {
                'multiplier': multiplier,
                'chosen_item': item,
                'cash_after': cash_after,
            }
            candidates.append((p, q, multiplier))
    candidates.sort(key=lambda x: x[2], reverse=True)
    return mapping, candidates

def build_greedy_cycles_from_start(start_port: str, mapping: Dict, cash: int, allowed_ports: Optional[set] = None, max_iters: int = 2000, max_route_len: int = 200):
    route_nodes = [start_port]
    steps = []
    iters = 0

    while True:
        iters += 1
        if iters > max_iters:
            break

        cur = route_nodes[-1]
        next_candidates_all = mapping.get(cur, {})
        if allowed_ports is not None:
            next_candidates = {q:info for q, info in next_candidates_all.items() if q in allowed_ports or q == start_port}
        else:
            next_candidates = next_candidates_all

        if not next_candidates:
            break

        q, info = max(next_candidates.items(), key=lambda kv: kv[1]['multiplier'])

        steps.append({
            'from': cur,
            'to': q,
            'multiplier': info.get('multiplier'),
            'chosen_item': info.get('chosen_item'),
        })
        route_nodes.append(q)

        first_idx = None
        for idx, node in enumerate(route_nodes[:-1]):
            if node == q:
                first_idx = idx
                break
        if first_idx is not None:
            route = route_nodes[first_idx:]
            cycle_len = len(route) - 1
            cycle_steps = steps[-cycle_len:] if cycle_len > 0 else []
            multipliers = [s['multiplier'] for s in cycle_steps]
            total_mul = prod(multipliers) if multipliers else 1.0
            avg_mul = total_mul ** (1.0 / len(multipliers)) if multipliers else 1.0
            last_step_cash = None
            if cycle_steps:
                last_from = cycle_steps[-1]['from']
                last_to = cycle_steps[-1]['to']
                info_last = mapping.get(last_from, {}).get(last_to, {})
                last_step_cash = info_last.get('cash_after')
            final_cash = int(last_step_cash) if last_step_cash is not None else None
            return route, cycle_steps, final_cash, avg_mul, total_mul

        if len(route_nodes) > max(1, len(mapping) + 5) or len(route_nodes) > max_route_len:
            break

    return None, None, None, None, None

def generate_routes_greedy_cover_with_recalc(ports: List[str], price_matrix: Dict, cash: int, top_k_start: int = 1):
    results_per_start = []

    mapping_full, singles = compute_single_step_multipliers_oneitem(price_matrix, ports, ports, cash)

    singles_sorted = sorted(singles, key=lambda x: x[2], reverse=True)
    start_ports_order = []
    for p, q, m in singles_sorted:
        if p not in start_ports_order:
            start_ports_order.append(p)

    for initial_start_choice in start_ports_order[:top_k_start]:
        remaining_ports = set(ports)
        routes = []
        current_start = initial_start_choice

        while True:
            allowed_for_calc = set(remaining_ports) | {current_start}
            mapping, _ = compute_single_step_multipliers_oneitem(price_matrix, list(allowed_for_calc), list(allowed_for_calc), cash)

            route, steps, final_cash, avg_mul, total_mul = build_greedy_cycles_from_start(current_start, mapping, cash, allowed_ports=allowed_for_calc)
            if route is None:
                break

            covered = set(route)
            routes.append({'route': route, 'steps': steps, 'avg_mul': avg_mul, 'total_mul': total_mul, 'covered': covered})

            remaining_ports -= covered

            if not remaining_ports:
                break

            mapping_remain, singles_remain = compute_single_step_multipliers_oneitem(price_matrix, list(remaining_ports), list(remaining_ports), cash)
            next_start = None
            best_m = -1.0
            for p in mapping_remain:
                outs = mapping_remain.get(p, {})
                if not outs:
                    continue
                q, info = max(outs.items(), key=lambda kv: kv[1]['multiplier'])
                if info['multiplier'] > best_m:
                    best_m = info['multiplier']
                    next_start = p

            if next_start is None:
                break

            current_start = next_start

        results_per_start.append({'initial_start': initial_start_choice, 'routes': routes, 'remaining_ports': remaining_ports})

    return results_per_start

# --------------------
# メイン: CSV取得と「各港から一手で最適な行き先」「ルート解析」表示のみ
# --------------------
st.markdown("# 各港から一手で最適な行き先 と ルート解析")
st.markdown(f'<div style="margin-top:6px;"><a href="{SPREADSHEET_URL}" target="_blank" rel="noopener noreferrer">スプレッドシートを開く（編集・表示）</a></div>', unsafe_allow_html=True)

# 価格取得
try:
    ports, price_matrix = fetch_price_matrix_from_csv_auto(CSV_URL)
except Exception as e:
    st.error(f"スプレッドシート（CSV）からの読み込みに失敗しました: {e}")
    st.stop()

# 単一遷移プレビュー（内部計算）
CASH_DEFAULT = 50000
mapping_preview, candidates_preview = compute_single_step_multipliers_oneitem(price_matrix, ports, ports, CASH_DEFAULT)

# --------------------
# 表示: 各港から一手で最適な行き先
# --------------------
st.subheader("各港から一手で最適な行き先（乗数・買う物）")
rows = []
for p in ports:
    outs = mapping_preview.get(p, {})
    if not outs:
        rows.append({"出発港": p, "最適到着": "-", "乗数": "-", "買う物": "-"})
        continue
    best_q, info = max(outs.items(), key=lambda kv: kv[1]['multiplier'])
    items_summary = f"{info.get('chosen_item') or '-'}"
    multiplier = info.get('multiplier', 1.0)
    rows.append({"出発港": p, "最適到着": best_q, "乗数": f"{multiplier:.2f}", "買う物": items_summary})

df_preview = pd.DataFrame(rows)
st.dataframe(df_preview, height=320)

# --------------------
# ルート解析（自動解析）
# --------------------
st.markdown("---")
st.subheader("ルート解析（自動）")

AUTO_TOP_K = 5
CASH_DEFAULT = 50000

# 単一遷移の候補を並べて開始候補順を作る
mapping_preview, candidates_preview = compute_single_step_multipliers_oneitem(price_matrix, ports, ports, CASH_DEFAULT)
singles_sorted = sorted(candidates_preview, key=lambda x: x[2], reverse=True)
start_ports_order = []
for p, q, m in singles_sorted:
    if p not in start_ports_order:
        start_ports_order.append(p)

start_ports_try = start_ports_order[:AUTO_TOP_K]

with st.spinner("自動解析（複数開始候補）実行中..."):
    all_results = generate_routes_greedy_cover_with_recalc(ports, price_matrix, CASH_DEFAULT, top_k_start=len(start_ports_try))
    kept_results = [r for r in all_results if r['initial_start'] in start_ports_try]

# 集計と表示
for res in kept_results:
    start = res['initial_start']
    st.markdown(f"### 開始港: {start}")
    routes = res.get('routes', [])
    if not routes:
        st.write("解析結果なし")
        continue

    # ルートごとに表示
    for idx, route_info in enumerate(routes, start=1):
        route = route_info.get('route', [])
        avg_mul = route_info.get('avg_mul', 0.0)
        total_mul = route_info.get('total_mul', 0.0)
        st.markdown(f"- ルート {idx}: {' → '.join(route)}")
        st.markdown(f"  - 平均乗数（ルート内）: {avg_mul:.3f}  合計乗数: {total_mul:.3f}")
    st.write("---")

st.markdown("※ 表示は一手最適化（単一品目近似）に基づく推定です。実際の運用では在庫・積載・時間等の制約を考慮してください。")
