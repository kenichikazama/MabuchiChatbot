"""
Simple Year-End Party Chatbot - Streamlit App
Input: MSNV -> Output: AI Response
"""
from urllib import response
import streamlit as st
import pandas as pd
pd.set_option('display.max_columns', None)
# Show full text in DataFrame
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
from dotenv import load_dotenv
import os
import time

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
        background: linear-gradient(135deg, #0f2027 0%, #1c3c72 50%, #2a5298 100%);
        color: white;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #FFF8B0 0%, #FFFCC2 50%, #FFF59D 100%);
        box-shadow: 0 0 5px #FFF59D, 0 0 10px #FFFCC2;
        color: #0f2027;
        border-radius: 12px;
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
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Functions ====================
@st.cache_resource
def get_ai_model():
    """Initialize AI model (cached)"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = ChatGoogleGenerativeAI(
                                    model=os.getenv("AI_MODEL"),
                                    api_key=os.getenv("GEMINI_API_KEY"),
                                    temperature=1.0,
                                    max_output_tokens=3000,
                                    thinking_level="minimal",
                                    )
    return model

@st.cache_data(ttl=1)  # Cache for 1 second 
def connect_to_sharepoint(refresh_key=0):
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
    
    response = File.open_binary(ctx, file_relative_url)
    file_stream = BytesIO(response.content)
    
    # ctx.web.get_file_by_server_relative_url(
    #     file_relative_url
    # ).download(file_stream).execute_query()
    
    file_stream.seek(0)
    raw = file_stream.getvalue()
    xls = pd.ExcelFile(file_stream)

    df = pd.read_excel(xls, "participants_profile")
    company_context = pd.read_excel(xls, "company_context")
    role_definition = pd.read_excel(xls, "role_definition")
    # print("company_context: ", company_context)
    # print("role_definition: ", role_definition)
    print("REFRESH KEY:", refresh_key)
    print("DOWNLOAD AT:", time.time())
    print("FILE SIZE:", len(raw))
    return df, company_context['text'][0], role_definition['text'][0]

def get_participant_by_id(user_id, use_sharepoint=True):
    """Get participant data by ID"""
    try:
        fix_response = None
        text_to_inject = None
        if use_sharepoint:
            df, company_context, role_definition = connect_to_sharepoint(st.session_state.refresh)
            # print("company_context after connect: ", company_context)
            # print("role_definition after connect: ", role_definition)
        else:
            # Fallback to local file
            df = pd.read_excel("data/guest_information.xlsx", sheet_name="participants_profile")
            company_context, role_definition = load_context_files()
            
        # kiểm tra nếu user_id là số thì tìm bằng "id", nếu không thì tìm bằng "name"
        # print("Looking for user_id:", user_id, "of type", type(user_id))
        if isinstance(user_id, int) or ((isinstance(user_id, str) and user_id.isdigit())):      
            result = df[df["id"] == int(user_id)]
        elif isinstance(user_id, str):
            # print("Searching in list:", df["name"].tolist())
            result = df[df["name"].str.lower().str.strip() == user_id.lower().strip()]
        else:
            st.error("Nhập MSNV hoặc tên hợp lệ!")
            return None
        print("Result DataFrame:", result)
        if result.empty:
            st.error("Không tìm thấy người này!")
            return None
        
        # Convert to dict and handle NaN
        data = result.iloc[0].to_dict()
        data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
        
        # tách cột fixed_response nếu có
        if "fixed_response" in data:
            # đổi thành NaN
            fix_response = data["fixed_response"]
            # xóa luôn khỏi data
            del data["fixed_response"]
        
        if "text_to_inject" in data:
            text_to_inject = data["text_to_inject"]
            del data["text_to_inject"]
        
        print("data:", data)
        print("User data retrieved:", data)
        print("Text to inject:", text_to_inject )
        return data, company_context, role_definition, fix_response, text_to_inject
        
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {str(e)}")
        return None

@st.cache_data
def load_context_files():
    """Load company context and role definitions"""
    try:         
        with open("..\\data\\company_context.txt", "r", encoding="utf-8") as f:
            company_context = f.read()
    except:
        company_context = ""
    
    try:
        with open("..\\data\\role_definition.txt", "r", encoding="utf-8") as f:
            role_definition = f.read()
    except:
        role_definition = ""
    
    return company_context, role_definition

def generate_response(user_data, model, company_context, role_definition, text_to_inject=None ):
    
    if user_data['nationality'] == 'JP':
        language = "Tiếng Anh"
        user_prompt = "Vì đây là người Nhật, hãy trả lời bằng tiếng Anh một cách tự nhiên và thân thiện dựa vào thông tin của họ:"
    else:
        language = "Tiếng Việt"
        user_prompt = "Đây là thông tin cá nhân của người dùng:"
        
    if text_to_inject:
        text_to_inject = f"\nHãy đảm bảo câu bói của bạn có chứa thông tin sau đây: {text_to_inject}"
    else:
        text_to_inject = ""
        
    system_prompt = f"""Bạn là một chatbot bói toán hài hước, thông minh, nói chuyện lưu loát dùng để giải trí trong buổi tiệc tất niên của công ty.
PHẢI LUÔN NHỚ RẰNG NĂM NAY LÀ NĂM 2025 (NĂM SAU LÀ NĂM 2026).
Bạn sẽ dựa vào thông tin cá nhân của người dùng để đưa ra câu bói ngắn gọn, dễ hiểu, hài hước và thú vị.
Hãy chắc chắn rằng câu bói của bạn liên quan trực tiếp đến thông tin cá nhân của người dùng.
Hãy sử dụng ngôn ngữ tự nhiên, thân thiện và gần gũi, xưng hô "Tôi" và "Bạn".
Hãy thêm vài icon lung linh vào câu bói để tăng độ hấp dẫn, hoặc icon liên quan đến nội dung câu bói.
Hãy tránh sử dụng các cụm từ quá trang trọng hoặc kỹ thuật.
Hãy giữ câu bói không dài quá 200 từ.
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
    
    print("Generating response with template:", template.format_messages())
    
    # Generate response
    # response_chunks = []
    # for chunk in model.stream(template.format_messages()):
    #     if hasattr(chunk, 'content') and len(chunk.content) > 0:
    #         if isinstance(chunk.content, list):
    #             response_chunks.append(chunk.content[0].get('text', ''))
    #         else:
    #             response_chunks.append(chunk.content)
    
    # return ''.join(response_chunks).strip()
    response = model.invoke(template.format_messages())
    print("Generated response:", response)
    return response
# ==================== Main UI ====================
def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #FFF59D;'>🎉 Year-End Party Chatbot 🎊</h1>
        <p style='color: #FFF59D; font-size: 1.2em;'>🧙‍♂️ Bói toán vui nhộn cho bữa tiệc tất niên 💫</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input form in white box
    with st.container():
        # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        
        with st.form(key="user_input_form"):
            st.markdown(" 🗝️ Nhập MSNV hoặc tên của bạn:")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                user_id = st.text_input(
                    "Nhập MSNV của bạn:",
                    placeholder="Ví dụ: 45678",
                    key="user_id_input"
                )
            
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                submit_button = st.form_submit_button("🪄 Bói ngay!") 
        
        # st.markdown("</div>", unsafe_allow_html=True)
        
    if "refresh" not in st.session_state:
        st.session_state.refresh = 0

    if st.button("🔄 Reload Excel from SharePoint"):
        st.cache_data.clear()
        st.session_state.refresh += 1
        # add loading spinner
        with st.spinner("Loading data from SharePoint..."): 
            time.sleep(30)  # Wait for cache to clear and data to reload
        st.success("✅ Dữ liệu đã được tải lại!")

        

    # Process when button clicked
    if submit_button and user_id:
        print("Processing user ID:", user_id, type(user_id))
        try:
            user_id_int = user_id
            
            with st.spinner("🔮 Đang bói toán cho bạn..."):
                # Get user data
                user_data, company_context, role_definition, fixed_response, text_to_inject = get_participant_by_id(user_id_int, True)
                
                if not user_data:
                    st.error("❌ Không tìm thấy thông tin với MSNV này!")
                    return
                # print("user_data retrieved:", user_data)
                # Load context
                print("company_context length:", len(company_context))
                # Get AI model
                model = get_ai_model()
                print("AI model initialized:", model)
                # Generate response
                if fixed_response is not None:
                    print("Using fixed response from data.")
                    response = fixed_response
                else:
                    response = generate_response(user_data, model, company_context, role_definition, text_to_inject)
                    
                    print("AI response metadata:")
                    print("input tokens:", response.usage_metadata['input_tokens'])
                    print("output tokens:", response.usage_metadata['output_tokens'])
                    response = response.content[0]['text']
            # Display result
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #FFF59D;'> {user_data.get('name', 'Bạn')} </h3>", unsafe_allow_html=True)
            
            if 'team' in user_data and user_data['team']:
                st.markdown(f"**🪐 Nhóm:** {user_data['team']}")
            
            st.markdown("---")
            st.markdown(f"<h3 style='color: #FFF59D;'>🔮 Lời bói của bạn:</h3>", unsafe_allow_html=True)
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