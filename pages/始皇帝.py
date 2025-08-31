import streamlit as st
import pandas as pd

@st.cache_data(ttl=300)
def load_tables():
    # 公開シートのCSVエクスポートURL（gidはシートID）
    csv_url = (
        "https://docs.google.com/spreadsheets/d/e/"
        "2PACX-1vTFOIQtAvilcjBplaklTqvDLg5KAYA8jkU9wL8pBEnQurFp9m62Z4rqbTGWPar0Y4keCqYSjm5qTM2t"
        "/pub?gid=236779120&single=true&output=csv"
    )

    # —— 表1: A1:J31 ——
    # 1行目をヘッダーに、データは2～31行目（30行分）、列はA～J
    df1 = pd.read_csv(
        csv_url,
        header=0,
        nrows=31,
        usecols=range(0, 10)
    )

    # —— 表2: B33:C35 ——
    # ヘッダーなしで33～35行目（3行分）、列はB,C
    df2 = pd.read_csv(
        csv_url,
        header=None,
        skiprows=32,
        nrows=3,
        usecols=[1, 2]
    )
    # 読み込んだあとに列名をつける
    df2.columns = ["商会", "合計値"]

    return df1, df2

# データ読み込み
df1, df2 = load_tables()

# Streamlit レイアウト設定
st.set_page_config(page_title="Spreadsheet Preview", layout="wide")

# 表示①：商会別合計（B33:C35）
st.title("商会別合計")
st.dataframe(df2, hide_index=True, use_container_width=True)

# 表示②：各階層（A1:J31）
st.title("各階層")
st.dataframe(df1, use_container_width=True)
