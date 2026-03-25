import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import random

st.set_page_config(page_title="PDF理論スロット", layout="wide")

st.title("📑 PDF理論スロット")

# --- 1. 暗記の設定 ---
st.header("1. 暗記の設定")
col1, col2 = st.columns([1, 2])

with col1:
    prob = st.slider("穴埋めの割合 (%)", 0, 100, 50) / 100
    
with col2:
    target_words_input = st.text_input(
        "隠したい単語（カンマ区切り）", 
        "納税義務,基準期間,特定期間,1,000万円,免税事業者,課税事業者,国内において"
    )
    target_words = [w.strip() for w in target_words_input.split(",") if w.strip()]

st.write("---")

# --- 2. ファイル読み込み ---
uploaded_file = st.file_uploader("理論マスターのPDFをアップロード", type="pdf")

if uploaded_file is not None:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    # ページ選択
    total_pages = len(doc)
    page_num = st.number_input(f"ページ選択 (全{total_pages}ページ)", min_value=1, max_value=total_pages, value=1) - 1
    
    # ページを画像化
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    draw = ImageDraw.Draw(img)
    
    # 穴埋め処理
    masked_locations = []
    for word in target_words:
        areas = page.search_for(word)
        for rect in areas:
            if random.random() < prob:
                masked_locations.append({"rect": rect, "word": word})
                draw.rectangle([rect.x0*2, rect.y0*2, rect.x1*2, rect.y1*2], fill="black")

    # --- 3. 表示 ---
    st.subheader(f"📖 第 {page_num + 1} ページ")
    st.image(img, use_container_width=True)

    if masked_locations:
        st.write("### 💡 答え合わせ")
        ans_cols = st.columns(3)
        for i, item in enumerate(masked_locations):
            with ans_cols[i % 3].expander(f"穴埋め {i+1}"):
                st.write(f"**{item['word']}**")
    
    doc.close()