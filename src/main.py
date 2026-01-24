"""
FastAPI Backend for Year-End Party Chatbot
"""
import os
import time
import pandas as pd
import json
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from io import BytesIO
import logging

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Year-End Party Chatbot API",
    description="API for entertainment chatbot at company year-end party",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Pydantic Models ====================
class AuthRequest(BaseModel):
    user_id: int

class ChatRequest(BaseModel):
    user_id: int
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    user_info: Optional[Dict[str, Any]] = None

# ==================== Data Service ====================
class SharePointService:
    """Service for handling SharePoint connections and data retrieval"""
    
    def __init__(self):
        self.site_url = os.getenv(
            "SHAREPOINT_SITE_URL",
            "https://mabmotor-my.sharepoint.com/personal/vnm13649_mabuchi-motor_com"
        )
        self.username = os.getenv("MICROSOFT_ACCOUNT")
        self.password = os.getenv("MICROSOFT_PASSWORD")
        self.file_relative_url = os.getenv(
            "SHAREPOINT_FILE_URL",
            "/personal/vnm13649_mabuchi-motor_com/Documents/Microsoft Teams Chat Files/guest_information 1.xlsx"
        )
        self._cached_df = None
        self._cache_time = None
        self._cache_duration = 300  # 5 minutes cache
    
    def connect_to_sharepoint(self) -> pd.DataFrame:
        """Connect to SharePoint and download Excel file"""
        try:
            # Check cache
            if self._cached_df is not None and self._cache_time:
                if time.time() - self._cache_time < self._cache_duration:
                    logger.info("Using cached SharePoint data")
                    return self._cached_df
            
            logger.info("Connecting to SharePoint...")
            start_time = time.time()
            
            ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            
            file_stream = BytesIO()
            ctx.web.get_file_by_server_relative_url(
                self.file_relative_url
            ).download(file_stream).execute_query()
            
            file_stream.seek(0)
            df = pd.read_excel(file_stream)
            
            # Cache the data
            self._cached_df = df
            self._cache_time = time.time()
            
            elapsed = time.time() - start_time
            logger.info(f"SharePoint connection successful. Time: {elapsed:.2f}s")
            
            return df
            
        except Exception as e:
            logger.error(f"SharePoint connection failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"SharePoint error: {str(e)}")
    
    def get_participant_by_id(
        self,
        user_id: int,
        file_path: Optional[str] = None,
        sheet_name: str = "participants_profile",
        id_column: str = "id",
        use_sharepoint: bool = True
    ) -> Dict[str, Any]:
        """Retrieve participant data by ID"""
        try:
            if use_sharepoint:
                df = self.connect_to_sharepoint()
            else:
                if not file_path:
                    raise ValueError("file_path required when not using SharePoint")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Filter by ID
            result = df[df[id_column] == user_id]
            
            if result.empty:
                return {
                    "status": "error",
                    "message": f"Không tìm thấy người dùng với id = {user_id}"
                }
            
            # Convert first row to dict, handling NaN values
            data = result.iloc[0].to_dict()
            # Convert NaN to None for JSON serialization
            data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
            
            return {
                "status": "success",
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error retrieving participant: {str(e)}")
            return {
                "status": "error",
                "message": f"Lỗi khi lấy thông tin: {str(e)}"
            }

# ==================== AI Service ====================
class ChatbotService:
    """Service for handling chatbot logic"""
    
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=1,
        )
        
        # Load context files
        self.company_context = self._load_file("data/company_context.txt")
        self.role_definitions = self._load_file("data/role_definition.txt")
        
        self.system_prompt = """Bạn là một chatbot bói toán hài hước, thông minh, nói chuyện lưu loát dùng để giải trí trong buổi tiệc tất niên của công ty.
Bạn sẽ dựa vào thông tin cá nhân của người dùng để đưa ra câu bói ngắn gọn, dễ hiểu, hài hước và thú vị.
Hãy chắc chắn rằng câu bói của bạn liên quan trực tiếp đến thông tin cá nhân của người dùng.
Hãy sử dụng ngôn ngữ tự nhiên, thân thiện và gần gũi, xưng hô "Tôi" và "Bạn".
Hãy tránh sử dụng các cụm từ quá trang trọng hoặc kỹ thuật.
Hãy giữ câu bói không dài quá 200 từ.
Hãy trả lời bằng tiếng Việt.
Nếu người dùng hỏi về lịch trình, chương trình, hoặc các hoạt động trong bữa tiệc, hãy trả lời dựa trên thông tin công ty được cung cấp.
"""
    
    def _load_file(self, filepath: str) -> str:
        """Load text file content"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}, using empty string")
            return ""
    
    def create_prompt(self, user_data: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> ChatPromptTemplate:
        """Create prompt template with user data and conversation history"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=[
                {"type": "text", "text": "Hãy sử dụng bối cảnh công ty sau đây để hiểu về văn hóa và môi trường làm việc của công ty: "},
                {"type": "text", "text": self.company_context},
                {"type": "text", "text": "Hãy sử dụng định nghĩa vai trò sau đây để hiểu về các vị trí công việc trong công ty: "},
                {"type": "text", "text": self.role_definitions},
                {"type": "text", "text": "Đây là thông tin cá nhân của người dùng: "},
                {"type": "text", "text": json.dumps(user_data, ensure_ascii=False)},
            ])
        ]
        
        # Add conversation history
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return ChatPromptTemplate(messages)
    
    async def generate_response(
        self,
        user_data: Dict[str, Any],
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate AI response"""
        try:
            # Add current user message to history
            conversation_history.append({"role": "user", "content": user_message})
            
            # Create prompt
            template = self.create_prompt(user_data, conversation_history)
            
            # Generate response
            response_chunks = []
            async for chunk in self.model.astream(template.format_messages()):
                if hasattr(chunk, 'content') and len(chunk.content) > 0:
                    if isinstance(chunk.content, list):
                        response_chunks.append(chunk.content[0].get('text', ''))
                    else:
                        response_chunks.append(chunk.content)
            
            response = ''.join(response_chunks)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Xin lỗi, tôi gặp chút vấn đề. Bạn có thể hỏi lại được không?"

# ==================== Initialize Services ====================
sharepoint_service = SharePointService()
chatbot_service = ChatbotService()

# ==================== API Endpoints ====================
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Year-End Party Chatbot API is running!",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.post("/api/auth")
async def authenticate_user(request: AuthRequest):
    """Authenticate user by ID"""
    try:
        user_data = sharepoint_service.get_participant_by_id(
            user_id=request.user_id,
            use_sharepoint=True
        )
        
        if user_data["status"] == "error":
            raise HTTPException(status_code=404, detail=user_data["message"])
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages"""
    try:
        # Get user data
        user_data_result = sharepoint_service.get_participant_by_id(
            user_id=request.user_id,
            use_sharepoint=True
        )
        
        if user_data_result["status"] == "error":
            raise HTTPException(status_code=404, detail=user_data_result["message"])
        
        user_data = user_data_result["data"]
        
        # Generate response
        response = await chatbot_service.generate_response(
            user_data=user_data,
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            response=response,
            user_info=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "sharepoint": "connected" if sharepoint_service._cached_df is not None else "not_cached",
            "chatbot": "ready"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)