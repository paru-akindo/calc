import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（盤面は可変長）")

# ユーザが種類ごとの枚数を選ぶ
card_defs = {}
for kind in ["1","2","3","4","5","6","7","8","9","10"]:
    card_defs[kind] = st.number_input(f"{kind}の枚数", min_value=0, max_value=4, value=2)

# ユニークID生成（手札）
hand_items = []
for kind, count in card_defs.items():
    for i in range(count):
        hand_items.append(f"{kind}-{i+1}")

# コンテナを渡す（盤面は最初は空）
containers = [
    {"name": "手札", "items": hand_items},
    {"name": "盤面", "items": []}
]

# 並べ替え UI
sorted_containers = sort_items(containers, multi_containers=True)

# 盤面を取り出す（返り値は list[dict]）
board = []
for c in sorted_containers:
    if c.get("name") == "盤面":
        board = c.get("items", [])

# 盤面を描画（3列で自動改行）
cols_per_row = 3
rows = [board[i:i+cols_per_row] for i in range(0, len(board), cols_per_row)]

st.subheader("盤面表示")
for row in rows:
    cols = st.columns(len(row))
    for col, card in zip(cols, row):
        kind = card.split("-")[0]
        col.image(
            f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{kind}.png",
            width=80,
        )
