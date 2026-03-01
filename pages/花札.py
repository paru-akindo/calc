import streamlit as st
from PIL import Image
import os

st.set_page_config(page_title="札メモ（huda）", layout="wide")
st.title("札メモ（huda）")

# カード画像フォルダ
CARD_DIR = "cards"

# カード一覧を読み込む
cards = sorted([f for f in os.listdir(CARD_DIR) if f.endswith(".png")])

# 裏面カードを先頭に
cards.sort(key=lambda x: (x != "card00.png", x))

# 選択中カードの初期値
if "selected" not in st.session_state:
    st.session_state.selected = "card00"

# 盤面サイズ選択
size_label = st.selectbox("盤面サイズ", ["2x3", "3x4", "4x4", "4x5"])
rows, cols = map(int, size_label.split("x"))

# 盤面の初期化
if "board" not in st.session_state or st.session_state.board_size != size_label:
    st.session_state.board = [["card00" for _ in range(cols)] for _ in range(rows)]
    st.session_state.board_size = size_label

# 盤面表示
st.subheader("盤面")

for r in range(rows):
    cols_ui = st.columns(cols)
    for c in range(cols):
        with cols_ui[c]:
            img = Image.open(f"{CARD_DIR}/{st.session_state.board[r][c]}.png")
            st.image(img, width=80)  # ← 枠ごと小さく
            if st.button(" ", key=f"{r}-{c}"):
                st.session_state.board[r][c] = st.session_state.selected
                st.experimental_rerun()

# カード一覧
st.subheader("カード選択")

scroll_cols = st.columns(len(cards))

for i, card in enumerate(cards):
    with scroll_cols[i]:
        img = Image.open(f"{CARD_DIR}/{card}")
        st.image(img, width=50)  # ← 一覧は少し大きめ
        if st.button(card.replace(".png", ""), key=f"sel-{card}"):
            st.session_state.selected = card.replace(".png", "")
            st.experimental_rerun()
