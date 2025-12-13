import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("사용 가능한 모델 목록:")
print("-" * 50)

try:
    models = genai.list_models()
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   지원 메서드: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"오류: {e}")
