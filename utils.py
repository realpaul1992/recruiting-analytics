# utils.py

from datetime import datetime, date
import pandas as pd

def format_date_display(date_obj):
    """Formatta una data in formato DD/MM/YYYY. Restituisce una stringa vuota se None o non valida."""
    if pd.isnull(date_obj):
        return ""
    if isinstance(date_obj, str):
        # Tentativo di parsing della stringa assumendo formato YYYY-MM-DD
        try:
            date_parsed = datetime.strptime(date_obj, '%Y-%m-%d').date()
            return date_parsed.strftime('%d/%m/%Y')
        except ValueError:
            return ""
    if isinstance(date_obj, (datetime, date)):
        return date_obj.strftime('%d/%m/%Y')
    return ""

def parse_date(date_str):
    """Parsa una stringa in formato DD/MM/YYYY a un oggetto date. Restituisce None se non valido."""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except (ValueError, TypeError):
        return None
