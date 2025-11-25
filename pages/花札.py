import streamlit as st
from streamlit_elements import elements, mui, dashboard

st.set_page_config(layout="wide")
st.title("🎴 トランプカード配置サンプル (Cloud対応)")

# 盤面サイズ選択
board_size = st.selectbox("盤面サイズを選択", ["2x3", "3x4", "4x4", "4x5"])
rows, cols = map(int, board_size.split("x"))

# カード画像
card_images = [
    f"https://raw.githubusercontent.com/paru-akindo/calc/main/image/{i}.png"
    for i in range(1, 21)
]

st.subheader("盤面とカード")

with elements("board"):
    layout = []

    # 枠（セル）
    for r in range(rows):
        for c in range(cols):
            layout.append(dashboard.Item(f"cell-{r}-{c}", c, r, 1, 1, isDraggable=False, isResizable=False))

    # カード
    for idx, _ in enumerate(card_images, start=1):
        layout.append(dashboard.Item(f"card-{idx}", (idx - 1) % cols, rows + ((idx - 1) // cols), 1, 1))

    # Grid 表示
    with dashboard.Grid(layout, cols=cols, rowHeight=130, preventCollision=False, compactType=None):
        # 枠を描画（key を一致させる）
        for r in range(rows):
            for c in range(cols):
                mui.Box(
                    key=f"cell-{r}-{c}",
                    sx={
                        "border": "2px dashed #888",
                        "height": "120px",
                        "width": "90px",
                        "bgcolor": "#f5f5f5",
                        "borderRadius": "6px"
                    }
                )

        # カードを描画
        for idx, img in enumerate(card_images, start=1):
            mui.Card(
                key=f"card-{idx}",
                sx={"width": "90px", "m": 0.5, "zIndex": 1}
            )(
                mui.CardMedia(
                    image=img,
                    sx={"height": 120}
                ),
                mui.CardContent(
                    mui.Typography("トランプ", variant="body2")
                )
            )
