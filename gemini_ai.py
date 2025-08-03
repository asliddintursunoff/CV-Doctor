from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import time



load_dotenv()
gemini_api = os.getenv("GEMINI_API")


def build_cv_review_prompt(cv_text: str, major: str) -> str:
    return f"""
Siz rezyume (CV) ekspertisiz. Quyidagi foydalanuvchi rezyumesini {major} sohasidagi ish uchun tahlil qiling.

1. Rezyumega **raqamli baho bering** (0 dan 100 gacha). Baho avval yozilsin, masalan: `67/100` kabi.
2. Baho berilgandan so‘ng, **kuchli tomonlari** haqida yozing.
3. So‘ng, **kuchsiz yoki yaxshilanishi kerak bo‘lgan joylar** haqida yozing.
4. Oxirida **ancha mukammal bo‘lishi uchun tavsiyalar** bering.

Matnda muhim fikrlar yoki sarlavhalar uchun `*yulduzcha*` belgisi ishlatmang. Buning o‘rniga bold (qalin) formatda yozing (ya’ni ikki yulduzcha orasida: `**matn**` qilib yozmang).


Natijalarni to‘liq O‘zbek tilida yozing.

Rezyume matni:
\"\"\"
{cv_text}
\"\"\"
"""





load_dotenv()
gemini_api = os.getenv("GEMINI_API")

def generate_response(text: str, major: str):
    prompt = build_cv_review_prompt(text, major)

    if not gemini_api:
        raise ValueError("❌ GEMINI_API key is missing.")

   
 

    client = genai.Client(api_key=gemini_api)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        response_mime_type="text/plain"
    )

   
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=contents,
        config=config,
     
    )

   
    return response.text  
