import streamlit as st
from streamlit_elements import elements, dashboard, mui

st.set_page_config(layout="wide")

with elements("demo"):
    # レイアウト定義
    layout = [
        dashboard.Item("cell-0-0", 0, 0, 1, 1),
        dashboard.Item("card-1", 1, 0, 1, 1),
    ]

    # Grid に渡す
    with dashboard.Grid(layout, cols=2, rowHeight=130):
        # 枠を描画（IDを最初の引数で渡す）
        mui.Box("cell-0-0", sx={"border": "2px solid red", "height": 120, "width": 90})

        # カードを描画（IDを最初の引数で渡す）
        mui.Card("card-1", sx={"width": 90})(
            mui.CardMedia(
                image="https://raw.githubusercontent.com/paru-akindo/calc/main/image/1.png",
                sx={"height": 120}
            )
        )
