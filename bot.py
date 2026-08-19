"""
SPG Daily Reporting Automation Bot
===================================
Telegram bot that automates daily SPG attendance and KPI reporting
directly into Google Sheets via the Google Sheets API.

Author  : Steven Diyanto
License : MIT
"""

import os
import re
import logging
from datetime import datetime

import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# -----------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------------------------------------------
load_dotenv()

TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN")
JSON_FILE  = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
SHEET_ID   = os.getenv("GOOGLE_SHEET_ID")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

if not all([TOKEN, JSON_FILE, SHEET_ID, SHEET_NAME]):
    raise EnvironmentError(
        "Pastikan semua variabel di file .env sudah diisi:\n"
        "  TELEGRAM_BOT_TOKEN, GOOGLE_SERVICE_ACCOUNT_FILE, "
        "GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME"
    )

# -----------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# DATABASE SPG (sample / demo data)
# -----------------------------------------------------------------
# NOTE: Replace this with your actual SPG roster.
# Each key is a short alias used for quick matching in messages.
SPG_DATA = {
    "rina": {
        "nama": "Rina Kartika",
        "program": "GROSIR",
        "id_toko": "7001001/7001002",
        "nama_toko": "TOKO MAKMUR (M2), TOKO SEJAHTERA (M2)",
    },
    "budi": {
        "nama": "Budi Santoso",
        "program": "GROSIR",
        "id_toko": "7002001/7002002",
        "nama_toko": "SUMBER REZEKI (M2), BERKAH JAYA (M4)",
    },
    "dewi": {
        "nama": "Dewi Lestari",
        "program": "GROSIR",
        "id_toko": "7003001/7003002",
        "nama_toko": "MAJU BERSAMA (M245), CAHAYA (M2)",
    },
    "hendra": {
        "nama": "Hendra Wijaya",
        "program": "GROSIR",
        "id_toko": "7004001/7004002",
        "nama_toko": "SINAR ABADI (M2), MANDIRI (M2)",
    },
    "sari": {
        "nama": "Sari Rahmawati",
        "program": "PASAR",
        "id_toko": "7005001/7005002",
        "nama_toko": "PRIMA PLASTIK (M2), ANUGRAH (M2)",
    },
    "eko": {
        "nama": "Eko Prasetyo",
        "program": "GROSIR",
        "id_toko": "7006001/7006002",
        "nama_toko": "CV. SENTOSA JAYA, HARAPAN (M2)",
    },
    "nita": {
        "nama": "Nita Permatasari",
        "program": "PASAR",
        "id_toko": "7007001/7007002",
        "nama_toko": "BINA USAHA (M2) / MELATI (M2)",
    },
}

# -----------------------------------------------------------------
# STATUS KEHADIRAN
# -----------------------------------------------------------------
STATUS_MAP = {
    "sakit": "SAKIT DENGAN SURAT DOKTER",
    "ijin":  "IJIN",
    "izin":  "IJIN",
    "cuti":  "CUTI",
    "alfa":  "ALFA",
    "off":   "OFF",
}

# -----------------------------------------------------------------
# GOOGLE SHEETS CONNECTION (with session caching)
# -----------------------------------------------------------------
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

_sheet_cache = None


def get_sheet():
    """
    Return a cached Google Sheets worksheet object.
    Re-authenticates automatically if the session has expired.
    """
    global _sheet_cache
    try:
        if _sheet_cache is not None:
            _sheet_cache.spreadsheet.title  # health-check
            return _sheet_cache
    except Exception:
        logger.info("Google Sheets session expired, re-authenticating...")
        _sheet_cache = None

    creds  = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, SCOPES)
    client = gspread.authorize(creds)
    _sheet_cache = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    logger.info("Connected to Google Sheets worksheet: '%s'", SHEET_NAME)
    return _sheet_cache


# -----------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------
def get_week(tanggal):
    """Return week number (1-5) based on day of month."""
    day = tanggal.day
    if day <= 7:  return 1
    if day <= 14: return 2
    if day <= 21: return 3
    if day <= 28: return 4
    return 5


