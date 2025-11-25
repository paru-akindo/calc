import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（ドラッグ＆ドロップ複数枚対応）")

# ユーザが種類ごとの枚数を選ぶ
card_defs = {}
for kind in ["1","2","3","4","5","6","7","8","9","10"]:
    card_defs[kind] = st.number_input(f"{kind}の枚数", min_value=0, max_value=4, value=2)

# ユニークID生成
cards = {}
cards["手札"] = []
cards["盤面"] = []

for kind, count in card_defs.items():
    for i in range(count):
        cards["手札"].append(f"{kind}-{i+1}")

# 並べ替え（手札→盤面へ移動可能）
sorted_cards = sort_items(cards, multi_containers=True)

# 盤面を描画（2×3）
board = sorted_cards.get("盤面", [])
cols_per_row = 3
rows = [board[i:i+cols_per_row] for i in range(0, len(board), cols_per_row)]

for row in rows:
    cols = st.columns(len(row))
    for col, card in zip(cols, row):
        kind = card.split("-")[0]
        col.image(f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{kind}.png", width=80)
