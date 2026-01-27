"""
Year-End Party Chatbot - Streamlit Cloud Version
This version is optimized for Streamlit Cloud deployment.
Uses st.secrets instead of .env file.
"""
import streamlit as st
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
import json
from io import BytesIO
from google import genai
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.files.file import File
import os
import time
import random
import html
import re
import base64

# ==================== Page Config ====================
st.set_page_config(
    page_title="Year-End Party Chatbot",
    page_icon="🎉",
    layout="centered"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #1c3c72 50%, #2a5298 100%) !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom input box */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 2px solid rgba(34, 211, 238, 0.5) !important;
        border-radius: 12px !important;
        color: #1e40af !important;
        font-size: 18px !important;
        padding: 16px !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #1e40af !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #fde047 !important;
        box-shadow: 0 0 0 2px rgba(253, 224, 71, 0.5) !important;
    }
    
    /* Custom button */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #fde047 0%, #fef3c7 50%, #fde68a 100%) !important;
        color: #0f2027 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 16px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(253, 224, 71, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 6px 12px rgba(253, 224, 71, 0.8) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #fde047 !important;
        color: #fde047 !important;
    }
    
    /* Alert boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(34, 211, 238, 0.5) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        color: white !important;
    }
    
    /* Animations */
    @keyframes twinkle {
        0%, 100% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.2); }
    }
    
    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .result-container {
        animation: slideUp 0.6s ease-out;
    }
    
    /* Stars background */
    .stars-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    }
    
    .star {
        position: absolute;
        background: #22d3ee;
        border-radius: 50%;
        animation: twinkle 1s infinite;
    }
    
    /* Zodiac wheel container */
    .zodiac-wheel {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
        opacity: 0.5;
        z-index: 0;

        /* Animation di chuyển vòng quanh màn hình */
        animation: float-around 60s linear infinite;
    }

    /* Nội dung bánh xe xoay tại chỗ */
    .zodiac-wheel-inner {
        width: 1000px;
        height: 1000px;
        animation: spin 60s linear infinite; /* xoay lâu hơn để không quá chóng mặt */
        position: relative;
    }

    /* Biểu tượng cung hoàng đạo */
    .zodiac-symbol {
        position: absolute;
        left: 50%;
        top: 50%;
    }

    /* Xoay bánh xe tại chỗ */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Di chuyển vòng quanh màn hình */
    @keyframes float-around {
        0% { transform: translate(-50%, -50%) translateX(0px) translateY(0px); }
        25% { transform: translate(-50%, -50%) translateX(0px) translateY(-0px); }
        50% { transform: translate(-50%, -50%) translateX(0px) translateY(-0px); }
        75% { transform: translate(-50%, -50%) translateX(-0px) translateY(-0px); }
        100% { transform: translate(-50%, -50%) translateX(0px) translateY(0px); }
    }
