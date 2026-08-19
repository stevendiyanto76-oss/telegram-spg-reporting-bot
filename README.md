# SPG Daily Reporting Automation Bot

> A Python-based Telegram bot that **automates daily SPG attendance and KPI reporting**, parsing structured messages and syncing data directly to **Google Sheets** via the Google Sheets API.

---

## Overview

In a typical field sales operation, SPG (Sales Promotion Girls/Boys) supervisors collect daily reports through Telegram group chats. These reports contain attendance statuses and KPI metrics (Selling, Call, EC) that must be manually entered into spreadsheets — a repetitive and error-prone process.

This bot eliminates that manual work entirely.

---

## Features

- **Auto-parse laporan harian** — baca format laporan dari Telegram dan ekstrak data otomatis
- **Multi-report dalam satu pesan** — mendukung laporan banyak SPG sekaligus
- **Flexible parsing** — toleran terhadap variasi spasi, format huruf, dan typo ringan
- **Attendance status** — input status HADIR / SAKIT / IJIN / CUTI / ALFA / OFF
- **Bulk OFF command** — liburkan semua SPG sekaligus dengan semua off
- **Google Sheets sync** — data langsung masuk ke sheet yang tepat, di baris yang benar
- **Session caching** — koneksi Google Sheets di-cache agar lebih efisien
- **Secure config** — semua credential diambil dari environment variable, tidak ada yang hard-coded

---

## Tech Stack

| Layer              | Technology                       |
|--------------------|----------------------------------|
| Language           | Python 3.11+                     |
| Telegram API       | python-telegram-bot 20.x (async) |
| Google Sheets API  | gspread + oauth2client           |
| Auth               | Google Service Account (OAuth2)  |
| Config Management  | python-dotenv                    |
| Parsing            | Built-in re (regex)              |

---

## How It Works

`
Telegram Message
      │
      ▼
  handle_message()
      │
      ├─► "semua off"        → bulk OFF untuk semua SPG
      │
      ├─► "FORMAT REPORT"    → parse_semua_laporan()
      │         │                   │
      │         │              Regex parser
      │         │            (nama, selling, call, ec)
      │         │                   │
      │         └──────────── cari_spg() ──► input_ke_sheet()
      │
      └─► "maria sakit"      → cari_spg() ──► input_ke_sheet()
                                                    │
                                              get_sheet() (cached)
                                                    │
                                           Google Sheets API
`

---

## Example Usage

**Format Laporan Harian:**
`
FORMAT REPORT SPG = MARIA
TOTAL SELLING = 25
TOTAL CALL    = 40
TOTAL EC      = 12
`

**Multi-report dalam satu pesan:**
`
FORMAT REPORT SPG = NOVI
TOTAL SELLING = 30
TOTAL CALL = 45
TOTAL EC = 8

FORMAT REPORT SPG = AGUS
TOTAL SELLING = 20
TOTAL CALL = 33
TOTAL EC = 5
`

**Status Absensi:**
`
maria sakit
agus off
novi ijin
`

**Libur Massal:**
`
semua off
`

---

## Google Sheets Structure

Data ditulis mulai kolom **G** sampai **S**:

| Kolom | Field         |
|-------|---------------|
| G     | Nama SPG      |
| H     | Keterangan    |
| I     | Program       |
| J     | Wilayah       |
| K     | Minggu ke-    |
| L     | Tanggal       |
| M     | ID Toko       |
| N     | Nama Toko     |
| O     | Total Selling |
| R     | Total Call    |
| S     | Total EC      |

---

## Installation

**1. Clone repository**
`ash
git clone https://github.com/YOUR_USERNAME/telegram-spg-reporting-bot.git
cd telegram-spg-reporting-bot
`

**2. Buat virtual environment**
`ash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Linux/Mac
`

**3. Install dependencies**
`ash
pip install -r requirements.txt
`

**4. Setup environment variables**
`ash
cp .env.example .env
# Edit file .env dan isi semua nilai yang diperlukan
`

**5. Setup Google Service Account**
- Buka [Google Cloud Console](https://console.cloud.google.com/)
- Buat Service Account dan download file JSON credentials
- Aktifkan Google Sheets API dan Google Drive API
- Share spreadsheet dengan email Service Account
- Letakkan file JSON credentials di folder proyek (jangan commit!)

**6. Jalankan bot**
`ash
python bot.py
`

---

## Environment Variables

| Variable                    | Description                                    |
|-----------------------------|------------------------------------------------|
| TELEGRAM_BOT_TOKEN        | Token dari @BotFather                          |
| GOOGLE_SERVICE_ACCOUNT_FILE | Path ke file JSON credentials               |
| GOOGLE_SHEET_ID           | ID Google Spreadsheet (dari URL)               |
| GOOGLE_SHEET_NAME         | Nama worksheet/tab di spreadsheet              |

---

## Security

> Pastikan hal-hal berikut **TIDAK pernah** masuk ke repository:
> - File .env
> - File JSON credentials Google Service Account
> - Token Telegram yang nyata
> - Data internal perusahaan atau pelanggan

File .gitignore sudah dikonfigurasi untuk mencegah ini secara otomatis.

---

## Project Structure

`
telegram-spg-reporting-bot/
├── bot.py                  # Main application
├── requirements.txt        # Python dependencies
├── .env.example            # Template environment variables
├── .gitignore              # Git exclusions
├── README.md               # Documentation
├── config/
│   └── README.md           # Petunjuk konfigurasi Google API
└── docs/
    └── architecture.md     # Diagram arsitektur sistem
`

---

## Future Improvements

- [ ] Database lokal (SQLite) sebagai backup sebelum sync ke Sheets
- [ ] Dashboard ringkasan mingguan via command /summary
- [ ] Notifikasi otomatis jika ada SPG belum lapor sampai jam tertentu
- [ ] Support multi-wilayah / multi-sheet
- [ ] Unit tests untuk parser laporan
- [ ] Docker support untuk deployment ke VPS

---

## License

MIT License — bebas digunakan dan dimodifikasi dengan menyertakan atribusi.

---

*Built with Python, python-telegram-bot, and Google Sheets API.*
