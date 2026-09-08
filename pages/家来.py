import streamlit as st
import requests
import csv

# 公開スプシの CSV URL（等級 → 係数）
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

st.title("家来予想売上計算（基礎値自動計算版）")

# 初期値セット
level = st.number_input("家来等級", min_value=1, value=700)

# 売上は「億」で入力（内部では ×1億 に変換）
sales_oku = st.number_input("現在の売上（億）", min_value=0.0, value=300.0)
current_sales = sales_oku * 100_000_000

# 資質は整数
current_quality = st.number_input("現在の資質", min_value=0, value=50000, step=1)
add_quality = st.number_input("追加する資質", min_value=0, value=0, step=1)

# バフは 0.5 刻み（%入力）
add_buff_percent_input = st.number_input(
    "追加するバフ（%）",
    min_value=0.0,
    value=0.0,
    step=0.5,
    format="%.1f"
)
add_buff_percent = add_buff_percent_input / 100.0

if st.button("計算する"):
    # 等級係数取得
    keys = sorted(coeff_map.keys())
    nearest = max([k for k in keys if k <= level])
    k = coeff_map[nearest]

    # ★ 基礎値を自動計算
    current_base = current_quality * k

    # 現在のバフ推定
    B = current_sales / current_base - 1

    # 新しい基礎値
    new_quality = current_quality + add_quality
    new_base = new_quality * k

    # 新しいバフ
    new_buff = B * (1 + add_buff_percent)

    # 新しい売上
    new_sales = new_base * (1 + new_buff)

    st.subheader("計算結果")
    st.write(f"現在の基礎値：{current_base:,.0f}")
    st.write(f"新しい基礎値：{new_base:,.0f}")
    st.write(f"新しいバフ：{new_buff * 100:.2f}%")
    st.write(f"予想売上：{new_sales:,.0f}")
