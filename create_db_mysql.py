# create_db_mysql.py

import pymysql

def create_database_mysql():
    """
    Crea le tabelle nel database MySQL su Railway replicando 
    la struttura e i dati di create_db.py (SQLite).
<<<<<<< HEAD
    Usa il driver pymysql, che non richiede dipendenze di sistema
    come 'pkg-config' o librerie di MySQL.
    """
    # Parametri di connessione MySQL (public host e port da Railway)
    host = "junction.proxy.rlwy.net"  # Esempio di public host
    port = 14718                      # Esempio di public port
    user = "root"                     # Il tuo username
    password = "GoHrUNytXgoikyAk..."  # La password
    db_name = "railway"

    try:
        # Connessione a MySQL con pymysql
=======
    Usa il driver pymysql.
    """
    host = "junction.proxy.rlwy.net"   # Public host su Railway
    port = 14718                       # Public port
    user = "root"                      # Username indicato da Railway
    password = "GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM"  # Password effettiva
    db_name = "railway"                # Nome DB, di solito "railway"

    try:
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port=port
        )
        c = conn.cursor()

<<<<<<< HEAD
        # ------------------------------------------------
        # 1) Tabelle di base
        # ------------------------------------------------
=======
        # 1) Tabelle di base
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
        c.execute('''
            CREATE TABLE IF NOT EXISTS settori (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')
<<<<<<< HEAD

=======
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
        c.execute('''
            CREATE TABLE IF NOT EXISTS project_managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')
<<<<<<< HEAD

=======
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')

<<<<<<< HEAD
        # ------------------------------------------------
        # 2) Tabella progetti
        # ------------------------------------------------
=======
        # 2) Tabella progetti
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
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

<<<<<<< HEAD
        # ------------------------------------------------
        # 3) Tabella recruiter_capacity
        # ------------------------------------------------
=======
        # 3) Tabella recruiter_capacity
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiter_capacity (
                recruiter_id INT PRIMARY KEY,
                capacity_max INT NOT NULL,
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

<<<<<<< HEAD
        # ------------------------------------------------
        # 4) Popola tabelle con dati iniziali
        # ------------------------------------------------
=======
        # 4) Popola tabelle con dati iniziali (solo se non già esistono)
>>>>>>> 1d2563ce (Aggiunto script create_db_mysql.py per la creazione tabelle su MySQL)
        settori_iniziali = ["Retail", "Estetico", "Tecnologico", "Finanziario", "Altro"]
        project_managers_iniziali = ["Paolo Patelli"]
        recruiters_iniziali = ["Paolo Carnevale", "Juan Sebastian", "Francesco Picaro", "Daniele Martignano"]

        # Inserisci settori
        for settore in settori_iniziali:
            try:
                c.execute("INSERT INTO settori (nome) VALUES (%s)", (settore,))
            except pymysql.IntegrityError:
                pass

        # Inserisci project_managers
        for pm in project_managers_iniziali:
            try:
                c.execute("INSERT INTO project_managers (nome) VALUES (%s)", (pm,))
            except pymysql.IntegrityError:
                pass

        # Inserisci recruiters
        for recruiter in recruiters_iniziali:
            try:
                c.execute("INSERT INTO recruiters (nome) VALUES (%s)", (recruiter,))
            except pymysql.IntegrityError:
                pass

        # Imposta capacity=5 per tutti i recruiters
        c.execute("SELECT id FROM recruiters")
        all_recs = c.fetchall()
        for (rec_id,) in all_recs:
            try:
                c.execute("INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (%s, 5)", (rec_id,))
            except pymysql.IntegrityError:
                pass

        conn.commit()
        conn.close()
        print("Database creato/aggiornato con successo su MySQL (Railway) con pymysql!")

    except pymysql.Error as e:
        print(f"Errore di connessione MySQL: {e}")


if __name__ == "__main__":
    create_database_mysql()
