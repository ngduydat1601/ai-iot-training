import os
import time
from dotenv import load_dotenv
from google import genai

# ==========================
# Load API Key
# ==========================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Không tìm thấy GEMINI_API_KEY trong file .env")

# ==========================
# Khởi tạo Gemini Client
# ==========================

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.6-flash"

MAX_RETRY = 3

# ==========================
# Gọi Gemini API
# ==========================

def ask_gemini(prompt):

    for attempt in range(1, MAX_RETRY + 1):

        try:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            # Parse response
            if response.text:
                return response.text

            return "Gemini không trả về nội dung."

        except Exception as e:

            print(f"\n[Lỗi] {e}")

            if attempt < MAX_RETRY:

                print(f"Retry {attempt}/{MAX_RETRY} sau 2 giây...\n")

                time.sleep(2)

            else:

                return "Không thể kết nối tới Gemini API."

# ==========================
# Main
# ==========================

def main():

    print("=" * 50)
    print("Simple Gemini Chatbot")
    print("Gõ 'exit' để thoát.")
    print("=" * 50)

    while True:

        prompt = input("\nBạn: ")

        if prompt.lower() == "exit":
            break

        answer = ask_gemini(prompt)

        print("\nGemini:")
        print(answer)

if __name__ == "__main__":
    main()