# Konfigurasi Google API

## Langkah Setup Google Service Account

### 1. Buat Project di Google Cloud Console
- Buka https://console.cloud.google.com/
- Klik "New Project" dan beri nama (misal: spg-bot)

### 2. Aktifkan API yang diperlukan
Di menu "APIs & Services" > "Library", aktifkan:
- **Google Sheets API**
- **Google Drive API**

### 3. Buat Service Account
- Buka "APIs & Services" > "Credentials"
- Klik "Create Credentials" > "Service Account"
- Isi nama Service Account, klik "Done"

### 4. Download JSON Key
- Klik nama Service Account yang baru dibuat
- Buka tab "Keys" > "Add Key" > "Create New Key"
- Pilih format **JSON** dan klik "Create"
- File JSON akan otomatis terunduh

### 5. Setup Spreadsheet
- Buka Google Spreadsheet yang akan digunakan
- Klik tombol "Share" di pojok kanan atas
- Tambahkan **email Service Account** sebagai Editor
  (Email tertera di file JSON, field client_email)

### 6. Konfigurasi .env
`env
GOOGLE_SERVICE_ACCOUNT_FILE=nama-file-credentials.json
GOOGLE_SHEET_ID=id-spreadsheet-dari-url
GOOGLE_SHEET_NAME=NAMA_WORKSHEET
`

### Cara mendapat GOOGLE_SHEET_ID
Dari URL spreadsheet:
`
https://docs.google.com/spreadsheets/d/SHEET_ID_INI/edit#gid=0
                                        ^^^^^^^^^^^^^^^^^^^
                                        Ini adalah SHEET_ID
`
"@ | Out-File -FilePath "c:\ut\telegram-spg-bot\config\README.md" -Encoding utf8

@"
# Arsitektur Sistem — SPG Daily Reporting Automation Bot

## Gambaran Umum

Bot ini menghubungkan tiga komponen utama:

`
[SPG / Supervisor]
       |
       | Kirim pesan laporan (Telegram)
       v
[Telegram Bot API]
       |
       | Webhook / Long Polling
       v
[bot.py — Python Application]
       |
       |-- parse_semua_laporan()   : Parsing teks laporan
       |-- cari_spg()             : Identifikasi SPG
       |-- input_ke_sheet()       : Tulis ke Sheets
       v
[Google Sheets API]
       |
       v
[Google Spreadsheet] --> Data tersimpan, siap untuk laporan
`

## Alur Data

### Laporan Harian (FORMAT REPORT)

1. SPG kirim laporan di Telegram
2. Bot menerima pesan via handle_message()
3. Deteksi pola "FORMAT REPORT" di teks
4. parse_semua_laporan() mengekstrak: nama, selling, call, ec
5. cari_spg() cocokkan nama dengan database SPG
6. input_ke_sheet() menulis satu baris data ke Google Sheets
7. Bot membalas konfirmasi berhasil/gagal

### Status Absensi (sakit / off / ijin / dll)

1. Supervisor kirim teks seperti "maria sakit"
2. Bot deteksi kata kunci status di teks
3. cari_spg() identifikasi SPG dari teks yang sama
4. input_ke_sheet() tulis dengan keterangan status
5. Bot balas konfirmasi

### Bulk OFF (semua off)

1. Supervisor kirim "semua off"
2. Bot iterasi semua SPG di SPG_DATA
3. input_ke_sheet() dipanggil untuk setiap SPG
4. Bot balas ringkasan hasil input

## Komponen Teknis

| Komponen              | Detail                                              |
|-----------------------|-----------------------------------------------------|
| **Async Runtime**     | asyncio via python-telegram-bot 20.x                |
| **Sheet Connection**  | Session caching dengan re-auth otomatis             |
| **Row Detection**     | ind_next_empty_row() — aman untuk concurrent use |
| **Text Parsing**      | Regex + string split, case-insensitive              |
| **Auth**              | OAuth2 Service Account (tidak butuh interaksi user) |
| **Config**            | python-dotenv — zero hard-coded credentials         |
