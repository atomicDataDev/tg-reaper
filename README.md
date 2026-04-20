# TG REAPER v2.0

**TG REAPER** is a professional, multi-functional Telegram automation tool built with **Telethon** and **Rich**. Designed for security researchers and automation enthusiasts, it features a high-performance terminal interface, a robust session management system, and advanced stealth capabilities.

## ⚖️ License & Disclaimer

This project is licensed under the [MIT License](LICENSE).

**WARNING:** This tool is for educational and authorized testing purposes only. Using it for spamming, harassment, or any activity that violates Telegram's Terms of Service is strictly prohibited and may result in your accounts being permanently banned. The developer is not responsible for any account bans, legal consequences, or misuse of this software.

---

## 🔥 Key Features

- **Advanced Session Manager:** Fully integrated session management via `manager.py`. Create, recreate, list, and verify sessions effortlessly.
- **Persistent Device Emulation:** Automatically generates and saves unique Desktop device fingerprints (OS, App Version, Device Model) into `accounts.json` for each session.
- **Account Actions:** Manage 2FA Cloud Passwords, login emails, intercept authentication codes, and terminate other active sessions directly from the manager.
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

To ensure stability and prevent accounts from being logged out, TG REAPER utilizes a **Persistent Device Profile** strategy:
- Every session mimics a valid **Desktop** environment (Windows, macOS, Linux).
- Device parameters (`device_model`, `system_version`, `app_version`, `lang_code`) are generated upon session creation and stored permanently in `accounts.json`.
- This ensures consistency and prevents "session drops" caused by device switching on subsequent logins.

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
   # Or manually: pip install telethon rich python-dotenv
   ```

3. **Environment Setup (API Keys):**
   Copy the provided `.env.example` file to `.env` in the root directory and add your credentials (obtained from [my.telegram.org](https://my.telegram.org/)). 
   ```bash
   cp .env.example .env
   ```

4. **Add Sessions:**
   Run `manager.py` and choose option `1` to create new `.session` files. Your sessions and their corresponding persistent device data will be automatically stored in `accounts/sessions` and `accounts.json`. You can see the structure of the data generated in the `accounts.example.json` file.

---

## ⚙️ Configuration

You can customize the tool's behavior by modifying the `config.py` file:

- `DM_MESSAGES`: List of phrases for direct messages.
- `COMMENT_MESSAGES`: Phrases for channel commenting.
- `MESSAGE_MODE`: Choose how messages are picked (sequential or random).
- `REPORT_REASONS`: Mapping of available complaint/report types.

---

## 📖 Usage

### Session Manager
Run the session management interface to create and maintain your accounts:
```bash
python manager.py
```
- List sessions, check health, recreate broken sessions, intercept codes, and manage emails/passwords.

### Main Application (Attack Modes)
Run the main application for automation and messaging tasks:
```bash
python main.py
```
- **Menu:** Use numeric keys to navigate between modes.
- **Stop:** Press `Ctrl+C` to safely interrupt any running process or cycle.
- **Targeting:** The tool supports inputs in the form of `@usernames`, phone numbers (in international format), and `t.me/` links.

---

## 📁 Project Structure

```python
tg-reaper/
├── main.py        # Main application entry point
├── manager.py     # Session Manager entry point
├── config.py      # Message templates and global behavior settings
├── ui/            # Rich-based terminal interface logic
├── .env           # (Create this) Your API keys
├── requirements.txt
├── accounts.example.json # Example structure of the accounts.json file
├── accounts.json  # Persistent storage for session device fingerprints
├── accounts/      # Directory containing your .session files
├── core/          # Core modules: Client factory, account store, device emulation
├── utils/         # Helpers: parsers, session handling
├── modes/         # Logic modules for each specific attack mode action
├── manager_modes/ # Logic modules for session management actions
└── crypto/        # Custom implementation for Secret Chat encryption (AES-IGE)
```