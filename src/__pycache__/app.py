"""
Simple Year-End Party Chatbot - Streamlit App
Input: MSNV -> Output: AI Response
"""
import streamlit as st
import pandas as pd
import json
from io import BytesIO
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from dotenv import load_dotenv
import os

load_dotenv()

# ==================== Page Config ====================
st.set_page_config(
    page_title="Year-End Party Chatbot",
    page_icon="🎉",
    layout="centered"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px;
        font-size: 16px;
        border-radius: 10px;
        font-weight: bold;
    }
    .result-box {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 20px;
        color: white; 
    }
</style>
""", unsafe_allow_html=True)

# ==================== Functions ====================
@st.cache_resource
def get_ai_model():
    """Initialize AI model (cached)"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=1,
    )

@st.cache_data(ttl=300)  # Cache for 5 minutes
def connect_to_sharepoint():
    """Connect to SharePoint and download Excel file"""
    site_url = os.getenv(
        "SHAREPOINT_SITE_URL",
        "https://mabmotor-my.sharepoint.com/personal/vnm13649_mabuchi-motor_com"
    )
    username = os.getenv("MICROSOFT_ACCOUNT")
    password = os.getenv("MICROSOFT_PASSWORD")
    file_relative_url = os.getenv(
        "SHAREPOINT_FILE_URL",
        "/personal/vnm13649_mabuchi-motor_com/Documents/Microsoft Teams Chat Files/guest_information 1.xlsx"
    )
    
    ctx = ClientContext(site_url).with_credentials(
        UserCredential(username, password)
    )
    
    file_stream = BytesIO()
    ctx.web.get_file_by_server_relative_url(
        file_relative_url
    ).download(file_stream).execute_query()
    
    file_stream.seek(0)
    df = pd.read_excel(file_stream)
    return df

def get_participant_by_id(user_id, use_sharepoint=True):
    """Get participant data by ID"""
    try:
        if use_sharepoint:
            df = connect_to_sharepoint()
        else:
            # Fallback to local file
            df = pd.read_excel("data/guest_information.xlsx", sheet_name="participants_profile")
        
        result = df[df["id"] == user_id]
        
        if result.empty:
            return None
        
        # Convert to dict and handle NaN
        data = result.iloc[0].to_dict()
        data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
        return data
        
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {str(e)}")
        return None

@st.cache_data
def load_context_files():
    """Load company context and role definitions"""
    try:
        with open("data/company_context.txt", "r", encoding="utf-8") as f:
            company_context = f.read()
    except:
        company_context = ""
    
    try:
        with open("data/role_definition.txt", "r", encoding="utf-8") as f:
            role_definitions = f.read()
    except:
        role_definitions = ""
    
    return company_context, role_definitions

def generate_response(user_data, model, company_context, role_definitions):
    """Generate AI response"""
    system_prompt = """Bạn là một chatbot bói toán hài hước, thông minh, nói chuyện lưu loát dùng để giải trí trong buổi tiệc tất niên của công ty.
Bạn sẽ dựa vào thông tin cá nhân của người dùng để đưa ra câu bói ngắn gọn, dễ hiểu, hài hước và thú vị.
Hãy chắc chắn rằng câu bói của bạn liên quan trực tiếp đến thông tin cá nhân của người dùng.
Hãy sử dụng ngôn ngữ tự nhiên, thân thiện và gần gũi, xưng hô "Tôi" và "Bạn".
Hãy tránh sử dụng các cụm từ quá trang trọng hoặc kỹ thuật.
Hãy giữ câu bói không dài quá 200 từ.
Hãy trả lời bằng tiếng Việt."""

    template = ChatPromptTemplate([
        SystemMessage(content=system_prompt),
        HumanMessage(content=[
            {"type": "text", "text": "Hãy sử dụng bối cảnh công ty sau đây để hiểu về văn hóa và môi trường làm việc của công ty: "},
            {"type": "text", "text": company_context},
            {"type": "text", "text": "Hãy sử dụng định nghĩa vai trò sau đây để hiểu về các vị trí công việc trong công ty: "},
            {"type": "text", "text": role_definitions},
            {"type": "text", "text": "Đây là thông tin cá nhân của người dùng: "},
            {"type": "text", "text": json.dumps(user_data, ensure_ascii=False)},
            {"type": "text", "text": "\nHãy tạo một câu bói vui nhộn và may mắn cho người này!"}
        ])
    ])
    
    # Generate response
    response_chunks = []
    for chunk in model.stream(template.format_messages()):
        if hasattr(chunk, 'content') and len(chunk.content) > 0:
            if isinstance(chunk.content, list):
                response_chunks.append(chunk.content[0].get('text', ''))
            else:
                response_chunks.append(chunk.content)
    
    return ''.join(response_chunks).strip()

# ==================== Main UI ====================
def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: white;'>🎉 Year-End Party Chatbot 🎊</h1>
        <p style='color: white; font-size: 1.2em;'>Bói toán vui nhộn cho bữa tiệc tất niên</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input form in white box
    with st.container():
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_id = st.text_input(
                "Nhập MSNV của bạn:",
                placeholder="Ví dụ: 45678 - Chị Hương hehe",
                key="user_id_input"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submit_button = st.button("🎯 Bói ngay!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Process when button clicked
    if submit_button and user_id:
        try:
            user_id_int = int(user_id)
            
            with st.spinner("🔮 Đang bói toán cho bạn..."):
                # Get user data
                user_data = get_participant_by_id(user_id_int)
                
                if not user_data:
                    st.error("❌ Không tìm thấy thông tin với MSNV này!")
                    return
                
                # Load context
                company_context, role_definitions = load_context_files()
                
                # Get AI model
                model = get_ai_model()
                
                # Generate response
                response = generate_response(user_data, model, company_context, role_definitions)
            
            # Display result
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.markdown(f"### 👤 {user_data.get('name', 'Bạn')}")
            
            if 'department' in user_data and user_data['department']:
                st.markdown(f"**Phòng ban:** {user_data['department']}")
            if 'position' in user_data and user_data['position']:
                st.markdown(f"**Vị trí:** {user_data['position']}")
            
            st.markdown("---")
            st.markdown("### 🔮 Lời bói của bạn:")
            st.markdown(response)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Try again button
            if st.button("🔄 Bói lại cho người khác"):
                st.rerun()
                
        except ValueError:
            st.error("❌ MSNV phải là số!")
        except Exception as e:
            st.error(f"❌ Có lỗi xảy ra: {str(e)}")
    
    elif submit_button:
        st.warning("⚠️ Vui lòng nhập MSNV!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: white;'>
        <p>💡 <strong>Lưu ý:</strong> MSNV là mã số nhân viên của bạn</p>
        <p>Made with ❤️ for Year-End Party 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()