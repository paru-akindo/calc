import streamlit as st
from streamlit_elements import elements, dashboard, mui

st.set_page_config(layout="wide")

with elements("demo"):
    layout = [
        dashboard.Item("first", 0, 0, 2, 2),
    ]

    with dashboard.Grid(layout, cols=2, rowHeight=150):
        mui.Box(
            "first",
            sx={
                "bgcolor": "black",   # 背景を黒に
                "color": "red",       # 文字色を赤に
                "height": 120,
                "width": 120,
                "border": "5px solid yellow"  # 太い黄色の枠線
            }
        )("VISIBLE")
