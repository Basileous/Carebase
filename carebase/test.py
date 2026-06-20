import os
from google import genai

# 1. Update this with your NEW key
MY_API_KEY = "AIzaSyCQ35hYQNoaR4v33Jj11O8_25F-EABTCNw" 

try:
    print("🔄 Connecting to Gemini API...")
    client = genai.Client(api_key=MY_API_KEY)
    
    # 2. Test model access (using the latest 2026 Flash model)
    response = client.models.generate_content(
        model="gemini-3-flash-preview", 
        contents="Hello! Are you working?"
    )
    
    print("\n✅ CONNECTION SUCCESSFUL!")
    print(f"🤖 AI Response: {response.text}")
    
    # 3. List other available models just in case
    print("\n📋 Your available models:")
    for model in client.models.list_models():
        if "generateContent" in model.supported_generation_methods:
            print(f" - {model.name}")

except Exception as e:
    print("\n❌ CONNECTION FAILED")
    print(f"🚨 Error Details: {e}")