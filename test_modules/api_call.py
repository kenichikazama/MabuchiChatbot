import os
import time
import pandas as pd
import json
from google import genai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_core.prompts import ChatPromptTemplate

# from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv
load_dotenv()



def get_participant_by_id(
    id,
    file_path="/mnt/data/guest_information.xlsx",
    sheet_name="participants_profile",
    id_column="id"
):
    """
    Trích xuất dữ liệu 1 người trong sheet participants_profiles theo id
    và trả về kết quả dạng JSON (dict)
    """

    # Đọc sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Lọc theo id
    result = df[df[id_column] == id]

    if result.empty:
        return {
            "status": "error",
            "message": f"Không tìm thấy người dùng với id = {id}"
        }

    # Lấy dòng đầu tiên và chuyển sang dict
    data = result.iloc[0].to_dict()

    return {
        "status": "success",
        "data": data
    }

    
# Set up LLM
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))


# Get user data from QR code
user_id = int(input("Enter MSNV: "))
user_data = get_participant_by_id(id=user_id, file_path="..\data\guest_information.xlsx", sheet_name="participants_profile", id_column="id")

if user_data['status'] != "success":
    print("Ai z bà?")

print("type:", type(user_data['data']))
user_data = json.dumps(user_data['data'], ensure_ascii=False)
print(user_data)
# loader = UnstructuredExcelLoader(r"..\data\guest_information.xlsx", mode="elements")
# docs = loader.load()

# Create Prompt Template
SYSTEM_PROMPT = """Bạn là một chatbot bói toán hài hước, thông minh, không nói nhảm, dùng để giải trí trong buổi tiệc tất niên của công ty."""

message = [
    SystemMessage(content="Bạn là một chatbot bói toán hài hước, thông minh, không nói nhảm, dùng để giải trí trong buổi tiệc tất niên của công ty."),
    HumanMessage(
    content=[
        {"type": "text", "text": "Hãy đưa ra câu bói ngắn gọn dễ hiểu về người có thông tin sau đây: "},
        {
            "type": "text",
            "text": user_data,
        },
        ]
    ),
]
response = model.invoke(message)
print("====>>", response)