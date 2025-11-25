import streamlit as st
from streamlit_elements import elements, mui, dashboard

st.set_page_config(layout="wide")

with elements("board"):
    layout = [
        dashboard.Item("cell-0-0", 0, 0, 1, 1),
        dashboard.Item("card-1", 1, 0, 1, 1),
    ]

    with dashboard.Grid(layout, cols=2, rowHeight=130):
        # 枠を描画
        with dashboard.Item("cell-0-0"):
            mui.Box(sx={"border":"2px solid red","height":120,"width":90})

        # カードを描画
        with dashboard.Item("card-1"):
            mui.Card(sx={"width":90})(
                mui.CardMedia(
                    image="https://raw.githubusercontent.com/paru-akindo/calc/main/image/1.png",
                    sx={"height":120}
                )
            )
