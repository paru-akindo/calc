import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（盤面を固定サイズに）")

# --- 初期化 ---
if "board" not in st.session_state:
    st.session_state.board = [f"1-{i+1}" for i in range(6)]  # 初期盤面は全部1

# ユーザが種類ごとの枚数を選ぶ
card_defs = {}
for kind in ["1","2","3","4","5","6","7","8","9","10"]:
    card_defs[kind] = st.number_input(f"{kind}の枚数", min_value=0, max_value=4, value=2)

# ユニークID生成（手札）
hand_items = []
for kind, count in card_defs.items():
    for i in range(count):
        hand_items.append(f"{kind}-{i+1}")

# コンテナを渡す（盤面は常に session_state.board を使う）
containers = [
    {"name": "手札", "items": hand_items},
    {"name": "盤面", "items": st.session_state.board}
]

# 並べ替え UI
sorted_containers = sort_items(containers, multi_containers=True)

# --- 返り値から盤面を更新 ---
for c in sorted_containers:
    if c.get("name") == "盤面":
        new_board = c.get("items", [])
        # 常に6マスに補正
        st.session_state.board = (new_board + ["空"]*6)[:6]

# --- 盤面を描画（2×3） ---
cols_per_row = 3
rows = [st.session_state.board[i:i+cols_per_row] for i in range(0, 6, cols_per_row)]

st.subheader("盤面表示 2×3")
for row in rows:
    cols = st.columns(3)
    for col, card in zip(cols, row):
        if str(card).startswith("空"):
            col.write("空")
        else:
            kind = str(card).split("-")[0]
            col.image(
                f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{kind}.png",
                width=80,
            )
