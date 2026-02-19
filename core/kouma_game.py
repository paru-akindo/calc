# core/kouma_game.py
from enum import Enum
from typing import Optional, List, Tuple
import time
import heapq
import random

random.seed(0)
ZOBRIST = [[random.getrandbits(64) for _ in range(7)] for _ in range(7)]

def zobrist_hash(visited_mask: int) -> int:
    h = 0
    for y in range(7):
        for x in range(7):
            if visited_mask & (1 << (y * 7 + x)):
                h ^= ZOBRIST[y][x]
    return h

class CellType(Enum):
    EMPTY = 0
    OBSTACLE = 1
    PLAYER = 2
    ZAKO = 3
    TREASURE = 4
    BOSS = 5
    CRYSTAL = 6

class Cell:
    def __init__(self, type: CellType, color: Optional[str], hp: int, boss_index=None):
        self.type = type
        self.color = color
        self.hp = hp
        self.boss_index = boss_index

class State:
    def __init__(self, x, y, attack, lock_color, boss_hp, visited, path, boss_killed):
        self.x = x
        self.y = y
        self.attack = attack
        self.lock_color = lock_color
        self.boss_hp = boss_hp
        self.visited = visited
        self.path = path
        self.boss_killed = boss_killed

def bit(x, y):
    return 1 << (y * 7 + x)

directions = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1)
]

def valid(x, y):
    return 0 <= x < 7 and 0 <= y < 7

def parse_cell(s: str, boss_counter: List[int]) -> Cell:
    if s == "P":
        return Cell(CellType.PLAYER, None, 0)
    if s in ["R", "G", "B", "Y"]:
        return Cell(CellType.ZAKO, s, 0)
    if s.startswith("T_"):
        color = s[2]
        hp = int(s[3:]) if len(s) > 3 else 1
        return Cell(CellType.TREASURE, color, hp)
    if s.startswith("B"):
        hp = int(s[1:]) if len(s) > 1 else 1
        idx = boss_counter[0]
        boss_counter[0] += 1
        return Cell(CellType.BOSS, None, hp, boss_index=idx)
    if s == "C":
        return Cell(CellType.CRYSTAL, None, 0)
    if s == "X":
        return Cell(CellType.OBSTACLE, None, 0)
    return Cell(CellType.EMPTY, None, 0)

def try_move(state: State, cell: Cell, nx: int, ny: int) -> Optional[State]:
    if state.visited & bit(nx, ny):
        return None

    attack = state.attack
    lock = state.lock_color
    boss_hp = list(state.boss_hp)
    boss_killed = state.boss_killed

    if cell.type == CellType.OBSTACLE:
        return None

    elif cell.type == CellType.EMPTY:
        attack += 1

    elif cell.type == CellType.ZAKO:
        color = cell.color
        if lock is None:
            lock = color
        elif lock != color:
            return None
        attack += 1

    elif cell.type == CellType.TREASURE:
        color = cell.color
        if lock is None:
            lock = color
        elif lock != color:
            return None
        if attack < cell.hp:
            return None
        attack = attack - cell.hp + 1

    elif cell.type == CellType.BOSS:
        if attack < cell.hp:
            return None
        attack = attack - cell.hp + 1
        lock = None
        idx = cell.boss_index
        if boss_hp[idx] > 0:
            boss_hp[idx] = 0
            boss_killed += 1

    elif cell.type == CellType.CRYSTAL:
        attack += 1
        lock = None

    new_visited = state.visited | bit(nx, ny)

    return State(
        x=nx,
        y=ny,
        attack=attack,
        lock_color=lock,
        boss_hp=tuple(boss_hp),
        visited=new_visited,
        path=state.path + [(nx, ny)],
        boss_killed=boss_killed
    )

def update_best(best: List[State], state: State):
    if not best:
        best.append(state)
        return
    b = best[0]
    if state.boss_killed > b.boss_killed:
        best.clear()
        best.append(state)
    elif state.boss_killed == b.boss_killed:
        if len(state.path) > len(b.path):
            best.clear()
            best.append(state)
        elif len(state.path) == len(b.path):
            best.append(state)

