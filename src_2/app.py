import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QFileDialog, QScrollArea, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QLinearGradient, QBrush, QPainter
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import pandas as pd
from datetime import datetime
import re

class GradientWidget(QWidget):
    """Widget với background gradient"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(102, 126, 234))
        gradient.setColorAt(1, QColor(118, 75, 162))
        painter.fillRect(self.rect(), gradient)

class ChatWorker(QThread):
    """Thread xử lý chat để không block UI"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, conversation, user_input, employee_info=""):
        super().__init__()
        self.conversation = conversation
        self.user_input = user_input
        self.employee_info = employee_info
        
    def run(self):
        try:
            full_context = self.user_input
            if self.employee_info and not self.employee_info.startswith("❌"):
                full_context += f"\n\n[Thông tin nhân viên từ hệ thống]:\n{self.employee_info}"
            
            response = self.conversation.predict(input=full_context)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))

class MessageBubble(QFrame):
    """Widget tin nhắn dạng bubble"""
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMaximumWidth(600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Label tên
        name_label = QLabel("👤 Bạn" if is_user else "🤖 AI Assistant")
        name_font = QFont("Segoe UI", 9, QFont.Bold)
        name_label.setFont(name_font)
        
        # Label nội dung
        content_label = QLabel(message)
        content_label.setWordWrap(True)
        content_font = QFont("Segoe UI", 10)
        content_label.setFont(content_font)
        content_label.setTextFormat(Qt.RichText)
        content_label.setOpenExternalLinks(True)
        
        layout.addWidget(name_label)
        layout.addWidget(content_label)
        
        # Style cho bubble
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f093fb, stop:1 #f5576c);
                    border-radius: 15px;
                    color: white;
                }
                QLabel {
                    background: transparent;
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: white;
                    border-radius: 15px;
                    color: #333;
                }
                QLabel {
                    background: transparent;
                    color: #333;
                }
            """)

class YearEndChatbot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conversation = None
        self.memory = None
        self.employee_data = None
        self.chat_worker = None
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("🎊 Year-End Party Chatbot 2025")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main widget với gradient background
        main_widget = GradientWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.create_header(main_layout)
        
        # Content area
        content_layout = QHBoxLayout()
        
        # Left panel - Settings
        self.create_settings_panel(content_layout)
        
        # Right panel - Chat
        self.create_chat_panel(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Footer
        self.create_footer(main_layout)
        
    def create_header(self, parent_layout):
        """Tạo header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 20px;
            }
        """)
        header_frame.setMaximumHeight(150)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title = QLabel("🎉 YEAR-END PARTY CHATBOT 2025 🎊")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #667eea;")
        
        # Subtitle
        subtitle = QLabel("Chào mừng bạn đến với trợ lý AI thông minh của bữa tiệc tất niên!")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #555; margin-top: 5px;")
        
        # Description
        desc = QLabel("✨ Hãy để tôi giúp bạn tìm hiểu về đồng nghiệp và tạo không khí vui vẻ! ✨")
        desc.setAlignment(Qt.AlignCenter)
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet("color: #888; margin-top: 5px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(desc)
        
        parent_layout.addWidget(header_frame)
        
    def create_settings_panel(self, parent_layout):
        """Tạo panel cài đặt bên trái"""
        settings_frame = QFrame()
        settings_frame.setMaximumWidth(350)
        settings_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        settings_layout = QVBoxLayout(settings_frame)
        
        # Title
        title = QLabel("🎈 Cấu hình Chatbot")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #667eea; margin-bottom: 10px;")
        settings_layout.addWidget(title)
        
        # API Key section
        api_label = QLabel("🔑 OpenAI API Key:")
        api_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        settings_layout.addWidget(api_label)
        
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setPlaceholderText("Nhập API key của bạn...")
        self.api_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 11px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        settings_layout.addWidget(self.api_input)
        
        # Connect button
        self.connect_btn = QPushButton("🚀 Kết nối")
        self.connect_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb, stop:1 #f5576c);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e082ea, stop:1 #e4465b);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d071d9, stop:1 #d3354a);
            }
        """)
        self.connect_btn.clicked.connect(self.initialize_chatbot)
        settings_layout.addWidget(self.connect_btn)
        
        settings_layout.addSpacing(20)
        
        # File upload section
        file_label = QLabel("📊 Dữ liệu nhân viên")
        file_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        settings_layout.addWidget(file_label)
        
        self.file_btn = QPushButton("📁 Tải file Excel")
        self.file_btn.setFont(QFont("Segoe UI", 10))
        self.file_btn.setCursor(Qt.PointingHandCursor)
        self.file_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #667eea;
                border: 2px solid #667eea;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #667eea;
                color: white;
            }
        """)
        self.file_btn.clicked.connect(self.load_employee_data)
        settings_layout.addWidget(self.file_btn)
        
        self.file_status = QLabel("❌ Chưa tải file")
        self.file_status.setFont(QFont("Segoe UI", 9))
        self.file_status.setStyleSheet("color: #999; margin-top: 5px;")
        settings_layout.addWidget(self.file_status)
        
        settings_layout.addSpacing(20)
        
        # Instructions
        instructions = QLabel("""
