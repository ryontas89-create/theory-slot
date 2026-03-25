import streamlit as st
import fitz  # PyMuPDF
import random
import base64

st.set_page_config(page_title="PDF理論スロット", layout="wide")

# --- 全画面化の魔法 ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 0rem; padding-right: 0rem; }
        header { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 状態の記憶 ---
if 'page_num' not in st.session_state:
    st.session_state.page_num = 0
if 'random_seed' not in st.session_state:
    st.session_state.random_seed = random.randint(0, 10000)

# --- 設定エリア ---
with st.expander("⚙️ 設定 ＆ PDFアップロード", expanded=True):
    prob = st.slider("ページ内の文字を隠す割合 (%)", 0, 100, 30) / 100
    st.caption("※スライダーを動かすと、PDF内のテキストのカタマリが自動で隠れます。")
    uploaded_file = st.file_uploader("理論マスターのPDFを選択してください", type="pdf")

# --- メイン表示エリア ---
if uploaded_file is not None:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    # --- ナビゲーション ---
    col_prev, col_page, col_shuffle, col_next = st.columns([2, 2, 2, 2])
    with col_prev:
        if st.button("◀️ 前へ", use_container_width=True):
            if st.session_state.page_num > 0:
                st.session_state.page_num -= 1
                st.session_state.random_seed = random.randint(0, 10000)
    with col_page:
        st.markdown(f"<h4 style='text-align: center; margin-top: 0px;'>{st.session_state.page_num + 1} / {total_pages}</h4>", unsafe_allow_html=True)
    with col_shuffle:
        if st.button("🔀 シャッフル", use_container_width=True):
            st.session_state.random_seed = random.randint(0, 10000)
    with col_next:
        if st.button("次へ ▶️", use_container_width=True):
            if st.session_state.page_num < total_pages - 1:
                st.session_state.page_num += 1
                st.session_state.random_seed = random.randint(0, 10000)

    random.seed(st.session_state.random_seed)

    page = doc[st.session_state.page_num]
    
    # 1. PDFを画像化（背景用）
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_base64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
    
    # 2. PDFが内部で持っている「文字のカタマリ（座標つき）」を直接取得
    words = page.get_text("words")
    
    candidate_words = []
    for w in words:
        text = w[4].strip()
        # カンマや数字1文字だけが隠れるのを防ぐため、2文字以上のカタマリを抽出
        if len(text) >= 2 and not text.isnumeric():
            candidate_words.append(w)
    
    # スライダーの確率でランダムに抽出
    num_to_hide = int(len(candidate_words) * prob)
    words_to_hide = random.sample(candidate_words, min(num_to_hide, len(candidate_words))) if num_to_hide > 0 else []

    page_width = page.rect.width
    page_height = page.rect.height

    # 3. HTMLの組み立て
    html_content = f"""
    <div style="position: relative; width: 100%; display: inline-block;">
        <img src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    """

    for w in words_to_hide:
        # PDFからの正確な座標データ
        x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
        
        # スマホ画面に合わせるためパーセンテージに変換
        left_pct = (x0 / page_width) * 100
        top_pct = (y0 / page_height) * 100
        width_pct = ((x1 - x0) / page_width) * 100
        height_pct = ((y1 - y0) / page_height) * 100

        # 黒塗りの箱（タップでフワッと透明になる魔法付き）
        html_content += f"""
        <div style="
            position: absolute;
            left: {left_pct - 0.5}%;
            top: {top_pct - 0.5}%;
            width: {width_pct + 1}%;
            height: {height_pct + 1}%;
            background-color: #2c3e50; /* 少しオシャレな濃いグレー */
            border-radius: 3px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.4); /* 立体感を出して押しやすく */
            cursor: pointer;
            transition: opacity 0.2s ease-out;
        " onclick="this.style.opacity='0'"></div>
        """

    html_content += "</div>"
    
    # 画面に描画
    st.markdown(html_content, unsafe_allow_html=True)
    
    # もし表紙などで隠す文字がゼロだった場合のメッセージ
    if len(words_to_hide) == 0:
        st.info("💡 このページには隠す文字がありません。「次へ」で本文のページに進んでみてください。")
        
    doc.close()
