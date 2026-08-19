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
# DATABASE SPG (sample / demo data — 100 entries)
# -----------------------------------------------------------------
# NOTE: Replace this with your actual SPG roster.
# Each key is a short alias used for quick matching in messages.
SPG_DATA = {
    "susi": {
        "nama": "Susi Siregar",
        "program": "PASAR",
        "id_toko": "6074341/6094098",
        "nama_toko": "JAYA MAKMUR (M3), MAKMUR PRIMA (M3)",
    },
    "laila": {
        "nama": "Laila Purnama",
        "program": "PASAR",
        "id_toko": "6018301/6032325",
        "nama_toko": "HIKMAH MULIA (M6), HARAPAN SENTOSA (M3)",
    },
    "putra": {
        "nama": "Putra Wicaksono",
        "program": "PASAR",
        "id_toko": "6047447/6028746",
        "nama_toko": "GROSIR AGUNG (M2), CAHAYA SEMBAKO (M2)",
    },
    "maya": {
        "nama": "Maya Syahputra",
        "program": "GROSIR",
        "id_toko": "6020969/6089192",
        "nama_toko": "ABADI SUKSES (M3), UD MAJU (M6)",
    },
    "hendri": {
        "nama": "Hendri Maulana",
        "program": "GROSIR",
        "id_toko": "6032953/6072512",
        "nama_toko": "TOKO JAYA (M245), SEJAHTERA MULIA (M245)",
    },
    "budi": {
        "nama": "Budi Mulyani",
        "program": "PASAR",
        "id_toko": "6056985/6020730",
        "nama_toko": "MANDIRI PLASTIK (M6), HIKMAH SENTOSA (M4)",
    },
    "dewi": {
        "nama": "Dewi Permatasari",
        "program": "PASAR",
        "id_toko": "6081959/6039117",
        "nama_toko": "MAKMUR AGUNG (M4), ANUGRAH MAKMUR (M245)",
    },
    "nanda": {
        "nama": "Nanda Yulianti",
        "program": "GROSIR",
        "id_toko": "6069514/6000074",
        "nama_toko": "ANUGRAH MANDIRI (M2), CAHAYA PLASTIK (M245)",
    },
    "nurul": {
        "nama": "Nurul Suherman",
        "program": "PASAR",
        "id_toko": "6007592/6031571",
        "nama_toko": "RIZKI SEMBAKO (M2), UD PRIMA (M6)",
    },
    "yusuf": {
        "nama": "Yusuf Susanto",
        "program": "PASAR",
        "id_toko": "6086474/6062296",
        "nama_toko": "HARAPAN ABADI (M6), BERKAH AGUNG (M3)",
    },
    "roni": {
        "nama": "Roni Yulianti",
        "program": "GROSIR",
        "id_toko": "6098994/6095673",
        "nama_toko": "BAROKAH MAKMUR (M3), BAROKAH UTAMA (M245)",
    },
    "dian": {
        "nama": "Dian Maulana",
        "program": "PASAR",
        "id_toko": "6059177/6015860",
        "nama_toko": "SUMBER INDAH (M2), UD MANDIRI (M6)",
    },
    "dedi": {
        "nama": "Dedi Hakim",
        "program": "GROSIR",
        "id_toko": "6077128/6028864",
        "nama_toko": "TOKO SEMBAKO (M2), BAROKAH BERKAH (M4)",
    },
    "wahyu": {
        "nama": "Wahyu Lestari",
        "program": "PASAR",
        "id_toko": "6043309/6009287",
        "nama_toko": "BINTANG INDAH (M4), BERKAH PRIMA (M6)",
    },
    "prasetyo": {
        "nama": "Prasetyo Sucipto",
        "program": "GROSIR",
        "id_toko": "6074847/6075525",
        "nama_toko": "CAHAYA INDAH (M4), CAHAYA BARU (M2)",
    },
    "rina": {
        "nama": "Rina Oktaviani",
        "program": "GROSIR",
        "id_toko": "6056498/6046438",
        "nama_toko": "ABADI BARU (M2), MANDIRI KELONTONG (M2)",
    },
    "vera": {
        "nama": "Vera Sucipto",
        "program": "GROSIR",
        "id_toko": "6044473/6014322",
        "nama_toko": "SUMBER MAKMUR (M3), DEPOT MULIA (M4)",
    },
    "ridwan": {
        "nama": "Ridwan Saputra",
        "program": "PASAR",
        "id_toko": "6036509/6060637",
        "nama_toko": "SUMBER SEMBAKO (M2), MANDIRI MULIA (M2)",
    },
    "umar": {
        "nama": "Umar Kartika",
        "program": "GROSIR",
        "id_toko": "6012224/6098771",
        "nama_toko": "SUMBER ABADI (M3), ABADI PRIMA (M4)",
    },
    "sinta": {
        "nama": "Sinta Wijaya",
        "program": "PASAR",
        "id_toko": "6021579/6049672",
        "nama_toko": "TOKO MAJU (M245), BERKAH LESTARI (M3)",
    },
    "hesti": {
        "nama": "Hesti Oktaviani",
        "program": "PASAR",
        "id_toko": "6094163/6063788",
        "nama_toko": "GROSIR MAKMUR (M2), PRIMA MAKMUR (M6)",
    },
    "eni": {
        "nama": "Eni Wijaya",
        "program": "PASAR",
        "id_toko": "6098038/6041104",
        "nama_toko": "TB KELONTONG (M6), RIZKI PRIMA (M6)",
    },
    "lia": {
        "nama": "Lia Wijaya",
        "program": "GROSIR",
        "id_toko": "6066562/6010500",
        "nama_toko": "WARUNG SEMBAKO (M4), ANUGRAH SEMBAKO (M3)",
    },
    "wawan": {
        "nama": "Wawan Sulistyo",
        "program": "PASAR",
        "id_toko": "6032271/6075880",
        "nama_toko": "ANUGRAH KELONTONG (M3), ANUGRAH SEMBAKO (M6)",
    },
    "dimas": {
        "nama": "Dimas Maulana",
        "program": "GROSIR",
        "id_toko": "6041467/6034179",
        "nama_toko": "DEPOT MANDIRI (M3), SUMBER SENTOSA (M4)",
    },
    "aisyah": {
        "nama": "Aisyah Anggraeni",
        "program": "GROSIR",
        "id_toko": "6041441/6098548",
        "nama_toko": "UD PLASTIK (M6), MANDIRI SUKSES (M2)",
    },
    "hasan": {
        "nama": "Hasan Yulianti",
        "program": "GROSIR",
        "id_toko": "6027938/6066307",
        "nama_toko": "BERKAH BERSAMA (M4), SENTOSA SEMBAKO (M245)",
    },
    "neni": {
        "nama": "Neni Kurniawan",
        "program": "PASAR",
        "id_toko": "6057433/6071200",
        "nama_toko": "BAROKAH UTAMA (M6), ANUGRAH BERKAH (M2)",
    },
    "lutfi": {
        "nama": "Lutfi Hartono",
        "program": "GROSIR",
        "id_toko": "6086951/6013577",
        "nama_toko": "GROSIR SENTOSA (M6), CV JAYA (M4)",
    },
    "dina": {
        "nama": "Dina Mulyani",
        "program": "GROSIR",
        "id_toko": "6079276/6027607",
        "nama_toko": "BAROKAH MANDIRI (M245), DEPOT BERKAH (M6)",
    },
    "lina": {
        "nama": "Lina Purnama",
        "program": "PASAR",
        "id_toko": "6006658/6012097",
        "nama_toko": "MAKMUR BARU (M2), BERKAH KELONTONG (M245)",
    },
    "reni": {
        "nama": "Reni Syahputra",
        "program": "GROSIR",
        "id_toko": "6034335/6021178",
        "nama_toko": "HIKMAH LESTARI (M6), HARAPAN BARU (M2)",
    },
    "joko": {
        "nama": "Joko Rahmawati",
        "program": "GROSIR",
        "id_toko": "6090573/6019536",
        "nama_toko": "HARAPAN KELONTONG (M6), SENTOSA PRATAMA (M4)",
    },
    "fajar": {
        "nama": "Fajar Susanto",
        "program": "GROSIR",
        "id_toko": "6005482/6040404",
        "nama_toko": "SENTOSA KELONTONG (M4), SENTOSA MAKMUR (M2)",
    },
    "surya": {
        "nama": "Surya Mubarok",
        "program": "GROSIR",
        "id_toko": "6073385/6053264",
        "nama_toko": "ANUGRAH BERSAMA (M4), SUMBER ABADI (M3)",
    },
    "ida": {
        "nama": "Ida Saputra",
        "program": "GROSIR",
        "id_toko": "6096542/6043540",
        "nama_toko": "ABADI INDAH (M2), BERKAH ABADI (M3)",
    },
    "zaenal": {
        "nama": "Zaenal Hermawan",
        "program": "PASAR",
        "id_toko": "6029154/6026158",
        "nama_toko": "MANDIRI SEJAHTERA (M4), PRIMA INDAH (M2)",
    },
    "eko": {
        "nama": "Eko Wicaksono",
        "program": "PASAR",
        "id_toko": "6043025/6036517",
        "nama_toko": "UD SENTOSA (M6), SENTOSA BERKAH (M3)",
    },
    "jaya": {
        "nama": "Jaya Gunawan",
        "program": "PASAR",
        "id_toko": "6003617/6015118",
        "nama_toko": "BERKAH ABADI (M2), RIZKI SENTOSA (M2)",
    },
    "ratna": {
        "nama": "Ratna Handayani",
        "program": "PASAR",
        "id_toko": "6045309/6095491",
        "nama_toko": "JAYA BARU (M2), ANUGRAH AGUNG (M3)",
    },
    "yeni": {
        "nama": "Yeni Nugroho",
        "program": "GROSIR",
        "id_toko": "6033386/6005817",
        "nama_toko": "BAROKAH BARU (M6), TOKO AGUNG (M4)",
    },
    "novi": {
        "nama": "Novi Handayani",
        "program": "GROSIR",
        "id_toko": "6009171/6087062",
        "nama_toko": "JAYA SUKSES (M245), JAYA JAYA (M6)",
    },
    "nisa": {
        "nama": "Nisa Oktaviani",
        "program": "GROSIR",
        "id_toko": "6053528/6042753",
        "nama_toko": "MAJU UTAMA (M4), HARAPAN BERSAMA (M3)",
    },
    "winda": {
        "nama": "Winda Priyanto",
        "program": "GROSIR",
        "id_toko": "6098059/6022810",
        "nama_toko": "ANUGRAH PRATAMA (M6), PRIMA MAJU (M2)",
    },
    "tika": {
        "nama": "Tika Mulyani",
        "program": "GROSIR",
        "id_toko": "6027549/6056346",
        "nama_toko": "RIZKI SUKSES (M3), MAKMUR MANDIRI (M3)",
    },
    "iwan": {
        "nama": "Iwan Priyanto",
        "program": "PASAR",
        "id_toko": "6028010/6067000",
        "nama_toko": "CAHAYA ABADI (M245), SEJAHTERA SEMBAKO (M6)",
    },
    "arif": {
        "nama": "Arif Gunawan",
        "program": "GROSIR",
        "id_toko": "6012240/6098453",
        "nama_toko": "SUMBER UTAMA (M4), SUMBER MAKMUR (M2)",
    },
    "rudi": {
        "nama": "Rudi Suherman",
        "program": "GROSIR",
        "id_toko": "6062277/6080120",
        "nama_toko": "UD LESTARI (M6), ABADI BERKAH (M4)",
    },
    "ika": {
        "nama": "Ika Kusuma",
        "program": "PASAR",
        "id_toko": "6052383/6031979",
        "nama_toko": "GROSIR BERKAH (M2), BAROKAH PLASTIK (M3)",
    },
    "mira": {
        "nama": "Mira Saputra",
        "program": "PASAR",
        "id_toko": "6091214/6067889",
        "nama_toko": "MANDIRI KELONTONG (M2), HARAPAN INDAH (M3)",
    },
    "asep": {
        "nama": "Asep Anggraeni",
        "program": "GROSIR",
        "id_toko": "6087500/6069616",
        "nama_toko": "HARAPAN SUKSES (M6), JAYA LESTARI (M6)",
    },
    "tuti": {
        "nama": "Tuti Cahyani",
        "program": "PASAR",
        "id_toko": "6058446/6020861",
        "nama_toko": "HIKMAH PRIMA (M4), MANDIRI SENTOSA (M245)",
    },
    "sari": {
        "nama": "Sari Kusuma",
        "program": "GROSIR",
        "id_toko": "6082149/6031358",
        "nama_toko": "BERKAH LESTARI (M4), UD UTAMA (M245)",
    },
    "hendra": {
        "nama": "Hendra Firmansyah",
        "program": "GROSIR",
        "id_toko": "6070798/6010561",
        "nama_toko": "GROSIR BERSAMA (M4), SUMBER MAJU (M4)",
    },
    "intan": {
        "nama": "Intan Utami",
        "program": "GROSIR",
        "id_toko": "6053424/6043369",
        "nama_toko": "HARAPAN LESTARI (M4), ABADI KELONTONG (M3)",
    },
    "riska": {
        "nama": "Riska Mubarok",
        "program": "GROSIR",
        "id_toko": "6076556/6091163",
        "nama_toko": "TOKO PRATAMA (M2), MAJU PRIMA (M245)",
    },
    "irfan": {
        "nama": "Irfan Fadilah",
        "program": "GROSIR",
        "id_toko": "6051116/6054921",
        "nama_toko": "HARAPAN MULIA (M3), ANUGRAH INDAH (M4)",
    },
    "lukman": {
        "nama": "Lukman Handayani",
        "program": "PASAR",
        "id_toko": "6063654/6003804",
        "nama_toko": "MAJU MANDIRI (M4), SEJAHTERA MAJU (M3)",
    },
    "sri": {
        "nama": "Sri Hasanah",
        "program": "PASAR",
        "id_toko": "6070008/6003534",
        "nama_toko": "MAJU PRATAMA (M2), RIZKI PLASTIK (M3)",
    },
    "bayu": {
        "nama": "Bayu Anggraeni",
        "program": "GROSIR",
        "id_toko": "6023819/6006590",
        "nama_toko": "BERKAH MAJU (M3), JAYA MAKMUR (M245)",
    },
    "rini": {
        "nama": "Rini Fadilah",
        "program": "GROSIR",
        "id_toko": "6049692/6036471",
        "nama_toko": "ABADI SENTOSA (M2), UD PRIMA (M6)",
    },
    "wulan": {
        "nama": "Wulan Suryadi",
        "program": "GROSIR",
        "id_toko": "6029389/6085215",
        "nama_toko": "UD BERKAH (M4), TB PLASTIK (M4)",
    },
    "ayu": {
        "nama": "Ayu Hasanah",
        "program": "GROSIR",
        "id_toko": "6019973/6031266",
        "nama_toko": "GROSIR PRIMA (M6), SEJAHTERA JAYA (M4)",
    },
    "krisna": {
        "nama": "Krisna Wahyuni",
        "program": "GROSIR",
        "id_toko": "6033586/6048351",
        "nama_toko": "WARUNG SUKSES (M4), ANUGRAH JAYA (M245)",
    },
    "galih": {
        "nama": "Galih Rahayu",
        "program": "PASAR",
        "id_toko": "6003365/6040888",
        "nama_toko": "RIZKI MAJU (M2), MAJU MAKMUR (M6)",
    },
    "wati": {
        "nama": "Wati Permatasari",
        "program": "PASAR",
        "id_toko": "6091382/6039529",
        "nama_toko": "SEJAHTERA SUKSES (M2), CV PRATAMA (M245)",
    },
    "zainal": {
        "nama": "Zainal Handayani",
        "program": "GROSIR",
        "id_toko": "6086706/6048571",
        "nama_toko": "UD AGUNG (M2), MAKMUR MANDIRI (M3)",
    },
    "erna": {
        "nama": "Erna Permatasari",
        "program": "PASAR",
        "id_toko": "6056822/6047472",
        "nama_toko": "MAKMUR LESTARI (M3), BAROKAH BERSAMA (M4)",
    },
    "oka": {
        "nama": "Oka Mardianto",
        "program": "GROSIR",
        "id_toko": "6035400/6080728",
        "nama_toko": "HARAPAN PRIMA (M6), MANDIRI BARU (M245)",
    },
    "ani": {
        "nama": "Ani Suherman",
        "program": "GROSIR",
        "id_toko": "6011359/6036559",
        "nama_toko": "MANDIRI INDAH (M6), MANDIRI PRATAMA (M3)",
    },
    "rina_s": {
        "nama": "Rina Santoso",
        "program": "GROSIR",
        "id_toko": "6064789/6042600",
        "nama_toko": "WARUNG PRIMA (M245), DEPOT SEJAHTERA (M245)",
    },
    "ujang": {
        "nama": "Ujang Budiman",
        "program": "GROSIR",
        "id_toko": "6091905/6036211",
        "nama_toko": "HARAPAN PLASTIK (M2), BINTANG MAKMUR (M4)",
    },
    "andi": {
        "nama": "Andi Kusuma",
        "program": "GROSIR",
        "id_toko": "6072768/6099374",
        "nama_toko": "SUMBER PRIMA (M3), MAKMUR PRIMA (M2)",
    },
    "saeful": {
        "nama": "Saeful Mulyani",
        "program": "PASAR",
        "id_toko": "6029045/6053005",
        "nama_toko": "BAROKAH INDAH (M245), PRIMA PRATAMA (M3)",
    },
    "agung": {
        "nama": "Agung Maulana",
        "program": "GROSIR",
        "id_toko": "6045056/6055771",
        "nama_toko": "HIKMAH MULIA (M3), JAYA SEJAHTERA (M245)",
    },
    "nanang": {
        "nama": "Nanang Purnama",
        "program": "PASAR",
        "id_toko": "6030217/6015814",
        "nama_toko": "HIKMAH MAKMUR (M6), JAYA JAYA (M4)",
    },
    "yanti": {
        "nama": "Yanti Siregar",
        "program": "PASAR",
        "id_toko": "6096810/6063464",
        "nama_toko": "BERKAH PRATAMA (M245), BINTANG SUKSES (M2)",
    },
    "oscar": {
        "nama": "Oscar Mulyani",
        "program": "GROSIR",
        "id_toko": "6029816/6047301",
        "nama_toko": "WARUNG UTAMA (M4), TOKO MULIA (M245)",
    },
    "imam": {
        "nama": "Imam Wijaya",
        "program": "PASAR",
        "id_toko": "6072529/6038290",
        "nama_toko": "BAROKAH BERSAMA (M2), MAKMUR PRIMA (M2)",
    },
    "viki": {
        "nama": "Viki Mulyani",
        "program": "GROSIR",
        "id_toko": "6061524/6062746",
        "nama_toko": "MANDIRI MANDIRI (M245), WARUNG KELONTONG (M3)",
    },
    "gilang": {
        "nama": "Gilang Rahmawati",
        "program": "PASAR",
        "id_toko": "6052521/6064454",
        "nama_toko": "UD PRATAMA (M4), MAKMUR KELONTONG (M4)",
    },
    "nia": {
        "nama": "Nia Hartono",
        "program": "PASAR",
        "id_toko": "6011164/6032530",
        "nama_toko": "CV MULIA (M6), ABADI SUKSES (M6)",
    },
    "lestari": {
        "nama": "Lestari Mubarok",
        "program": "PASAR",
        "id_toko": "6068494/6049856",
        "nama_toko": "MANDIRI LESTARI (M3), PRIMA PRATAMA (M245)",
    },
    "mulyadi": {
        "nama": "Mulyadi Hasanah",
        "program": "GROSIR",
        "id_toko": "6007894/6079905",
        "nama_toko": "HIKMAH JAYA (M4), DEPOT BERKAH (M245)",
    },
    "yanto": {
        "nama": "Yanto Kurniawan",
        "program": "PASAR",
        "id_toko": "6031439/6022782",
        "nama_toko": "HARAPAN SEMBAKO (M3), WARUNG PLASTIK (M3)",
    },
    "putri": {
        "nama": "Putri Hermawan",
        "program": "PASAR",
        "id_toko": "6038175/6004278",
        "nama_toko": "SUMBER UTAMA (M3), BAROKAH UTAMA (M2)",
    },
    "rizki": {
        "nama": "Rizki Purnama",
        "program": "PASAR",
        "id_toko": "6081927/6077304",
        "nama_toko": "SEJAHTERA MAKMUR (M6), ABADI JAYA (M4)",
    },
    "tono": {
        "nama": "Tono Setiawan",
        "program": "GROSIR",
        "id_toko": "6018643/6009359",
        "nama_toko": "TB ABADI (M6), PRIMA SUKSES (M245)",
    },
    "fitri": {
        "nama": "Fitri Hidayat",
        "program": "GROSIR",
        "id_toko": "6061433/6090266",
        "nama_toko": "PRIMA MAJU (M6), BERKAH AGUNG (M3)",
    },
    "maman": {
        "nama": "Maman Prasetyo",
        "program": "PASAR",
        "id_toko": "6078385/6005224",
        "nama_toko": "ABADI MANDIRI (M2), ANUGRAH SENTOSA (M2)",
    },
    "kurnia": {
        "nama": "Kurnia Priyanto",
        "program": "PASAR",
        "id_toko": "6075392/6076955",
        "nama_toko": "TOKO SENTOSA (M4), RIZKI KELONTONG (M3)",
    },
    "yuni": {
        "nama": "Yuni Mardianto",
        "program": "GROSIR",
        "id_toko": "6057963/6036458",
        "nama_toko": "WARUNG PRATAMA (M3), ABADI BERKAH (M2)",
    },
    "mega": {
        "nama": "Mega Suryadi",
        "program": "GROSIR",
        "id_toko": "6053523/6043687",
        "nama_toko": "JAYA JAYA (M3), WARUNG MANDIRI (M3)",
    },
    "indah": {
        "nama": "Indah Oktaviani",
        "program": "GROSIR",
        "id_toko": "6052488/6099680",
        "nama_toko": "HARAPAN KELONTONG (M245), MANDIRI SEMBAKO (M245)",
    },
    "vina": {
        "nama": "Vina Hidayat",
        "program": "PASAR",
        "id_toko": "6052976/6067449",
        "nama_toko": "TOKO MULIA (M2), MANDIRI BARU (M4)",
    },
    "tari": {
        "nama": "Tari Ramadhan",
        "program": "PASAR",
        "id_toko": "6081609/6099148",
        "nama_toko": "CAHAYA BERKAH (M4), MANDIRI KELONTONG (M245)",
    },
    "tarno": {
        "nama": "Tarno Susanto",
        "program": "PASAR",
        "id_toko": "6037752/6057424",
        "nama_toko": "BAROKAH PRIMA (M6), CV PLASTIK (M4)",
    },
    "nita": {
        "nama": "Nita Hartono",
        "program": "GROSIR",
        "id_toko": "6072199/6001792",
        "nama_toko": "HARAPAN BARU (M2), UD INDAH (M3)",
    },
    "siti": {
        "nama": "Siti Mardianto",
        "program": "GROSIR",
        "id_toko": "6020181/6065323",
        "nama_toko": "BAROKAH UTAMA (M3), BINTANG SENTOSA (M3)",
    },
    "fikri": {
        "nama": "Fikri Suherman",
        "program": "GROSIR",
        "id_toko": "6059871/6072255",
        "nama_toko": "GROSIR MAJU (M6), DEPOT SUKSES (M4)",
    }
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
        spg["nama"],         # G - Nama SPG
        keterangan,          # H - Keterangan kehadiran
        spg["program"],      # I - Program
        "CIREBON",           # J - Wilayah
        get_week(now),       # K - Minggu ke-
        format_tanggal(now), # L - Tanggal
        spg["id_toko"],      # M - ID Toko
        spg["nama_toko"],    # N - Nama Toko
        selling or "",       # O - Total Selling
        "",                  # P - (reserved)
        "",                  # Q - (reserved)
        call or "",          # R - Total Call
        ec or "",            # S - Total EC
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
        "Ketik: susi sakit | laila off | putra ijin\n\n"
        "[3] Libur Massal:\n"
        "Ketik: semua off\n\n"
        "[4] Daftar SPG:\n"
        "Ketik: /daftar"
    )


async def cmd_daftar(update, context):
    """Handler for /daftar command — show all registered SPG."""
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
