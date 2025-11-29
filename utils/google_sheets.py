# utils/google_sheets.py
import os
from django.conf import settings

import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    """
    يرجع client مفوض لـ gspread باستخدام Service Account JSON.
    """
    # نحاول قراءة المسار من env ثم من settings
    creds_path = os.getenv('GOOGLE_CREDS') or getattr(settings, 'GOOGLE_CREDS', None)
    if not creds_path:
        raise RuntimeError("Google credentials path not set. Set GOOGLE_CREDS in .env or settings.")

    # إذا المسار نسبي، نجعله نسبي إلى BASE_DIR (settings.BASE_DIR موجود عادة)
    if not os.path.isabs(creds_path):
        # settings.BASE_DIR غالبًا Path object أو str
        base = getattr(settings, 'BASE_DIR', None)
        if base:
            creds_path = os.path.join(str(base), creds_path)

    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    return client

def append_order_to_sheet(row):
    """
    row: قائمة من القيم ['order_id', 'email', 'status', 'total', 'created_at', ...]
    تضيف الصف في أول ورقة (sheet1).
    """
    client = get_gspread_client()

    # نحصل على ID الشيت من env أو settings
    sheet_id = os.getenv('GOOGLE_SHEET_ID') or getattr(settings, 'GOOGLE_SHEET_ID', None)
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID not set in environment or settings.")

    sh = client.open_by_key(sheet_id)
    worksheet = sh.sheet1  # أول ورقة - ممكن تغيّرها لو عندك اسم ورقة آخر
    worksheet.append_row(row)
    return True
