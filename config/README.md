# Konfigurasi Google API

## Langkah Setup Google Service Account

### 1. Buat Project di Google Cloud Console
Buka https://console.cloud.google.com/ dan klik New Project.

### 2. Aktifkan API yang diperlukan
Di menu APIs and Services > Library, aktifkan:
- Google Sheets API
- Google Drive API

### 3. Buat Service Account
- Buka APIs and Services > Credentials
- Klik Create Credentials > Service Account
- Isi nama Service Account, klik Done

### 4. Download JSON Key
- Klik nama Service Account yang baru dibuat
- Buka tab Keys > Add Key > Create New Key
- Pilih format JSON dan klik Create
- File JSON akan otomatis terunduh

### 5. Setup Spreadsheet
- Buka Google Spreadsheet yang akan digunakan
- Klik tombol Share di pojok kanan atas
- Tambahkan email Service Account sebagai Editor
  (Email tertera di file JSON, field client_email)

### 6. Konfigurasi .env

  GOOGLE_SERVICE_ACCOUNT_FILE=nama-file-credentials.json
  GOOGLE_SHEET_ID=id-spreadsheet-dari-url
  GOOGLE_SHEET_NAME=NAMA_WORKSHEET

### Cara mendapat GOOGLE_SHEET_ID

Dari URL spreadsheet:
  https://docs.google.com/spreadsheets/d/SHEET_ID_INI/edit#gid=0
                                          ^^^^^^^^^^^^^
                                          Ini adalah SHEET_ID
