import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt
import os
import zipfile  # Import per gestire ZIP
from io import BytesIO
import urllib.parse

#######################################
# FUNZIONI DI ACCESSO AL DB (MySQL)
#######################################

def get_connection():
    """
    Ritorna una connessione MySQL usando pymysql.
    """
    return pymysql.connect(
        host="junction.proxy.rlwy.net",
        port=14718,
        user="root",
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",
        database="railway",
        cursorclass=pymysql.cursors.DictCursor  # Per ottenere risultati come dizionari
    )

def carica_settori():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM settori ORDER BY nome ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def carica_project_managers():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def carica_recruiters():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def inserisci_dati(cliente, settore_id, pm_id, rec_id, data_inizio):
    """
    Inserisce un nuovo progetto in MySQL.
    """
    conn = get_connection()
    c = conn.cursor()

    # Valori di default
    stato_progetto = None
    data_fine = None
    tempo_totale = None
    recensione_stelle = None
    recensione_data = None
    tempo_previsto = None  # gestito altrove

    query = """
        INSERT INTO progetti (
            cliente,
            settore_id,
            project_manager_id,
            sales_recruiter_id,
            stato_progetto,
            data_inizio,
            data_fine,
            tempo_totale,
            recensione_stelle,
            recensione_data,
            tempo_previsto
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    c.execute(query, (
        cliente,
        settore_id,
        pm_id,
        rec_id,
        stato_progetto,
        data_inizio,
        data_fine,
        tempo_totale,
        recensione_stelle,
        recensione_data,
        tempo_previsto
    ))
    conn.commit()
    conn.close()

    # Esegui backup (ZIP)
    backup_database()

def carica_dati_completo():
    """
    Carica i progetti uniti a settori, pm, recruiters, includendo 'tempo_previsto'.
    """
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT
            p.id,
            p.cliente,
            s.nome AS settore,
            pm.nome AS project_manager,
            r.nome AS sales_recruiter,
            p.stato_progetto,
            p.data_inizio,
            p.data_fine,
            p.tempo_totale,
            p.recensione_stelle,
            p.recensione_data,
            p.tempo_previsto
        FROM progetti p
        JOIN settori s ON p.settore_id = s.id
        JOIN project_managers pm ON p.project_manager_id = pm.id
        JOIN recruiters r ON p.sales_recruiter_id = r.id
    """
    c.execute(query)
    rows = c.fetchall()

    columns = [
        'id','cliente','settore','project_manager','sales_recruiter',
        'stato_progetto','data_inizio','data_fine','tempo_totale',
        'recensione_stelle','recensione_data','tempo_previsto'
    ]
    conn.close()

    df = pd.DataFrame(rows, columns=columns)
    
    # Convertiamo 'tempo_previsto' a numerico
    if "tempo_previsto" in df.columns:
        df["tempo_previsto"] = pd.to_numeric(df["tempo_previsto"], errors="coerce")
        df["tempo_previsto"] = df["tempo_previsto"].fillna(0).astype(int)
    
    # Aggiungi 'data_inizio_dt' e 'recensione_data_dt' subito dopo
    df['data_inizio_dt'] = pd.to_datetime(df['data_inizio'], errors='coerce')
    df['recensione_data_dt'] = pd.to_datetime(df['recensione_data'], errors='coerce')
    
    return df

#######################################
# DEFINIZIONE DELLE FUNZIONI CRUD
#######################################

# Funzioni per Riunioni
def carica_riunioni():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, recruiter_id, data_riunione, partecipato FROM riunioni ORDER BY data_riunione DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def inserisci_riunione(recruiter_id, data_riunione, partecipato):
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO riunioni (recruiter_id, data_riunione, partecipato)
        VALUES (%s, %s, %s)
    """
    c.execute(query, (recruiter_id, data_riunione, partecipato))
    conn.commit()
    conn.close()
    st.success("Riunione inserita con successo!")
    backup_database()

def modifica_riunione(riunione_id, recruiter_id, data_riunione, partecipato):
    conn = get_connection()
    c = conn.cursor()
    query = """
        UPDATE riunioni
        SET recruiter_id = %s, data_riunione = %s, partecipato = %s
        WHERE id = %s
    """
    c.execute(query, (recruiter_id, data_riunione, partecipato, riunione_id))
    conn.commit()
    conn.close()
    st.success("Riunione aggiornata con successo!")
    backup_database()

def elimina_riunione(riunione_id):
    conn = get_connection()
    c = conn.cursor()
    query = "DELETE FROM riunioni WHERE id = %s"
    c.execute(query, (riunione_id,))
    conn.commit()
    conn.close()
    st.success("Riunione eliminata con successo!")
    backup_database()

# Funzioni per Referrals
def carica_referrals():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, recruiter_id, cliente_nome, data_referral, stato FROM referrals ORDER BY data_referral DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def inserisci_referral(recruiter_id, cliente_nome, data_referral, stato):
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO referrals (recruiter_id, cliente_nome, data_referral, stato)
        VALUES (%s, %s, %s, %s)
    """
    c.execute(query, (recruiter_id, cliente_nome, data_referral, stato))
    conn.commit()
    conn.close()
    st.success("Referral inserito con successo!")
    backup_database()

def modifica_referral(referral_id, recruiter_id, cliente_nome, data_referral, stato):
    conn = get_connection()
    c = conn.cursor()
    query = """
        UPDATE referrals
        SET recruiter_id = %s, cliente_nome = %s, data_referral = %s, stato = %s
        WHERE id = %s
    """
    c.execute(query, (recruiter_id, cliente_nome, data_referral, stato, referral_id))
    conn.commit()
    conn.close()
    st.success("Referral aggiornato con successo!")
    backup_database()

def elimina_referral(referral_id):
    conn = get_connection()
    c = conn.cursor()
    query = "DELETE FROM referrals WHERE id = %s"
    c.execute(query, (referral_id,))
    conn.commit()
    conn.close()
    st.success("Referral eliminato con successo!")
    backup_database()