</style>
""", unsafe_allow_html=True)

# ==================== Background Elements ====================
# Add stars
random.seed(42)
stars_html = '<div class="stars-bg">'
for i in range(50):
    x = random.randint(0, 100)
    y = random.randint(0, 100)
    size = random.randint(2, 4)
    delay = random.uniform(0, 3)
    stars_html += f'<div class="star" style="left:{x}%; top:{y}%; width:{size}px; height:{size}px; animation-delay:{delay}s;"></div>'
stars_html += '</div>'
random.seed()
st.markdown(stars_html, unsafe_allow_html=True)

with open(r"D:\KenIChi\Chatbot\data\images\zodiac_signs\1.svg", "r", encoding="utf-8") as f:
    leo_svg = f.read()

# Add zodiac wheel
import base64
def render_svg(svg_file, width=50, height=50):
    with open(svg_file, "r") as f:
        lines = f.readlines()
    svg = "".join(lines)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}" width="{width}" height="{height}"/>'
    return html

zodiac_symbols = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
zodiac_svg_path = r".\data\images\zodiac_signs"
zodiac_svg_files = [f"{zodiac_svg_path}\\{file}" for file in ["1.svg", "2.svg", "3.svg", "4.svg", "5.svg", "6.svg", "7.svg", "8.svg", "9.svg", "10.svg", "11.svg", "12.svg"]]
zodiac_html = [render_svg(file, width=200, height=200) for file in zodiac_svg_files]
wheel_html = '<div class="zodiac-wheel"><div class="zodiac-wheel-inner">'
for i, symbol in enumerate(zodiac_html):
    angle = i * 30
    wheel_html += f'''<div class="zodiac-symbol" style="transform: translate(-50%, -50%) rotate({angle}deg) translateY(-450px) rotate(-{angle}deg);">
        {symbol}
    </div>'''
wheel_html += '</div></div>'
st.markdown(wheel_html, unsafe_allow_html=True)

def get_secret(key, default=None):
    """Get secret from Streamlit secrets or environment variable"""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# ==================== Functions ====================
@st.cache_resource(show_spinner=False)
def get_ai_model():
    """Initialize AI model (cached)"""
    model = ChatGoogleGenerativeAI(
        model=get_secret("AI_MODEL"),
        api_key=get_secret("GEMINI_API_KEY"),
        temperature=1.0,
        max_output_tokens=2000,
        thinking_level="minimal",
        thinking_budget=0,
        include_thoughts=False,
    )
    return model

@st.cache_resource(show_spinner=False)
def connect_to_sharepoint(refresh_key=0):
    """Connect to SharePoint and download Excel file"""
    site_url = get_secret(
        "SHAREPOINT_SITE_URL",
        "https://mabmotor-my.sharepoint.com/personal/vnm13649_mabuchi-motor_com"
    )
    username = get_secret("MICROSOFT_ACCOUNT")
    password = get_secret("MICROSOFT_PASSWORD")
    file_relative_url = get_secret(
        "SHAREPOINT_FILE_URL",
        "/personal/vnm13649_mabuchi-motor_com/Documents/Microsoft Teams Chat Files/guest_information 1.xlsx"
    )
    
    ctx = ClientContext(site_url).with_credentials(
        UserCredential(username, password)
    )
    
    response = File.open_binary(ctx, file_relative_url)
    file_stream = BytesIO(response.content)
    
    file_stream.seek(0)
    raw = file_stream.getvalue()
    xls = pd.ExcelFile(file_stream)

    df = pd.read_excel(xls, "participants_profile")
    company_context = pd.read_excel(xls, "company_context")
    role_definition = pd.read_excel(xls, "role_definition")
    
    return df, company_context['text'][0], role_definition['text'][0]

@st.cache_resource(show_spinner=False)
def get_participant_by_id(user_id, use_sharepoint=True):
    """Get participant data by ID"""
    try:
        fix_response = None
        text_to_inject = None
        if use_sharepoint:
            df, company_context, role_definition = connect_to_sharepoint(st.session_state.refresh)
        else:
            df = pd.read_excel("data/guest_information.xlsx", sheet_name="participants_profile")
            company_context, role_definition = load_context_files()
            
        if isinstance(user_id, int) or ((isinstance(user_id, str) and user_id.isdigit())):      
            result = df[df["id"] == int(user_id)]
        elif isinstance(user_id, str):
            result = df[df["name"].str.lower().str.strip() == user_id.lower().strip()]
        else:
            st.error("Nhập MSNV hoặc tên hợp lệ!")
            return None
            
        if result.empty:
            st.error("Không tìm thấy người này!")
            return None
        
        data = result.iloc[0].to_dict()
        data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
        
        if "fixed_response" in data:
            fix_response = data["fixed_response"]
            del data["fixed_response"]
        
        if "text_to_inject" in data:
            text_to_inject = data["text_to_inject"]
            del data["text_to_inject"]
        
        return data, company_context, role_definition, fix_response, text_to_inject
        
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {str(e)}")
        return None

@st.cache_data
@st.cache_resource(show_spinner=False)
def load_context_files():
    """Load company context and role definitions"""
    try:         
        with open("data\\company_context.txt", "r", encoding="utf-8") as f:
            company_context = f.read()
    except:
        company_context = ""
    
    try:
        with open("data\\role_definition.txt", "r", encoding="utf-8") as f:
            role_definition = f.read()
    except:
        role_definition = ""
    
    return company_context, role_definition

def generate_response(user_data, model, company_context, role_definition, text_to_inject=None):
    if user_data['nationality'] == 'JP':
        language = "Tiếng Anh"
        user_prompt = "Vì đây là người Nhật, hãy trả lời bằng tiếng Anh một cách tự nhiên và thân thiện dựa vào thông tin của họ:"
    else:
        language = "Tiếng Việt"
        user_prompt = "Đây là thông tin cá nhân của người dùng:"
        
    if text_to_inject:
        text_to_inject = f"\nHãy đảm bảo câu bói của bạn có chứa thông tin sau đây: {text_to_inject}"
    else:
        text_to_inject = ""
        
    system_prompt = f"""Bạn là một chatbot bói toán hài hước, thông minh, nói chuyện lưu loát dùng để giải trí trong buổi tiệc tất niên của công ty.
