"""
Streamlit UI for Year-End Party Chatbot
"""
import streamlit as st
import requests
from typing import Dict, Any, List
import time

# ==================== Configuration ====================
API_URL = "https://boughten-carlo-malapertly.ngrok-free.dev"  # Change this when deploying

# ==================== Page Config ====================
st.set_page_config(
    page_title="Year-End Party Chatbot",
    page_icon="🎉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Input box */
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 20px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: white;
        text-align: center;
    }
    
    /* Success/Error boxes */
    .stSuccess, .stError {
        border-radius: 10px;
    }
    
    /* Auth container */
    .auth-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State Initialization ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# ==================== API Functions ====================
def authenticate_user(user_id: int) -> Dict[str, Any]:
    """Authenticate user via API"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth",
            json={"user_id": user_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Lỗi kết nối API: {str(e)}")
        return {"status": "error", "message": str(e)}

def send_message(user_id: int, message: str, conversation_history: List[Dict[str, str]]) -> str:
    """Send message to chatbot API"""
    try:
        response = requests.post(
            f"{API_URL}/api/chat",
            json={
                "user_id": user_id,
                "message": message,
                "conversation_history": conversation_history
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        st.error(f"Lỗi kết nối API: {str(e)}")
        return "Xin lỗi, có lỗi xảy ra khi kết nối với chatbot."

# ==================== UI Components ====================
def show_header():
    """Display header"""
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🎉 Year-End Party Chatbot 🎊</h1>
        <p style='color: white; font-size: 1.2em;'>Trợ lý AI vui nhộn cho bữa tiệc tất niên</p>
    </div>
    """, unsafe_allow_html=True)

def show_login_page():
    """Display login page"""
    show_header()
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
            
            st.markdown("### 🔐 Đăng nhập")
            st.markdown("Nhập MSNV của bạn để bắt đầu trò chuyện")
            
            with st.form("login_form"):
                user_id_input = st.text_input(
                    "Mã số nhân viên (MSNV)",
                    placeholder="Nhập MSNV của bạn",
                    key="user_id_input"
                )
                
                submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
                
                if submitted:
                    if user_id_input:
                        try:
                            user_id = user_id_input
                            
                            with st.spinner("Đang xác thực..."):
                                result = authenticate_user(user_id)
                            
                            if result["status"] == "success":
                                st.session_state.authenticated = True
                                st.session_state.user_id = user_id
                                st.session_state.user_info = result["data"]
                                
                                # Add welcome message
                                welcome_msg = f"Xin chào {result['data'].get('name', 'bạn')}! Tôi là trợ lý AI cho bữa tiệc Year-End Party! Hãy hỏi tôi bất cứ điều gì nhé! 🎉"
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": welcome_msg
                                })
                                
                                st.success("Đăng nhập thành công!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(result.get("message", "Không tìm thấy thông tin người dùng"))
                        except ValueError:
                            st.error("MSNV phải là số!")
                    else:
                        st.warning("Vui lòng nhập MSNV")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Info section
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; color: white;'>
                <p>💡 <strong>Lưu ý:</strong> MSNV là mã số nhân viên của bạn</p>
                <p>🎯 Chatbot sẽ tạo câu bói vui dựa trên thông tin của bạn</p>
            </div>
            """, unsafe_allow_html=True)

def show_chat_page():
    """Display chat page"""
    # Header with logout
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        st.markdown(f"### 👤 {st.session_state.user_info.get('name', 'User')}")
    with col3:
        if st.button("Đăng xuất", use_container_width=True):
            # Reset session state
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.rerun()
    
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ..."):
                response = send_message(
                    st.session_state.user_id,
                    prompt,
                    st.session_state.conversation_history
                )
            
            st.markdown(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.conversation_history.append({"role": "assistant", "content": response})
        
        st.rerun()

def show_sidebar():
    """Display sidebar with user info"""
    with st.sidebar:
        if st.session_state.authenticated and st.session_state.user_info:
            st.markdown("### 📋 Thông tin của bạn")
            
            user_info = st.session_state.user_info
            
            # Display key info
            if "name" in user_info:
                st.markdown(f"**Tên:** {user_info['name']}")
            if "department" in user_info:
                st.markdown(f"**Phòng ban:** {user_info['department']}")
            if "position" in user_info:
                st.markdown(f"**Vị trí:** {user_info['position']}")
            
            st.markdown("---")
            
            # Clear chat button
            if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_history = []
                
                # Add welcome message again
                welcome_msg = f"Xin chào {user_info.get('name', 'bạn')}! Tôi đã sẵn sàng cho cuộc trò chuyện mới! 🎉"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": welcome_msg
                })
                st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Hướng dẫn")
        st.markdown("""
        - Hỏi tôi về vận may trong năm mới
        - Hỏi về sự nghiệp, công việc
        - Hỏi về chương trình tiệc
        - Chat thoải mái để giải trí!
        """)

# ==================== Main App ====================
def main():
    """Main application"""
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_sidebar()
        show_chat_page()

if __name__ == "__main__":
    main()