# Funzioni per Formazione
def carica_formazione():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, recruiter_id, corso_nome, data_completamento FROM formazione ORDER BY data_completamento DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def inserisci_formazione(recruiter_id, corso_nome, data_completamento):
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO formazione (recruiter_id, corso_nome, data_completamento)
        VALUES (%s, %s, %s)
    """
    c.execute(query, (recruiter_id, corso_nome, data_completamento))
    conn.commit()
    conn.close()
    st.success("Formazione inserita con successo!")
    backup_database()

def modifica_formazione(formazione_id, recruiter_id, corso_nome, data_completamento):
    conn = get_connection()
    c = conn.cursor()
    query = """
        UPDATE formazione
        SET recruiter_id = %s, corso_nome = %s, data_completamento = %s
        WHERE id = %s
    """
    c.execute(query, (recruiter_id, corso_nome, data_completamento, formazione_id))
    conn.commit()
    conn.close()
    st.success("Formazione aggiornata con successo!")
    backup_database()

def elimina_formazione(formazione_id):
    conn = get_connection()
    c = conn.cursor()
    query = "DELETE FROM formazione WHERE id = %s"
    c.execute(query, (formazione_id,))
    conn.commit()
    conn.close()
    st.success("Formazione eliminata con successo!")
    backup_database()

# Funzioni per Retention
def carica_retention():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, progetto_id, data_assunzione, data_cessazione FROM retention ORDER BY data_assunzione DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def inserisci_retention(progetto_id, data_assunzione, data_cessazione):
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO retention (progetto_id, data_assunzione, data_cessazione)
        VALUES (%s, %s, %s)
    """
    c.execute(query, (progetto_id, data_assunzione, data_cessazione))
    conn.commit()
    conn.close()
    st.success("Retention inserita con successo!")
    backup_database()

def modifica_retention(retention_id, progetto_id, data_assunzione, data_cessazione):
    conn = get_connection()
    c = conn.cursor()
    query = """
        UPDATE retention
        SET progetto_id = %s, data_assunzione = %s, data_cessazione = %s
        WHERE id = %s
    """
    c.execute(query, (progetto_id, data_assunzione, data_cessazione, retention_id))
    conn.commit()
    conn.close()
    st.success("Retention aggiornata con successo!")
    backup_database()

def elimina_retention(retention_id):
    conn = get_connection()
    c = conn.cursor()
    query = "DELETE FROM retention WHERE id = %s"
    c.execute(query, (retention_id,))
    conn.commit()
    conn.close()
    st.success("Retention eliminata con successo!")
    backup_database()

#######################################
# GESTIONE BACKUP in ZIP (Esportazione + Ripristino)
#######################################

def backup_database():
    """
    Esegue un "backup" esportando i dati di ciascuna tabella in un CSV
    all’interno di un archivio ZIP nella cartella 'backup'.
    Sovrascrive l'archivio ZIP esistente.
    """
    backup_dir = "backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backup_zip_path = os.path.join(backup_dir, "backup.zip")
    
    # Crea un nuovo archivio ZIP, sovrascrivendo quello esistente
    with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        conn = get_connection()
        c = conn.cursor()

        # Legge l’elenco delle tabelle
        c.execute("SHOW TABLES")
        tables = c.fetchall()

        st.info("Inizio backup MySQL in ZIP...")

        for (table_name,) in tables:
            # Query: SELECT * FROM <table_name>
            c.execute(f"SELECT * FROM {table_name}")
            rows = c.fetchall()
            if not rows:
                st.warning(f"Nessun dato trovato nella tabella {table_name}.")
                continue
            col_names = rows[0].keys()

            df_table = pd.DataFrame(rows)
            csv_data = df_table.to_csv(index=False, encoding="utf-8")

            # Scrivi il CSV direttamente nell'archivio ZIP
            backup_zip.writestr(f"{table_name}.csv", csv_data)

        conn.close()
    
    st.success("Backup completato: archivio ZIP creato in /backup/backup.zip.")

def restore_from_zip(zip_file):
    """
    Ripristina il database da un archivio ZIP contenente CSV delle tabelle.
    - Estrae ogni CSV e ripristina la relativa tabella.
    """
    if not zipfile.is_zipfile(zip_file):
        st.error("Il file caricato non è un archivio ZIP valido.")
        return

    with zipfile.ZipFile(zip_file, 'r') as backup_zip:
        # Ottieni la lista dei file CSV nell'archivio
        csv_files = [f for f in backup_zip.namelist() if f.endswith('.csv')]

        if not csv_files:
            st.error("L'archivio ZIP non contiene file CSV di backup.")
            return

        conn = get_connection()
        c = conn.cursor()

        st.info("Inizio ripristino database da ZIP...")

        for csv_file in csv_files:
            table_name = os.path.splitext(os.path.basename(csv_file))[0]
            st.write(f"Ripristino tabella '{table_name}'...")

            # Leggi il contenuto del CSV
            with backup_zip.open(csv_file) as f:
                df = pd.read_csv(f)

            # Esegui TRUNCATE sulla tabella
            try:
                c.execute(f"TRUNCATE TABLE {table_name}")
            except pymysql.Error as e:
                st.error(f"Errore TRUNCATE {table_name}: {e}")
                conn.close()
                return

            # Prepara le colonne e i placeholder per l'INSERT
            col_names = df.columns.tolist()
            placeholders = ",".join(["%s"] * len(col_names))
            col_list_str = ",".join(col_names)
            insert_query = f"INSERT INTO {table_name} ({col_list_str}) VALUES ({placeholders})"

            # Inserisci le righe
            try:
                for row in df.itertuples(index=False, name=None):
                    c.execute(insert_query, row)
            except pymysql.Error as e:
                st.error(f"Errore durante l'INSERT nella tabella {table_name}: {e}")
                conn.rollback()
                conn.close()
                return

        conn.commit()
        conn.close()
        st.success("Ripristino completato con successo da ZIP.")

#######################################
# CAPACITA' PER RECRUITER
#######################################
def carica_recruiters_capacity():
    """
    Restituisce un DataFrame con recruiter e la loro capacità.
    """
    conn = get_connection()
    c = conn.cursor()
    query = '''
        SELECT r.nome AS sales_recruiter,
               IFNULL(rc.capacity_max, 5) AS capacity
        FROM recruiters r
        LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
        ORDER BY r.nome
    '''
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return pd.DataFrame(rows, columns=['sales_recruiter', 'capacity'])

