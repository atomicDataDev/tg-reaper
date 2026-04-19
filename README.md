# TG REAPER v1.0 

**TG REAPER** is a professional, multi-functional Telegram automation tool built with **Telethon** and **Rich**. Designed for security researchers and automation enthusiasts, it features a high-performance terminal interface and a robust session management system.

## ⚖️ License & Disclaimer

This project is licensed under the [MIT License](LICENSE).

**WARNING:** This tool is for educational and authorized testing purposes only. Using it for spamming, harassment, or any activity that violates Telegram's Terms of Service is strictly prohibited and may result in your accounts being permanently banned. The developer is not responsible for any account bans, legal consequences, or misuse of this software.

---

## 🔥 Key Features

- **Multi-Session Support & Manager:** Use unlimited `.session` files. Automatically check account health, verify authorization, and remove "dead" sessions.
- **SpamBot Checker:** Instant status check for account restrictions and spam-bans via `@SpamBot`.
- **DM Sender & Commenter:** Send automated direct messages to users (via username/phone) or drop comments on the latest channel posts using a "Round-robin" account distribution.
- **Mass Subscription:** Join channels and groups using multiple accounts simultaneously.
- **Reporting System:** Automated mass complaints against profiles or specific messages (Spam, Violence, Drugs, etc.).
- **Calls & Combo Mode:** High-intensity calling and "Call + Message" combinations to bypass ignore lists.
- **Secret Chats (TTL):** Create encrypted secret chats (AES-IGE) and automatically force Self-Destruct Timers.
- **TTL Spam:** Rapidly toggle auto-deletion settings in normal chats to trigger multiple notifications.
- **Advanced UI:** Clean, color-coded terminal interface with tables and progress bars powered by Rich.

---

## 🛡️ Anti-Detection System

To ensure stability and prevent accounts from being logged out, TG REAPER utilizes a **Unified Desktop Profile** strategy:
- Every session mimics a **Windows 10 Telegram Desktop** environment.
- Fixed device parameters (`device_model: Desktop`, `system_version: Windows 10`, `app_version: 4.16.8 x64`) prevent "session drops" caused by device switching.
- Fully compatible with `.session` files created by other popular management tools.

---

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/atomicDataDev/tg-reaper.git
   cd tg-reaper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or manually: pip install telethon rich cryptography python-dotenv
   ```

3. **Environment Setup (API Keys):**
   Create a `.env` file in the root directory and add your credentials as it shown in `.env.example` obtained from [my.telegram.org](https://my.telegram.org/) 

4. **Add Sessions:**
   Place your existing Telegram `.session` files into the `sessions/` directory.

---

## ⚙️ Configuration

You can customize the tool's behavior by modifying the `config.py` file:

- `DM_MESSAGES`: List of phrases for direct messages.

- `COMMENT_MESSAGES`: Phrases for channel commenting.

- `MESSAGE_MODE`: Choose how messages are picked (sequential or random).

- `REPORT_REASONS`: Mapping of available complaint/report types.

---

## 📖 Usage

Run the main application:
```bash
python main.py
```

### Controls & Navigation:
- **Menu:** Use numeric keys (0-9) to navigate between modes.

- **Stop:** Press `Ctrl+C` to safely interrupt any running process or cycle.

- **Targeting:** The tool supports inputs in the form of `@usernames`, phone numbers (in international format), and `t.me/` links.

---

## 📁 Project Structure

```python
tg-reaper/
├── main.py        # Application entry point
├── config.py      # Message templates and global behavior settings
├── ui.py          # Rich-based terminal interface logic
├── .env           # (Create this) Your API keys
├── requirements.txt
├── sessions/      # Directory for your .session files
├── utils/         # Core logic: parsers, session handling, device emulation
├── modes/         # Logic modules for each specific menu action
└── crypto/        # Custom implementation for Secret Chat encryption (AES-IGE)
```