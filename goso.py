import streamlit as st

def calculate_max_points(silver_count: int, gold_count: int, express_count: int):
    """
    銀の馬符、金の馬符、急行令の数から最大ポイントを算出。
    金の馬符を優先的に使い、残りで銀の馬符を消費するグリーディ戦略を採用。
    """
    # 金の馬符の最大使用数
    max_gold_use = min(gold_count, express_count // 4)
    # 残った急行令で銀の馬符使用
    remaining_express = express_count - 4 * max_gold_use
    max_silver_use = min(silver_count, remaining_express // 4)
    # 獲得点数
    total_points = max_gold_use * 40000 + max_silver_use * 5000
    return max_silver_use, max_gold_use, total_points

def main():
    st.title("護送計算")

    # ユーザー入力
    silver = st.number_input("銀の馬符の数", min_value=0, step=1, value=0)
    gold = st.number_input("金の馬符の数", min_value=0, step=1, value=0)
    express = st.number_input("急行令の数", min_value=0, step=1, value=0)

    # ボタンを押したときに計算
    if st.button("最大ポイントを計算"):
        silver_use, gold_use, points = calculate_max_points(silver, gold, express)

        st.markdown("---")
        st.write(f"• 金の馬符 使用数：**{gold_use}** 個")
        st.write(f"• 銀の馬符 使用数：**{silver_use}** 個")
        st.success(f"最大獲得点数：**{points}** 点")

if __name__ == "__main__":
    main()
