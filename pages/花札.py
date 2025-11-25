import streamlit as st
from streamlit_sortables import sort_items

st.title("神経衰弱の途中経過記録（2×3盤面）")

# セッション状態にカードリストを保持
if "cards" not in st.session_state:
    st.session_state.cards = []

# ユーザがカードをめくったときに追加
new_card = st.selectbox("めくったカードを選んで追加", [str(i) for i in range(1, 11)])
if st.button("追加"):
    # 同じカード番号でも複数枚区別できるように番号を付与
    count = sum(1 for c in st.session_state.cards if c.startswith(new_card))
    st.session_state.cards.append(f"{new_card}-{count+1}")

# 並べ替え可能にする
sorted_cards = sort_items(st.session_state.cards, multi_containers=False)

# 並べ替え結果を 2×3 の盤面に表示
cols_per_row = 3
rows = [sorted_cards[i:i+cols_per_row] for i in range(0, len(sorted_cards), cols_per_row)]

for row in rows:
    cols = st.columns(len(row))
    for col, card in zip(cols, row):
        # 種類部分（例: "3-1" → "3"）を取り出す
        kind = card.split("-")[0]
        # 画像を表示（例: 3.png）
        col.image(f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{kind}.png", width=80)
