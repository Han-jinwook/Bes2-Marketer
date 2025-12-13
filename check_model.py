import os
os.environ["GEMINI_API_KEY"] = "AIzaSyCW9IZb9kriP8CrSL8EI2vjqkbFBzpzqB8"

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

models_to_test = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro"
]

print("=" * 60)
print("Gemini 모델 테스트 시작")
print("=" * 60)

working_model = None

for model_name in models_to_test:
    try:
        print(f"\n테스트 중: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("안녕하세요")
        print(f"✅ SUCCESS: {model_name}")
        print(f"응답: {response.text[:100]}")
        if not working_model:
            working_model = model_name
    except Exception as e:
        print(f"❌ FAILED: {model_name}")
        print(f"에러: {str(e)[:200]}")

print("\n" + "=" * 60)
if working_model:
    print(f"🎉 작동하는 모델: {working_model}")
else:
    print("⚠️ 모든 모델 실패 - API 키 또는 할당량 문제")
print("=" * 60)
