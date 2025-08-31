import streamlit as st

def calculate_rescue(
    silver_count: int,
    gold_count: int,
    express_count: int
):
    """
    銀の馬符、金の馬符、急行令の数から、
    - 最大ポイント
    - 使用した急行令枚数
    - 使用した各アイテム数
    - 残りアイテム数
    を計算して返す。
    """
    # 金の馬符を優先使用
    max_gold_use = min(gold_count, express_count // 4)
    remaining_express = express_count - max_gold_use * 4

    # 次に銀の馬符を使用
    max_silver_use = min(silver_count, remaining_express // 4)
    used_express = max_gold_use * 4 + max_silver_use * 4

    # 得点計算
    total_points = max_gold_use * 40_000 + max_silver_use * 5_000

    # 残りアイテム
    rem_gold = gold_count - max_gold_use
    rem_silver = silver_count - max_silver_use
    rem_express = express_count - used_express

    return {
        "gold_used": max_gold_use,
        "silver_used": max_silver_use,
        "express_used": used_express,
        "total_points": total_points,
        "rem_gold": rem_gold,
        "rem_silver": rem_silver,
        "rem_express": rem_express
    }

def main():
    st.title("護送計算")

    # 入力
    silver = st.number_input("銀の馬符の数", min_value=0, step=1, value=0)
    gold   = st.number_input("金の馬符の数", min_value=0, step=1, value=0)
    express = st.number_input("急行令の数", min_value=0, step=1, value=0)

    if st.button("計算する"):
        result = calculate_rescue(silver, gold, express)

        st.markdown("---")
        st.write(f"• 使用した急行令：**{result['express_used']}** 枚")
        st.write(f"• 金の馬符 使用数：**{result['gold_used']}** 枚")
        st.write(f"• 銀の馬符 使用数：**{result['silver_used']}** 枚")
        st.success(f"最大獲得点数：**{result['total_points']}** 点")

        st.markdown("**残りアイテム**")
        st.write(f"- 金の馬符：{result['rem_gold']} 枚")
        st.write(f"- 銀の馬符：{result['rem_silver']} 枚")
        st.write(f"- 急行令：{result['rem_express']} 枚")

if __name__ == "__main__":
    main()
