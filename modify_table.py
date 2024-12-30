import sqlite3

def modify_table():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Crea una nuova tabella senza NOT NULL su stato_progetto
    c.execute('''
        CREATE TABLE IF NOT EXISTS progetti_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            settore TEXT NOT NULL,
            project_manager TEXT NOT NULL,
            sales_recruiter TEXT NOT NULL,
            stato_progetto TEXT,  -- Permette NULL
            data_inizio TEXT,     -- Permette NULL
            data_fine TEXT,       -- Permette NULL
            tempo_totale INTEGER
        )
    ''')

    # Copia i dati dalla vecchia tabella alla nuova
    c.execute('''
        INSERT INTO progetti_new (id, cliente, settore, project_manager, sales_recruiter, stato_progetto, data_inizio, data_fine, tempo_totale)
        SELECT id, cliente, settore, project_manager, sales_recruiter, stato_progetto, data_inizio, data_fine, tempo_totale
        FROM progetti
    ''')

    # Elimina la vecchia tabella
    c.execute('DROP TABLE progetti')

    # Rinomina la nuova tabella
    c.execute('ALTER TABLE progetti_new RENAME TO progetti')

    conn.commit()
    conn.close()
    print("Tabella 'progetti' modificata con successo. Il campo 'stato_progetto' ora permette valori NULL.")

if __name__ == "__main__":
    modify_table()