<b>📖 Hướng dẫn sử dụng:</b><br><br>
<b>1.</b> Nhập OpenAI API Key<br>
<b>2.</b> Tải file Excel nhân viên<br>
<b>3.</b> Bắt đầu trò chuyện!<br><br>

<b>💡 Ví dụ câu hỏi:</b><br>
• "Thông tin NV001"<br>
• "Gợi ý game cho tiệc"<br>
• "Tạo lời chúc năm mới"
        """)
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Segoe UI", 9))
        instructions.setStyleSheet("""
            QLabel {
                background: #f0f7ff;
                padding: 15px;
                border-radius: 10px;
                color: #333;
                border-left: 4px solid #667eea;
            }
        """)
        settings_layout.addWidget(instructions)
        
        # Clear chat button
        settings_layout.addStretch()
        
        self.clear_btn = QPushButton("🔄 Làm mới cuộc trò chuyện")
        self.clear_btn.setFont(QFont("Segoe UI", 9))
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #ffeaa7;
                color: #333;
                border: none;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #fdcb6e;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_chat)
        settings_layout.addWidget(self.clear_btn)
        
        parent_layout.addWidget(settings_frame)
        
    def create_chat_panel(self, parent_layout):
        """Tạo panel chat bên phải"""
        chat_frame = QFrame()
        chat_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        chat_layout = QVBoxLayout(chat_frame)
        
        # Chat title
        chat_title = QLabel("💬 Trò chuyện")
        chat_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        chat_title.setStyleSheet("color: #667eea; margin-bottom: 10px;")
        chat_layout.addWidget(chat_title)
        
        # Scroll area cho messages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Container cho messages
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addStretch()
        self.messages_layout.setSpacing(15)
        
        scroll.setWidget(self.messages_widget)
        chat_layout.addWidget(scroll)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("💬 Nhập tin nhắn của bạn...")
        self.message_input.setFont(QFont("Segoe UI", 11))
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("🚀")
        self.send_btn.setFont(QFont("Segoe UI", 16))
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setFixedSize(60, 50)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #556dd9, stop:1 #653a91);
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)
        
        chat_layout.addLayout(input_layout)
        
        parent_layout.addWidget(chat_frame)
        
        # Thêm welcome message
        self.add_bot_message("""🎊 Xin chào! Tôi là trợ lý AI cho bữa tiệc Year-End Party!

Tôi có thể giúp bạn:
✨ Tìm hiểu thông tin về đồng nghiệp
🎮 Gợi ý trò chơi và hoạt động vui nhộn
🎉 Tạo lời chúc năm mới ý nghĩa
💡 Tư vấn tổ chức tiệc sáng tạo

