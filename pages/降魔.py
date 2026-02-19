# ui/streamlit_app.py
import streamlit as st
import html
from core import kouma_game
import time

st.set_page_config(layout="wide", page_title="Kouma Simulator (Streamlit)")

def empty_board():
    return [["" for _ in range(7)] for _ in range(7)]

if "board" not in st.session_state:
    st.session_state.board = empty_board()
if "selected" not in st.session_state:
    st.session_state.selected = "P"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.title("Kouma Simulator — Streamlit")

with st.sidebar:
    st.header("パレット")
    palette = [
        ("P","P"),("R","R"),("B","B"),("G","G"),("Y","Y"),
        ("B5","B5"),("X","X"),("T_R5","T_R5"),("T_B5","T_B5"),
        ("T_G5","T_G5"),("T_Y5","T_Y5"),("C","C")
    ]
    for key,label in palette:
        if st.button(label, key=f"pal_{key}"):
            st.session_state.selected = key
    st.markdown("---")
    st.write("選択中:", st.session_state.selected)
    st.markdown("---")
    st.write("実行モード: **memo（固定）**")
    max_steps = st.number_input("max_steps (nomemo 用)", value=200000, step=10000)
    beam_width = st.number_input("beam_width (beam 用)", value=300, step=50)

cols = st.columns(7)
for y in range(7):
    row_cols = st.columns(7)
    for x in range(7):
        key = f"cell_{x}_{y}"
        val = st.session_state.board[y][x]
        label = val if val else "・"
        if row_cols[x].button(label, key=key):
            sel = st.session_state.selected
            if sel == "P":
                for yy in range(7):
                    for xx in range(7):
                        if st.session_state.board[yy][xx] == "P":
                            st.session_state.board[yy][xx] = ""
                st.session_state.board[y][x] = "P"
            else:
                st.session_state.board[y][x] = sel if st.session_state.board[y][x] != sel else ""

st.markdown("---")

if st.button("シミュレーション実行"):
    board_input = st.session_state.board
    boss_counter = [0]
    parsed = []
    for row in board_input:
        parsed_row = []
        for s in row:
            parsed_row.append(kouma_game.parse_cell(s if s else "", boss_counter))
        parsed.append(parsed_row)

    t0 = time.time()
    results, stats = kouma_game.simulate_board(parsed, mode="memo", max_steps=max_steps, beam_width=beam_width)
    t1 = time.time()
    stats["wall_time_ms"] = int((t1 - t0) * 1000)
    st.session_state.last_result = {"paths": results, "stats": stats}

st.sidebar.markdown("---")
st.sidebar.write("注意: beam は UI からは使えません（サーバ版で修正予定）")

if st.session_state.last_result:
    res = st.session_state.last_result
    st.subheader("結果")
    paths = res["paths"]
    stats = res["stats"]
    if not paths:
        st.write("経路が見つかりませんでした。")
    else:
        for i, s in enumerate(paths[:5]):
            moves = s.path
            distance = max(0, len(moves) - 1)
            st.markdown(f"**候補 {i+1}** — 倒したボス数: **{s.boss_killed}**, 経路長: **{distance}**, 最終攻撃力: **{s.attack}**")
        st.markdown("**探索統計**")
        st.write(stats)

        svg_w = 420
        svg_h = 420
        cell_w = svg_w / 7
        cell_h = svg_h / 7

        def board_to_svg(board, path_states):
            svg = []
            svg.append(f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">')
            svg.append(f'<rect width="100%" height="100%" fill="#111"/>')
            for i in range(8):
                x = i * cell_w
                y = i * cell_h
                svg.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{svg_h}" stroke="#333" stroke-width="1"/>')
                svg.append(f'<line x1="0" y1="{y}" x2="{svg_w}" y2="{y}" stroke="#333" stroke-width="1"/>')
            for y in range(7):
                for x in range(7):
                    cx = x * cell_w + cell_w/2
                    cy = y * cell_h + cell_h/2
                    val = st.session_state.board[y][x]
                    if val == "P":
                        svg.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="18" fill="#fff" font-weight="bold">P</text>')
                    elif val and val.startswith("B"):
                        svg.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="18" fill="#ffd54f" font-weight="bold">{html.escape(val[1:])}</text>')
                    elif val in ["R","G","B","Y"]:
                        color_map = {"R":"#ef5350","G":"#66bb6a","B":"#42a5f5","Y":"#ffd54f"}
                        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{cell_w*0.12}" fill="{color_map[val]}"/>')
                    elif val and val.startswith("T_"):
                        color = val[2]
                        color_map = {"R":"#ef5350","G":"#66bb6a","B":"#42a5f5","Y":"#ffd54f"}
                        svg.append(f'<rect x="{cx-8}" y="{cy-8}" width="16" height="16" fill="{color_map.get(color,\"#999\")}" />')
                    elif val == "X":
                        svg.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="18" fill="#fff">×</text>')
            first = path_states[0].path
            if len(first) > 1:
                points = []
                for (x,y) in first:
                    px = x * cell_w + cell_w/2
                    py = y * cell_h + cell_h/2
                    points.append(f"{px},{py}")
                points_str = " ".join(points)
                svg.append(f'<polyline points="{points_str}" fill="none" stroke="yellow" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/>')
                for (x,y) in first:
                    px = x * cell_w + cell_w/2
                    py = y * cell_h + cell_h/2
                    svg.append(f'<circle cx="{px}" cy="{py}" r="4" fill="#fff" />')
            svg.append('</svg>')
            return "\n".join(svg)

        svg_html = board_to_svg(st.session_state.board, paths)
        st.components.v1.html(svg_html, height=svg_h+10)
