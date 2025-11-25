import streamlit as st
from streamlit_sortables import sort_items

st.title("花札カード並べ替え")

# 並べ替え対象はカードIDだけ
cards = ["card1", "card2", "card3"]

sorted_cards = sort_items(cards, multi_containers=False)

# 並べ替え結果に応じて画像を表示
for card in sorted_cards:
    if card == "card1":
        st.image("https://raw.githubusercontent.com/paru-akindo/calc/master/image/1.png", width=80)
    elif card == "card2":
        st.image("https://raw.githubusercontent.com/paru-akindo/calc/master/image/2.png", width=80)
    elif card == "card3":
        st.image("https://raw.githubusercontent.com/paru-akindo/calc/master/image/3.png", width=80)
