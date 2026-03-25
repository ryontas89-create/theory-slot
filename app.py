import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
import random
import base64

st.set_page_config(page_title="PDF理論スロット", layout="wide")

# --- 全画面化 ---
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
    st.caption("※アップロード後、「次へ」ボタンで文字が多いページに進んでください。")
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
                st.rerun()
    with col_page:
        st.markdown(f"<h4 style='text-align: center; margin-top: 0px;'>{st.session_state.page_num + 1} / {total_pages}</h4>", unsafe_allow_html=True)
    with col_shuffle:
        if st.button("🔀 シャッフル", use_container_width=True):
            st.session_state.random_seed = random.randint(0, 10000)
            st.rerun()
    with col_next:
        if st.button("次へ ▶️", use_container_width=True):
            if st.session_state.page_num < total_pages - 1:
                st.session_state.page_num += 1
                st.session_state.random_seed = random.randint(0, 10000)
                st.rerun()

    random.seed(st.session_state.random_seed)

    # ページ取得
    page = doc[st.session_state.page_num]
    
    # 1. 画像化
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_base64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
    
    # 2. PDFの文字データを直接抽出（絶対にズレない・取りこぼさない）
    words = page.get_text("words")
    candidate_words = []
    for w in words:
        text = w[4].strip()
        # 記号や1文字だけの数字を隠さないようにフィルタリング
        if len(text) >= 2 and not text.isnumeric():
            candidate_words.append(w)
    
    num_to_hide = int(len(candidate_words) * prob)
    words_to_hide = random.sample(candidate_words, min(num_to_hide, len(candidate_words))) if num_to_hide > 0 else []

    page_width = page.rect.width
    page_height = page.rect.height

    # 3. 隔離された専用の箱（iframe）に入れるHTMLを作成
    # ここならStreamlitに邪魔されず、JavaScript（タップ機能）が100%動きます
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ margin: 0; padding: 0; background-color: #fff; }}
        .container {{ position: relative; width: 100%; display: block; }}
        img {{ width: 100%; height: auto; display: block; }}
        .mask {{
            position: absolute;
            background-color: #2c3e50;
            border-radius: 3px;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.4);
            cursor: pointer;
            /* 0.2秒でフワッと消えるアニメーション */
            transition: opacity 0.2s ease-out; 
        }}
    </style>
    <script>
        // タップされたら透明にして、二度とタップ判定しないようにする関数
        function reveal(element) {{
            element.style.opacity = '0';
            element.style.pointerEvents = 'none';
        }}
    </script>
    </head>
    <body>
        <div class="container">
            <img src="data:image/png;base64,{img_base64}">
    """

    for w in words_to_hide:
        left_pct = (w[0] / page_width) * 100
        top_pct = (w[1] / page_height) * 100
        width_pct = ((w[2] - w[0]) / page_width) * 100
        height_pct = ((w[3] - w[1]) / page_height) * 100
        
        # タップで reveal() 関数を呼び出す
        html_content += f'<div class="mask" style="left: {left_pct - 0.5}%; top: {top_pct - 0.5}%; width: {width_pct + 1}%; height: {height_pct + 1}%;" onclick="reveal(this)"></div>'

    html_content += """
        </div>
    </body>
    </html>
    """
    
    # 隔離された箱（iframe）で表示。iPhoneでスクロールしやすいように縦幅を1200に設定。
    components.html(html_content, height=1200, scrolling=True)
    
    if len(words_to_hide) == 0:
        st.info("💡 このページには隠す文字がありません。「次へ」で本文のページに進んでみてください。")
        
    doc.close()
