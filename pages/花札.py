import streamlit as st
from streamlit_elements import elements, mui, dashboard

st.set_page_config(layout="wide")
st.title("🎴 トランプカード配置サンプル (Cloud対応)")

# 盤面サイズ選択
board_size = st.selectbox("盤面サイズを選択", ["2x3", "3x4", "4x4", "4x5"])
rows, cols = map(int, board_size.split("x"))

# カード画像の準備（images/ ディレクトリに置いたものを参照）
card_images = [f"image/{i}.png" for i in range(1, 11)]

# カラム分割（左に盤面、右にカード一覧）
col_board, col_cards = st.columns([3, 1])

with col_cards:
    st.header("カード一覧")
    for idx, img in enumerate(card_images, start=1):
        st.image(img, use_column_width=True, caption=f"カード{idx}")

with col_board:
    st.subheader("盤面")

    # elements コンテナ
    with elements("board"):
        layout = []

        # 盤面セルを dashboard.Item として定義
        for r in range(rows):
            for c in range(cols):
                layout.append(dashboard.Item(f"cell-{r}-{c}", c, r, 1, 1))

        # カードも dashboard.Item として定義（初期位置は盤面の下）
        for idx, img in enumerate(card_images, start=1):
            layout.append(dashboard.Item(f"card-{idx}", idx % cols, rows, 1, 1))

        # グリッド表示
        with dashboard.Grid(layout):
            # 盤面セルの描画
            for r in range(rows):
                for c in range(cols):
                    mui.Paper(f"セル {r},{c}", elevation=3,
                              style={"padding": "10px", "textAlign": "center"})

            # カードの描画（画像付き）
            for idx, img in enumerate(card_images, start=1):
                mui.Card(
                    key=f"card-{idx}",
                    style={"maxWidth": 80, "margin": "5px"}
                )(
                    mui.CardMedia(
                        image=img,
                        style={"height": 120}
                    ),
                    mui.CardContent(
                        mui.Typography(f"カード{idx}", variant="body2")
                    )
                )
