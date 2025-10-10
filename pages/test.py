# trade_suggester.py
import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple

st.set_page_config(page_title="Trade Suggester", layout="wide")

# --- Data: ports, items, base prices, modifiers (from user provided table) ---
PORTS = ["博多","開京","明州","泉州","広州","淡水","安南","ボニ","タイ","真臘","スル","三仏","ジョ","大光","天竺","セイ","ペル","大食","ミス","末羅"]

ITEMS = [
    ("鳳梨",100),("魚肉",100),("酒",100),("水稲",100),("木材",100),("ヤシ",100),
    ("海鮮",200),("絹糸",200),("水晶",200),("茶葉",200),("鉄鉱",200),
    ("香料",300),("玉器",300),("白銀",300),("皮革",300),
    ("真珠",500),("燕の巣",500),("陶器",500),
    ("象牙",1000),("鹿茸",1000)
]

MODIFIERS = [
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

def build_price_matrix():
    price = {}
    for idx, (name, base) in enumerate(ITEMS):
        row = {}
        mods = MODIFIERS[idx]
        for p_idx, port in enumerate(PORTS):
            row[port] = base + mods[p_idx]
        price[name] = row
    return price

price_matrix = build_price_matrix()

# --- Sidebar inputs ---
st.title("Trade Suggester (Streamlit)")

st.sidebar.header("入力")
current_port = st.sidebar.selectbox("現在の港", PORTS, index=0)
cash = st.sidebar.number_input("現在の資産 (整数)", min_value=0, value=5000, step=1000)

# Compute "cheapness" at current port: modifier (元値差分) sorted ascending (more negative => cheaper)
# For display, build dataframe of items with modifier and local buy price
mod_list = []
for idx, (item, base) in enumerate(ITEMS):
    mod = MODIFIERS[idx][PORTS.index(current_port)]
    buy_price = price_matrix[item][current_port]
    mod_list.append({"品目": item, "元値": base, "修正値": mod, "買値": buy_price})

df_mod = pd.DataFrame(mod_list).sort_values(by="修正値")  # ascending: more negative first

st.sidebar.markdown("### マイナスが大きい（買うと得）上位5")
top5 = df_mod.head(5).reset_index(drop=True)
# For each top5 show item and input field for available stock at current port
stock_inputs = {}
for i, row in top5.iterrows():
    item = row["品目"]
    st.sidebar.write(f"{i+1}. {item}  (買値: {row['買値']} , 修正値: {row['修正値']})")
    stock_inputs[item] = st.sidebar.number_input(f"{item} の在庫（現在港）", min_value=0, value=0, step=1, key=f"stock_{i}")

st.sidebar.markdown("---")
st.sidebar.write("必要なら他商品在庫を追加で入力してください（任意）")
# optional free-form additional stocks
more_items = st.sidebar.multiselect("追加商品を選ぶ（任意）", [it[0] for it in ITEMS if it[0] not in top5["品目"].tolist()])
for it in more_items:
    stock_inputs[it] = st.sidebar.number_input(f"{it} の在庫（現在港）", min_value=0, value=0, step=1, key=f"stock_extra_{it}")

# Button to run analysis
if st.sidebar.button("解析する"):
    # Build candidate trades: for each item with stock>0, consider all destination ports != current_port
    candidates = []
    for item, base in ITEMS:
        stock_here = stock_inputs.get(item, 0)
        if stock_here <= 0:
            continue
        buy_price = price_matrix[item][current_port]
        # For each dest, compute unit profit
        for dest in PORTS:
            if dest == current_port:
                continue
            sell_price = price_matrix[item][dest]
            unit_profit = sell_price - buy_price
            if unit_profit <= 0:
                continue
            # maximum affordable quantity given cash
            max_by_cash = cash // buy_price if buy_price > 0 else stock_here
            qty = min(stock_here, max_by_cash)
            if qty <= 0:
                continue
            total_profit = unit_profit * qty
            candidates.append({
                "品目": item,
                "到着港": dest,
                "買値": buy_price,
                "売値": sell_price,
                "単位差益": unit_profit,
                "購入上限(在庫)": stock_here,
                "購入上限(資金)": max_by_cash,
                "推奨購入数": qty,
                "期待総利益": total_profit
            })
    if len(candidates) == 0:
        st.warning("購入可能な候補が見つかりません。在庫入力と資金を確認してください。")
    else:
        cand_df = pd.DataFrame(candidates)
        cand_df = cand_df.sort_values(by="期待総利益", ascending=False).reset_index(drop=True)
        st.subheader("推奨トップ候補（期待総利益順）")
        # Show top 3
        top_k = cand_df.head(3)
        for i, r in top_k.iterrows():
            st.markdown(f"### #{i+1} : {r['品目']} → {r['到着港']}")
            st.write(f"- 単位差益: {r['単位差益']}")
            st.write(f"- 買値: {r['買値']} / 売値: {r['売値']}")
            st.write(f"- 推奨購入数: {int(r['推奨購入数'])}")
            st.write(f"- 期待総利益: {int(r['期待総利益'])}")
            st.divider()
        st.subheader("全候補（上位20）")
        st.dataframe(cand_df.head(20).astype({"買値":"int","売値":"int","単位差益":"int","購入上限(在庫)":"int","購入上限(資金)":"int","推奨購入数":"int","期待総利益":"int"}), use_container_width=True)

# Footer instructions
st.sidebar.markdown("---")
st.sidebar.write("注: 現在は簡易モデルです。拡張機能（在庫補充、価格日次更新、複数港予約、移動時間アイテムなど）は今後追加できます。")
