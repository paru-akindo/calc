import streamlit as st
from streamlit_elements import elements, mui, dashboard

st.set_page_config(layout="wide")
st.title("🎴 トランプカード配置サンプル (Cloud対応)")

# 盤面サイズ選択
board_size = st.selectbox("盤面サイズを選択", ["2x3", "3x4", "4x4", "4x5"])
rows, cols = map(int, board_size.split("x"))

# カード画像の準備（images/ ディレクトリに置いたものを参照）
card_images = [f"../image/{i}.png" for i in range(1, 11)]

st.sidebar.header("カード一覧")
for img in card_images:
    st.sidebar.image(img, use_column_width=True)

# ダッシュボードレイアウト
with elements("board"):
    layout = []
    i = 0
    for r in range(rows):
        for c in range(cols):
            layout.append(dashboard.Item(f"cell-{r}-{c}", c, r, 1, 1))
            i += 1

    with dashboard.Grid(layout):
        for r in range(rows):
            for c in range(cols):
                mui.Paper(f"セル {r},{c}", elevation=3, style={"padding": "10px", "textAlign": "center"})
