# modify_progetti_forecast.py

import sqlite3

def add_forecast_columns():
    """
    Aggiunge le colonne 'data_chiusura_prevista' (TEXT) e 'tempo_previsto' (INTEGER)
    nella tabella 'progetti', se non esistono già.
    """
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Verifica le colonne esistenti in 'progetti'
    c.execute("PRAGMA table_info(progetti)")
    columns = [row[1] for row in c.fetchall()]

    if 'data_chiusura_prevista' not in columns:
        c.execute("ALTER TABLE progetti ADD COLUMN data_chiusura_prevista TEXT")
        print("Aggiunta colonna 'data_chiusura_prevista' in progetti.")
    else:
        print("Colonna 'data_chiusura_prevista' già esistente.")

    if 'tempo_previsto' not in columns:
        c.execute("ALTER TABLE progetti ADD COLUMN tempo_previsto INTEGER")
        print("Aggiunta colonna 'tempo_previsto' in progetti.")
    else:
        print("Colonna 'tempo_previsto' già esistente.")

    conn.commit()
    conn.close()
    print("Migrazione terminata con successo!")

if __name__ == "__main__":
    add_forecast_columns()
