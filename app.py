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
    "a","an","the","and","or","but","if","in","on","at","to",
    "for","of","with","by","from","up","about","into","through",
    "is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should",
    "may","might","shall","can",
    "i","me","my","we","our","you","your","he","she","it",
    "they","them","their","this","that","these","those",
    "not","no","so","as","than","then","also","just","more",
    "s","t","re","ve","ll"
}

st.set_page_config(page_title="Word Frequency Analyzer", layout="wide")

# ================= FUNCTIONS =================

def extract_text_txt(b):
    try:
        return b.decode("utf-8")
    except:
        return b.decode("latin-1")

def extract_text_docx(b):
    doc = Document(io.BytesIO(b))
    return "\n".join(p.text for p in doc.paragraphs)

def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())

def count_words(tokens, stopwords, min_len):
    filtered = [w for w in tokens if w not in stopwords and len(w) >= min_len]
    counter = collections.Counter(filtered)
    return pd.DataFrame(counter.most_common(), columns=["Word","Freq"])

def plot_chart(df, top_n, color, chart_type, theme):

    data = df.head(top_n)

    if theme == "Dark":
        bg = "#111111"
        fg = "white"
        grid = "#333333"
    else:
        bg = "white"
        fg = "black"
        grid = "#dddddd"

    fig, ax = plt.subplots(figsize=(10,6))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    if chart_type == "Horizontal Bar":
        data = data.iloc[::-1]
        ax.barh(data["Word"], data["Freq"], color=color)

    elif chart_type == "Vertical Bar":
        ax.bar(data["Word"], data["Freq"], color=color)
        plt.xticks(rotation=60)

    elif chart_type == "Pie":
        ax.pie(data["Freq"], labels=data["Word"], autopct="%1.1f%%",
               textprops={"color": fg})

    elif chart_type == "Line":
        ax.plot(data["Word"], data["Freq"], marker="o", color=color)
        plt.xticks(rotation=60)

    elif chart_type == "Area":
        ax.fill_between(data["Word"], data["Freq"], alpha=0.4, color=color)
        plt.xticks(rotation=60)

    elif chart_type == "Histogram":
        ax.hist(df["Freq"], bins=20, color=color)

    ax.set_title(f"Top {top_n} Word Visualization", color=fg)
    ax.tick_params(colors=fg)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(color=grid, linestyle="--", alpha=0.5)

    plt.tight_layout()
    return fig


# ================= SIDEBAR =================

with st.sidebar:
    st.header("Settings")

    theme = st.selectbox("Theme", ["Dark","Light"])

    top_n = st.slider("Top N",5,50,20)
    min_len = st.slider("Min word length",1,6,2)
    color = st.color_picker("Chart color","#f4b942")

    chart_type = st.selectbox(
        "Chart type",
        [
            "Horizontal Bar",
            "Vertical Bar",
            "Pie",
            "Line",
            "Area",
            "Histogram"
        ]
    )

    extra = st.text_area("Extra stopwords")
    stopwords = DEFAULT_STOPWORDS | set(extra.lower().split())

# ================= UI =================

st.title("📖 Word Frequency Analyzer")

file = st.file_uploader("Upload .txt or .docx")

if file:

    bytes_data = file.read()
    ext = file.name.split(".")[-1].lower()

    if ext == "txt":
        text = extract_text_txt(bytes_data)
    else:
        text = extract_text_docx(bytes_data)

    tokens = tokenize(text)
    df = count_words(tokens, stopwords, min_len)

    c1,c2 = st.columns(2)
    c1.metric("Total tokens", len(tokens))
    c2.metric("Unique words", len(df))

    fig = plot_chart(df, top_n, color, chart_type, theme)
    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(df.head(top_n), use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download CSV", csv, "word_freq.csv")
