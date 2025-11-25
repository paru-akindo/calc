import streamlit as st
from streamlit_dnd_component import st_dnd

st.set_page_config(page_title="カード配置サンプル", layout="wide")
st.title("🎴 トランプカード配置サンプル")

# 盤面サイズ選択
board_size = st.selectbox("盤面サイズを選択", ["2x3", "3x4", "4x4", "4x5"])
rows, cols = map(int, board_size.split("x"))

# カード画像の準備（例として 10 枚）
card_images = [f"../image/{i}.png" for i in range(1, 11)]

st.sidebar.header("カード一覧")
for img in card_images:
    st.sidebar.image(img, use_column_width=True)

st.write("👇 下の盤面にカードをドラッグ＆ドロップしてください")

# DNDコンポーネントで盤面を作成
result = st_dnd(
    items=[{"id": f"card{i}", "text": f"カード{i}", "img": card_images[i-1]} for i in range(1, 11)],
    dropzones=[{"id": f"cell-{r}-{c}", "text": f"セル {r},{c}"} for r in range(rows) for c in range(cols)],
    horizontal=True,
)

st.write("### 配置結果")
st.json(result)
