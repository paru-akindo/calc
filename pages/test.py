# main.py
import streamlit as st
import requests
import json
import re
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="効率よく買い物しよう！", layout="wide")

# --------------------
# --- 定数（フォールバック用）
# --------------------
PORTS = ["博多","開京","明州","泉州","広州","淡水","安南","ボニ","タイ","真臘","スル","三仏斉","ジョホール","大光国","天竺","セイロン","ペルシャ","大食国","ミスル","末羅国"]

ITEMS = [
    ("鳳梨",100),("魚肉",100),("酒",100),("水稲",100),("木材",100),("ヤシ",100),
    ("海鮮",200),("絹糸",200),("水晶",200),("茶葉",200),("鉄鉱",200),
    ("香料",300),("玉器",300),("白銀",300),("皮革",300),
    ("真珠",500),("燕の巣",500),("陶器",500),
    ("象牙",1000),("鹿茸",1000)
]

MODIFIERS_PERCENT = [
    # 必要なら元の配列をここに入れてください（移行フォールバック用）
]

# --------------------
# --- jsonbin 設定（必要なら差し替え）
# --------------------
JSONBIN_API_KEY = "$2a$10$wkVzPCcsW64wR96r26OsI.HDd3ijLveJn6sxJoSjfzByIRyODPCHq"
JSONBIN_BIN_ID = "68e8924443b1c97be9611391"
JSONBIN_BASE = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
JSONBIN_HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# --------------------
# --- ユーティリティ関数
# --------------------
def safe_rerun():
    try:
        rerun_fn = getattr(st, "experimental_rerun")
        rerun_fn()
    except Exception:
        return

def fetch_cfg_from_jsonbin():
    try:
        resp = requests.get(f"{JSONBIN_BASE}/latest", headers=JSONBIN_HEADERS, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and "record" in payload:
            return payload["record"]
        return payload
    except Exception:
        return None

def save_cfg_to_jsonbin(cfg: dict):
    resp = requests.put(JSONBIN_BASE, headers=JSONBIN_HEADERS, data=json.dumps(cfg, ensure_ascii=False))
    resp.raise_for_status()
    return resp

def normalize_items(raw_items) -> List[Tuple[str,int]]:
    out = []
    for it in raw_items:
        if isinstance(it, (list, tuple)):
            name, base = it[0], int(it[1])
        elif isinstance(it, dict):
            name, base = it["name"], int(it["base"])
        else:
            raise ValueError("Unknown item format")
        out.append((name, base))
    return out

def port_has_actual_prices_by_diff(port_prices: dict, items: List[Tuple[str,int]], tol: int = 0) -> bool:
    # 欠損や非数値は未入力と見なす
    for name, base in items:
        if name not in port_prices:
            return False
        v = port_prices[name]
        if not isinstance(v, (int, float)):
            return False
    # 1つでも base と違えば実入力ありと判定
    for name, base in items:
        p = port_prices.get(name)
        if abs(int(round(p)) - int(base)) > tol:
            return True
    return False

# 数値入力ウィジェット（空欄許容・厳格整数）
def numeric_input_optional_strict(label: str, key: str, placeholder: str = "", allow_commas: bool = True, min_value: int = None, max_value: int = None):
    invalid_flag = f"{key}_invalid"
    if invalid_flag not in st.session_state:
        st.session_state[invalid_flag] = False

    raw = st.text_input(label, value="", placeholder=placeholder, key=key)

    js = f"""
    <script>
    try {{
      const labels = Array.from(document.querySelectorAll('label'));
      const el = labels.find(l => l.innerText && l.innerText.trim().startsWith("{label.replace('"','\\"')}"));
      if (el) {{
        const input = el.parentElement.querySelector('input');
        if (input) {{
          input.setAttribute('inputmode','numeric');
          input.setAttribute('pattern','[0-9,]*');
        }}
      }}
    }} catch(e){{}}
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

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
        st.error(f"「{label}」の数値変換でエラーが発生しました。入力: {raw}")
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

# 価格行列を PRICES (port->item) から item->port に変換
def build_price_matrix_from_prices(prices_cfg: Dict[str, Dict[str,int]], items=ITEMS, ports=PORTS):
    price = {name: {} for name, _ in items}
    for port in ports:
        port_row = prices_cfg.get(port, {})
        for name, _ in items:
            price[name][port] = int(port_row.get(name, 0))
    return price

# 貪欲プランニング（既存ロジック）
def greedy_plan_for_destination(current_port: str, dest_port: str, cash: int, stock: Dict[str,int], price_matrix: Dict[str,Dict[str,int]]):
    candidates = []
    for item, base in ITEMS:
        avail = stock.get(item, 0)
        if avail <= 0:
            continue
        buy = price_matrix[item][current_port]
        sell = price_matrix[item][dest_port]
        unit_profit = sell - buy
        if unit_profit <= 0:
            continue
        candidates.append((item, buy, sell, unit_profit, avail))
    candidates.sort(key=lambda x: x[3], reverse=True)
    remaining_cash = cash
    plan = []
    for item, buy, sell, unit_profit, avail in candidates:
        max_by_cash = remaining_cash // buy if buy > 0 else 0
        qty = min(avail, max_by_cash)
        if qty <= 0:
            continue
        plan.append((item, qty, buy, sell, unit_profit))
        remaining_cash -= qty * buy
        if remaining_cash <= 0:
            break
    total_cost = sum(q * b for _, q, b, _, _ in plan)
    total_profit = sum(q * up for _, q, _, _, up in plan)
    return plan, total_cost, total_profit

# --------------------
# --- アプリ本体
# --------------------
st.title("効率よく買い物しよう！ / 管理")

# 1) jsonbin からCFG取得（失敗したら組み込み定義を使用）
cfg = fetch_cfg_from_jsonbin()
if cfg is None:
    st.warning("jsonbin から読み込みできませんでした。埋め込み定義を使用します。")
    cfg = {"PORTS": PORTS, "ITEMS": [list(i) for i in ITEMS]}

PORTS_CFG = cfg.get("PORTS", PORTS)
ITEMS_CFG = normalize_items(cfg.get("ITEMS", [list(i) for i in ITEMS]))
PRICES_CFG = cfg.get("PRICES", {})

# 2) 全港が実値入力済みか判定
tol = st.sidebar.number_input("判定許容差 tol (0=完全一致を未入力扱い)", min_value=0, value=0, step=1)
all_populated = True
missing_ports = []
for port in PORTS_CFG:
    port_prices = PRICES_CFG.get(port, {})
    if not port_has_actual_prices_by_diff(port_prices, ITEMS_CFG, tol=tol):
        all_populated = False
        missing_ports.append(port)

if all_populated:
    # --- 全港実値あり: シミュレーション画面を表示（PRICES を直接利用）
    st.success("全ての港に実価格が入力されています。シミュレーション画面を表示します。")

    price_matrix = build_price_matrix_from_prices(PRICES_CFG, items=ITEMS_CFG, ports=PORTS_CFG)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("効率よく買い物しよう！（実価格ベース）")

        current_port = st.selectbox("現在港", PORTS_CFG, index=0)
        cash = numeric_input_optional_strict("所持金", key="cash_input", placeholder="例: 5000", allow_commas=True, min_value=0)

        # 割安判定は「他港平均より安い」差分を利用
        item_diffs = []
        for i, (item_name, base) in enumerate(ITEMS_CFG):
            prices_for_item = [price_matrix[item_name][p] for p in PORTS_CFG]
            avg_price = sum(prices_for_item) / len(prices_for_item) if prices_for_item else base
            this_price = price_matrix[item_name][current_port]
            diff = avg_price - this_price
