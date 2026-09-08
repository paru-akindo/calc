import streamlit as st
import requests
import csv
import math

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

# 有効数字5桁で切り捨て
def sig_floor5(n):
    if n == 0:
        return 0
    digits = math.floor(math.log10(abs(n))) + 1
    scale = 10 ** (digits - 5)
    return math.floor(n / scale) * scale

# 骨データ
bones = [
    {"name": "頭骨", "add_quality": 0,   "add_buff": 0.50},
    {"name": "左腕", "add_quality": 450, "add_buff": 0.20},
    {"name": "右腕", "add_quality": 150, "add_buff": 0.40},
    {"name": "左腿", "add_quality": 600, "add_buff": 0.10},
    {"name": "右腿", "add_quality": 300, "add_buff": 0.30},
    {"name": "体幹", "add_quality": 750, "add_buff": 0.00},
]
common_buff = 0.16

st.title("家来予想売上計算")

# 入力欄
col1, col2 = st.columns(2)
with col1:
    level = st.number_input("家来等級", min_value=1, value=700)
with col2:
    current_quality = st.number_input("現在の資質", min_value=0, value=50000)

sales_oku = st.number_input("現在の売上（億）", min_value=0.0, value=300.0)
current_sales = sales_oku * 100_000_000

col3, col4 = st.columns(2)
with col3:
    add_quality = st.number_input("追加する資質", min_value=0, value=0)
with col4:
    add_buff_percent_input = st.number_input("追加するバフ（%）", min_value=0.0, value=0.0, step=0.1)
add_buff_percent = add_buff_percent_input / 100.0

check_bone = st.checkbox("骨おすすめ調査")

if st.button("計算する"):

    # 等級係数取得
    keys = sorted(coeff_map.keys())
    nearest = max([k for k in keys if k <= level])
    k = coeff_map[nearest]

    # 現在基礎値
    current_base = current_quality * k

    # 現在バフ
    B_now = current_sales / current_base - 1

    # 新しい基礎値
    new_quality = current_quality + add_quality
    new_base = new_quality * k

    # 新しいバフ
    B_new = B_now + add_buff_percent

    # 新しい売上
    new_sales = new_base * (1 + B_new)

    # 有効数字5桁で切り捨て
    final_sales = sig_floor5(new_sales)
    final_sales_oku = final_sales / 1e8

    # 表示用フォーマット
    def to_oku(x):
        return f"{x/100_000_000:,.4g}"

    current_buff_percent = round(B_now * 100)
    new_buff_percent = round(B_new * 100)

    st.subheader("結果比較表")
    st.table({
        "項目": ["売上（億）", "基礎値（億）", "バフ（%）"],
        "現在": [
            to_oku(current_sales),
            to_oku(current_base),
            f"{current_buff_percent}"
        ],
        "予想": [
            to_oku(final_sales),
            to_oku(new_base),
            f"{new_buff_percent}"
        ]
    })

    # 骨おすすめ調査
    if check_bone:
        st.subheader("骨おすすめ調査結果")

        bone_results = []

        for bone in bones:
            total_quality = current_quality + add_quality + bone["add_quality"]
            total_buff = B_now + add_buff_percent + bone["add_buff"] + common_buff

            base2 = total_quality * k
            sales2 = base2 * (1 + total_buff)

            sales2_final = sig_floor5(sales2)
            sales2_oku = sales2_final / 1e8

            bone_results.append({
                "骨": bone["name"],
                "資質増加": bone["add_quality"],
                "バフ増加(%)": int(bone["add_buff"] * 100),
                "総バフ(%)": int(total_buff * 100),
                "売上（億）": sales2_oku,
            })

        bone_results_sorted = sorted(bone_results, key=lambda x: x["売上（億）"], reverse=True)

        best = bone_results_sorted[0]
        st.success(f"最適な骨：{best['骨']}（売上 {best['売上（億）']} 億）")

        st.table(bone_results_sorted)
