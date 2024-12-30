# create_db.py

import sqlite3

def create_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Tabelle di base
    c.execute('''
        CREATE TABLE IF NOT EXISTS settori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_managers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS recruiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # Tabella progetti
    c.execute('''
        CREATE TABLE IF NOT EXISTS progetti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            settore_id INTEGER NOT NULL,
            project_manager_id INTEGER NOT NULL,
            sales_recruiter_id INTEGER NOT NULL,
            stato_progetto TEXT,
            data_inizio TEXT,
            data_fine TEXT,
            tempo_totale INTEGER,
            recensione_stelle INTEGER,
            recensione_data TEXT,
            FOREIGN KEY (settore_id) REFERENCES settori(id),
            FOREIGN KEY (project_manager_id) REFERENCES project_managers(id),
            FOREIGN KEY (sales_recruiter_id) REFERENCES recruiters(id)
        )
    ''')

    # Nuova tabella per capacità personalizzata per ogni recruiter
    c.execute('''
        CREATE TABLE IF NOT EXISTS recruiter_capacity (
            recruiter_id INTEGER PRIMARY KEY,
            capacity_max INTEGER NOT NULL,
            FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
        )
    ''')

    # Popola tabelle con dati iniziali se vuote
    settori_iniziali = ["Retail", "Estetico", "Tecnologico", "Finanziario", "Altro"]
    project_managers_iniziali = ["Paolo Patelli"]
    recruiters_iniziali = ["Paolo Carnevale", "Juan Sebastian", "Francesco Picaro", "Daniele Martignano"]

    for settore in settori_iniziali:
        try:
            c.execute("INSERT INTO settori (nome) VALUES (?)", (settore,))
        except sqlite3.IntegrityError:
            pass

    for pm in project_managers_iniziali:
        try:
            c.execute("INSERT INTO project_managers (nome) VALUES (?)", (pm,))
        except sqlite3.IntegrityError:
            pass

    for recruiter in recruiters_iniziali:
        try:
            c.execute("INSERT INTO recruiters (nome) VALUES (?)", (recruiter,))
        except sqlite3.IntegrityError:
            pass

    # Inserisci record di default in recruiter_capacity per tutti i recruiter
    c.execute("SELECT id FROM recruiters")
    all_recs = c.fetchall()
    for (rec_id,) in all_recs:
        try:
            c.execute("INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (?, ?)", (rec_id, 5))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print("Database creato/aggiornato con successo, SENZA data_chiusura_prevista e tempo_previsto.")

if __name__ == "__main__":
    create_database()
