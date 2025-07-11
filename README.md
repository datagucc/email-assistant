Here’s a full `README.md` in English tailored to your Smart Email Assistant project, showcasing features, setup, usage, and security:

---

# 📬 Smart Email Assistant

Smart Email Assistant is a powerful, privacy-first tool that connects to your Gmail inbox to **automatically classify**, **summarize**, and **draft replies** using LLMs. It improves your email workflow while keeping you in control — all emails are processed locally or through secure, sanitized APIs.

---

## 🚀 Features

* ✉️ **Multi-source email ingestion**: Supports `.eml` files, IMAP, and Gmail API
* 🧠 **Multi-axis classification**: By type, priority, source, and required action
* 📝 **LLM-generated reply drafts**: Personalized replies saved directly to Gmail as drafts
* 📦 **Weekly digest of newsletters**: Summarized and sent to your preferred inbox
* 🔐 **Security-focused**: Input sanitation, prompt injection protection, and safe draft generation
* 🏷️ **Gmail labeling**: Auto-labels your emails in Gmail with category-specific colors
* ⛔ **Smart filters**: Ignores spam, junk, and "do not reply" emails

---

## 📂 Folder Structure

```
email_assistant/
│
├── Modules/
│   ├── gmail_service.py          # Gmail API logic
│   ├── classification.py         # Custom classifiers
│   ├── summarizer.py             # LLM summary and reply
│   ├── security.py               # Injection and input sanitization
│   └── utils.py                  # Helpers: decoding, parsing, etc.
│
├── data/
│   └── drafts/                   # Draft backups (optional)
│
├── main_prod.py                  # Main production script
└── README.md
```

---

## 🛠️ Setup

1. **Clone the repo**

```bash
git clone https://github.com/yourusername/email-assistant.git
cd email-assistant
```

2. **Install dependencies**

```bash
python -m venv email_venv
source email_venv/bin/activate
pip install -r requirements.txt
```

3. **Configure Gmail API**

* Create a Google Cloud Project
* Enable Gmail API
* Generate OAuth 2.0 credentials
* Add your email addresses as test users
* Save the `credentials.json` in the root folder

4. **Authenticate once**

```bash
python authenticate_gmail.py
```

---

## ⚙️ Usage

```bash
python main_prod.py
```

By default, the script:

* Connects to Gmail
* Classifies emails
* Applies labels with colors
* Generates smart drafts
* Marks as unread if needed

---

## 🔒 Security

* **Input cleaning**: HTML/JS removed, unescaped safely
* **LLM injection protection**: Regex-based filters for common injection patterns in multiple languages
* **Link blocking**: No automatic link parsing or clicking
* **No code execution**: LLMs are instructed not to process executable content

---

## ✅ Roadmap

* [x] Multi-inbox classification
* [x] LLM-based summaries
* [x] Draft replies
* [x] Gmail API integration
* [ ] Web dashboard for visualization
* [ ] OAuth token refresh automation

---

## 📧 Author

**Augustin Nollevaux**
[LinkedIn](https://www.linkedin.com/in/augustin-nollevaux/) – Freelance Data Engineer & Builder

---

Let me know if you'd like to add badges, GIFs, a quickstart demo, or sections for contributing, license, or tests.
