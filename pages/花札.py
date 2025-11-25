import streamlit as st
from streamlit_elements import elements, mui, dashboard

st.set_page_config(layout="wide")
st.title("🎴 トランプカード配置サンプル (Cloud対応)")

# 盤面サイズ（カードを置ける枠の数）
board_size = st.selectbox("盤面サイズを選択", ["2x3", "3x4", "4x4", "4x5"])
rows, cols = map(int, board_size.split("x"))

# カード画像（必要枚数に応じて調整）
card_images = [
    f"https://raw.githubusercontent.com/paru-akindo/calc/main/image/{i}.png"
    for i in range(1, 21)
]

st.subheader("盤面とカード")

with elements("board"):
    layout = []

    # 枠（セル）をレイアウトに追加
    for r in range(rows):
        for c in range(cols):
            layout.append(
                dashboard.Item(
                    id=f"cell-{r}-{c}",
                    x=c,
                    y=r,
                    w=1,
                    h=1,
                    isDraggable=False,
                    isResizable=False
                )
            )

    # カードを下段に配置
    for idx, _ in enumerate(card_images, start=1):
        layout.append(
            dashboard.Item(
                id=f"card-{idx}",
                x=(idx - 1) % cols,
                y=rows + ((idx - 1) // cols),
                w=1,
                h=1,
                isDraggable=True,
                isResizable=False
            )
        )

    # Grid 表示（枠とカードを描画）
    with dashboard.Grid(layout=layout, cols=cols, rowHeight=130, preventCollision=False, compactType=None):

        # 枠（セル）を描画：各 Item に紐付ける
        for r in range(rows):
            for c in range(cols):
                with dashboard.Item(id=f"cell-{r}-{c}"):
                    mui.Box(
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
            with dashboard.Item(id=f"card-{idx}"):
                mui.Card(
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
