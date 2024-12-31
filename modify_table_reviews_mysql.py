# modify_table_reviews_mysql.py

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

def modify_progetti_table_mysql():
    """
    Aggiunge le colonne 'recensione_stelle' e 'recensione_data' 
    se non esistono già, su MySQL.
    """
    conn = get_connection()
    c = conn.cursor()

    # 1) Recupera l'elenco delle colonne in 'progetti'
    c.execute("SHOW COLUMNS FROM progetti")
    columns_info = c.fetchall()  # es: (Field, Type, Null, Key, Default, Extra)
    existing_cols = [col[0] for col in columns_info]

    # 2) Se mancano, le aggiungiamo con ALTER TABLE
    if 'recensione_stelle' not in existing_cols:
        try:
            c.execute("ALTER TABLE progetti ADD COLUMN recensione_stelle INT")
            print("Aggiunta colonna 'recensione_stelle' alla tabella 'progetti'.")
        except pymysql.err.ProgrammingError as e:
            print(f"Errore aggiunta recensione_stelle: {e}")
    else:
        print("Colonna 'recensione_stelle' già esistente.")

    if 'recensione_data' not in existing_cols:
        try:
            # Puoi anche usare DATE, DATETIME, etc. Se preferisci:
            c.execute("ALTER TABLE progetti ADD COLUMN recensione_data VARCHAR(255)")
            print("Aggiunta colonna 'recensione_data' alla tabella 'progetti'.")
        except pymysql.err.ProgrammingError as e:
            print(f"Errore aggiunta recensione_data: {e}")
    else:
        print("Colonna 'recensione_data' già esistente.")

    conn.commit()
    conn.close()

    print("Modifica terminata con successo (recensione_stelle e recensione_data).")

if __name__ == "__main__":
    modify_progetti_table_mysql()
