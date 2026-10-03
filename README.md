# WhatsApp Web Relay (Selenium)

Automation script that watches a source chat on WhatsApp Web, detects new messages,
and forwards them to a destination chat. It preserves formatting, emojis, and
Chinese/Unicode text.

## Features
- Detects new messages in a source chat and relays them to a destination chat
- Filters out picture/media-only messages
- Keyword-based detection of job-posting messages
- Unicode/emoji handling: Chrome's `send_keys` only supports BMP characters, so the
  script pastes through the clipboard (`pyperclip`) instead
- Preserves line breaks and detects WhatsApp CSS bullets
- Expands "read more" messages before copying

## Requirements
- Python 3.9+
- Google Chrome (Selenium 4.6+ manages ChromeDriver automatically)
- Install dependencies: `pip install -r requirements.txt`

## Setup
1. Clone or download this repo.
2. Open the script and set your chat names:
```python
   SOURCE_CHAT = "Your Source Chat Name"
   DESTINATION_CHAT = "Your Destination Chat Name"
```
3. Run the script: `python your_script_name.py`
4. Scan the QR code in the Chrome window that opens.

## How it works
1. Opens WhatsApp Web and waits for login.
2. Polls the source chat for the latest message.
3. Extracts the text with formatting (bullets, emojis, line breaks).
4. Copies it to the clipboard and pastes it into the destination chat.

## Disclaimer
For personal and educational use only. Automating WhatsApp Web may violate
WhatsApp's Terms of Service and can get an account restricted. Use at your own risk.
