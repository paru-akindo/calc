import streamlit as st
import pandas as pd
import glob

st.title("南海対戦")

# --- CSS（スマホ対応：名前欄を細く固定） ---
st.markdown("""
<style>
.small-selectbox > div > div {
    width: 150px !important;
}
</style>
""", unsafe_allow_html=True)

# --- 商会一覧を取得 ---
guild_files = sorted(glob.glob("data/*.csv"))
guild_names = [f.split("/")[-1].replace(".csv", "") for f in guild_files]

# --- 商会選択 ---
selected_guild = st.selectbox("商会を選択", guild_names)
df = pd.read_csv(f"data/{selected_guild}.csv")

st.subheader("今回出てきた敵を入力")

# --- 横並びで敵入力 ---
def enemy_input(label):
    col1, col2 = st.columns([1, 1])
    with col1:
        name = st.selectbox(
            f"{label}：商会員名",
            df["商会員名"],
            key=f"name_{label}"
        )
        st.markdown('<div class="small-selectbox"></div>', unsafe_allow_html=True)
    with col2:
        attr = st.selectbox(
            f"{label}：属性",
            ["士", "農", "工", "商", "侠"],
            key=f"attr_{label}"
        )
    return name, attr

enemy1 = enemy_input("敵1")
enemy2 = enemy_input("敵2")
enemy3 = enemy_input("敵3")

# --- スコア計算 ---
def calc_score(name, attr):
    row = df[df["商会員名"] == name].iloc[0]
    attr_power = row[attr]
    total_power = row[["士", "農", "工", "商", "侠"]].sum()
    score = attr_power + total_power * 0.3
    return attr_power, total_power, score

# --- 色付け関数（matplotlib 不要） ---
def color_score(val):
    min_v = df_show["スコア"].min()
    max_v = df_show["スコア"].max()
    ratio = (val - min_v) / (max_v - min_v + 1e-9)
    r = int(255 * ratio)
    g = int(255 * (1 - ratio))
    b = 100
    return f"background-color: rgb({r},{g},{b}); color: white;"

# --- 判定ボタン ---
if st.button("どれを倒す？"):
    candidates = []
    for name, attr in [enemy1, enemy2, enemy3]:
        attr_power, total_power, score = calc_score(name, attr)
        candidates.append({
            "商会員名": name,
            "属性": attr,
            "属性強さ": attr_power,
            "総合強さ": total_power,
            "スコア": score
        })

    df_show = pd.DataFrame(candidates)
    
    # --- CSS ベースの色付け ---
    styled = (
        df_show.style
        .applymap(color_score, subset=["スコア"])
        .format({
            "属性強さ": "{:.0f}",
            "総合強さ": "{:.0f}",
            "スコア": "{:.0f}"
        })
    )

    st.subheader("候補の比較")
    st.dataframe(styled, use_container_width=True)

    # --- 最適な敵 ---
    best = min(candidates, key=lambda x: x["スコア"])
    st.success(f"倒すべき敵は **{best['商会員名']}（{best['属性']}）** です！")
