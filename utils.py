# utils.py

from datetime import datetime

def format_date_display(date_obj):
    """Formatta una data in formato DD/MM/YYYY. Restituisce una stringa vuota se None."""
    if date_obj:
        return date_obj.strftime('%d/%m/%Y')
    return ""

def parse_date(date_str):
    """Parsa una stringa in formato DD/MM/YYYY a un oggetto date. Restituisce None se non valido."""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except (ValueError, TypeError):
        return None
