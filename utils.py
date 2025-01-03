# utils.py

from datetime import datetime, date
import pandas as pd

def format_date_display(x):
    """
    Converte una data in formato 'YYYY-MM-DD', un oggetto datetime.date o datetime.datetime a 'DD/MM/YYYY'.
    Se il valore è vuoto, None o NaN, restituisce una stringa vuota.
    Gestisce anche oggetti non conformi restituendo la rappresentazione in stringa originale.
    """
    if pd.isna(x) or x is None or x == '':
        return ""
    if isinstance(x, (datetime, date)):
        return x.strftime('%d/%m/%Y')
    elif isinstance(x, str):
        try:
            date_obj = datetime.strptime(x, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        except ValueError:
            return x  # Se il formato non è corretto, restituisce la stringa originale
    else:
        return str(x)  # Per qualsiasi altro tipo di dato, converte in stringa

def parse_date(date_str):
    """
    Converte una stringa di data in formato 'YYYY-MM-DD' a un oggetto datetime.date.
    Se la stringa è vuota, None o in un formato non valido, restituisce None.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
