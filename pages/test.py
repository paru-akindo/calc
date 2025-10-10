# main.py
import streamlit as st
import requests
import json
import re
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

st.set_page_config(page_title="効率よく買い物しよう！", layout="wide")

# --------------------
# 定数
# --------------------
PORTS = ["博多","開京","明州","泉州","広州","淡水","安南","ボニ","タイ","真臘","スル","三仏斉","ジョホール","大光国","天竺","セイロン","ペルシャ","大食国","ミスル","末羅国"]

ITEMS = [
    ("鳳梨",100),("魚肉",100),("酒",100),("水稲",100),("木材",100),("ヤシ",100),
    ("海鮮",200),("絹糸",200),("水晶",200),("茶葉",200),("鉄鉱",200),
    ("香料",300),("玉器",300),("白銀",300),("皮革",300),
    ("真珠",500),("燕の巣",500),("陶器",500),
    ("象牙",1000),("鹿茸",1000)
]

# --------------------
# jsonbin 設定（必要なら置き換えてください）
# --------------------
JSONBIN_API_KEY = "$2a$10$wkVzPCcsW64wR96r26OsI.HDd3ijLveJn6sxJoSjfzByIRyODPCHq"
JSONBIN_BIN_ID = "68e8924443b1c97be9611391"
JSONBIN_BASE = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
JSONBIN_HEADERS = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}

# --------------------
# ヘルパー関数
# --------------------
def safe_rerun():
    try:
        getattr(st, "experimental_rerun")()
    except Exception:
        return

def fetch_cfg_from_jsonbin():
    try:
        r = requests.get(f"{JSONBIN_BASE}/latest", headers=JSONBIN_HEADERS, timeout=8)
        r.raise_for_status()
        payload = r.json()
        return payload.get("record", payload)
    except Exception:
        return None

def save_cfg_to_jsonbin(cfg: dict):
    r = requests.put(JSONBIN_BASE, headers=JSONBIN_HEADERS, data=json.dumps(cfg, ensure_ascii=False))
    r.raise_for_status()
    return r

def normalize_items(raw_items) -> List[Tuple[str,int]]:
    out = []
    for it in raw_items:
        if isinstance(it, (list, tuple)):
            out.append((it[0], int(it[1])))
        elif isinstance(it, dict):
            out.append((it["name"], int(it["base"])))
        else:
            raise ValueError("Unknown item format")
    return out

def port_has_actual_prices(port_prices: dict, items: List[Tuple[str,int]]) -> bool:
    for name, _ in items:
        if name not in port_prices or not isinstance(port_prices[name], (int, float)):
            return False
    for name, base in items:
        if int(round(port_prices.get(name))) != int(base):
            return True
    return False

def numeric_input_optional_strict(label: str, key: str, placeholder: str = "", allow_commas: bool = True, min_value: int = None):
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

    val = int(s)
    if min_value is not None and val < min_value:
        st.error(f"「{label}」は {min_value} 以上で入力してください。")
        st.session_state[invalid_flag] = True
        return None

    st.session_state[invalid_flag] = False
    return val

def build_price_matrix_from_prices(prices_cfg: Dict[str, Dict[str,int]], items=ITEMS, ports=PORTS):
    price = {name: {} for name, _ in items}
    for port in ports:
        port_row = prices_cfg.get(port, {})
        for name, _ in items:
            price[name][port] = int(port_row.get(name, 0))
    return price

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
# アプリ本体（最初の合成版を簡潔に整理）
# --------------------
st.title("効率よく買い物しよう！ / 管理（色付きテーブル）")

# 1) JSON を取得（未取得なら組み込み定義）
cfg = fetch_cfg_from_jsonbin()
if cfg is None:
    st.warning("jsonbin から読み込みできませんでした。組み込み定義を使用します。")
    cfg = {"PORTS": PORTS, "ITEMS": [list(i) for i in ITEMS]}

PORTS_CFG = cfg.get("PORTS", PORTS)
ITEMS_CFG = normalize_items(cfg.get("ITEMS", [list(i) for i in ITEMS]))
PRICES_CFG = cfg.get("PRICES", {})

# 2) 全港入力確認（完全一致基準）
all_populated = True
missing_ports = []
for port in PORTS_CFG:
    port_prices = PRICES_CFG.get(port, {})
    if not port_has_actual_prices(port_prices, ITEMS_CFG):
        all_populated = False
        missing_ports.append(port)

# UI: 表示切替チェックボックス（メイン表示領域）
show_price_table = st.checkbox("価格表を表示（実価格）", value=False)
show_correction_table = st.checkbox("補正表を表示（基礎値差）", value=False)

