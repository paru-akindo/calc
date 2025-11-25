import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（最小動作確認版）")

# 手札を仮に作成
hand_items = [f"{kind}-{i+1}" for kind in range(1, 4) for i in range(2)]

# コンテナを定義（盤面は最初は空）
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

# 盤面を描画（3列ごとに並べる）
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