def aggiorna_capacity_recruiter(recruiter_id, nuova_capacity):
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO recruiter_capacity (recruiter_id, capacity_max)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE capacity_max = VALUES(capacity_max)
    """
    c.execute(query, (recruiter_id, nuova_capacity))
    conn.commit()
    conn.close()
    st.success(f"Capacità per Recruiter ID {recruiter_id} aggiornata a {nuova_capacity}.")
    backup_database()

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD
#######################################
def calcola_leaderboard(df, start_date, end_date):
    """
    Calcola la leaderboard basata sui criteri di punteggio definiti.
    """
    df_temp = df.copy()
    df_temp['data_inizio_dt'] = pd.to_datetime(df_temp['data_inizio'], errors='coerce')
    df_temp['recensione_stelle'] = df_temp['recensione_stelle'].fillna(0).astype(int)

    # Calcolo Bonus da Recensioni
    df_temp['bonus_recensione'] = df_temp['recensione_stelle'].apply(
        lambda x: 500 if x == 5 else (400 if x == 4 else 0)
    )

    # Calcolo Bonus per Progetti Completati in Meno di 60 Giorni
    df_temp['bonus_progetto_veloce'] = df_temp.apply(
        lambda row: 50 if (row['stato_progetto'] == 'Completato' and row['tempo_totale'] < 60) else 0, axis=1
    )

    # Calcolo Bonus/Malus per Retention
    # Assumo che la tabella 'retention' abbia una relazione con 'progetti' tramite 'progetto_id'
    retention_data = carica_retention()
    retention_df = pd.DataFrame(retention_data)
    retention_df['data_assunzione_dt'] = pd.to_datetime(retention_df['data_assunzione'], errors='coerce')
    retention_df['data_cessazione_dt'] = pd.to_datetime(retention_df['data_cessazione'], errors='coerce')

    # Calcola la durata dell'impiego in mesi
    retention_df['durata_mesi'] = (retention_df['data_cessazione_dt'] - retention_df['data_assunzione_dt']).dt.days / 30

    # Assegna punti basati sulla durata
    retention_df['bonus_retention'] = retention_df['durata_mesi'].apply(
        lambda x: 300 if x >= 6 else (-200 if x < 3 else 0)
    )

    # Merge con i progetti
    df_temp = df_temp.merge(retention_df[['progetto_id', 'bonus_retention']], left_on='id', right_on='progetto_id', how='left')
    df_temp['bonus_retention'] = df_temp['bonus_retention'].fillna(0)

    # Calcolo Bonus per Partecipazione alle Riunioni
    riunioni_data = carica_riunioni()
    riunioni_df = pd.DataFrame(riunioni_data)
    riunioni_df = riunioni_df.merge(carica_recruiters(), left_on='recruiter_id', right_on='id', how='left')
    riunioni_df['bonus_riunione'] = riunioni_df['partecipato'].apply(lambda x: 100 if x else 0)
    bonus_riunione = riunioni_df.groupby('nome')['bonus_riunione'].sum().reset_index()
    bonus_riunione.rename(columns={'nome': 'sales_recruiter', 'bonus_riunione': 'bonus_riunione'}, inplace=True)

    # Calcolo Bonus per Referral
    referrals_data = carica_referrals()
    referrals_df = pd.DataFrame(referrals_data)
    referrals_df = referrals_df.merge(carica_recruiters(), left_on='recruiter_id', right_on='id', how='left')
    referrals_df['bonus_referral'] = referrals_df['stato'].apply(lambda x: 1000 if x.lower() == 'acquisito' else 0)
    bonus_referral = referrals_df.groupby('nome')['bonus_referral'].sum().reset_index()
    bonus_referral.rename(columns={'nome': 'sales_recruiter', 'bonus_referral': 'bonus_referral'}, inplace=True)

    # Calcolo Bonus per Formazione
    formazione_data = carica_formazione()
    formazione_df = pd.DataFrame(formazione_data)
    formazione_df = formazione_df.merge(carica_recruiters(), left_on='recruiter_id', right_on='id', how='left')
    formazione_df['bonus_formazione'] = formazione_df['corso_nome'].apply(lambda x: 300 if x else 0)
    bonus_formazione = formazione_df.groupby('nome')['bonus_formazione'].sum().reset_index()
    bonus_formazione.rename(columns={'nome': 'sales_recruiter', 'bonus_formazione': 'bonus_formazione'}, inplace=True)

    # Aggrega tutti i bonus
    bonus_totali = bonus_riunione.merge(bonus_referral, on='sales_recruiter', how='left').merge(bonus_formazione, on='sales_recruiter', how='left')
    bonus_totali = bonus_totali.fillna(0)

    # Calcolo Punteggio Totale
    leaderboard = df_temp.groupby('sales_recruiter').agg(
        completati=('id', lambda x: (df_temp.loc[x, 'stato_progetto'] == 'Completato').sum()),
        bonus_recensione=('bonus_recensione', 'sum'),
        bonus_progetto_veloce=('bonus_progetto_veloce', 'sum'),
        bonus_retention=('bonus_retention', 'sum')
    ).reset_index()

    # Merge con altri bonus
    leaderboard = leaderboard.merge(bonus_totali, on='sales_recruiter', how='left')
    leaderboard = leaderboard.fillna(0)

    # Calcola punteggio totale
    leaderboard['punteggio'] = (
        leaderboard['completati'] * 10 +
        leaderboard['bonus_recensione'] +
        leaderboard['bonus_progetto_veloce'] +
        leaderboard['bonus_retention'] +
        leaderboard['bonus_riunione'] +
        leaderboard['bonus_referral'] +
        leaderboard['bonus_formazione']
    )

    # Assegna badge
    def assegna_badge(punteggio):
        if punteggio >= 10000:
            return "Gold"
        elif punteggio >= 5000:
            return "Silver"
        elif punteggio >= 2000:
            return "Bronze"
        return "Grey"

    leaderboard['badge'] = leaderboard['punteggio'].apply(assegna_badge)

    # Ordina per punteggio
    leaderboard = leaderboard.sort_values('punteggio', ascending=False)

    return leaderboard

#######################################
# UTILITIES PER FORMATTARE LE DATE
#######################################
def format_date_display(x):
    """Formatta le date dal formato 'YYYY-MM-DD' a 'DD/MM/YYYY'."""
    if not x:
        return ""
    try:
        return datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError:
        return x  # Se il formato non è corretto o è vuoto, lascio inalterato

def parse_date(date_str):
    """Converti una stringa di data in un oggetto datetime.date (assumendo formato 'YYYY-MM-DD')."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