Bạn sẽ dựa vào thông tin cá nhân của người dùng để đưa ra câu bói ngắn gọn, dễ hiểu, hài hước và thú vị.
Hãy chắc chắn rằng câu bói của bạn liên quan trực tiếp đến thông tin cá nhân của người dùng.
Hãy nhớ rằng câu bói của bạn đưa ra là cho năm 2026 (năm Bính Ngọ) nếu bạn cần tham khảo năm.
Hãy sử dụng ngôn ngữ tự nhiên, thân thiện và gần gũi, xưng hô "Tôi" và "Bạn".
Hãy thêm vài icon lung linh vào câu bói để tăng độ hấp dẫn, hoặc icon liên quan đến nội dung câu bói.
Hãy tránh sử dụng các cụm từ quá trang trọng hoặc kỹ thuật.
Hãy giữ câu bói dưới 200 từ.
Hãy trả lời bằng {language}."""

    template = ChatPromptTemplate([
        SystemMessage(content=system_prompt),
        HumanMessage(content=[
            {"type": "text", "text": "Hãy sử dụng bối cảnh công ty sau đây để hiểu về văn hóa và môi trường làm việc của công ty: "},
            {"type": "text", "text": company_context},
            {"type": "text", "text": "Hãy sử dụng định nghĩa vai trò sau đây để hiểu về các vị trí công việc trong công ty: "},
            {"type": "text", "text": role_definition},
            {"type": "text", "text": user_prompt},
            {"type": "text", "text": json.dumps(user_data, ensure_ascii=False)},
            {"type": "text", "text": text_to_inject},
            {"type": "text", "text": "\nHãy tạo một câu bói vui nhộn và may mắn cho người này!"}
        ])
    ])
    
    response = model.invoke(template.format_messages())
    return response

# ==================== Main UI ====================
def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 40px 20px; position: relative; z-index: 1;'>
        <h1 style="
            font-size: 3.5rem;
            margin-bottom: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            white-space: nowrap;
        ">
            <span>🎉</span>
            <span style="
                background: linear-gradient(135deg, #fde047, #fef3c7, #fde047);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                text-shadow: 0 0 20px rgba(253,224,71,0.35);
            ">
                Year-End Party Chatbot
            </span>
            <span>🎊</span>
        </h1>
        <p style='color: #fde047; font-size: 1.5rem; margin-bottom: 24px; animation: float 3s ease-in-out infinite;'>
            🧙‍♂️ Uncover the Hidden Pain of Your Office Life 💫
        </p>
        <div style='
            display: inline-block;
            background: white;
            padding: 16px 32px;
            border-radius: 50px;
            box-shadow: 0 4px 12px rgba(34, 211, 238, 0.5);
        '>
            <span style='color: #1e40af; font-weight: bold; font-size: 1.5rem;'>PRODUCTION ENGINEERING DEPARTMENT 2</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    

    
    # Input section
    st.markdown("<h3 style='color: #fde047; text-align: center; margin: 30px 0 20px 0;'>🌙 Enter your Full Name or Employee ID ✨</h3>", unsafe_allow_html=True)
    
    with st.form(key="user_input_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            # st.write("")
            # st.write("")
            user_id = st.text_input(
                "",
                placeholder="E.g.: 45678 or Maria Ozawa, Tokuda Shigeo",
                key="user_id_input",
                label_visibility="collapsed",
            )
        
        with col2:
            # st.write("")
            # st.write("")
            submit = st.form_submit_button("🪄 Go for it!")
    
    # Reload button
    if st.button("🔄 Reload Excel from SharePoint"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.refresh = st.session_state.get('refresh', 0) + 1
        with st.spinner("⏳ Loading data..."):
            time.sleep(2)
        st.success("✅ Done!")
    
    # Process
    if submit and user_id:
        with st.spinner("🔮 Reading your office destiny..."):
            result = get_participant_by_id(user_id, True)
            
            if result:
                user_data, company_context, role_definition, fixed_response, text_to_inject = result
                
                if user_data:
                    model = get_ai_model()
                    
                    if fixed_response is not None:
                        response = fixed_response
                    else:
                        ai_response = generate_response(user_data, model, company_context, role_definition, text_to_inject)
                        response = ai_response.content[0]['text']
                    
                    # Display result - Header section
                    team_html = f'''<p style='
                                        color: #64748b; 
                                        margin-bottom: 24px; 
                                        font-size: 1.2rem;
                                        font-weight: bold;
                                    '>
                                        <strong>🏢 Nhóm:</strong> {user_data['team']}
                                    </p>''' if user_data.get('team') else "Khách mời"  
                    
                    st.markdown(f"""
                        <div class='result-container' style='
                            background: white; 
                            border-radius: 24px; 
                            padding: 32px; 
                            box-shadow: 0 8px 32px rgba(34, 211, 238, 0.3); 
                            margin: 32px auto; 
                            max-width: 800px;'>
                            <h2 style='
                                font-size: 2rem; 
                                color: #f59e0b; 
                                margin-bottom: 16px; 
                                border-bottom: 2px solid #fde047; 
                                padding-bottom: 16px; 
                                font-weight: bold;'>
                                ✨ {user_data.get('name', 'Bạn')}
                            </h2>
                            {team_html}
                            <h3 style='
                                font-size: 1.5rem; 
                                color: #f59e0b; 
                                margin-bottom: 16px;'>
                                🔮 Lời bói của bạn:
                            </h3>
                            <div style='    
                                background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%); 
                                padding: 24px; 
                                border-radius: 16px; 
                                border: 2px solid #fde047;'>
                                <p style='
                                    color: #1f2937; 
                                    font-size: 1.1rem; 
                                    line-height: 1.8; 
                                    margin: 0;'>{response}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔄 Fortune-tell for someone else"):
                        st.rerun()
    
    elif submit:
        st.warning("⚠️ Please enter your Employee ID or Full Name!")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #22d3ee; margin-top: 48px; padding: 24px;'>
        <p style='margin-bottom: 8px;'>💡 <strong>Note:</strong> Please enter your full name with accents or your employee ID</p>
        <p>Made with ❤️ for Year-End Party 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    if "refresh" not in st.session_state:
        st.session_state.refresh = 0
    main()