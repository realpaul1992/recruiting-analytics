# modify_progetti_forecast_mysql.py

import pymysql

def get_connection():
    """
    Connessione MySQL via pymysql.
    """
    return pymysql.connect(
        host="junction.proxy.rlwy.net",
        port=14718,
        user="root",
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",
        database="railway"
    )

def add_forecast_columns_mysql():
    """
    Aggiunge 'data_chiusura_prevista' (VARCHAR) e 'tempo_previsto' (INT) 
    se non esistono in progetti. 
    """
    conn = get_connection()
    c = conn.cursor()

    # 1) Recupera elenco colonne
    c.execute("SHOW COLUMNS FROM progetti")
    columns_info = c.fetchall()
    existing_cols = [col[0] for col in columns_info]

    # 2) Aggiungiamo se mancano
    if 'data_chiusura_prevista' not in existing_cols:
        try:
            c.execute("ALTER TABLE progetti ADD COLUMN data_chiusura_prevista VARCHAR(255)")
            print("Aggiunta colonna 'data_chiusura_prevista' in progetti.")
        except pymysql.err.ProgrammingError as e:
            print(f"Errore aggiunta data_chiusura_prevista: {e}")
    else:
        print("Colonna 'data_chiusura_prevista' già esistente.")

    if 'tempo_previsto' not in existing_cols:
        try:
            c.execute("ALTER TABLE progetti ADD COLUMN tempo_previsto INT")
            print("Aggiunta colonna 'tempo_previsto' in progetti.")
        except pymysql.err.ProgrammingError as e:
            print(f"Errore aggiunta tempo_previsto: {e}")
    else:
        print("Colonna 'tempo_previsto' già esistente.")

    conn.commit()
    conn.close()
    print("Migrazione terminata con successo (data_chiusura_prevista, tempo_previsto).")

if __name__ == "__main__":
    add_forecast_columns_mysql()
