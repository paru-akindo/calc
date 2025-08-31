# pages/酒屋.py
import streamlit as st

st.title("酒屋計算")

# ① GitHub の Raw URL
image_url = "https://raw.githubusercontent.com/paru-akindo/calc/main/image/sake.jpg"

# ② 画像表示
st.image(
    image_url,
    caption="銀塊のアイコン",
    width=300
)

# ③ 計算入力
base_silver = st.number_input("基礎銀塊", min_value=0.0, format="%.2f")
collection_bonus = st.number_input("収蔵品効果", min_value=0.0, format="%.2f")
elixir = st.number_input("美酒", min_value=0.0, format="%.2f")

# ④ 計算
if st.button("計算する"):
    result = (base_silver + collection_bonus) * elixir * 2
    st.success(f"計算結果：{result:.2f}")