def memo_key(state: State):
    return (state.x, state.y, state.lock_color, state.boss_hp, zobrist_hash(state.visited))

def dfs_with_memo(state: State, board, best, memo, max_steps=200000):
    stack = [state]
    steps = 0
    while stack:
        cur = stack.pop()
        steps += 1
        if steps > max_steps:
            break
        key = memo_key(cur)
        prev = memo.get(key)
        if prev is not None:
            prev_attack, prev_boss_killed = prev
            if prev_attack >= cur.attack and prev_boss_killed >= cur.boss_killed:
                continue
        memo[key] = (cur.attack, cur.boss_killed)
        update_best(best, cur)
        for dx, dy in directions:
            nx, ny = cur.x + dx, cur.y + dy
            if not valid(nx, ny):
                continue
            cell = board[ny][nx]
            next_state = try_move(cur, cell, nx, ny)
            if next_state is None:
                continue
            stack.append(next_state)

def dfs_no_memo(state: State, board, best, counters, max_steps=500000):
    if counters["nodes"] >= max_steps:
        return
    counters["nodes"] += 1
    update_best(best, state)
    for dx, dy in directions:
        nx, ny = state.x + dx, state.y + dy
        if not valid(nx, ny):
            continue
        cell = board[ny][nx]
        next_state = try_move(state, cell, nx, ny)
        if next_state is None:
            continue
        dfs_no_memo(next_state, board, best, counters, max_steps)

def beam_search(initial: State, board, beam_width=200, max_steps=200000):
    pq = [(-initial.boss_killed, -len(initial.path), -initial.attack, initial)]
    memo = {}
    best = []
    steps = 0
    while pq and steps < max_steps:
        layer = []
        for _ in range(min(len(pq), beam_width)):
            layer.append(heapq.heappop(pq))
        next_candidates = []
        for _, _, _, state in layer:
            update_best(best, state)
            for dx, dy in directions:
                nx, ny = state.x + dx, state.y + dy
                if not valid(nx, ny):
                    continue
                cell = board[ny][nx]
                next_state = try_move(state, cell, nx, ny)
                if next_state is None:
                    continue
                key = memo_key(next_state)
                prev = memo.get(key)
                if prev is not None:
                    prev_attack, prev_boss_killed = prev
                    if prev_attack >= next_state.attack and prev_boss_killed >= next_state.boss_killed:
                        continue
                memo[key] = (next_state.attack, next_state.boss_killed)
                heapq.heappush(next_candidates, (-next_state.boss_killed, -len(next_state.path), -next_state.attack, next_state))
                steps += 1
                if steps >= max_steps:
                    break
            if steps >= max_steps:
                break
        pq = heapq.nsmallest(beam_width, next_candidates)
    return best

def simulate_board(board, mode="memo", max_steps=200000, beam_width=300):
    start_x = start_y = None
    boss_hp = []
    for y in range(7):
        for x in range(7):
            cell = board[y][x]
            if cell.type == CellType.BOSS:
                boss_hp.append(cell.hp)
            if cell.type == CellType.PLAYER:
                start_x, start_y = x, y

    initial = State(
        x=start_x,
        y=start_y,
        attack=0,
        lock_color=None,
        boss_hp=tuple(boss_hp),
        visited=bit(start_x, start_y),
        path=[(start_x, start_y)],
        boss_killed=0
    )

    best = []
    stats = {"search_time_ms": 0, "nodes_visited": 0}
    t0 = time.time()

    if mode == "nomemo":
        counters = {"nodes": 0}
        dfs_no_memo(initial, board, best, counters, max_steps=max_steps)
        stats["nodes_visited"] = counters["nodes"]
    elif mode == "beam":
        best = beam_search(initial, board, beam_width=beam_width, max_steps=max_steps)
        stats["nodes_visited"] = -1
    else:
        memo = {}
        dfs_with_memo(initial, board, best, memo, max_steps=max_steps)
        stats["nodes_visited"] = len(memo)

    t1 = time.time()
    stats["search_time_ms"] = int((t1 - t0) * 1000)
    return best, stats
