def simulate_until_next_stage(stage, rank, current, buff):
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    stage_list = list(required_training.keys())
    current_stage_index = stage_list.index(stage)
    next_stage = stage_list[current_stage_index + 1]

    # 計算用：自分の境地の「自分から下」だけ
    ranks = sorted(required_training[stage].keys(), reverse=True)
    start_index = ranks.index(rank)
    calc_steps = [(stage, r) for r in ranks[start_index:]]  # ← 翰林は入れない

    # タイトル用：計算段位を1つ後ろにずらす
    display_steps = []
    for i in range(len(calc_steps)):
        if i < len(calc_steps) - 1:
            # 1つ後ろの段位をタイトルにする
            stg_disp, rnk_disp = calc_steps[i + 1]
        else:
            # 最後だけ次境地の最初の段位
            next_stage_ranks = sorted(
                [r for r, v in required_training[next_stage].items() if v > 0],
                reverse=True
            )
            stg_disp, rnk_disp = next_stage, next_stage_ranks[0]

        # 計算は calc_steps[i] を使う
        stg_calc, rnk_calc = calc_steps[i]
        base_speed = training_speeds[stg_calc][rnk_calc]
        required = required_training[stg_calc][rnk_calc]
        remaining = max(0, required - current)

        t, _, _ = simulate_time(remaining, base_speed, buff)
        reach_time = now + timedelta(seconds=t)

        display_steps.append({
            "stage": stg_disp,
            "rank": rnk_disp,
            "reach_time": reach_time.strftime("%Y-%m-%d %H:%M")
        })

        now = reach_time
        current = 0

    return display_steps
