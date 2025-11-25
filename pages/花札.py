import streamlit as st
from streamlit_sortables import sort_items

st.title("花札カード並べ替え")

cards = [
    "![card1](https://raw.githubusercontent.com/paru-akindo/calc/main/image/1.png)",
    "![card2](https://raw.githubusercontent.com/paru-akindo/calc/main/image/2.png)",
    "![card3](https://raw.githubusercontent.com/paru-akindo/calc/main/image/3.png)",
]

sorted_cards = sort_items(cards, multi_containers=False)

st.write("並べ替え後:", sorted_cards)
