# Architecture — SPG Daily Reporting Automation Bot

## System Overview

This bot connects three main components:

```text
[SPG / Supervisor]
       |
       | Send report message (Telegram)
       v
[Telegram Bot API]
       |
       | Long Polling
       v
[bot.py — Python Application]
       |
       |-- parse_semua_laporan()  : Parse report text
       |-- cari_spg()            : Identify SPG
       |-- input_ke_sheet()      : Write to Sheets
       v
[Google Sheets API]
       |
       v
[Google Spreadsheet] --> Data saved, ready for reporting
```

## Data Flow

### Daily Report (FORMAT REPORT)

1. SPG sends report message in Telegram
2. Bot receives message via `handle_message()`
3. Detects "FORMAT REPORT" pattern in text
4. `parse_semua_laporan()` extracts: nama, selling, call, ec
5. `cari_spg()` matches name against SPG database
6. `input_ke_sheet()` writes one data row to Google Sheets
7. Bot replies with success/failure confirmation

### Attendance Status (sakit / off / ijin / etc.)

1. Supervisor sends text like "rina sakit"
2. Bot detects status keyword in the text
3. `cari_spg()` identifies the SPG from the same text
4. `input_ke_sheet()` writes with the appropriate status
5. Bot replies with confirmation

### Bulk OFF (semua off)

1. Supervisor sends "semua off"
2. Bot iterates over all SPG in `SPG_DATA`
3. `input_ke_sheet()` is called for each SPG
4. Bot replies with a summary of all inputs

## Technical Components

| Component | Details |
|-----------|---------|
| **Async Runtime** | asyncio via python-telegram-bot 20.x |
| **Sheet Connection** | Session caching with automatic re-authentication |
| **Row Detection** | `find_next_empty_row()` — safe row finder |
| **Text Parsing** | Regex + string split, case-insensitive |
| **Authentication** | OAuth2 Service Account (no user interaction needed) |
| **Configuration** | python-dotenv — zero hard-coded credentials |