def format_tanggal(tanggal):
    """Format date to Indonesian string, e.g. '19 Agustus 2026'."""
    bulan = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    return f"{tanggal.day} {bulan[tanggal.month]} {tanggal.year}"


def cari_spg(nama_input):
    """Find SPG by alias key or full name (case-insensitive)."""
    nama_lower = nama_input.lower()
    for key, spg in SPG_DATA.items():
        if key in nama_lower or spg["nama"].lower() in nama_lower:
            return spg
    return None


def find_next_empty_row(sheet, start_row=6):
    """Find the next empty row in column G, starting from start_row."""
    col_values = sheet.col_values(7)
    return max(len(col_values) + 1, start_row)


def input_ke_sheet(spg, keterangan, selling=None, call=None, ec=None):
    """Write one row of SPG report data to Google Sheets (columns G-S)."""
    sheet = get_sheet()
    now   = datetime.now()
    baris = find_next_empty_row(sheet)

    row_data = [[
        spg["nama"],        # G - Nama SPG
        keterangan,         # H - Keterangan kehadiran
        spg["program"],     # I - Program
        "CIREBON",          # J - Wilayah
        get_week(now),      # K - Minggu ke-
        format_tanggal(now),# L - Tanggal
        spg["id_toko"],     # M - ID Toko
        spg["nama_toko"],   # N - Nama Toko
        selling or "",      # O - Total Selling
        "",                 # P - (reserved)
        "",                 # Q - (reserved)
        call or "",         # R - Total Call
        ec or "",           # S - Total EC
    ]]
    sheet.update(f"G{baris}:S{baris}", row_data)
    logger.info("Input OK row=%d | %s | %s", baris, spg["nama"], keterangan)


# -----------------------------------------------------------------
# LAPORAN PARSER
# -----------------------------------------------------------------
def parse_semua_laporan(text):
    """
    Parse one or more SPG report blocks from a Telegram message.

    Supported format (flexible with spacing and casing):

        FORMAT REPORT SPG = RINA
        TOTAL SELLING = 25
        TOTAL CALL    = 40
        TOTAL EC      = 12

    Returns a list of dicts with keys: 'nama', 'selling', 'call', 'ec'.
    """
    hasil_list = []
    text = re.sub(r"[^\w\s\n=\/\-\(\)\.,:@#%]", " ", text)

    # Split into blocks (one per FORMAT REPORT header)
    bagian = []
    current = []
    for line in text.strip().splitlines():
        if "FORMAT REPORT" in line.upper():
            if current:
                bagian.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        bagian.append("\n".join(current))

    for blok in bagian:
        hasil = {}
        lines = blok.strip().splitlines()
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_upper = line_clean.upper()

            # --- Extract SPG name ---
            if "FORMAT REPORT" in line_upper:
                nama = re.sub(
                    r"FORMAT\s+REPORT\s+(SPG|SPB)\s*[=:]?\s*", "",
                    line_clean, flags=re.IGNORECASE,
                ).strip()
                if not nama and i + 1 < len(lines):
                    nama = lines[i + 1].strip()
                if nama:
                    hasil["nama"] = nama.title()

            # --- Extract KPIs ---
            elif "TOTAL SELLING" in line_upper:
                v = "".join(filter(str.isdigit, line_clean.split("=")[-1]))
                if v:
                    hasil["selling"] = v

            elif "TOTAL CALL" in line_upper:
                v = "".join(filter(str.isdigit, line_clean.split("=")[-1]))
                if v:
                    hasil["call"] = v

            elif "TOTAL EC" in line_upper:
                v = "".join(filter(str.isdigit, line_clean.split("=")[-1]))
                if v:
                    hasil["ec"] = v

        if "nama" in hasil:
            hasil_list.append(hasil)

    return hasil_list