#######################################
# CONFIG E LAYOUT
#######################################
STATI_PROGETTO = ["Completato", "In corso", "Bloccato"]
STATO_REFERRAL_OPTIONS = ["Acquisito", "Non Acquisito"]  # Assicurati che questi valori corrispondano ai tuoi dati
PARTICIPATO_OPTIONS = [True, False]

# Carichiamo i riferimenti
settori_db = carica_settori()
pm_db = carica_project_managers()
rec_db = carica_recruiters()

st.title("Gestione Progetti di Recruiting")
st.sidebar.title("Navigazione")
scelta = st.sidebar.radio("Vai a", ["Inserisci Dati", "Dashboard", "Gestisci Opzioni", "Gestisci"])

#######################################
# 1. INSERISCI DATI
#######################################
if scelta == "Inserisci Dati":
    st.header("Inserimento Nuovo Progetto")
    
    with st.form("form_inserimento_progetto"):
        cliente = st.text_input("Nome Cliente")
        
        # Settore
        settori_nomi = [s['nome'] for s in settori_db]
        settore_sel = st.selectbox("Settore Cliente", settori_nomi)
        settore_id = None
        for s in settori_db:
            if s['nome'] == settore_sel:
                settore_id = s['id']
                break
        
        # Project Manager
        pm_nomi = [p['nome'] for p in pm_db]
        pm_sel = st.selectbox("Project Manager", pm_nomi)
        pm_id = None
        for p in pm_db:
            if p['nome'] == pm_sel:
                pm_id = p['id']
                break
        
        # Recruiter
        rec_nomi = [r['nome'] for r in rec_db]
        rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
        rec_id = None
        for r in rec_db:
            if r['nome'] == rec_sel:
                rec_id = r['id']
                break
        
        # Data di Inizio
        data_inizio_str = st.text_input("Data di Inizio (GG/MM/AAAA)", 
                                        value="", 
                                        placeholder="Lascia vuoto se non disponibile")

        # Tempo Previsto
        tempo_previsto = st.number_input("Tempo Previsto (giorni)", min_value=0, step=1, value=0)

        submitted = st.form_submit_button("Inserisci Progetto")
        if submitted:
            if not cliente.strip():
                st.error("Il campo 'Nome Cliente' è obbligatorio!")
                st.stop()
            
            if data_inizio_str.strip():
                try:
                    di = datetime.strptime(data_inizio_str.strip(), '%d/%m/%Y')
                    data_inizio_sql = di.strftime('%Y-%m-%d')
                except ValueError:
                    st.error("Formato Data Inizio non valido. Usa GG/MM/AAAA.")
                    st.stop()
            else:
                data_inizio_sql = None
            
            inserisci_dati(cliente.strip(), settore_id, pm_id, rec_id, data_inizio_sql)
            st.success("Progetto inserito con successo!")

