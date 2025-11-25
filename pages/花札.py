import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（盤面を固定サイズに）")

# ユーザが種類ごとの枚数を選ぶ
card_defs = {}
for kind in ["1","2","3","4","5","6","7","8","9","10"]:
    card_defs[kind] = st.number_input(f"{kind}の枚数", min_value=0, max_value=4, value=2)

# ユニークID生成（手札）
hand_items = []
for kind, count in card_defs.items():
    for i in range(count):
        hand_items.append(f"{kind}-{i+1}")

# 初期盤面（全部1で6マス）
board_items = [f"1-{i+1}" for i in range(6)]

# コンテナを渡す
containers = [
    {"name": "手札", "items": hand_items},
    {"name": "盤面", "items": board_items}
]

sorted_containers = sort_items(containers, multi_containers=True)

# --- 返り値の形に合わせて安全に取り出す ---
def get_items(result, name):
    if isinstance(result, list):  # list[dict] の場合
        for c in result:
            if isinstance(c, dict) and c.get("name") == name:
                return c.get("items", [])
    elif isinstance(result, dict):  # dict[str, list] の場合
        return result.get(name, [])
    return []

board = get_items(sorted_containers, "盤面")

# --- 常に6マスに調整 ---
fixed_board = board[:6]
while len(fixed_board) < 6:
    fixed_board.append("空")

# 盤面を描画（2×3）
cols_per_row = 3
rows = [fixed_board[i:i+cols_per_row] for i in range(0, len(fixed_board), cols_per_row)]

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
