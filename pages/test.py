# main.py
import streamlit as st
from typing import Dict, List, Tuple

st.set_page_config(page_title="貿易 全港評価（複数品目購入可）", layout="wide")

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

def greedy_plan_for_destination(current_port: str, dest_port: str, cash: int, stock: Dict[str,int], price_matrix: Dict[str,Dict[str,int]]):
    """
    dest_port に向けて、current_port の在庫と所持金で複数商品を購入する貪欲プランを返す。
    戻り: plan(list of (item, qty, buy_price, sell_price, unit_profit)), total_cost, total_profit
    """
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
    # 単位差益で降順ソート
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

# UI --- 中央寄せ
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("全港評価：次に行く港 上位3 を提案")
    price_matrix = build_price_matrix_percent()

    current_port = st.selectbox("現在港", PORTS, index=0)
    cash = st.number_input("所持金", min_value=0, value=5000, step=100)

    st.write("現在港在庫（各品目の在庫数を入力してください）")
    stock_inputs = {}
    cols = st.columns(4)
    for i, (item_name, _) in enumerate(ITEMS):
        c = cols[i % 4]
        with c:
            stock_inputs[item_name] = st.number_input(f"{item_name}", min_value=0, value=0, key=f"stk_{i}")

    top_k = st.slider("表示上位何港を出すか（上位k）", min_value=1, max_value=10, value=3)

    if st.button("全港を評価"):
        results = []
        for dest in PORTS:
            if dest == current_port:
                continue
            plan, cost, profit = greedy_plan_for_destination(current_port, dest, cash, stock_inputs, price_matrix)
            results.append((dest, plan, cost, profit))
        # 総利益で降順ソートして上位k
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
                st.write("品目 | 購入数 | 購入単価 | 売値 | 単位差益 | 想定利益")
                for item, qty, buy, sell, unit_profit in plan:
                    st.write(f"{item} | {qty} | {buy} | {sell} | {unit_profit} | {qty * unit_profit}")
                st.write("---")

with col3:
    if st.checkbox("価格表を表示"):
        import pandas as pd
        rows = []
        for item, _ in ITEMS:
            row = {"品目": item}
            for p in PORTS:
                row[p] = price_matrix[item][p]
            rows.append(row)
        df = pd.DataFrame(rows)
        st.dataframe(df.set_index("品目"), height=600)
