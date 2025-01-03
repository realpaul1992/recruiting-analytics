# create_db_mysql.py

import pymysql

def create_database_mysql():
    """
    Crea le tabelle nel database MySQL su Railway,
    replicando la struttura della vecchia create_db.py (SQLite).

    In particolare, aggiunge:
      - settori, project_managers, recruiters
      - progetti (con TUTTI i campi, inclusi tempo_previsto e data_chiusura_prevista se vuoi)
      - recruiter_capacity
      - candidati, riunioni, referrals, formazione
      - Popolazione di tabelle con dati iniziali (Retail, Estetico, ecc.)
    """

    # Parametri di connessione (modifica con i tuoi valori)
    host = "junction.proxy.rlwy.net"   
    port = 14718                       
    user = "root"                      
    password = "GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM"  
    db_name = "railway"

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            autocommit=True  # Abilita il commit automatico
        )
        c = conn.cursor()

        #
        # 1) Tabelle di base
        #
        c.execute('''
            CREATE TABLE IF NOT EXISTS settori (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS project_managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE
            )
        ''')

        #
        # 2) Tabella progetti
        #
        # Basandoci su "create_db.py" e la colonna "tempo_previsto"
        # Se vuoi anche "data_chiusura_prevista", inseriscila qui di seguito.
        c.execute('''
            CREATE TABLE IF NOT EXISTS progetti (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente VARCHAR(255) NOT NULL,
                settore_id INT NOT NULL,
                project_manager_id INT NOT NULL,
                sales_recruiter_id INT NOT NULL,
                stato_progetto VARCHAR(255),
                data_inizio DATE,
                data_fine DATE,
                tempo_totale INT,
                recensione_stelle INT,
                recensione_data DATE,
                tempo_previsto INT,  -- se presente nella tua app
                data_chiusura_prevista DATE, -- se lo desideri
                FOREIGN KEY (settore_id) REFERENCES settori(id),
                FOREIGN KEY (project_manager_id) REFERENCES project_managers(id),
                FOREIGN KEY (sales_recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        #
        # 3) Tabella recruiter_capacity
        #
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiter_capacity (
                recruiter_id INT PRIMARY KEY,
                capacity_max INT NOT NULL,
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        #
        # 4) Creazione delle nuove tabelle
        #

        # 4.1) Tabella candidati
        c.execute('''
            CREATE TABLE IF NOT EXISTS candidati (
                id INT AUTO_INCREMENT PRIMARY KEY,
                progetto_id INT NOT NULL,
                recruiter_id INT NOT NULL,
                candidato_nome VARCHAR(255) NOT NULL,
                data_inserimento DATE NOT NULL,
                data_placement DATE NOT NULL,
                data_dimissioni DATE,
                FOREIGN KEY (progetto_id) REFERENCES progetti(id),
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        # 4.2) Tabella riunioni
        c.execute('''
            CREATE TABLE IF NOT EXISTS riunioni (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recruiter_id INT NOT NULL,
                data_riunione DATE NOT NULL,
                partecipato BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        # 4.3) Tabella referrals
        c.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recruiter_id INT NOT NULL,
                cliente_nome VARCHAR(255) NOT NULL,
                data_referral DATE NOT NULL,
                stato VARCHAR(50) NOT NULL, -- es: 'In corso', 'Chiuso'
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        # 4.4) Tabella formazione
        c.execute('''
            CREATE TABLE IF NOT EXISTS formazione (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recruiter_id INT NOT NULL,
                corso_nome VARCHAR(255) NOT NULL,
                data_completamento DATE NOT NULL,
                FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
            )
        ''')

        #
        # 5) Popola tabelle con dati iniziali se vuote
        #
        settori_iniziali = ["Retail", "Estetico", "Tecnologico", "Finanziario", "Altro"]
        project_managers_iniziali = ["Paolo Patelli"]
        recruiters_iniziali = [
            "Paolo Carnevale", 
            "Juan Sebastian", 
            "Francesco Picaro", 
            "Daniele Martignano"
        ]

        # Inserisci settori
        for settore in settori_iniziali:
            try:
                c.execute("INSERT INTO settori (nome) VALUES (%s)", (settore,))
            except pymysql.IntegrityError:
                pass  # Ignora errori di duplicazione

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
                c.execute(
                    "INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (%s, 5)",
                    (rec_id,)
                )
            except pymysql.IntegrityError:
                pass  # Ignora se la capacità è già stata impostata

        print("Database creato/aggiornato con successo su MySQL (Railway) con pymysql!")
        print("(Tabelle: settori, project_managers, recruiters, progetti, recruiter_capacity, candidati, riunioni, referrals, formazione)")

    except pymysql.Error as e:
        print(f"Errore di connessione MySQL: {e}")

if __name__ == "__main__":
    create_database_mysql()