if all_populated:
    st.success("すべての港に実価格が入力されています。シミュレーション画面を表示します。")
    price_matrix = build_price_matrix_from_prices(PRICES_CFG, items=ITEMS_CFG, ports=PORTS_CFG)

    col_left, col_main = st.columns([1, 2])

    with col_left:
        st.header("シミュレーション")
        current_port = st.selectbox("現在港", PORTS_CFG, index=0)
        cash = numeric_input_optional_strict("所持金", key="cash_input", placeholder="例: 5000", allow_commas=True, min_value=0)

        # 在庫入力対象の選定: 価格 / 基礎値 小さい順、同率は価格小さい順
        item_scores = []
        for item_name, base in ITEMS_CFG:
            this_price = price_matrix[item_name][current_port]
            ratio = this_price / float(base) if base != 0 else float('inf')
            item_scores.append((item_name, ratio, this_price))
        item_scores.sort(key=lambda t: (t[1], t[2]))
        top5 = [name for name, _, _ in item_scores][:5]

        st.write("在庫入力（上位5）: 価格 / 基礎値 が小さい順、同率は価格が安い順")
        stock_inputs = {}
        cols = st.columns(2)
        for i, name in enumerate(top5):
            c = cols[i % 2]
            with c:
                stock_inputs[name] = numeric_input_optional_strict(f"{name} 在庫数", key=f"stk_{name}", placeholder="例: 10", allow_commas=True, min_value=0)

        top_k = st.slider("表示上位何港を出すか（上位k）", min_value=1, max_value=10, value=3)

        if st.button("検索"):
            if cash is None:
                st.error("所持金を入力してください（空欄不可）。")
            else:
                invalid_found = False
                for name in stock_inputs.keys():
                    if st.session_state.get(f"stk_{name}_invalid", False):
                        st.error(f"{name} の入力が不正です。")
                        invalid_found = True
                if invalid_found:
                    st.error("不正入力があるため中止します。")
                else:
                    current_stock = {n: 0 for n, _ in ITEMS_CFG}
                    for name in stock_inputs:
                        val = stock_inputs.get(name)
                        current_stock[name] = int(val) if val is not None else 0

                    results = []
                    for dest in PORTS_CFG:
                        if dest == current_port:
                            continue
                        plan, cost, profit = greedy_plan_for_destination(current_port, dest, cash, current_stock, price_matrix)
                        results.append((dest, plan, cost, profit))
                    results.sort(key=lambda x: x[3], reverse=True)
                    top_results = results[:top_k]

                    if not top_results or all(r[3] <= 0 for r in top_results):
                        st.info("利益の見込める到着先は見つかりませんでした。")
                    else:
                        for rank, (dest, plan, cost, profit) in enumerate(top_results, start=1):
                            st.markdown(f"### {rank}. 到着先: {dest}　想定合計利益: {profit}　合計購入金額: {cost}")
                            if not plan:
                                st.write("購入候補がありません。")
                                continue
                            df = pd.DataFrame([{
                                "品目": item,
                                "購入数": qty,
                                "購入単価": buy,
                                "売価": sell,
                                "単位差益": unit_profit,
                                "想定利益": qty * unit_profit
                            } for item, qty, buy, sell, unit_profit in plan])
                            totals = {"品目":"合計", "購入数": int(df["購入数"].sum()) if not df.empty else 0, "購入単価": np.nan, "売価": np.nan, "単位差益": np.nan, "想定利益": int(df["想定利益"].sum()) if not df.empty else 0}
                            df_disp = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
                            num_format = {"購入単価":"{:,.0f}", "売価":"{:,.0f}", "単位差益":"{:,.0f}", "購入数":"{:,.0f}", "想定利益":"{:,.0f}"}
                            styled = df_disp.style.format(num_format, na_rep="")
                            st.dataframe(styled, height=240)

    # テーブル表示（色付きグラデーション）
    with col_main:
        st.header("テーブル表示")

        # 実価格表
        if show_price_table:
            rows = []
            for item, base in ITEMS_CFG:
                row = {"品目": item}
                for p in PORTS_CFG:
                    row[p] = price_matrix[item][p]
                rows.append(row)
            df_price = pd.DataFrame(rows).set_index("品目")

            def price_cell_css(price_val, base):
                try:
                    price_int = int(price_val)
                except Exception:
                    return ""
                pct = (price_int - base) / float(base) * 100 if base != 0 else 0.0
                if pct > 20:
                    pct = 20
                if pct < -20:
                    pct = -20
                if pct >= 0:
                    t = pct / 20.0
                    r = int(255 * (0.9 * t + 0.1))
                    g = int(255 * (1 - 0.8 * t))
                    b = int(255 * (1 - 0.9 * t))
                else:
                    t = (-pct) / 20.0
                    r = int(255 * (1 - 0.9 * t))
                    g = int(255 * (0.9 * t + 0.1))
                    b = int(255 * (1 - 0.9 * t))
                text_color = "#000" if (r + g + b) > 380 else "#fff"
                return f"background-color: rgb({r},{g},{b}); color: {text_color}"

            def price_styler(df):
                sty = pd.DataFrame("", index=df.index, columns=df.columns)
                base_map = dict(ITEMS_CFG)
                for item in df.index:
                    base = base_map[item]
                    for col in df.columns:
                        sty.at[item, col] = price_cell_css(df.at[item, col], base)
                return sty

            st.subheader("実価格表")
            styled_price = df_price.style.apply(lambda _: price_styler(df_price), axis=None)
            st.dataframe(styled_price, height=380)

        # 補正表（基礎値差を数値表示、%なし）
        if show_correction_table:
            rows = []
            for item, base in ITEMS_CFG:
                row = {"品目": item}
                for p in PORTS_CFG:
                    price = price_matrix[item][p]
                    pct = int(round((price - base) / float(base) * 100)) if base != 0 else 0
                    row[p] = pct  # 表示は数値（例 -7, 10）
                rows.append(row)
            df_corr = pd.DataFrame(rows).set_index("品目")

            def corr_cell_css(pct_val):
                try:
                    v = int(pct_val)
                except Exception:
                    return ""
                if v > 20:
                    v = 20
                if v < -20:
                    v = -20
                if v >= 0:
                    t = v / 20.0
                    r = int(255 * (0.9 * t + 0.1))
                    g = int(255 * (1 - 0.8 * t))
                    b = int(255 * (1 - 0.9 * t))
                else:
                    t = (-v) / 20.0
                    r = int(255 * (1 - 0.9 * t))
                    g = int(255 * (0.9 * t + 0.1))
                    b = int(255 * (1 - 0.9 * t))
                text_color = "#000" if (r + g + b) > 380 else "#fff"
                return f"background-color: rgb({r},{g},{b}); color: {text_color}"

            def corr_styler(df):
                sty = pd.DataFrame("", index=df.index, columns=df.columns)
                for item in df.index:
                    for col in df.columns:
                        sty.at[item, col] = corr_cell_css(df.at[item, col])
                return sty

            st.subheader("基礎値100換算 補正（数値表示）")
            styled_corr = df_corr.style.apply(lambda _: corr_styler(df_corr), axis=None)
            styled_corr = styled_corr.format("{:+d}", na_rep="")
            st.dataframe(styled_corr, height=380)

