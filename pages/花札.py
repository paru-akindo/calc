import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱記録（手札と盤面を別枠に・ドラッグ対応）")

# ユーザが種類ごとの枚数を選ぶ
card_defs = {}
for kind in ["1","2","3","4","5","6","7","8","9","10"]:
    card_defs[kind] = st.number_input(f"{kind}の枚数", min_value=0, max_value=4, value=2)

# ユニークID生成（同種の複数枚を区別）
hand_items = []
for kind, count in card_defs.items():
    for i in range(count):
        hand_items.append(f"{kind}-{i+1}")

# 盤面を固定サイズでダミー枠を用意（2×3 = 6マス）
board_items = [f"空-{i+1}" for i in range(6)]

# コンテナを list[dict] で渡す（multi_containers=True 必須形）
containers = [
    {"name": "手札", "items": hand_items},
    {"name": "盤面", "items": board_items},
]

# 並べ替え UI（手札と盤面が別領域として表示）
sorted_containers = sort_items(containers, multi_containers=True)

# 返り値の形に合わせて安全に取り出す
def get_items_by_name(result, name):
    # list[dict{name, items}] の場合
    if isinstance(result, list):
        for c in result:
            if isinstance(c, dict) and c.get("name") == name:
                return c.get("items", [])
        return []
    # dict[str, list] の場合（キーがコンテナ名）
    if isinstance(result, dict):
        return result.get(name, [])
    # 不明形の場合
    return []

board = get_items_by_name(sorted_containers, "盤面")

# 盤面描画（2×3）
cols_per_row = 3
rows = [board[i:i+cols_per_row] for i in range(0, len(board), cols_per_row)]

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
