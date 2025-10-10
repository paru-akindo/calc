import streamlit as st
import requests
import json
import re
from typing import List, Tuple, Dict

st.set_page_config(page_title="JSONBin 港価格編集", layout="wide")

# ---------- jsonbin 設定 ----------
API_KEY = "$2a$10$wkVzPCcsW64wR96r26OsI.HDd3ijLveJn6sxJoSjfzByIRyODPCHq"
BIN_ID = "68e8924443b1c97be9611391"
BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": API_KEY
}

# ---------- ユーティリティ ----------
def fetch_cfg():
    resp = requests.get(f"{BASE_URL}/latest", headers=HEADERS, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    if isinstance(payload, dict) and "record" in payload:
        return payload["record"]
    return payload

def save_cfg(cfg: dict):
    resp = requests.put(BASE_URL, headers=HEADERS, data=json.dumps(cfg, ensure_ascii=False))
    resp.raise_for_status()
    return resp

def normalize_items(raw_items) -> List[Tuple[str,int]]:
    out = []
    for it in raw_items:
        if isinstance(it, (list, tuple)):
            name, base = it[0], int(it[1])
        elif isinstance(it, dict):
            name, base = it["name"], int(it["base"])
        else:
            raise ValueError("Unknown item format")
        out.append((name, base))
    return out

def port_has_actual_prices_by_diff(port_prices: dict, items: List[Tuple[str,int]], tol: int = 0) -> bool:
    # 欠損や非数値は未入力と見なす
    for name, base in items:
        if name not in port_prices:
            return False
        v = port_prices[name]
        if not isinstance(v, (int, float)):
            return False
    # 全て base に近ければ未入力扱い（False）
    all_close = True
    for name, base in items:
        p = port_prices.get(name)
        if abs(int(round(p)) - int(base)) > tol:
            all_close = False
            break
    return not all_close

def parse_int_strict(s: str):
    s = (s or "").strip()
    if s == "":
        return None
    s = s.replace(",", "")
    s = s.translate(str.maketrans("０１２３４５６７８９－＋．，", "0123456789-+.,"))
    if not re.fullmatch(r"\d+", s):
        return None
    try:
        return int(s)
    except Exception:
        return None

def safe_rerun():
    """st.experimental_rerun が無ければ無視するフォールバック"""
    try:
        rerun_fn = getattr(st, "experimental_rerun")
        rerun_fn()
    except Exception:
        # 無ければ何もしない
        return

# ---------- 初期読み込み ----------
try:
    cfg = fetch_cfg()
except Exception as e:
    st.error(f"jsonbin からの読み込みに失敗しました: {e}")
    st.stop()

if not isinstance(cfg, dict) or "PORTS" not in cfg or "ITEMS" not in cfg:
    st.error("JSON スキーマが不正です。PORTS と ITEMS を含めてください。")
    st.stop()

PORTS = cfg["PORTS"]
ITEMS = normalize_items(cfg["ITEMS"])
PRICES = cfg.get("PRICES", {})

st.title("未更新の港を選んで価格を一括登録")

# サイドバー情報
tol = st.sidebar.number_input("判定の許容差 tol (0=完全一致のみ未更新扱い)", min_value=0, value=0, step=1)
st.sidebar.write("BIN ID:", BIN_ID)
st.sidebar.write("読み込んだ港数:", len(PORTS))
st.sidebar.write("品目数:", len(ITEMS))

# 判定
unpopulated = []
populated = []
for port in PORTS:
    port_prices = PRICES.get(port, {})
    if port_has_actual_prices_by_diff(port_prices, ITEMS, tol=tol):
        populated.append(port)
    else:
        unpopulated.append(port)

st.sidebar.markdown(f"- 未更新の港: **{len(unpopulated)}**")
st.sidebar.markdown(f"- 更新済みの港: **{len(populated)}**")

if not unpopulated:
    st.success("すべての港が入力済みのようです。")
    st.write("必要なら JSON を確認してから終了してください。")
    st.json(cfg)
    st.stop()

selected_port = st.selectbox("未更新の港を選択してください", options=unpopulated)

st.markdown(f"## {selected_port} の価格を入力（整数のみ、空欄は不可）")
current = PRICES.get(selected_port, {})

cols = st.columns(2)
inputs: Dict[str, str] = {}
for i, (name, base) in enumerate(ITEMS):
    c = cols[i % 2]
    default = "" if name not in current else str(current[name])
    with c:
        inputs[name] = st.text_input(f"{name} (base: {base})", value=default, key=f"{selected_port}_{name}")

st.write("---")
col_ok, col_cancel, col_reload = st.columns([1,1,1])

with col_ok:
    if st.button("この港の価格を保存"):
        new_row = {}
        invalids = []
        for name, base in ITEMS:
            raw = inputs.get(name, "")
            v = parse_int_strict(raw)
            if v is None:
                invalids.append(name)
            else:
                if v < 0:
                    invalids.append(name)
                else:
                    new_row[name] = v
        if invalids:
            st.error("以下の品目の入力が不正です（整数で入力してください、空欄不可）: " + ", ".join(invalids))
        else:
            PRICES[selected_port] = new_row
            cfg["PRICES"] = PRICES
            try:
                resp = save_cfg(cfg)
                status = resp.status_code
                resp_json = {}
                try:
                    resp_json = resp.json()
                except Exception:
                    resp_json = {}
                st.success(f"{selected_port} の価格を保存しました。HTTP {status}")
                st.write(resp_json)
                # 入力欄をクリア
                for name, _ in ITEMS:
                    st.session_state.pop(f"{selected_port}_{name}", None)
                # 試みて rerun 実行、無ければ instruct to reload
                try:
                    safe_rerun()
                except Exception:
                    st.info("ページを手動で再読み込みしてください（ブラウザの更新）。")
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")
                st.write("保存後に手動でページを再読み込みして変更を確認してください。")

with col_cancel:
    if st.button("入力をクリア"):
        for name, _ in ITEMS:
            st.session_state.pop(f"{selected_port}_{name}", None)
        # 明示的に再描画（safe_rerun を呼ぶだけ試す）
        safe_rerun()

with col_reload:
    if st.button("最新データを再取得"):
        try:
            cfg = fetch_cfg()
            PRICES = cfg.get("PRICES", {})
            st.success("最新データを取得しました。ページが更新されます。")
            safe_rerun()
        except Exception as e:
            st.error(f"再取得に失敗しました: {e}")

st.markdown("---")
st.write("編集のヒント: すべての品目に整数を入力してから保存してください。保存後、該当港は未更新リストから消えます。")