else:
    st.warning("一部の港が未更新です。管理画面で入力してください。")
    st.write("未更新港:", missing_ports)

    if "mode" not in st.session_state:
        st.session_state["mode"] = "view"
    if st.button("管理画面を開く（未更新港を編集）"):
        st.session_state["mode"] = "admin"
        safe_rerun()

    if st.session_state.get("mode") == "admin":
        st.header("管理画面: 未更新港の編集")
        selected_port = st.selectbox("編集する未更新の港を選択", options=missing_ports)
        st.markdown(f"## {selected_port} の価格を入力（整数のみ）")
        current = PRICES_CFG.get(selected_port, {})

        cols = st.columns(2)
        inputs: Dict[str,str] = {}
        for i, (name, base) in enumerate(ITEMS_CFG):
            c = cols[i % 2]
            default = "" if name not in current else str(current[name])
            with c:
                inputs[name] = st.text_input(f"{name} (base: {base})", value=default, key=f"{selected_port}_{name}")

        st.write("---")
        col_ok, col_cancel, col_reload = st.columns([1,1,1])

        with col_ok:
            if st.button("この港の価格を保存"):
                new_row = {}
                invalids = []
                for name, base in ITEMS_CFG:
                    raw = inputs.get(name, "")
                    s = (raw or "").strip().replace(",", "")
                    s = s.translate(str.maketrans("０１２３４５６７８９－＋．，", "0123456789-+.,"))
                    if s == "" or not re.fullmatch(r"\d+", s):
                        invalids.append(name)
                    else:
                        v = int(s)
                        if v < 0:
                            invalids.append(name)
                        else:
                            new_row[name] = v
                if invalids:
                    st.error("不正な入力があります: " + ", ".join(invalids))
                else:
                    PRICES_CFG[selected_port] = new_row
                    cfg["PRICES"] = PRICES_CFG
                    try:
                        resp = save_cfg_to_jsonbin(cfg)
                        st.success(f"{selected_port} を保存しました。HTTP {resp.status_code}")
                        new_cfg = fetch_cfg_from_jsonbin()
                        if new_cfg:
                            cfg = new_cfg
                            PRICES_CFG = cfg.get("PRICES", {})
                            safe_rerun()
                        else:
                            st.info("保存成功。ページを手動で再読み込みしてください。")
                    except Exception as e:
                        st.error(f"保存に失敗しました: {e}")

        with col_cancel:
            if st.button("入力をクリア"):
                for name, _ in ITEMS_CFG:
                    st.session_state.pop(f"{selected_port}_{name}", None)
                safe_rerun()

        with col_reload:
            if st.button("最新データを再取得"):
                new_cfg = fetch_cfg_from_jsonbin()
                if new_cfg:
                    cfg = new_cfg
                    PRICES_CFG = cfg.get("PRICES", {})
                    st.success("最新データを取得しました。")
                    safe_rerun()
                else:
                    st.error("再取得に失敗しました。")
