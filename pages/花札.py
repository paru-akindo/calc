import streamlit as st
from streamlit_sortables import sort_items

st.title("花札カード並べ替え")

# 花札カード画像のリスト
cards = [
    '<img src="https://raw.githubusercontent.com/paru-akindo/calc/image/1.png" width="80">',
    '<img src="https://raw.githubusercontent.com/paru-akindo/calc/image/2.png" width="80">',
    '<img src="https://raw.githubusercontent.com/paru-akindo/calc/image/3.png" width="80">',
]

# 並べ替え可能にする
sorted_cards = sort_items(cards, multi_containers=False)

st.write("並べ替え後:", sorted_cards)
