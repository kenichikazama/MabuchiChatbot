import os
import time
from google import genai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import UnstructuredExcelLoader
# from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv
load_dotenv()



client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """Bạn là một chatbot bói toán hài hước, thông minh, không nói nhảm, dùng để giải trí trong buổi tiệc tất niên của công ty."""



loader = UnstructuredExcelLoader(r"D:\KenIChi\Chatbot\data\guest_information.xlsx", mode="elements")
docs = loader.load()
print(docs)
message = [
    SystemMessage(content="Bạn là một chatbot bói toán hài hước, thông minh, không nói nhảm, dùng để giải trí trong buổi tiệc tất niên của công ty."),
    HumanMessage(
    content=[
        {"type": "text", "text": "Hãy đưa ra câu bói ngắn gọn dễ hiểu về người có MSNV 13443 dựa vào nội dung đính kèm."},
        {
            "type": "text",
            "text": docs[0].page_content,
        },
        ]
    ),
]
response = model.invoke(message)
print("====>>", response)