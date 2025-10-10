# main.py
import streamlit as st
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="効率よく買い物しよう！", layout="wide")

PORTS = ["博多","開京","明州","泉州","広州","淡水","安南","ボニ","タイ","真臘","スル","三仏斉","ジョホール","大光国","天竺","セイロン","ペルシャ","大食国","ミスル","末羅国"]

ITEMS = [
    ("鳳梨",100),("魚肉",100),("酒",100),("水稲",100),("木材",100),("ヤシ",100),
    ("海鮮",200),("絹糸",200),("水晶",200),("茶葉",200),("鉄鉱",200),
    ("香料",300),("玉器",300),("白銀",300),("皮革",300),
    ("真珠",500),("燕の巣",500),("陶器",500),
    ("象牙",1000),("鹿茸",1000)
]

MODIFIERS_PERCENT = [
    [-7,3,3,-8,0,-8,-1,-1,-6,-13,-3,8,6,19,5,-2,-2,5,9,3],
    [9,7,-8,0,-1,6,10,-6,-2,-7,-9,-5,-13,8,-1,4,-4,-4,20,0],
    [6,5,10,8,-2,0,8,-1,-4,-8,7,-14,-2,-3,-8,20,7,-6,6,4],
    [-9,-7,-8,10,4,-6,-18,2,9,10,1,12,-6,4,-5,8,-1,1,-2,-2],
    [-11,1,-10,-5,-2,10,-1,2,-9,-1,2,-8,1,-5,-7,-2,6,9,7,13],
    [-3,13,-1,-7,-7,3,-6,0,1,-5,3,-9,0,9,5,-14,9,5,4,2],
    [-3,5,14,-1,9,-9,-5,9,9,9,-17,5,-7,-9,-6,1,-3,-9,3,-5],
    [2,7,0,-6,-19,-4,-6,-4,9,-8,-8,5,9,0,3,-2,19,1,-1,-3],
    [-7,8,3,-2,-1,4,8,-6,-9,3,7,7,-4,9,13,-4,-19,0,-5,-2],
    [20,2,-4,-18,-9,-3,-6,-2,9,-3,4,-7,1,7,5,-2,6,-2,5,8],
    [-8,-6,-4,15,1,1,9,-6,-6,-1,-4,4,5,-19,1,0,9,-2,-8,1],
    [2,9,8,-2,5,-7,0,8,2,6,14,-8,-9,3,-13,-3,6,-7,-3,10],
    [5,9,-6,2,14,9,-8,3,6,-2,-2,5,-6,5,5,-2,2,-11,-9,10],
    [2,7,1,-3,9,-8,-5,2,-9,8,4,-4,19,-7,6,-7,-4,-9,-9,-19],
    [-4,5,-6,-1,0,-8,13,-5,2,9,9,0,10,-5,6,10,1,2,-15,-5],
    [2,7,-4,-7,-9,-17,8,1,9,-4,3,8,-5,8,9,-3,-9,15,-1,-9],
    [2,5,-1,0,-3,10,4,-14,-8,-6,1,1,8,3,-8,1,-4,-5,10,6],
    [0,-7,-14,9,3,10,1,17,6,8,-4,1,8,-2,4,2,7,8,-9,9],
    [-7,-5,7,-7,8,9,3,8,-17,15,0,-4,3,6,2,-10,0,-5,9,5],
    [-9,-18,0,-6,2,0,-5,3,14,-3,-8,-6,-7,-5,7,3,-5,2,-6,-9]
]

# ---------------------------
# ユーティリティ: 空欄許容・厳格整数チェック入力欄
# ---------------------------
def numeric_input_optional_strict(label: str, key: str, placeholder: str = "", allow_commas: bool = True, min_value: int = None, max_value: int = None):
    """
    - 初期は空欄。
    - 空欄 -> returns None.
    - 整数のみ許可。全角数字とカンマを許容して内部で半角に変換。
    - 数字以外が入力された場合は st.error を出し、st.session_state[f"{key}_invalid"]=True を立てる。
    - 正常値の場合は st.session_state[f"{key}_invalid"]=False を設定して int を返す。
    """
    # reset invalid flag default
    invalid_flag = f"{key}_invalid"
    if invalid_flag not in st.session_state:
        st.session_state[invalid_flag] = False

    raw = st.text_input(label, value="", placeholder=placeholder, key=key)

    # try to set numeric keyboard hint (browser dependent)
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

    s = raw.strip()
    if s == "":
        st.session_state[invalid_flag] = False
        return None

    # normalize: remove commas if allowed, convert full-width digits
    if allow_commas:
        s = s.replace(",", "")
    s = s.translate(str.maketrans("０１２３４５６７８９－＋．，", "0123456789-+.,"))

    # strict integer check: only digits (no sign)
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

