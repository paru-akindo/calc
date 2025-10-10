# main.py
import streamlit as st
from typing import Dict, List, Tuple

st.set_page_config(page_title="貿易次動作提案（%補正）", layout="wide")

PORTS = ["博多","開京","明州","泉州","広州","淡水","安南","ボニ","タイ","真臘","スル","三仏","ジョ","大光","天竺","セイ","ペル","大食","ミス","末羅"]

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

def recommend_next_steps_percent(
    current_port: str,
    cash: int,
    current_stock: Dict[str,int],
    price_matrix: Dict[str,Dict[str,int]],
    top_n_ports: int = 6,
    score_mode: str = "total"
) -> List[Tuple[str,str,int,int,int]]:
    results = []
    for dest in PORTS:
        if dest == current_port:
            continue
        best_item = None
        best_unit_profit = -10**9
        best_qty = 0
        for item, _base in ITEMS:
            stock_here = current_stock.get(item, 0)
            if stock_here <= 0:
                continue
            buy_price = price_matrix[item][current_port]
            sell_price = price_matrix[item][dest]
            unit_profit = sell_price - buy_price
            if unit_profit <= 0:
                continue
            max_by_cash = cash // buy_price if buy_price > 0 else stock_here
            qty = min(stock_here, max_by_cash)
            if qty <= 0:
                continue
            # 評価は単位差益ではなく想定総利益にも切替可能
            if unit_profit > best_unit_profit:
                best_unit_profit = unit_profit
                best_item = item
                best_qty = qty
        if best_item is not None:
            total_profit = best_unit_profit * best_qty
            results.append((dest, best_item, best_unit_profit, best_qty, total_profit))
    if score_mode == "unit":
        results.sort(key=lambda x: x[2], reverse=True)
    else:
        results.sort(key=lambda x: x[4], reverse=True)
    return results[:top_n_ports]

# UI --- 中央寄せ
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("貿易 次の一手提案（補正値=%）")
    price_matrix = build_price_matrix_percent()

    # 左メニューがある環境向けに中央入力フォーム
    current_port = st.selectbox("現在港", PORTS, index=0)
    cash = st.number_input("所持金", min_value=0, value=5000, step=100)
    # 現在港在庫を簡易に入力するインターフェイス
    st.write("現在港の在庫（0以上の整数を入力）")
    stock_inputs = {}
    cols = st.columns(4)
    for i, (item_name, _) in enumerate(ITEMS):
        c = cols[i % 4]
        with c:
            stock_inputs[item_name] = st.number_input(f"{item_name}", min_value=0, value=0, key=f"stk_{i}")

    score_mode = st.selectbox("ソート基準", ["total","unit"], index=0, format_func=lambda x: "総利益優先" if x=="total" else "単位差益優先")
    top_n = st.slider("表示上位数", min_value=3, max_value=12, value=6)

    if st.button("提案を表示"):
        recs = recommend_next_steps_percent(current_port, cash, stock_inputs, price_matrix, top_n_ports=top_n, score_mode=score_mode)
        if not recs:
            st.info("購入可能な利益商品が見つかりませんでした。所持金・在庫・港を確認してください。")
        else:
            st.write("到着港 | 推奨品目 | 単位差益 | 購入上限 | 想定総利益")
            for dest, item, unit, qty, total in recs:
                st.write(f"{dest} | {item} | {unit} | {qty} | {total}")

# 補助表示（右寄せカラムに価格表を簡易表示）
with col3:
    if st.checkbox("価格表を表示"):
        st.write("価格（元値×(1+補正%/100)）")
        # 表示量を抑えるため、簡易テーブルを作成
        import pandas as pd
        rows = []
        for item, _ in ITEMS:
            row = {"品目": item}
            for p in PORTS:
                row[p] = price_matrix[item][p]
            rows.append(row)
        df = pd.DataFrame(rows)
        st.dataframe(df.set_index("品目"), height=600)
