import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import pandas as pd
from datetime import datetime
import os

# Cấu hình trang
st.set_page_config(
    page_title="🎊 Year-End Party Chatbot",
    page_icon="🎉",
    layout="wide"
)

# CSS tùy chỉnh cho giao diện năm mới
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-left: 20%;
    }
    .bot-message {
        background: white;
        color: #333;
        margin-right: 20%;
    }
    .title-box {
        background: rgba(255,255,255,0.95);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .employee-info {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ff6b6b;
    }
    .stButton>button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="title-box">
        <h1>🎉 YEAR-END PARTY CHATBOT 2025 🎊</h1>
        <p style="font-size: 1.2em; color: #667eea;">
            Chào mừng bạn đến với trợ lý AI thông minh của bữa tiệc tất niên!
        </p>
        <p style="color: #888;">✨ Hãy để tôi giúp bạn tìm hiểu về đồng nghiệp và tạo không khí vui vẻ! ✨</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎈 Cấu hình Chatbot")
    
    # API Key input
    api_key = st.text_input(
        "🔑 OpenAI API Key:",
        type="password",
        placeholder="Nhập API key của bạn...",
        help="Nhập API key từ OpenAI để kích hoạt chatbot"
    )
    
    # File upload
    st.markdown("### 📊 Dữ liệu nhân viên")
    uploaded_file = st.file_uploader(
        "Tải lên file Excel danh sách nhân viên",
        type=['xlsx', 'xls'],
        help="File Excel cần có các cột: Mã NV, Tên, Phòng ban, Vị trí, v.v."
    )
    
    # Hướng dẫn
    with st.expander("📖 Hướng dẫn sử dụng"):
        st.markdown("""
        **Cách sử dụng chatbot:**
        1. Nhập OpenAI API Key của bạn
        2. Tải lên file Excel chứa thông tin nhân viên
        3. Bắt đầu trò chuyện! Bạn có thể:
           - Hỏi về nhân viên bằng mã số
           - Trò chuyện tự do về bất kỳ chủ đề nào
           - Yêu cầu gợi ý game, hoạt động cho tiệc
        
        **Ví dụ câu hỏi:**
        - "Cho tôi biết thông tin về nhân viên NV001"
        - "Gợi ý hoạt động vui cho tiệc tất niên"
        - "Tạo lời chúc năm mới cho team"
        """)
    
    if st.button("🔄 Làm mới cuộc trò chuyện"):
        st.session_state.messages = []
        st.session_state.memory = None
        st.rerun()

# Khởi tạo session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'memory' not in st.session_state:
    st.session_state.memory = None
if 'employee_data' not in st.session_state:
    st.session_state.employee_data = None

# Đọc dữ liệu nhân viên từ file Excel
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.session_state.employee_data = df
        st.sidebar.success(f"✅ Đã tải {len(df)} nhân viên!")
        
        # Hiển thị preview
        with st.sidebar.expander("👀 Xem trước dữ liệu"):
            st.dataframe(df.head(), use_container_width=True)
    except Exception as e:
        st.sidebar.error(f"❌ Lỗi đọc file: {str(e)}")

# Hàm tìm kiếm thông tin nhân viên
def get_employee_info(employee_id):
    if st.session_state.employee_data is None:
        return "Chưa có dữ liệu nhân viên. Vui lòng tải file Excel lên!"
    
    df = st.session_state.employee_data
    
    # Tìm nhân viên theo mã
    employee = df[df.iloc[:, 0].astype(str).str.contains(str(employee_id), case=False, na=False)]
    
    if len(employee) > 0:
        info = employee.iloc[0]
        result = "🎯 **THÔNG TIN NHÂN VIÊN**\n\n"
        for col in df.columns:
            result += f"**{col}:** {info[col]}\n"
        return result
    else:
        return f"❌ Không tìm thấy nhân viên với mã: {employee_id}"

# Khởi tạo chatbot
def initialize_chatbot(api_key):
    if not api_key:
        return None, None
    
    try:
        # Khởi tạo LLM
        llm = ChatOpenAI(
            api_key=api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # Template cho chatbot
        template = """Bạn là trợ lý AI thông minh và thân thiện cho bữa tiệc Year-End Party của công ty. 
        Nhiệm vụ của bạn là tạo không khí vui vẻ, hỗ trợ tìm hiểu về nhân viên, và đưa ra các gợi ý sáng tạo cho tiệc.

        Phong cách giao tiếp:
        - Nhiệt tình, vui vẻ, đầy năng lượng
        - Sử dụng emoji phù hợp
        - Thân thiện nhưng chuyên nghiệp
        - Khuyến khích sự tương tác và vui chơi

        Lịch sử hội thoại:
        {history}

        Người dùng: {input}
        Trợ lý AI:"""
        
        prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=template
        )
        
        # Khởi tạo memory
        memory = ConversationBufferMemory(return_messages=True)
        
        # Tạo conversation chain
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            verbose=False
        )
        
        return conversation, memory
    except Exception as e:
        st.error(f"❌ Lỗi khởi tạo chatbot: {str(e)}")
        return None, None

