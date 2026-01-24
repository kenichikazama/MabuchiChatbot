import os
import time
import pandas as pd
pd.set_option('display.max_columns', None)         # Hiện tất cả cột
import json
from google import genai
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_core.prompts import ChatPromptTemplate
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from io import BytesIO

# from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv
load_dotenv()


def connect_to_sharepoint():
    # ==== CONFIG ====
    site_url = r"https://mabmotor-my.sharepoint.com/personal/vnm13649_mabuchi-motor_com"
    username = os.getenv("MICROSOFT_ACCOUNT")
    password = os.getenv("MICROSOFT_PASSWORD")

    file_relative_url = (
        "/personal/vnm13649_mabuchi-motor_com/"
        "Documents/Microsoft Teams Chat Files/guest_information 1.xlsx"
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

    # print(df.head())
    return df


def get_participant_by_id(
    id="6969696969",
    name="default_name",
    file_path="/mnt/data/guest_information.xlsx",
    sheet_name="participants_profile",
    id_column="id",
    isSharePoint=False,
):
    """
    Trích xuất dữ liệu 1 người trong sheet participants_profiles theo id hoặc tên
    và trả về kết quả dạng JSON (dict)
    """

    # Đọc sheet
    if isSharePoint:
        start_time = time.time()
        df = connect_to_sharepoint() 
        end_time = time.time()
        print("Thời gian kết nối SharePoint và tải file:", end_time - start_time, "giây")
    else:
        df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Lọc theo id
    # Nếu không có id thì sẽ tìm theo tên
    result = df[df[id_column] == id]
    if result.empty:
        result = df[df["name"] == name]
        
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
model = ChatGoogleGenerativeAI(
                                model="gemini-3-flash-preview",
                                api_key=os.getenv("GEMINI_API_KEY"),
                                temperature=1,
                                )


# Get user data from QR code
user_id = int(input("Enter MSNV: "))
user_data = get_participant_by_id(id=user_id, file_path="..\data\guest_information.xlsx", sheet_name="participants_profile", id_column="id", isSharePoint=True)

if user_data['status'] != "success":
    print("Ai z bà?")
    
if user_data['nationality'] == 'JP':
    LANGUAGE = "tiếng Anh"
    USER_PROMPT = "Vì đây là người Nhật, hãy trả lời bằng tiếng Anh một cách tự nhiên và thân thiện dựa vào thông tin của họ:"
else:
    LANGUAGE = "tiếng Việt"
    USER_PROMPT = "Đây là thông tin cá nhân của người dùng:"

print("type:", type(user_data['data']))
user_data = json.dumps(user_data['data'], ensure_ascii=False)
print(user_data)  

# đọc dữ liệu từ file txt
company_context = r"D:\KenIChi\Chatbot\data\company_context.txt"
with open(company_context, "r", encoding="utf-8") as f:
    company_context = f.read()
role_definitions = r"D:\KenIChi\Chatbot\data\role_definition.txt"
with open(role_definitions, "r", encoding="utf-8") as f:
    role_definitions = f.read()

# Create Prompt Template
AIMessage(content="Xin chào! Tôi là trợ lý AI cho bữa tiệc Year-End Party!").pretty_print()
SYSTEM_PROMPT = f"""Bạn là một chatbot bói toán hài hước, thông minh, nói chuyện lưu loát dùng để giải trí trong buổi tiệc tất niên năm 2025 (Năm sau là năm 2026) của công ty.
Bạn sẽ dựa vào thông tin cá nhân của người dùng để đưa ra câu bói ngắn gọn, dễ hiểu, hài hước và thú vị.
Hãy chắc chắn rằng câu bói của bạn liên quan trực tiếp đến thông tin cá nhân của người dùng.
Hãy sử dụng ngôn ngữ tự nhiên, thân thiện và gần gũi, xưng hô "Tôi" và "Bạn".
Hãy tránh sử dụng các cụm từ quá trang trọng hoặc kỹ thuật.
Hãy giữ câu bói không dài quá 200 từ.
Hãy trả lời bằng {LANGUAGE}.
"""


template = ChatPromptTemplate(
    [
        SystemMessage(content=SYSTEM_PROMPT),
        
        HumanMessage(
            content=[
                {"type": "text", "text": "Hãy sử dụng bối cảnh công ty sau đây để hiểu về văn hóa và môi trường làm việc của công ty: "},
                {
                    "type": "text",
                    "text": company_context,
                },
                {"type": "text", "text": "Hãy sử dụng định nghĩa vai trò sau đây để hiểu về các vị trí công việc trong công ty: "},
                {
                    "type": "text",
                    "text": role_definitions,
                },
                {"type": "text", "text": USER_PROMPT},
                {
                    "type": "text",
                    "text": user_data,
                },
                
            ]
        ),
        
    ]
)

for chunk in model.stream(template.format_messages()):
    if len(chunk.content) > 0:
        print(chunk.content[0]['text'])