# ---------------------------
# 既存ロジック（価格と最適化）
# ---------------------------
def build_price_matrix_percent():
    price = {}
    for idx, (name, base) in enumerate(ITEMS):
        row = {}
        mods = MODIFIERS_PERCENT[idx]
        for p_idx, port in enumerate(PORTS):
            pct = mods[p_idx]
            val = base * (1 + pct / 100.0)
            row[port] = int(round(val))
        price[name] = row
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

# ---------------------------
# UI --- 中央寄せ
# ---------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("効率よく買い物しよう！")
    price_matrix = build_price_matrix_percent()

    current_port = st.selectbox("現在港", PORTS, index=0)

    # 所持金: 初期空欄を許容する入力欄（厳格）
    cash = numeric_input_optional_strict("所持金", key="cash_input", placeholder="例: 5000", allow_commas=True, min_value=0)

    # 現在港で補正%がマイナスの上位5品目を抽出
    port_idx = PORTS.index(current_port)
    item_pcts = []
    for i, (item_name, _) in enumerate(ITEMS):
        pct = MODIFIERS_PERCENT[i][port_idx]
        item_pcts.append((item_name, pct))
    negative_items = [t for t in item_pcts if t[1] < 0]
    negative_items.sort(key=lambda x: x[1])
    top5_negative = negative_items[:5]

    st.write("現在港で割安（補正%がマイナス）な上位5品目（この5つのみ在庫入力）。")
    stock_inputs = {}
    if top5_negative:
        cols = st.columns(2)
        for i, (item_name, pct) in enumerate(top5_negative):
            c = cols[i % 2]
            with c:
                # 各在庫入力欄も空欄可で厳格チェック
                stock_inputs[item_name] = numeric_input_optional_strict(f"{item_name} 在庫数", key=f"stk_{item_name}", placeholder="例: 10", allow_commas=True, min_value=0)
    else:
        st.info("該当港で補正%がマイナスの品目はありません。全品目を入力したい場合は指示してください。")

    top_k = st.slider("表示上位何港を出すか（上位k）", min_value=1, max_value=10, value=3)

    if st.button("検索"):
        # バリデーション: 所持金は必須（未入力ならエラー）
        if cash is None:
            st.error("所持金を入力してください（空欄不可）。")
        else:
            # 在庫の不正入力フラグをチェック
            invalid_found = False
            for i, (item_name, _) in enumerate(top5_negative):
                flag = st.session_state.get(f"stk_{item_name}_invalid", False)
                if flag:
                    st.error(f"{item_name} の入力が不正です。半角の整数で入力してください。")
                    invalid_found = True
            if invalid_found:
                st.error("不正な在庫入力があるため検索を中止します。")
            else:
                # current_stock は上位5入力のみ反映、空欄(None)は0扱い
                current_stock = {name: 0 for name, _ in ITEMS}
                for name in stock_inputs:
                    val = stock_inputs.get(name)
                    current_stock[name] = int(val) if val is not None else 0

                results = []
                for dest in PORTS:
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

                        # DataFrame 作成（表形式で見やすく）
                        df = pd.DataFrame([{
                            "品目": item,
                            "購入数": qty,
                            "購入単価": buy,
                            "売価": sell,
                            "単位差益": unit_profit,
                            "想定利益": qty * unit_profit
                        } for item, qty, buy, sell, unit_profit in plan])

                        # 合計行は数値列は数値で保持、非数値は NaN にする
                        totals = {
                            "品目": "合計",
                            "購入数": int(df["購入数"].sum()) if not df.empty else 0,
                            "購入単価": np.nan,
                            "売価": np.nan,
                            "単位差益": np.nan,
                            "想定利益": int(df["想定利益"].sum()) if not df.empty else 0
                        }
                        df_disp = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)

                        # Styler 表示（NaN を空文字に）
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

with col3:
    if st.checkbox("価格表を表示"):
        rows = []
        for item, _ in ITEMS:
            row = {"品目": item}
            for p in PORTS:
                row[p] = price_matrix[item][p]
            rows.append(row)
        df_all = pd.DataFrame(rows).set_index("品目")
        st.dataframe(df_all, height=600)
