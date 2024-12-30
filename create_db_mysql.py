# create_db_mysql.py

import MySQLdb

def create_database_mysql():
    """
    Crea le tabelle nel database MySQL su Railway,
    replicando la logica presente in create_db.py (SQLite).
    """
    # Parametri di connessione MySQL (Public host e port da Railway)
    host = "junction.proxy.rlwy.net"       # Esempio di public host
    port = 14718                           # Esempio di public port
    user = "root"                          # Il tuo user (es. "root")
    password = "GoHrUNytXgoikyAk..."       # La tua password
    db_name = "railway"                    # Nome database, di solito "railway"

    try:
        # Connessione a MySQL
        conn = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=db_name,
            port=port
        )
        c = conn.cursor()

        # ------------------------------------------------
        # 1) Tabelle di base
        # ------------------------------------------------
        # settori
        c.execute('''
            CREATE TABLE IF NOT EXISTS settori (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')

        # project_managers
        c.execute('''
            CREATE TABLE IF NOT EXISTS project_managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')

        # recruiters
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')

        # ------------------------------------------------
        # 2) Tabella progetti
        # ------------------------------------------------
        c.execute('''
            CREATE TABLE IF NOT EXISTS progetti (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente VARCHAR(255) NOT NULL,
                settore_id INT NOT NULL,
                project_manager_id INT NOT NULL,
                sales_recruiter_id INT NOT NULL,
                stato_progetto VARCHAR(255),
                data_inizio VARCHAR(255),
                data_fine VARCHAR(255),
                tempo_totale INT,
                recensione_stelle INT,
                recensione_data VARCHAR(255),
                FOREIGN KEY (settore_id) REFERENCES settori(id),
                FOREIGN KEY (project_manager_id) REFERENCES project_managers(id),
                FOREIGN KEY (sales_recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        # ------------------------------------------------
        # 3) Tabella recruiter_capacity
        # ------------------------------------------------
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiter_capacity (
                recruiter_id INT PRIMARY KEY,
                capacity_max INT NOT NULL,
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        # ------------------------------------------------
        # 4) Popola tabelle con dati iniziali se vuote
        # ------------------------------------------------
        settori_iniziali = ["Retail", "Estetico", "Tecnologico", "Finanziario", "Altro"]
        project_managers_iniziali = ["Paolo Patelli"]
        recruiters_iniziali = ["Paolo Carnevale", "Juan Sebastian", "Francesco Picaro", "Daniele Martignano"]

        # 4a) Inserisci settori
        for settore in settori_iniziali:
            try:
                c.execute("INSERT INTO settori (nome) VALUES (%s)", (settore,))
            except MySQLdb.IntegrityError:
                pass

        # 4b) Inserisci project_managers
        for pm in project_managers_iniziali:
            try:
                c.execute("INSERT INTO project_managers (nome) VALUES (%s)", (pm,))
            except MySQLdb.IntegrityError:
                pass

        # 4c) Inserisci recruiters
        for recruiter in recruiters_iniziali:
            try:
                c.execute("INSERT INTO recruiters (nome) VALUES (%s)", (recruiter,))
            except MySQLdb.IntegrityError:
                pass

        # 4d) Inserisci record di default in recruiter_capacity (capacity=5)
        c.execute("SELECT id FROM recruiters")
        all_recs = c.fetchall()
        for (rec_id,) in all_recs:
            try:
                c.execute(
                    "INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (%s, %s)",
                    (rec_id, 5)
                )
            except MySQLdb.IntegrityError:
                pass

        conn.commit()
        conn.close()
        print("Database creato/aggiornato con successo su MySQL (Railway), SENZA data_chiusura_prevista e tempo_previsto.")

    except MySQLdb.Error as e:
        print(f"Errore di connessione MySQL: {e}")

if __name__ == "__main__":
    create_database_mysql()