# -----------------------------------------------------------------
# TELEGRAM HANDLERS
# -----------------------------------------------------------------
async def cmd_start(update, context):
    """Handler for /start command."""
    await update.message.reply_text(
        "SPG Reporting Bot\n\n"
        "Cara penggunaan:\n\n"
        "[1] Format Laporan Harian:\n"
        "FORMAT REPORT SPG = NAMA\n"
        "TOTAL SELLING = 25\n"
        "TOTAL CALL    = 40\n"
        "TOTAL EC      = 12\n\n"
        "[2] Status Absensi:\n"
        "Ketik: rina sakit | budi off | dewi ijin\n\n"
        "[3] Libur Massal:\n"
        "Ketik: semua off\n\n"
        "[4] Daftar SPG:\n"
        "Ketik: /daftar"
    )


async def cmd_daftar(update, context):
    """Handler for /daftar command — show all SPG."""
    lines = ["Daftar SPG Aktif:\n"]
    for spg in SPG_DATA.values():
        lines.append(f"- {spg['nama']} ({spg['program']})")
    await update.message.reply_text("\n".join(lines))


async def handle_message(update, context):
    """Main handler for all incoming text messages."""
    text  = update.message.text.strip()
    lower = text.lower()

    # 1. SEMUA OFF
    if lower == "semua off":
        await update.message.reply_text("Sedang menginput semua SPG menjadi OFF...")
        hasil_lines = ["Semua SPG berhasil diinput OFF:\n"]
        for spg in SPG_DATA.values():
            try:
                input_ke_sheet(spg=spg, keterangan="OFF")
                hasil_lines.append(f"- {spg['nama']}")
            except Exception as exc:
                logger.error("Gagal %s: %s", spg["nama"], exc)
                hasil_lines.append(f"GAGAL: {spg['nama']} - {exc}")
        await update.message.reply_text("\n".join(hasil_lines))
        return

    # 2. FORMAT REPORT
    if "FORMAT REPORT" in text.upper():
        semua_data = parse_semua_laporan(text)
        if not semua_data:
            await update.message.reply_text("Format laporan tidak dikenali.")
            return

        hasil_lines = ["Hasil Input Laporan:\n"]
        for data in semua_data:
            spg = cari_spg(data.get("nama", ""))
            if not spg:
                hasil_lines.append(f"SPG '{data.get('nama')}' tidak ditemukan\n")
                continue
            try:
                input_ke_sheet(
                    spg=spg,
                    keterangan="HADIR",
                    selling=data.get("selling"),
                    call=data.get("call"),
                    ec=data.get("ec"),
                )
                hasil_lines.append(
                    f"OK {spg['nama']}\n"
                    f"   Selling: {data.get('selling', '-')} | "
                    f"Call: {data.get('call', '-')} | "
                    f"EC: {data.get('ec', '-')}\n"
                )
            except Exception as exc:
                logger.error("Error %s: %s", spg["nama"], exc)
                hasil_lines.append(f"ERROR {spg['nama']}: {exc}\n")
        await update.message.reply_text("\n".join(hasil_lines))
        return

    # 3. STATUS ABSENSI
    for kata, status in STATUS_MAP.items():
        if kata in lower:
            spg = cari_spg(text)
            if spg:
                try:
                    input_ke_sheet(spg=spg, keterangan=status)
                    await update.message.reply_text(
                        f"Data berhasil diinput!\n\n"
                        f"Nama    : {spg['nama']}\n"
                        f"Status  : {status}\n"
                        f"Selling : -\n"
                        f"Call    : -\n"
                        f"EC      : -"
                    )
                except Exception as exc:
                    await update.message.reply_text(f"Error: {exc}")
                return

    # 4. TIDAK DIKENALI
    await update.message.reply_text(
        "Pesan tidak dikenali. Ketik /start untuk panduan."
    )


# -----------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------
def main():
    """Entry point — build and run the Telegram bot."""
    logger.info("Starting SPG Reporting Bot...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("daftar", cmd_daftar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()