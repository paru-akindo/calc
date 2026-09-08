import streamlit as st
import requests
import csv

# 公開スプシの CSV URL
SHEET_ID = "1eKGxILItNdSp4WYDZeABumgEwAdZZVvFLkXKaDbDLsA"
GID = "1597068058"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data
def load_coefficients():
    res = requests.get(CSV_URL)
    res.encoding = "utf-8"

    reader = csv.DictReader(res.text.splitlines())
    coeff = {}

    for row in reader:
        level = int(row["level"])
        coef = float(row["coefficient"].replace(",", ""))
        coeff[level] = coef

    return coeff

coeff_map = load_coefficients()

st.title("家来予想計算")

level = st.number_input("家来等級", min_value=1, value=832)
current_sales = st.number_input("現在の売上", min_value=0.0, value=70270000000.0)
current_base = st.number_input("現在の基礎", min_value=0.0, value=1124000000.0)
current_quality = st.number_input("現在の資質", min_value=0.0, value=12400.0)
add_quality = st.number_input("追加する資質", min_value=0.0, value=120.0)
add_buff_percent = st.number_input("追加するバフ％（例：5% → 0.05）", min_value=0.0, value=0.05)

if st.button("計算する"):
    # 現在のバフ推定
    B = current_sales / current_base - 1

    # 係数取得
    keys = sorted(coeff_map.keys())
    nearest = max([k for k in keys if k <= level])
    k = coeff_map[nearest]

    # 新しい基礎値
    new_quality = current_quality + add_quality
    new_base = new_quality * k

    # 新しいバフ
    new_buff = B * (1 + add_buff_percent)

    # 新しい売上
    new_sales = new_base * (1 + new_buff)

    st.subheader("計算結果")
    st.write(f"新しい基礎値：{new_base:,.0f}")
    st.write(f"新しいバフ：{new_buff * 100:.2f}%")
    st.write(f"予想売上：{new_sales:,.0f}")
