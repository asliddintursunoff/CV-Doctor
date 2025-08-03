# 🤖 CV Analyzer Bot with Gemini AI

This is a Telegram bot that analyzes users' CVs (PDF/DOCX) using **Google Gemini AI** and provides a structured score and personalized feedback in **Uzbek language**. Ideal for job seekers wanting to improve their resumes for specific roles.

---

## 🚀 Features

- 📎 Accepts CVs in PDF or DOCX format
- 🧠 Uses Gemini AI to:
  - Score the CV (0–100)
  - Provide strengths, weaknesses, and suggestions
- 🌐 Feedback is generated in **Uzbek**
- 📱 Phone number verification (via Telegram contact)
- 🔄 Animated typing feedback while Gemini processes input
- 🧼 Cleans up markdown for better message formatting
- 💾 Stores user data (SQL)

---

## 🛠️ Tech Stack

- Python 3.12+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Google Gemini AI SDK (`google.generativeai`)
- PyPDF2 / python-docx
- PostgreSQL (for user data)


---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/asliddintursunoff/CV-Doctor.git
cd CV-Doctor
