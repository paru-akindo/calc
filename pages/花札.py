import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（最小動作確認版）")

# 手札と盤面の初期データ
hand_items = [f"{kind}-{i+1}" for kind in range(1, 4) for i in range(2)]
board_items = ["空-1", "空-2", "空-3"]

# コンテナを渡す
containers = [
    {"name": "手札", "items": hand_items},
    {"name": "盤面", "items": board_items}
]

# 並べ替え UI
sorted_containers = sort_items(containers, multi_containers=True)

# 手札と盤面を取り出す
hand, board = [], []
for c in sorted_containers:
    if c["name"] == "手札":
        hand = c["items"]
    elif c["name"] == "盤面":
        board = c["items"]

# 手札表示
st.subheader("手札")
st.write(hand)

# 盤面表示
st.subheader("盤面")
cols_per_row = 3
rows = [board[i:i+cols_per_row] for i in range(0, len(board), cols_per_row)]
for row in rows:
    cols = st.columns(len(row))
    for col, card in zip(cols, row):
        if card.startswith("空"):
            col.write("空")
        else:
            kind = card.split("-")[0]
            col.image(
                f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{kind}.png",
                width=80,
            )
