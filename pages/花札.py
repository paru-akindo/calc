import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（手札と盤面を別枠に）")

# ユーザが種類ごとの枚数を選ぶ
card_defs = {}
for kind in ["1","2","3","4","5","6","7","8","9","10"]:
    card_defs[kind] = st.number_input(f"{kind}の枚数", min_value=0, max_value=4, value=2)

# ユニークID生成
hand_items = []
for kind, count in card_defs.items():
    for i in range(count):
        hand_items.append(f"{kind}-{i+1}")

# 盤面を固定サイズでダミー枠を用意（例: 2×3 = 6マス）
board_items = [f"空-{i+1}" for i in range(6)]

# コンテナをリスト形式で渡す
containers = [
    {"name": "手札", "items": hand_items},
    {"name": "盤面", "items": board_items}
]

# 並べ替え（手札と盤面が別枠として表示される）
sorted_cards = sort_items(containers, multi_containers=True)

# 盤面を取り出す
board = []
for c in sorted_cards:
    if c["name"] == "盤面":
        board = c["items"]

# 盤面を描画（2×3）
cols_per_row = 3
rows = [board[i:i+cols_per_row] for i in range(0, len(board), cols_per_row)]

for row in rows:
    cols = st.columns(len(row))
    for col, card in zip(cols, row):
        if card.startswith("空"):
            col.write("空")
        else:
            kind = card.split("-")[0]
            col.image(f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{kind}.png", width=80)
