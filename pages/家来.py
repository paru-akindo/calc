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

st.title("家来予想売上計算")

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
    step=0.1,
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

    # ★ 現在のバフ（内部は実数）
    B_now = current_sales / current_base - 1

    # ★ 新しい基礎値
    new_quality = current_quality + add_quality
    new_base = new_quality * k

    # ★ 新しいバフ（内部は実数・丸めない）
    B_new = B_now + add_buff_percent

    # ★ 売上計算（内部は実数）
    new_sales = new_base * (1 + B_new)

    # ★ 表示用フォーマット（億・有効数字4桁）
    def to_oku(x):
        return f"{x/100_000_000:,.4g}"

    # ★ バフは表示時だけ整数丸め
    current_buff_percent = round(B_now * 100)
    new_buff_percent = round(B_new * 100)

    # ★ 表データ
    table = {
        "項目": ["売上（億）", "基礎値（億）", "バフ（%）"],
        "現在": [
            to_oku(current_sales),
            to_oku(current_base),
            f"{current_buff_percent}"
        ],
        "予想": [
            to_oku(new_sales),
            to_oku(new_base),
            f"{new_buff_percent}"
        ]
    }

    st.subheader("結果比較表")
    st.table(table)
