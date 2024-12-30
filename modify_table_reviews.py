# modify_table_reviews.py

import sqlite3

def modify_progetti_table():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Verifica se le colonne esistono già
    c.execute("PRAGMA table_info(progetti)")
    columns = [info[1] for info in c.fetchall()]
    
    if 'recensione_stelle' not in columns:
        c.execute("ALTER TABLE progetti ADD COLUMN recensione_stelle INTEGER")
        print("Aggiunta colonna 'recensione_stelle' alla tabella 'progetti'.")
    else:
        print("Colonna 'recensione_stelle' già esistente.")
    
    if 'recensione_data' not in columns:
        c.execute("ALTER TABLE progetti ADD COLUMN recensione_data TEXT")
        print("Aggiunta colonna 'recensione_data' alla tabella 'progetti'.")
    else:
        print("Colonna 'recensione_data' già esistente.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    modify_progetti_table()
