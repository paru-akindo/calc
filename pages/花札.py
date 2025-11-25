import streamlit as st

st.title("神経衰弱の途中経過記録（2×3盤面）")

# 盤面をセッションに保持（6マス）
if "board" not in st.session_state:
    st.session_state.board = ["empty"] * 6

# ユーザがカードをめくったときに追加
new_card = st.selectbox("めくったカードを選んで追加", [str(i) for i in range(1, 11)])
pos = st.number_input("置く場所 (0〜5)", min_value=0, max_value=5, step=1)

if st.button("追加"):
    st.session_state.board[pos] = new_card

# 盤面を描画（2×3）
for row in range(2):
    cols = st.columns(3)
    for col, card in zip(cols, st.session_state.board[row*3:(row+1)*3]):
        if card == "empty":
            col.write("空")
        else:
            col.image(f"https://raw.githubusercontent.com/paru-akindo/calc/master/image/{card}.png", width=80)
