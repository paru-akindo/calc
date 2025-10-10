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

# 旧来の%補正（移行期用フォールバック）
MODIFIERS_PERCENT = [
    # 省略表示: 実環境では元の配列をここに置いてください
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
def fetch_cfg_from_jsonbin():
    try:
        resp = requests.get(f"{JSONBIN_BASE}/latest", headers=JSONBIN_HEADERS, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and "record" in payload:
            return payload["record"]
        return payload
    except Exception as e:
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
    # すべて base に近ければ未入力扱い（False）、1つでも差があれば True
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

    # 数字キーボード誘導（ブラウザ依存）
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

# フォールバック: 旧来の%から価格行列生成（移行期用）
def build_price_matrix_percent(items=ITEMS, modifiers=MODIFIERS_PERCENT, ports=PORTS):
    price = {}
    for idx, (name, base) in enumerate(items):
        row = {}
        mods = modifiers[idx]
        for p_idx, port in enumerate(ports):
            pct = mods[p_idx]
            val = base * (1 + pct / 100.0)
            row[port] = int(round(val))
        price[name] = row
    return price

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
    cfg = {
        "PORTS": PORTS,
        "ITEMS": [list(i) for i in ITEMS],
        # PRICES がなければフォールバックで % を使う
    }

# 正規化
PORTS_CFG = cfg.get("PORTS", PORTS)
ITEMS_CFG = normalize_items(cfg.get("ITEMS", [list(i) for i in ITEMS]))
PRICES_CFG = cfg.get("PRICES", {})  # 形式: {port: {item: price, ...}, ...}

# 2) 全港が実値入力済みか判定（tolはサイドバーで調整可）
tol = st.sidebar.number_input("判定許容差 tol (0=完全一致を未入力扱い)", min_value=0, value=0, step=1)
all_populated = True
for port in PORTS_CFG:
    port_prices = PRICES_CFG.get(port, {})
    if not port_has_actual_prices_by_diff(port_prices, ITEMS_CFG, tol=tol):
        all_populated = False
        break

if all_populated:
    # --- 全港実値あり: シミュレーション画面を表示（PRICES を直接利用）
    st.success("全ての港に実価格が入力されています。シミュレーション画面を表示します。")

    # price_matrix: item -> port -> price
    price_matrix = build_price_matrix_from_prices(PRICES_CFG, items=ITEMS_CFG, ports=PORTS_CFG)

    # UI --- 中央寄せ（シミュレーション本体は既存ロジックを活用）
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("効率よく買い物しよう！（実価格ベース）")

        current_port = st.selectbox("現在港", PORTS_CFG, index=0)
        cash = numeric_input_optional_strict("所持金", key="cash_input", placeholder="例: 5000", allow_commas=True, min_value=0)

        # 現在港で価格が割安（実際に buy < sell を期待）な上位5品目を抽出（今は%ではないので差を直接使う）
        port_idx = PORTS_CFG.index(current_port)
        item_diffs = []
        for i, (item_name, base) in enumerate(ITEMS_CFG):
            # 差を見るため、平均等は用いず対他港の差で判断する
            # ここでは「同港でのbaseとの差」ではなく、単純にその港に対して価格が低めかを判断するため
            # 他港との平均価格との差を使う実装にする
            prices_for_item = [price_matrix[item_name][p] for p in PORTS_CFG]
            avg_price = sum(prices_for_item) / len(prices_for_item) if prices_for_item else base
            this_price = price_matrix[item_name][current_port]
            diff = avg_price - this_price  # 正なら割安
            item_diffs.append((item_name, diff, this_price, avg_price))
        # 割安順ソート（差が大きい順）
        item_diffs.sort(key=lambda x: x[1], reverse=True)
        top5_negative = [(name, diff) for name, diff, _, _ in item_diffs if diff > 0][:5]

        st.write("現在港で割安（他港平均より安い）な上位5品目（この5つのみ在庫入力）。")
        stock_inputs = {}
        if top5_negative:
            cols = st.columns(2)
            for i, (item_name, diff) in enumerate(top5_negative):
                c = cols[i % 2]
                with c:
                    stock_inputs[item_name] = numeric_input_optional_strict(f"{item_name} 在庫数", key=f"stk_{item_name}", placeholder="例: 10", allow_commas=True, min_value=0)
        else:
            st.info("該当港で割安と判断される品目はありません。全品目を入力したい場合は指示してください。")

        top_k = st.slider("表示上位何港を出すか（上位k）", min_value=1, max_value=10, value=3)

        if st.button("検索"):
            if cash is None:
                st.error("所持金を入力してください（空欄不可）。")
            else:
                invalid_found = False
                for item_name, _ in top5_negative:
                    flag = st.session_state.get(f"stk_{item_name}_invalid", False)
                    if flag:
                        st.error(f"{item_name} の入力が不正です。半角の整数で入力してください。")
                        invalid_found = True
                if invalid_found:
                    st.error("不正な在庫入力があるため検索を中止します。")
                else:
                    current_stock = {name: 0 for name, _ in ITEMS_CFG}
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
                        st.info("所持金・在庫の範囲で利益が見込める到着先が見つかりませんでした。")
                    else:
                        for rank, (dest, plan, cost, profit) in enumerate(top_results, start=1):
                            st.markdown(f"### {rank}. 到着先: {dest}  想定合計利益: {profit}  合計購入金額: {cost}")
                            if not plan:
                                st.write("購入候補がありません（利益が出ない、もしくは在庫不足）。")
                                continue

                            df = pd.DataFrame([{
                                "品目": item,
                                "購入数": qty,
                                "購入単価": buy,
                                "売価": sell,
                                "単位差益": unit_profit,
                                "想定利益": qty * unit_profit
                            } for item, qty, buy, sell, unit_profit in plan])

                            totals = {
                                "品目": "合計",
                                "購入数": int(df["購入数"].sum()) if not df.empty else 0,
                                "購入単価": np.nan,
                                "売価": np.nan,
                                "単位差益": np.nan,
                                "想定利益": int(df["想定利益"].sum()) if not df.empty else 0
                            }
                            df_disp = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
                            num_format = {
                                "購入単価": "{:,.0f}",
                                "売価": "{:,.0f}",
                                "単位差益": "{:,.0f}",
                                "購入数": "{:,.0f}",
                                "想定利益": "{:,.0f}"
                            }
                            styled = df_disp.style.format(num_format, na_rep="")
                            st.dataframe(styled, height=200)
                            st.write("---")

    # 右カラムの価格表表示（実価格）
    with st.sidebar:
        if st.checkbox("価格表を表示（実価格）"):
            rows = []
            for item, _ in ITEMS_CFG:
                row = {"品目": item}
                for p in PORTS_CFG:
                    # PRICES_CFG: port -> {item: price}
                    row[p] = PRICES_CFG.get(p, {}).get(item, None)
                rows.append(row)
            df_all = pd.DataFrame(rows).set_index("品目")
            st.dataframe(df_all, height=600)

else:
    # --- 一部港が未入力: 編集ページ（既存の json 編集UI を簡易表示）
    st.warning("一部の港が未更新（実価格が入力されていない）です。未更新の港を埋めてください。")

    # 簡易的な未更新港一覧表示と編集へ誘導
    missing_ports = []
    for port in PORTS_CFG:
        port_prices = PRICES_CFG.get(port, {})
        if not port_has_actual_prices_by_diff(port_prices, ITEMS_CFG, tol=tol):
            missing_ports.append(port)

    st.write("未更新の港（例）:", missing_ports)
    st.info("管理画面（編集・保存）に移動して各港を登録してください。")

    # 簡易リンク的UI: JSON を表示して手動で更新可能
    st.subheader("現在の JSON（PRICES を含む）")
    st.json({
        "PORTS": PORTS_CFG,
        "ITEMS": [list(i) for i in ITEMS_CFG],
        "PRICES": PRICES_CFG
    })

    st.markdown("---")
    st.markdown("編集ワークフローの推奨: ① jsonbin 管理画面で PRICES を埋める ② または管理ツールで未更新港を選んで編集・保存してください。")

# ---------- end