Hãy bắt đầu trò chuyện với tôi nhé! 🚀""")
        
    def create_footer(self, parent_layout):
        """Tạo footer"""
        footer = QLabel("🎊 Made with ❤️ for Year-End Party 2025 | Powered by LangChain & OpenAI 🎊")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("""
            color: white;
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
        """)
        parent_layout.addWidget(footer)
        
    def initialize_chatbot(self):
        """Khởi tạo chatbot"""
        api_key = self.api_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "⚠️ Thiếu API Key", 
                              "Vui lòng nhập OpenAI API Key!")
            return
        
        try:
            # llm = ChatOpenAI(
            #     api_key=api_key,
            #     model_name="gpt-3.5-turbo",
            #     temperature=0.7
            # )
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=1.0,  # Gemini 3.0+ defaults to 1.0
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
            
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
            
            self.memory = ConversationBufferMemory(return_messages=True)
            self.conversation = ConversationChain(
                llm=llm,
                memory=self.memory,
                prompt=prompt,
                verbose=False
            )
            
            QMessageBox.information(self, "✅ Thành công", 
                                  "Đã kết nối chatbot thành công!")
            self.connect_btn.setText("✅ Đã kết nối")
            self.connect_btn.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", 
                               f"Không thể khởi tạo chatbot:\n{str(e)}")
    
    def load_employee_data(self):
        """Tải dữ liệu nhân viên từ Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            try:
                df = pd.read_excel(file_path)
                self.employee_data = df
                self.file_status.setText(f"✅ Đã tải {len(df)} nhân viên")
                self.file_status.setStyleSheet("color: #27ae60;")
                QMessageBox.information(self, "✅ Thành công", 
                                      f"Đã tải {len(df)} nhân viên!")
            except Exception as e:
                QMessageBox.critical(self, "❌ Lỗi", 
                                   f"Không thể đọc file:\n{str(e)}")
    
    def get_employee_info(self, employee_id):
        """Tìm kiếm thông tin nhân viên"""
        if self.employee_data is None:
            return "❌ Chưa có dữ liệu nhân viên. Vui lòng tải file Excel!"
        
        df = self.employee_data
        employee = df[df.iloc[:, 0].astype(str).str.contains(str(employee_id), case=False, na=False)]
        
        if len(employee) > 0:
            info = employee.iloc[0]
            result = "🎯 <b>THÔNG TIN NHÂN VIÊN</b><br><br>"
            for col in df.columns:
                result += f"<b>{col}:</b> {info[col]}<br>"
            return result
        else:
            return f"❌ Không tìm thấy nhân viên với mã: {employee_id}"
    
    def add_user_message(self, message):
        """Thêm tin nhắn người dùng"""
        bubble = MessageBubble(message, is_user=True)
        # bubble.setAlignment(Qt.AlignRight)
        
        # Xóa stretch cuối
        item = self.messages_layout.takeAt(self.messages_layout.count() - 1)
        
        # Thêm bubble
        bubble_layout = QHBoxLayout()
        bubble_layout.addStretch()
        bubble_layout.addWidget(bubble, alignment=Qt.AlignRight)
        self.messages_layout.addLayout(bubble_layout)
        
        # Thêm stretch lại
        self.messages_layout.addStretch()
        
        # Scroll xuống cuối
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def add_bot_message(self, message):
        """Thêm tin nhắn bot"""
        bubble = MessageBubble(message, is_user=False)
        # bubble.setAlignment(Qt.AlignLeft)
        
        # Xóa stretch cuối
        item = self.messages_layout.takeAt(self.messages_layout.count() - 1)
        
        # Thêm bubble
        bubble_layout = QHBoxLayout()
        bubble_layout.addWidget(bubble, alignment=Qt.AlignLeft)
        bubble_layout.addStretch()
        self.messages_layout.addLayout(bubble_layout)
        
        # Thêm stretch lại
        self.messages_layout.addStretch()
        
        # Scroll xuống cuối
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll chat xuống cuối"""
        scroll = self.messages_widget.parent()
        if isinstance(scroll, QScrollArea):
            scroll.verticalScrollBar().setValue(
                scroll.verticalScrollBar().maximum()
            )
    
    def send_message(self):
        """Gửi tin nhắn"""
        if not self.conversation:
            QMessageBox.warning(self, "⚠️ Chưa kết nối", 
                              "Vui lòng kết nối chatbot trước!")
            return
        
        user_input = self.message_input.text().strip()
        if not user_input:
            return
        
        # Thêm tin nhắn người dùng
        self.add_user_message(user_input)
        self.message_input.clear()
        
        # Tìm thông tin nhân viên nếu có
        employee_info = ""
        if any(keyword in user_input.lower() for keyword in ["nv", "nhân viên", "mã số", "employee"]):
            codes = re.findall(r'\b[A-Za-z]*\d+[A-Za-z0-9]*\b', user_input)
            if codes:
                employee_info = self.get_employee_info(codes[0])
        
        # Disable input trong khi xử lý
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⏳")
        
        # Tạo worker thread
        self.chat_worker = ChatWorker(self.conversation, user_input, employee_info)
        self.chat_worker.finished.connect(self.on_response_received)
        self.chat_worker.error.connect(self.on_response_error)
        self.chat_worker.start()
    
    def on_response_received(self, response):
        """Xử lý khi nhận được phản hồi"""
        self.add_bot_message(response)
        
        # Enable lại input
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("🚀")
        self.message_input.setFocus()
    
    def on_response_error(self, error):
        """Xử lý lỗi"""
        QMessageBox.critical(self, "❌ Lỗi", f"Đã xảy ra lỗi:\n{error}")
        
        # Enable lại input
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("🚀")
    
    def clear_chat(self):
        """Xóa lịch sử chat"""
        reply = QMessageBox.question(
            self, "🔄 Xác nhận", 
            "Bạn có chắc muốn xóa toàn bộ lịch sử chat?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Xóa tất cả messages
            while self.messages_layout.count() > 1:
                item = self.messages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.clear_layout(item.layout())
            
            # Reset memory
            if self.memory:
                self.memory.clear()
            
            # Thêm lại welcome message
            self.add_bot_message("""🎊 Xin chào! Tôi là trợ lý AI cho bữa tiệc Year-End Party!

Tôi có thể giúp bạn:
✨ Tìm hiểu thông tin về đồng nghiệp
🎮 Gợi ý trò chơi và hoạt động vui nhộn
🎉 Tạo lời chúc năm mới ý nghĩa
💡 Tư vấn tổ chức tiệc sáng tạo

Hãy bắt đầu trò chuyện với tôi nhé! 🚀""")
    
    def clear_layout(self, layout):
        """Xóa tất cả widget trong layout"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set app font
    app.setFont(QFont("Segoe UI", 10))
    
    window = YearEndChatbot()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()