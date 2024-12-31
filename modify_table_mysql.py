# modify_table_mysql.py

import pymysql

def get_connection():
    """
    Restituisce una connessione MySQL usando pymysql.
    Sostituisci host, port, user, password, database 
    con i tuoi parametri di Railway.
    """
    return pymysql.connect(
        host="junction.proxy.rlwy.net",
        port=14718,
        user="root",
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",
        database="railway"
    )

def modify_table_mysql():
    """
    Ricrea la tabella 'progetti' senza vincolo NOT NULL su stato_progetto:
    1) Crea progetti_new
    2) Copia dati da progetti
    3) Elimina progetti
    4) Rinomina progetti_new -> progetti
    """
    conn = get_connection()
    c = conn.cursor()
    
    # 1) Crea tabella progetti_new (MySQL)
    #    Sostituiamo i tipi 'TEXT' con VARCHAR(255) 
    #    e “AUTOINCREMENT” con “AUTO_INCREMENT”.
    c.execute('''
        CREATE TABLE IF NOT EXISTS progetti_new (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cliente VARCHAR(255) NOT NULL,
            settore VARCHAR(255) NOT NULL,
            project_manager VARCHAR(255) NOT NULL,
            sales_recruiter VARCHAR(255) NOT NULL,
            stato_progetto VARCHAR(255) NULL,
            data_inizio VARCHAR(255),
            data_fine VARCHAR(255),
            tempo_totale INT
        )
    ''')

    # 2) Copia i dati dalla vecchia tabella “progetti” in “progetti_new”
    #    Per MySQL, assumiamo che la tabella “progetti” esista già.
    try:
        c.execute('''
            INSERT INTO progetti_new (id, cliente, settore, project_manager, sales_recruiter, 
                                      stato_progetto, data_inizio, data_fine, tempo_totale)
            SELECT id, cliente, settore, project_manager, sales_recruiter, stato_progetto,
                   data_inizio, data_fine, tempo_totale
            FROM progetti
        ''')
    except pymysql.err.ProgrammingError as e:
        print(f"Errore durante la copia dati: {e}")
        print("Assicurati che la tabella 'progetti' esista con le stesse colonne corrispondenti.")
        conn.rollback()
        conn.close()
        return

    # 3) Elimina la vecchia tabella progetti
    try:
        c.execute("DROP TABLE progetti")
    except pymysql.err.ProgrammingError as e:
        print(f"Errore durante DROP TABLE progetti: {e}")
        conn.rollback()
        conn.close()
        return

    # 4) Rinomina la nuova tabella
    #    In MySQL si fa con RENAME TABLE progetti_new TO progetti
    try:
        c.execute("RENAME TABLE progetti_new TO progetti")
    except pymysql.err.ProgrammingError as e:
        print(f"Errore durante RENAME TABLE: {e}")
        conn.rollback()
        conn.close()
        return

    conn.commit()
    conn.close()
    print("Tabella 'progetti' modificata con successo su MySQL. Stato_progetto ora consente valori NULL.")

if __name__ == "__main__":
    modify_table_mysql()
