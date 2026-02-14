import streamlit as st
import pandas as pd
import glob

st.title("商会バトル最適敵選択アプリ")

# --- CSS（スマホ対応：名前欄を細く固定） ---
st.markdown("""
<style>
.small-selectbox > div > div {
    width: 150px !important;  /* ← 名前欄の幅を固定 */
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

# --- 横並びで敵入力（スマホでも崩れにくい） ---
def enemy_input(label):
    col1, col2 = st.columns([1, 1])  # 均等にしておく
    with col1:
        name = st.selectbox(
            f"{label}：商会員名",
            df["商会員名"],
            key=f"name_{label}"
        )
        # 名前欄に幅固定 CSS を適用
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

# --- 判定ボタン ---
if st.button("どれを倒すべき？"):
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

    # --- スコアに色付け（低いほど緑、高いほど赤） ---
    styled = df_show.style.background_gradient(
        subset=["スコア"],
        cmap="RdYlGn_r"
    )

    st.subheader("候補の比較")
    st.dataframe(styled, use_container_width=True)

    # --- 最適な敵 ---
    best = min(candidates, key=lambda x: x["スコア"])
    st.success(f"倒すべき敵は **{best['商会員名']}（{best['属性']}）** です！")