# Main chat interface
if api_key:
    if st.session_state.memory is None:
        conversation, memory = initialize_chatbot(api_key)
        if conversation:
            st.session_state.conversation = conversation
            st.session_state.memory = memory
            # Tin nhắn chào mừng
            welcome_msg = """🎊 Xin chào! Tôi là trợ lý AI cho bữa tiệc Year-End Party! 

Tôi có thể giúp bạn:
✨ Tìm hiểu thông tin về đồng nghiệp (nhập mã nhân viên)
🎮 Gợi ý các trò chơi và hoạt động vui nhộn
🎉 Tạo lời chúc năm mới ý nghĩa
💡 Tư vấn tổ chức tiệc sáng tạo

Hãy bắt đầu trò chuyện với tôi nhé! 🚀"""
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <div><strong>👤 Bạn:</strong></div>
                    <div style="margin-top: 0.5rem;">{message["content"]}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message bot-message">
                    <div><strong>🤖 AI Assistant:</strong></div>
                    <div style="margin-top: 0.5rem;">{message["content"]}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Input chat
    user_input = st.chat_input("💬 Nhập tin nhắn của bạn...")
    
    if user_input:
        # Thêm tin nhắn người dùng
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Kiểm tra xem có phải yêu cầu thông tin nhân viên không
        employee_info = ""
        if any(keyword in user_input.lower() for keyword in ["nv", "nhân viên", "mã số", "employee"]):
            # Trích xuất mã nhân viên
            import re
            codes = re.findall(r'\b[A-Za-z]*\d+[A-Za-z0-9]*\b', user_input)
            if codes:
                employee_info = get_employee_info(codes[0])
        
        # Tạo context đầy đủ cho chatbot
        full_context = user_input
        if employee_info and not employee_info.startswith("❌"):
            full_context += f"\n\n[Thông tin nhân viên từ hệ thống]:\n{employee_info}"
        
        # Gọi chatbot
        try:
            with st.spinner("🤔 Đang suy nghĩ..."):
                response = st.session_state.conversation.predict(input=full_context)
            
            # Thêm phản hồi
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
            st.info("💡 Tip: Kiểm tra lại API key hoặc kết nối internet")

else:
    st.info("👈 Vui lòng nhập OpenAI API Key ở sidebar để bắt đầu!")
    
    # Hiển thị demo
    st.markdown("""
    ### 🌟 Tính năng nổi bật:
    
    - **💾 Nhớ lịch sử trò chuyện**: Chatbot ghi nhớ toàn bộ cuộc hội thoại
    - **📊 Truy xuất thông tin nhân viên**: Tự động tìm kiếm trong file Excel
    - **🎨 Giao diện đẹp mắt**: Thiết kế gradient màu sắc năm mới
    - **🎭 Tính cách thú vị**: AI vui vẻ, nhiệt tình phù hợp với tiệc tất niên
    - **💡 Đa năng**: Tư vấn game, hoạt động, lời chúc...
    
    ### 🎯 Demo file Excel mẫu:
    
    File Excel cần có các cột như:
    - Mã NV (VD: NV001, EMP123)
    - Họ và tên
    - Phòng ban
    - Vị trí/Chức vụ
    - Email
    - Số điện thoại
    - Sở thích (tùy chọn)
    """)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: white; padding: 1rem;">
        <p>🎊 Made with ❤️ for Year-End Party 2025 🎊</p>
        <p style="font-size: 0.9em;">Powered by LangChain & OpenAI</p>
    </div>
""", unsafe_allow_html=True)