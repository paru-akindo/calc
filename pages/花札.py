import streamlit as st
from streamlit_sortables import sort_items

st.title("Streamlit Sortables Demo")

# 並べ替え対象のリスト
items = ["松", "桜", "菊", "梅"]

# sort_items で並べ替え可能にする
sorted_items = sort_items(items, multi_containers=False)

st.write("並べ替え後のリスト:", sorted_items)
