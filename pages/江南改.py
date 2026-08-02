def simulate_until_next_stage(stage, rank, current, buff):
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    stage_list = list(required_training.keys())
    current_stage_index = stage_list.index(stage)

    if current_stage_index + 1 >= len(stage_list):
        return []

    next_stage = stage_list[current_stage_index + 1]

    ranks = sorted(required_training[stage].keys(), reverse=True)
    start_index = ranks.index(rank)

    target_steps = []

    # ★ 修正：学士1のときは現在段位をタイトルに含めない
    if not (stage == "学士" and rank == 1):
        for r in ranks[start_index:]:
            if required_training[stage][r] > 0:
                target_steps.append((stage, r))

    # 次の境地の最初の段位（元ソース通り）
    next_stage_ranks = sorted(
        [r for r, v in required_training[next_stage].items() if v > 0],
        reverse=True
    )
    next_stage_first_rank = next_stage_ranks[0]
    target_steps.append((next_stage, next_stage_first_rank))

    steps = []
    current_time = now
    current_value = current

    for stg, rnk in target_steps:
        base_speed = training_speeds[stg][rnk]
        required = required_training[stg][rnk]
        remaining = max(0, required - current_value)

        t, _, _ = simulate_time(remaining, base_speed, buff)
        reach_time = current_time + timedelta(seconds=t)

        steps.append({
            "stage": stg,
            "rank": rnk,
            "reach_time": reach_time.strftime("%Y-%m-%d %H:%M")
        })

        current_time = reach_time
        current_value = 0

    return steps
