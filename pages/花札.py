import streamlit as st
from streamlit_elements import elements, dashboard, mui

with elements("demo"):
    layout = [
        dashboard.Item("first", 0, 0, 2, 2),
        dashboard.Item("second", 2, 0, 2, 2),
    ]

    with dashboard.Grid(layout, cols=4, rowHeight=100):
        mui.Box("first", sx={"bgcolor": "red"})
        mui.Box("second", sx={"bgcolor": "blue"})
