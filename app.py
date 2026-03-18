import re
import io
import collections
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

try:
    from docx import Document
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    from docx import Document


DEFAULT_STOPWORDS = {
    "a","an","the","and","or","but","if","in","on","at","to","for","of",
    "with","by","from","up","about","into","through","is","are","was",
    "were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","shall","can",
    "i","me","my","we","our","you","your","he","she","it","they",
    "them","their","this","that","these","those","not","no","so",
    "as","than","then","also","just","more","s","t","re","ve","ll"
}

st.set_page_config(
    page_title="Word Frequency Analyzer",
    layout="wide"
)

# ====================== FUNCTIONS ======================

def extract_text_from_txt(file_bytes):
    try:
        return file_bytes.decode("utf-8")
    except:
        return file_bytes.decode("latin-1")

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_generic(uploaded):
    bytes_data = uploaded.read()
    ext = uploaded.name.split(".")[-1].lower()
    if ext == "txt":
        return extract_text_from_txt(bytes_data)
    if ext == "docx":
        return extract_text_from_docx(bytes_data)
    return ""

def tokenize(text):
    text = text.lower()
    return re.findall(r"[a-z]+", text)

def count_words(tokens, stopwords, min_len):
    filtered = [w for w in tokens if w not in stopwords and len(w) >= min_len]
    counter = collections.Counter(filtered)
    df = pd.DataFrame(counter.most_common(), columns=["คำ","จำนวนครั้ง"])
    return df

def plot_chart(df, top_n, color):
    data = df.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10,6))
    ax.barh(data["คำ"], data["จำนวนครั้ง"], color=color)
    ax.set_title(f"Top {top_n} Words")
    return fig

def build_compare(df_src, df_trg):
    merged = pd.merge(
        df_src,
        df_trg,
        on="คำ",
        how="outer",
        suffixes=("_ต้นฉบับ","_แปล")
    ).fillna(0)

    merged["diff"] = merged["จำนวนครั้ง_แปล"] - merged["จำนวนครั้ง_ต้นฉบับ"]
    merged = merged.sort_values("diff", ascending=False)
    return merged

def lexical_div(tokens, df):
    if len(tokens) == 0:
        return 0
    return len(df)/len(tokens)


# ====================== SIDEBAR ======================

with st.sidebar:
    st.header("Settings")
    top_n = st.slider("Top N",5,50,20)
    min_len = st.slider("Min word length",1,6,2)
    color = st.color_picker("Chart color","#f4b942")

    extra = st.text_area("Extra stopwords")
    extra_sw = set(extra.lower().split())
    stopwords = DEFAULT_STOPWORDS | extra_sw


# ====================== HEADER ======================

st.title("📖 Word Frequency Analyzer")
st.caption("Tool for translators & linguistic analysis")

# ====================== COMPARE MODE ======================

st.divider()
st.header("🔬 Compare Translation")

c1, c2 = st.columns(2)

with c1:
    src_file = st.file_uploader("Upload SOURCE", type=["txt","docx"], key="src")

with c2:
    trg_file = st.file_uploader("Upload TRANSLATION", type=["txt","docx"], key="trg")

if src_file and trg_file:

    raw_src = extract_text_generic(src_file)
    raw_trg = extract_text_generic(trg_file)

    tok_src = tokenize(raw_src)
    tok_trg = tokenize(raw_trg)

    df_src = count_words(tok_src, stopwords, min_len)
    df_trg = count_words(tok_trg, stopwords, min_len)

    cmp_df = build_compare(df_src, df_trg)

    st.subheader("Translation Metrics")

    ratio = len(tok_trg)/len(tok_src) if len(tok_src)>0 else 0
    lex_src = lexical_div(tok_src, df_src)
    lex_trg = lexical_div(tok_trg, df_trg)

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Source words", len(tok_src))
    m2.metric("Translated words", len(tok_trg))
    m3.metric("Expansion Ratio", f"{ratio:.2f}")
    m4.metric("Lexical richness Δ", f"{lex_trg-lex_src:.3f}")

    st.subheader("Words Over-used in Translation")
    st.dataframe(cmp_df.head(top_n), use_container_width=True)

    st.subheader("Words Reduced / Missing")
    st.dataframe(cmp_df.tail(top_n).sort_values("diff"), use_container_width=True)

    csv = cmp_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download Compare CSV", csv, "compare.csv")


# ====================== SINGLE FILE MODE ======================

st.divider()
st.header("📂 Analyze Single Document")

file = st.file_uploader("Upload file", type=["txt","docx"], key="single")

if file:

    raw = extract_text_generic(file)
    tokens = tokenize(raw)
    df = count_words(tokens, stopwords, min_len)

    st.metric("Total tokens", len(tokens))
    st.metric("Unique words", len(df))

    fig = plot_chart(df, top_n, color)
    st.pyplot(fig)

    st.dataframe(df.head(top_n), use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download CSV", csv, "freq.csv")