#######################################
# 2. DASHBOARD
#######################################
elif scelta == "Dashboard":
    st.header("Dashboard di Controllo")
    df = carica_dati_completo()
    
    if df.empty:
        st.info("Nessun progetto disponibile nel DB.")
    else:
        # Creiamo le Tab
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Panoramica",
            "Carico Proiettato / Previsione",
            "Bonus e Premi",
            "Backup",
            "Classifica",
            "Gestione"
        ])

        ################################
        # TAB 1: Panoramica
        ################################
        with tab1:
            st.subheader("Tempo Medio Generale e per Recruiter/Settore")

            # Filtro per Anno
            st.markdown("### Filtro per Anno")
            anni_disponibili = sorted(df['data_inizio_dt'].dt.year.dropna().unique())
            if len(anni_disponibili) == 0:
                st.warning("Nessun dato disponibile per i filtri.")
                st.stop()
            # Converti gli anni in interi
            anni_disponibili = [int(y) for y in anni_disponibili]
            anno_selezionato = st.selectbox("Seleziona Anno", options=anni_disponibili, index=len(anni_disponibili)-1, key='panoramica_anno')
            
            # Filtra i dati in base all'anno selezionato
            try:
                start_date = datetime(anno_selezionato, 1, 1)
                end_date = datetime(anno_selezionato, 12, 31)
            except TypeError as e:
                st.error(f"Errore nella selezione di Anno: {e}")
                st.stop()

            df_filtered = df[
                (df['data_inizio_dt'] >= pd.Timestamp(start_date)) &
                (df['data_inizio_dt'] <= pd.Timestamp(end_date))
            ]

            if df_filtered.empty:
                st.info("Nessun dato disponibile per l'anno selezionato.")
            else:
                # Tempo Medio Globale
                df_comp = df_filtered[df_filtered['stato_progetto'] == 'Completato']
                tempo_medio_globale = df_comp['tempo_totale'].dropna().mean() or 0
                st.metric("Tempo Medio Globale (giorni)", round(tempo_medio_globale,2))

                # Tempo medio per recruiter
                rec_media = df_comp.groupby('sales_recruiter')['tempo_totale'].mean().reset_index()
                rec_media['tempo_totale'] = rec_media['tempo_totale'].fillna(0).round(2)
                fig_rec = px.bar(
                    rec_media,
                    x='sales_recruiter',
                    y='tempo_totale',
                    labels={'tempo_totale':'Giorni Medi'},
                    title='Tempo Medio di Chiusura per Recruiter',
                    color='tempo_totale',  # Aggiunta di colore per stile
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_rec, use_container_width=True)

                # Tempo medio per settore
                sett_media = df_comp.groupby('settore')['tempo_totale'].mean().reset_index()
                sett_media['tempo_totale'] = sett_media['tempo_totale'].fillna(0).round(2)
                fig_sett = px.bar(
                    sett_media,
                    x='settore',
                    y='tempo_totale',
                    labels={'tempo_totale':'Giorni Medi'},
                    title='Tempo Medio di Chiusura per Settore',
                    color='tempo_totale',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_sett, use_container_width=True)

                st.subheader("Progetti Attivi (In corso + Bloccato)")
                df_attivi = df_filtered[df_filtered['stato_progetto'].isin(["In corso", "Bloccato"])]
                attivi_count = df_attivi.groupby('sales_recruiter').size().reset_index(name='Progetti Attivi')
                fig_attivi = px.bar(
                    attivi_count,
                    x='sales_recruiter',
                    y='Progetti Attivi',
                    title='Numero di Progetti Attivi per Recruiter',
                    color='Progetti Attivi',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig_attivi, use_container_width=True)

                st.subheader("Capacità di Carico e Over Capacity")
                df_capacity = carica_recruiters_capacity()
                recruiters_unici = df['sales_recruiter'].unique()
                cap_df = pd.DataFrame({'sales_recruiter': recruiters_unici})
                cap_df = cap_df.merge(attivi_count, on='sales_recruiter', how='left').fillna(0)
                cap_df = cap_df.merge(df_capacity, on='sales_recruiter', how='left').fillna(5)
                cap_df['capacity'] = cap_df['capacity'].astype(int)
                cap_df['Progetti Attivi'] = cap_df['Progetti Attivi'].astype(int)
                cap_df['Capacità Disponibile'] = cap_df['capacity'] - cap_df['Progetti Attivi']
                cap_df.loc[cap_df['Capacità Disponibile'] < 0, 'Capacità Disponibile'] = 0

                overcap = cap_df[cap_df['Capacità Disponibile'] == 0]
                if not overcap.empty:
                    st.warning("Attenzione! I seguenti Recruiter sono a capacità 0:")
                    st.write(overcap[['sales_recruiter','Progetti Attivi','capacity','Capacità Disponibile']])

                fig_carico = px.bar(
                    cap_df,
                    x='sales_recruiter',
                    y=['Progetti Attivi','Capacità Disponibile'],
                    barmode='group',
                    title='Capacità di Carico per Recruiter',
                    color_discrete_sequence=['#636EFA', '#EF553B']  # Colori simili al grafico avvicinamento
                )
                st.plotly_chart(fig_carico, use_container_width=True)

        ################################
        # TAB 2: Carico Proiettato / Previsione
        ################################
        with tab2:
            st.subheader("Progetti che si chiuderanno nei prossimi giorni/settimane")
            st.write("""
                Escludiamo i progetti che hanno tempo_previsto=0 (non impostato).
                Calcoliamo la data di fine calcolata = data_inizio + tempo_previsto (giorni).
            """)

            # In carica_dati_completo() abbiamo convertito tempo_previsto in int
            df_ok = df[(df['tempo_previsto'].notna()) & (df['tempo_previsto'] > 0)]
            df_ok['fine_calcolata'] = pd.to_datetime(df_ok['data_inizio'], errors='coerce') + \
                                      pd.to_timedelta(df_ok['tempo_previsto'], unit='D')

            df_incorso = df_ok[df_ok['stato_progetto'] == 'In corso'].copy()

            st.subheader("Mostriamo i Progetti In Corso con tempo_previsto > 0")
            st.dataframe(df_incorso[['cliente','stato_progetto','data_inizio','tempo_previsto','fine_calcolata','sales_recruiter']])

            st.write("**Vuoi vedere quali progetti si chiuderanno entro X giorni da oggi?**")
            orizzonte_giorni = st.number_input("Seleziona i giorni di orizzonte", value=14, min_value=1)
            today = datetime.today()
            df_prossimi = df_incorso[df_incorso['fine_calcolata'] <= (today + timedelta(days=orizzonte_giorni))]
            if not df_prossimi.empty:
                st.info(f"Progetti in corso che si chiuderanno entro {orizzonte_giorni} giorni:")
                st.dataframe(df_prossimi[['cliente','sales_recruiter','fine_calcolata']])
                
                st.subheader("Recruiter che si libereranno in questo orizzonte")
                closings = df_prossimi.groupby('sales_recruiter').size().reset_index(name='progetti_che_chiudono')
                df_capacity = carica_recruiters_capacity()
                df_attivi = df[df['stato_progetto'].isin(["In corso","Bloccato"])]
                attivi_count = df_attivi.groupby('sales_recruiter').size().reset_index(name='Progetti Attivi')

                rec_df = df_capacity.merge(attivi_count, on='sales_recruiter', how='left').fillna(0)
                rec_df['Progetti Attivi'] = rec_df['Progetti Attivi'].astype(int)
                rec_df = rec_df.merge(closings, on='sales_recruiter', how='left').fillna(0)
                rec_df['progetti_che_chiudono'] = rec_df['progetti_che_chiudono'].astype(int)

                rec_df['Nuovi Attivi'] = rec_df['Progetti Attivi'] - rec_df['progetti_che_chiudono']
                rec_df.loc[rec_df['Nuovi Attivi'] < 0, 'Nuovi Attivi'] = 0
                rec_df['Capacità Disponibile'] = rec_df['capacity'] - rec_df['Nuovi Attivi']
                rec_df.loc[rec_df['Capacità Disponibile'] < 0, 'Capacità Disponibile'] = 0

                st.dataframe(rec_df[['sales_recruiter','capacity','Progetti Attivi','progetti_che_chiudono','Nuovi Attivi','Capacità Disponibile']])
                st.write("""
                    Da questa tabella vedi quanti progetti chiudono per ogni recruiter 
                    entro l'orizzonte selezionato, 
                    e di conseguenza la nuova 'Capacità Disponibile' calcolata.
                """)
            else:
                st.info("Nessun progetto in corso si chiuderà in questo orizzonte.")

        ################################
        # TAB 3: Bonus e Premi
        ################################
        with tab3:
            st.subheader("Bonus e Premi")
            st.write("""
                Esempio: 4 stelle => 400€, 5 stelle => 500€, ecc.
            """)
            st.markdown("### Filtro per Anno")
            anni_disponibili_bonus = sorted(df['data_inizio_dt'].dt.year.dropna().unique())
            if len(anni_disponibili_bonus) == 0:
                st.warning("Nessun dato disponibile per il filtro dei bonus.")
                st.stop()
            # Converti gli anni in interi
            anni_disponibili_bonus = [int(y) for y in anni_disponibili_bonus]
            anno_bonus = st.selectbox("Seleziona Anno", options=anni_disponibili_bonus, index=len(anni_disponibili_bonus)-1, key='bonus_anno')
            
            # Filtra i dati in base all'anno selezionato
            try:
                start_date_bonus = datetime(anno_bonus, 1, 1)
                end_date_bonus = datetime(anno_bonus, 12, 31)
            except TypeError as e:
                st.error(f"Errore nella selezione di Anno per i bonus: {e}")
                st.stop()

            # Calcola il bonus totale per ogni recruiter
            leaderboard_df = calcola_leaderboard(
                df=df,
                start_date=start_date_bonus,
                end_date=end_date_bonus
            )

            if leaderboard_df.empty:
                st.info("Nessun progetto completato in questo periodo.")
            else:
                st.write("Classifica Annuale con punteggio e badge:")
                st.dataframe(leaderboard_df)

                fig_leader = px.bar(
                    leaderboard_df,
                    x='sales_recruiter',
                    y='punteggio',
                    color='badge',
                    title='Leaderboard Annuale',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "Grey": "grey"  # Colore di default per badge vuoti
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

                st.markdown("""
                **Formula Punteggio**  
                - +10 punti ogni progetto completato  
                - +500 punti per ogni recensione a 5 stelle  
                - +400 punti per ogni recensione a 4 stelle  
                - +50 punti per ogni progetto completato in meno di 60 giorni  
                - +300 punti per la retention (6+ mesi)  
                - -200 punti per la retention (meno di 3 mesi)  
                - +100 punti per ogni riunione a cui partecipa  
                - +1000 punti per ogni nuovo cliente acquisito tramite referral  
                - +300 punti per ogni corso completato  
                """)

                st.markdown("""
                **Badge**  
                - **Gold:** Punteggio >= 10000  
                - **Silver:** Punteggio >= 5000  
                - **Bronze:** Punteggio >= 2000  
                - **Grey:** Altri punteggi  
                """)

        ################################
        # TAB 4: Backup
        ################################
        with tab4:
            st.subheader("Gestione Backup (Esportazione e Ripristino)")
            
            st.markdown("### Esporta Dati in ZIP")
            if st.button("Esegui Backup Ora", key='backup_now'):
                with st.spinner("Eseguendo il backup..."):
                    backup_database()

            backup_zip_path = os.path.join('backup', 'backup.zip')
            if os.path.exists(backup_zip_path):
                with open(backup_zip_path, 'rb') as f:
                    st.download_button(
                        label="Scarica Backup ZIP",
                        data=f,
                        file_name="backup.zip",
                        mime='application/zip'
                    )
            else:
                st.info("Nessun file ZIP di backup presente.")
            
            st.markdown("---")
            st.markdown("### Ripristina Dati da ZIP")
            uploaded_zip = st.file_uploader("Carica l'archivio ZIP di backup", type=['zip'], key='upload_zip')
            if uploaded_zip is not None:
                if st.button("Ripristina DB da ZIP", key='restore_db'):
                    with st.spinner("Ripristinando il database..."):
                        restore_from_zip(uploaded_zip)

        ################################
        # TAB 5: Classifica
        ################################
        with tab5:
            st.subheader("Classifica (Matplotlib)")

            st.markdown("### Filtro per Anno")
            anni_leader = sorted(df['data_inizio_dt'].dt.year.dropna().unique())
            if len(anni_leader) == 0:
                st.warning("Nessun dato disponibile per il leaderboard.")
                st.stop()
            # Converti gli anni in interi
            anni_leader = [int(y) for y in anni_leader]
            anno_leader = st.selectbox("Seleziona Anno", options=anni_leader, index=len(anni_leader)-1, key='leaderboard_anno')

            # Filtra i dati per il leaderboard basato sull'anno selezionato
            try:
                start_date_leader = datetime(anno_leader, 1, 1)
                end_date_leader = datetime(anno_leader, 12, 31)
            except TypeError as e:
                st.error(f"Errore nella selezione di Anno per il leaderboard: {e}")
                st.stop()

            df_leader_filtered = df[
                (df['data_inizio_dt'] >= pd.Timestamp(start_date_leader)) &
                (df['data_inizio_dt'] <= pd.Timestamp(end_date_leader))
            ]

            st.write(f"Anno in analisi: {anno_leader}")

            leaderboard_df = calcola_leaderboard(df_leader_filtered, start_date_leader, end_date_leader)
            if leaderboard_df.empty:
                st.info("Nessun progetto completato in questo periodo.")
            else:
                st.write("Classifica Annuale con punteggio e badge:")
                st.dataframe(leaderboard_df)

                fig_leader = px.bar(
                    leaderboard_df,
                    x='sales_recruiter',
                    y='punteggio',
                    color='badge',
                    title='Leaderboard Annuale',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "Grey": "grey"
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

                st.markdown("""
                **Formula Punteggio**  
                - +10 punti ogni progetto completato  
                - +500 punti per ogni recensione a 5 stelle  
                - +400 punti per ogni recensione a 4 stelle  
                - +50 punti per ogni progetto completato in meno di 60 giorni  
                - +300 punti per la retention (6+ mesi)  
                - -200 punti per la retention (meno di 3 mesi)  
                - +100 punti per ogni riunione a cui partecipa  
                - +1000 punti per ogni nuovo cliente acquisito tramite referral  
                - +300 punti per ogni corso completato  
                """)

                st.markdown("""
                **Badge**  
                - **Gold:** Punteggio >= 10000  
                - **Silver:** Punteggio >= 5000  
                - **Bronze:** Punteggio >= 2000  
                - **Grey:** Altri punteggi  
                """)

            ################################
            # Grafici nella Classifica
            ################################
            st.subheader("Grafici della Classifica")

            # **Tempo Medio per Recruiter**
            st.markdown("**1) Tempo Medio per Recruiter**")
            df_comp = df_leader_filtered[
                (df_leader_filtered['stato_progetto'] == 'Completato') &
                (df_leader_filtered['data_inizio_dt'] >= pd.Timestamp(start_date_leader)) &
                (df_leader_filtered['data_inizio_dt'] <= pd.Timestamp(end_date_leader))
            ].copy()
            veloce = df_comp.groupby('sales_recruiter')['tempo_totale'].mean().reset_index()
            veloce['tempo_totale'] = veloce['tempo_totale'].fillna(0)
            veloce = veloce.sort_values(by='tempo_totale', ascending=True)
            if veloce.empty:
                st.info("Nessun progetto completato per calcolare la velocità.")
            else:
                fig2, ax2 = plt.subplots(figsize=(8,6))
                ax2.bar(veloce['sales_recruiter'], veloce['tempo_totale'], color='#636EFA')  # Colore simile al grafico avvicinamento
                ax2.set_title("Tempo Medio (giorni) - Più basso = più veloce")
                ax2.set_xlabel("Recruiter")
                ax2.set_ylabel("Tempo Medio (giorni)")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig2)

            # **Bonus Totale per Recruiter**
            st.markdown("**2) Bonus Totale per Recruiter**")
            if not leaderboard_df.empty:
                fig3, ax3 = plt.subplots(figsize=(8,6))
                ax3.bar(leaderboard_df['sales_recruiter'], leaderboard_df['punteggio'], color='#EF553B')  # Colore simile al grafico avvicinamento
                ax3.set_title("Bonus Totale Ottenuto")
                ax3.set_xlabel("Recruiter")
                ax3.set_ylabel("Bonus Totale (€)")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig3)
            else:
                st.info("Nessun bonus calcolato.")

#######################################
# 3. GESTISCI OPZIONI
#######################################
elif scelta == "Gestisci Opzioni":
    st.write("Gestione settori, PM, recruiters e capacity in `manage_options.py`.")
    st.markdown("### Nota")
    st.markdown("""
    La gestione delle opzioni (settori, Project Managers, Recruiters e Capacità) è gestita nel file `manage_options.py`.
    Assicurati di navigare a quella pagina per gestire le tue opzioni.
    """)

#######################################
# 4. GESTISCI
#######################################
elif scelta == "Gestisci":
    st.header("Gestione Avanzata")

    # Creiamo le Tab per Riunioni, Referrals, Formazione, Retention
    tab_riunioni, tab_referrals, tab_formazione, tab_retention = st.tabs(["Riunioni", "Referrals", "Formazione", "Retention"])

    ###################################
    # TAB: Riunioni
    ###################################
    with tab_riunioni:
        st.subheader("Gestione Riunioni")
        
        # Form per inserire una nuova riunione
        with st.form("form_inserisci_riunione"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            data_riunione = st.date_input("Data Riunione", value=datetime.today())
            partecipato = st.selectbox("Partecipato", PARTICIPATO_OPTIONS)
            
            submit_riunione = st.form_submit_button("Inserisci Riunione")
            if submit_riunione:
                inserisci_riunione(recruiter_id, data_riunione, partecipato)
        
        st.write("---")
        st.subheader("Modifica / Elimina Riunioni Esistenti")
        riunioni = carica_riunioni()
        if riunioni:
            for riunione in riunioni:
                ri_id = riunione['id']
                recruiter_id = riunione['recruiter_id']
                data_riunione = riunione['data_riunione']
                partecipato = riunione['partecipato']
                
                with st.expander(f"Riunione ID {ri_id} - {data_riunione}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox(
                        "Recruiter", 
                        recruiter_nomi, 
                        index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)),
                        key=f"recruiter_{ri_id}"
                    )
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    data_riunione_new = st.date_input(
                        "Data Riunione", 
                        value=datetime.strptime(data_riunione, '%Y-%m-%d').date(), 
                        key=f"data_riunione_{ri_id}"
                    )
                    partecipato_new = st.selectbox(
                        "Partecipato", 
                        PARTICIPATO_OPTIONS, 
                        index=int(partecipato), 
                        key=f"partecipato_{ri_id}"
                    )
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod = st.button("Modifica", key=f"mod_riunione_{ri_id}")
                    with col2:
                        btn_del = st.button("Elimina", key=f"del_riunione_{ri_id}")
                    
                    if btn_mod:
                        modifica_riunione(ri_id, recruiter_id_new, data_riunione_new, partecipato_new)
                    
                    if btn_del:
                        elimina_riunione(ri_id)
        else:
            st.info("Nessuna riunione presente nel DB.")

    ###################################
    # TAB: Referrals
    ###################################
    with tab_referrals:
        st.subheader("Gestione Referrals")
        
        # Form per inserire un nuovo referral
        with st.form("form_inserisci_referral"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            cliente_nome = st.text_input("Nome Cliente")
            data_referral = st.date_input("Data Referral", value=datetime.today())
            stato_referral = st.selectbox("Stato Referral", STATO_REFERRAL_OPTIONS)
            
            submit_referral = st.form_submit_button("Inserisci Referral")
            if submit_referral:
                if not cliente_nome.strip():
                    st.error("Il campo 'Nome Cliente' è obbligatorio!")
                else:
                    inserisci_referral(recruiter_id, cliente_nome, data_referral, stato_referral)
        
        st.write("---")
        st.subheader("Modifica / Elimina Referrals Esistenti")
        referrals = carica_referrals()
        if referrals:
            for referral in referrals:
                ref_id = referral['id']
                recruiter_id = referral['recruiter_id']
                cliente_nome = referral['cliente_nome']
                data_referral = referral['data_referral']
                stato = referral['stato']
                
                with st.expander(f"Referral ID {ref_id} - {cliente_nome}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox(
                        "Recruiter", 
                        recruiter_nomi, 
                        index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)),
                        key=f"recruiter_ref_{ref_id}"
                    )
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    cliente_nome_new = st.text_input("Nome Cliente", value=cliente_nome, key=f"cliente_ref_{ref_id}")
                    data_referral_new = st.date_input(
                        "Data Referral", 
                        value=datetime.strptime(data_referral, '%Y-%m-%d').date(), 
                        key=f"data_referral_{ref_id}"
                    )
                    stato_referral_new = st.selectbox(
                        "Stato Referral", 
                        STATO_REFERRAL_OPTIONS, 
                        index=STATO_REFERRAL_OPTIONS.index(stato),
                        key=f"stato_referral_{ref_id}"
                    )
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_ref = st.button("Modifica", key=f"mod_referral_{ref_id}")
                    with col2:
                        btn_del_ref = st.button("Elimina", key=f"del_referral_{ref_id}")
                    
                    if btn_mod_ref:
                        if not cliente_nome_new.strip():
                            st.error("Il campo 'Nome Cliente' è obbligatorio!")
                        else:
                            modifica_referral(ref_id, recruiter_id_new, cliente_nome_new, data_referral_new, stato_referral_new)
                    
                    if btn_del_ref:
                        elimina_referral(ref_id)
        else:
            st.info("Nessun referral presente nel DB.")

    ###################################
    # TAB: Formazione
    ###################################
    with tab_formazione:
        st.subheader("Gestione Formazione")
        
        # Form per inserire una nuova formazione
        with st.form("form_inserisci_formazione"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            corso_nome = st.text_input("Nome Corso")
            data_completamento = st.date_input("Data Completamento", value=datetime.today())
            
            submit_formazione = st.form_submit_button("Inserisci Formazione")
            if submit_formazione:
                if not corso_nome.strip():
                    st.error("Il campo 'Nome Corso' è obbligatorio!")
                else:
                    inserisci_formazione(recruiter_id, corso_nome, data_completamento)
        
        st.write("---")
        st.subheader("Modifica / Elimina Formazione Esistenti")
        formazioni = carica_formazione()
        if formazioni:
            for formazione in formazioni:
                form_id = formazione['id']
                recruiter_id = formazione['recruiter_id']
                corso_nome = formazione['corso_nome']
                data_completamento = formazione['data_completamento']
                
                with st.expander(f"Formazione ID {form_id} - {corso_nome}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox(
                        "Recruiter", 
                        recruiter_nomi, 
                        index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)),
                        key=f"recruiter_formazione_{form_id}"
                    )
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    corso_nome_new = st.text_input("Nome Corso", value=corso_nome, key=f"corso_formazione_{form_id}")
                    data_completamento_new = st.date_input(
                        "Data Completamento", 
                        value=datetime.strptime(data_completamento, '%Y-%m-%d').date(), 
                        key=f"data_completamento_formazione_{form_id}"
                    )
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_form = st.button("Modifica", key=f"mod_formazione_{form_id}")
                    with col2:
                        btn_del_form = st.button("Elimina", key=f"del_formazione_{form_id}")
                    
                    if btn_mod_form:
                        if not corso_nome_new.strip():
                            st.error("Il campo 'Nome Corso' è obbligatorio!")
                        else:
                            modifica_formazione(form_id, recruiter_id_new, corso_nome_new, data_completamento_new)
                    
                    if btn_del_form:
                        elimina_formazione(form_id)
        else:
            st.info("Nessuna formazione presente nel DB.")

    ###################################
    # TAB: Retention
    ###################################
    with tab_retention:
        st.subheader("Gestione Retention dei Candidati")
        
        # Form per inserire una nuova retention
        with st.form("form_inserisci_retention"):
            progetti = carica_dati_completo()
            progetti_completati = progetti[progetti['stato_progetto'] == 'Completato']
            progetto_nomi = progetti_completati['cliente'].tolist()
            progetto_sel = st.selectbox("Progetto", progetto_nomi)
            progetto_id = None
            for p in progetti_completati.itertuples():
                if p.cliente == progetto_sel:
                    progetto_id = p.id
                    break
            
            data_assunzione = st.date_input("Data Assunzione", value=datetime.today())
            data_cessazione = st.date_input("Data Cessazione (lascia vuoto se ancora in posizione)")
            
            submit_retention = st.form_submit_button("Inserisci Retention")
            if submit_retention:
                inserisci_retention(progetto_id, data_assunzione, data_cessazione if data_cessazione != datetime.today().date() else None)
        
        st.write("---")
        st.subheader("Modifica / Elimina Retention Esistenti")
        retention = carica_retention()
        if retention:
            for ret in retention:
                ret_id = ret['id']
                progetto_id = ret['progetto_id']
                data_assunzione = ret['data_assunzione']
                data_cessazione = ret['data_cessazione']
                
                with st.expander(f"Retention ID {ret_id} - Progetto ID {progetto_id}"):
                    progetti = carica_dati_completo()
                    progetto = progetti[progetti['id'] == progetto_id]
                    if not progetto.empty:
                        progetto_nome = progetto.iloc[0]['cliente']
                    else:
                        progetto_nome = "Progetto Non Trovato"

                    progetti_completati = progetti[progetti['stato_progetto'] == 'Completato']
                    progetto_nomi = progetti_completati['cliente'].tolist()
                    progetto_sel = st.selectbox(
                        "Progetto", 
                        progetto_nomi, 
                        index=progetto_nomi.index(progetto_nome) if progetto_nome in progetto_nomi else 0,
                        key=f"progetto_retention_{ret_id}"
                    )
                    progetto_id_new = None
                    for p in progetti_completati.itertuples():
                        if p.cliente == progetto_sel:
                            progetto_id_new = p.id
                            break

                    data_assunzione_new = st.date_input(
                        "Data Assunzione", 
                        value=datetime.strptime(data_assunzione, '%Y-%m-%d').date(), 
                        key=f"data_assunzione_retention_{ret_id}"
                    )
                    data_cessazione_new = st.date_input(
                        "Data Cessazione", 
                        value=datetime.strptime(data_cessazione, '%Y-%m-%d').date() if data_cessazione else datetime.today().date(),
                        key=f"data_cessazione_retention_{ret_id}"
                    )
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_ret = st.button("Modifica", key=f"mod_retention_{ret_id}")
                    with col2:
                        btn_del_ret = st.button("Elimina", key=f"del_retention_{ret_id}")
                    
                    if btn_mod_ret:
                        modifica_retention(ret_id, progetto_id_new, data_assunzione_new, data_cessazione_new)
                    
                    if btn_del_ret:
                        elimina_retention(ret_id)
        else:
            st.info("Nessuna retention presente nel DB.")

#######################################
# FINE DEL CODICE
#######################################
