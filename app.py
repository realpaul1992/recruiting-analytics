# app.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt
import os
import zipfile  # Import per gestire ZIP
from io import BytesIO

#######################################
# FUNZIONI DI ACCESSO AL DB (MySQL)
#######################################

def get_connection():
    """
    Ritorna una connessione MySQL usando pymysql.
    Utilizza le variabili d'ambiente definite in Streamlit Secrets.
    """
    try:
        connection = pymysql.connect(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets["DB_PORT"]),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            cursorclass=pymysql.cursors.DictCursor  # Per avere dizionari anziché tuple
        )
        return connection
    except pymysql.err.OperationalError as e:
        st.error("Impossibile connettersi al database. Controlla le credenziali e l'accessibilità del database.")
        st.stop()
    except Exception as e:
        st.error(f"Errore inaspettato: {e}")
        st.stop()

def carica_settori():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM settori ORDER BY nome ASC")
            settori = c.fetchall()
    finally:
        conn.close()
    return settori

def carica_project_managers():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
            project_managers = c.fetchall()
    finally:
        conn.close()
    return project_managers

def carica_recruiters():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            recruiters = c.fetchall()
    finally:
        conn.close()
    return recruiters

def carica_candidati():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, sales_recruiter_id, candidato_nome, data_inserimento, data_placement, data_dimissioni FROM candidati")
            candidati = c.fetchall()
    except pymysql.Error as e:
        st.error(f"Errore nel caricamento dei candidati: {e}")
        return []
    finally:
        conn.close()
    return candidati

def carica_riunioni():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, recruiter_id, data_riunione, partecipato FROM riunioni")
            riunioni = c.fetchall()
    except pymysql.Error as e:
        st.error(f"Errore nel caricamento delle riunioni: {e}")
        return []
    finally:
        conn.close()
    return riunioni

def carica_referrals():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, recruiter_id, cliente_nome, data_referral, stato FROM referrals")
            referrals = c.fetchall()
    except pymysql.Error as e:
        st.error(f"Errore nel caricamento dei referrals: {e}")
        return []
    finally:
        conn.close()
    return referrals

def carica_formazione():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, recruiter_id, corso_nome, data_completamento FROM formazione")
            formazione = c.fetchall()
    except pymysql.Error as e:
        st.error(f"Errore nel caricamento della formazione: {e}")
        return []
    finally:
        conn.close()
    return formazione

def inserisci_dati(cliente, settore_id, pm_id, rec_id, data_inizio):
    """
    Inserisce un nuovo progetto in MySQL.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
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
    except pymysql.Error as e:
        st.error(f"Errore nell'inserimento del progetto: {e}")
    finally:
        conn.close()

def carica_dati_completo():
    """
    Carica i progetti uniti a settori, pm, recruiters, includendo 'tempo_previsto'.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
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

        df = pd.DataFrame(rows, columns=columns)
        
        # Convertiamo 'tempo_previsto' a numerico
        if "tempo_previsto" in df.columns:
            df["tempo_previsto"] = pd.to_numeric(df["tempo_previsto"], errors="coerce")
            df["tempo_previsto"] = df["tempo_previsto"].fillna(0).astype(int)
        
        # Aggiungi 'data_inizio_dt' e 'recensione_data_dt' subito dopo
        df['data_inizio_dt'] = pd.to_datetime(df['data_inizio'], errors='coerce')
        df['recensione_data_dt'] = pd.to_datetime(df['recensione_data'], errors='coerce')
        
    finally:
        conn.close()

    return df

#######################################
# DEFINIZIONE DELLA FUNZIONE calcola_bonus
#######################################
def calcola_bonus(stelle):
    """
    Calcola il bonus in base al numero di stelle della recensione.
    - 4 stelle: 300€
    - 5 stelle: 500€
    - Altri valori: 0€
    """
    if stelle == 4:
        return 300
    elif stelle == 5:
        return 500
    else:
        return 0

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
        try:
            with conn.cursor() as c:
                # Legge l’elenco delle tabelle
                c.execute("SHOW TABLES")
                tables = c.fetchall()

                st.info("Inizio backup MySQL in ZIP...")

                for (table_name,) in tables:
                    # Query: SELECT * FROM <table_name>
                    c.execute(f"SELECT * FROM {table_name}")
                    rows = c.fetchall()
                    col_names = [desc[0] for desc in c.description]

                    df_table = pd.DataFrame(rows, columns=col_names)
                    csv_data = df_table.to_csv(index=False, encoding="utf-8")

                    # Scrivi il CSV direttamente nell'archivio ZIP
                    backup_zip.writestr(f"{table_name}.csv", csv_data)

        finally:
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
        try:
            with conn.cursor() as c:
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

        except pymysql.Error as e:
            st.error(f"Errore nel ripristino del database: {e}")
            conn.rollback()
        finally:
            conn.close()

    conn.commit()
    st.success("Ripristino completato con successo da ZIP.")

#######################################
# CAPACITA' PER RECRUITER
#######################################
def carica_recruiters_capacity():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute('''
                SELECT r.id, r.nome AS sales_recruiter,
                       IFNULL(rc.capacity_max, 5) AS capacity
                FROM recruiters r
                LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
                ORDER BY r.nome
            ''')
            rows = c.fetchall()
    except pymysql.Error as e:
        st.error(f"Errore nel caricamento della capacità dei recruiter: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    df_capacity = pd.DataFrame(rows, columns=['id', 'sales_recruiter', 'capacity'])
    return df_capacity

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD MENSILE
#######################################
def calcola_leaderboard_mensile(df_progetti, df_candidati, df_riunioni, df_referrals, df_formazione, start_date, end_date):
    """
    Calcola la leaderboard basata su vari criteri di punteggio.
    """
    # Filtra i progetti completati nel periodo
    df_temp = df_progetti.copy()
    df_temp['data_inizio_dt'] = pd.to_datetime(df_temp['data_inizio'], errors='coerce')
    df_temp['data_fine_dt'] = pd.to_datetime(df_temp['data_fine'], errors='coerce')
    df_temp['recensione_stelle'] = df_temp['recensione_stelle'].fillna(0).astype(int)

    # Bonus da recensioni
    df_temp['bonus_recensione'] = df_temp['recensione_stelle'].apply(calcola_bonus)

    # Punteggio per completamento rapido (<60 giorni)
    df_temp['giorni_completamento'] = (df_temp['data_fine_dt'] - df_temp['data_inizio_dt']).dt.days
    df_temp['bonus_completamento'] = df_temp['giorni_completamento'].apply(lambda x: 50 if x < 60 else 0)

    # Filtro progetti completati nel periodo
    mask = (
        (df_temp['stato_progetto'] == 'Completato') &
        (df_temp['data_inizio_dt'] >= pd.Timestamp(start_date)) &
        (df_temp['data_inizio_dt'] <= pd.Timestamp(end_date))
    )
    df_filtro = df_temp[mask].copy()

    if df_filtro.empty:
        return pd.DataFrame([], columns=[
            'sales_recruiter','completati','tempo_medio','bonus_totale','bonus_completamento',
            'bonus_retenzione','bonus_riunioni','bonus_referrals','bonus_formazione','punteggio','badge'
        ])

    # Calcola completati e tempo medio
    group = df_filtro.groupby('sales_recruiter')
    completati = group.size().reset_index(name='completati')
    tempo_medio = group['tempo_totale'].mean().reset_index(name='tempo_medio')
    bonus_recensione = group['bonus_recensione'].sum().reset_index(name='bonus_totale')
    bonus_completamento = group['bonus_completamento'].sum().reset_index(name='bonus_completamento')

    # Merge i primi tre dataframe
    leaderboard = completati.merge(tempo_medio, on='sales_recruiter', how='left')
    leaderboard = leaderboard.merge(bonus_recensione, on='sales_recruiter', how='left')
    leaderboard = leaderboard.merge(bonus_completamento, on='sales_recruiter', how='left')

    # Calcola bonus per retenzione
    df_candidati_filtered = pd.DataFrame(df_candidati)
    df_candidati_filtered['data_placement_dt'] = pd.to_datetime(df_candidati_filtered['data_placement'], errors='coerce')
    df_candidati_filtered['data_dimissioni_dt'] = pd.to_datetime(df_candidati_filtered['data_dimissioni'], errors='coerce')

    # Calcola mesi di permanenza
    df_candidati_filtered['mesi_permanenza'] = ((df_candidati_filtered['data_dimissioni_dt'] - df_candidati_filtered['data_placement_dt']).dt.days) / 30

    # Candidati che rimangono >=6 mesi
    df_retenzione_stayed = df_candidati_filtered[df_candidati_filtered['mesi_permanenza'] >= 6]
    bonus_retenzione = df_retenzione_stayed.groupby('sales_recruiter_id').size().reset_index(name='bonus_retenzione')
    bonus_retenzione['bonus_retenzione'] = bonus_retenzione['bonus_retenzione'] * 300

    # Candidati che lasciano <=3 mesi
    df_retenzione_left = df_candidati_filtered[df_candidati_filtered['mesi_permanenza'] <= 3]
    bonus_retenzione_left = df_retenzione_left.groupby('sales_recruiter_id').size().reset_index(name='bonus_retenzione_left')
    bonus_retenzione_left['bonus_retenzione_left'] = bonus_retenzione_left['bonus_retenzione_left'] * -200

    # Merge bonus_retenzione e bonus_retenzione_left
    bonus_retenzione_total = pd.merge(bonus_retenzione, bonus_retenzione_left, on='sales_recruiter_id', how='outer').fillna(0)
    bonus_retenzione_total['bonus_retenzione'] = bonus_retenzione_total['bonus_retenzione'] + bonus_retenzione_total['bonus_retenzione_left']
    bonus_retenzione_total = bonus_retenzione_total[['sales_recruiter_id', 'bonus_retenzione']]

    # Merge con il dataframe principale
    leaderboard = leaderboard.merge(bonus_retenzione_total, left_on='sales_recruiter', right_on='sales_recruiter_id', how='left')
    leaderboard['bonus_retenzione'] = leaderboard['bonus_retenzione'].fillna(0)

    # Calcola bonus per riunioni partecipate
    df_riunioni_filtered = pd.DataFrame(df_riunioni)
    df_riunioni_filtered['data_riunione_dt'] = pd.to_datetime(df_riunioni_filtered['data_riunione'], errors='coerce')
    df_riunioni_filtered = df_riunioni_filtered[
        (df_riunioni_filtered['data_riunione_dt'] >= pd.Timestamp(start_date)) &
        (df_riunioni_filtered['data_riunione_dt'] <= pd.Timestamp(end_date)) &
        (df_riunioni_filtered['partecipato'] == True)
    ]
    bonus_riunioni = df_riunioni_filtered.groupby('recruiter_id').size().reset_index(name='bonus_riunioni')
    bonus_riunioni['bonus_riunioni'] = bonus_riunioni['bonus_riunioni'] * 100

    # Merge con il dataframe principale
    leaderboard = leaderboard.merge(bonus_riunioni, left_on='sales_recruiter', right_on='recruiter_id', how='left')
    leaderboard['bonus_riunioni'] = leaderboard['bonus_riunioni'].fillna(0)

    # Calcola bonus per referrals
    df_referrals_filtered = pd.DataFrame(df_referrals)
    df_referrals_filtered['data_referral_dt'] = pd.to_datetime(df_referrals_filtered['data_referral'], errors='coerce')
    # Considera solo referrals nel periodo e con stato 'Chiuso' (nuovo cliente acquisito)
    df_referrals_filtered = df_referrals_filtered[
        (df_referrals_filtered['data_referral_dt'] >= pd.Timestamp(start_date)) &
        (df_referrals_filtered['data_referral_dt'] <= pd.Timestamp(end_date)) &
        (df_referrals_filtered['stato'] == 'Chiuso')
    ]
    bonus_referrals = df_referrals_filtered.groupby('recruiter_id').size().reset_index(name='bonus_referrals')
    bonus_referrals['bonus_referrals'] = bonus_referrals['bonus_referrals'] * 1000

    # Merge con il dataframe principale
    leaderboard = leaderboard.merge(bonus_referrals, left_on='sales_recruiter', right_on='recruiter_id', how='left')
    leaderboard['bonus_referrals'] = leaderboard['bonus_referrals'].fillna(0)

    # Calcola bonus per formazione
    df_formazione_filtered = pd.DataFrame(df_formazione)
    df_formazione_filtered['data_completamento_dt'] = pd.to_datetime(df_formazione_filtered['data_completamento'], errors='coerce')
    df_formazione_filtered = df_formazione_filtered[
        (df_formazione_filtered['data_completamento_dt'] >= pd.Timestamp(start_date)) &
        (df_formazione_filtered['data_completamento_dt'] <= pd.Timestamp(end_date))
    ]
    bonus_formazione = df_formazione_filtered.groupby('recruiter_id').size().reset_index(name='bonus_formazione')
    bonus_formazione['bonus_formazione'] = bonus_formazione['bonus_formazione'] * 300

    # Merge con il dataframe principale
    leaderboard = leaderboard.merge(bonus_formazione, left_on='sales_recruiter', right_on='recruiter_id', how='left')
    leaderboard['bonus_formazione'] = leaderboard['bonus_formazione'].fillna(0)

    # Calcola punteggio totale
    leaderboard['punteggio'] = (
        leaderboard['completati'] * 10 +
        leaderboard['bonus_totale'] +
        leaderboard['bonus_completamento'] +
        leaderboard['bonus_retenzione'] +
        leaderboard['bonus_riunioni'] +
        leaderboard['bonus_referrals'] +
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
        return ""

    leaderboard['badge'] = leaderboard['punteggio'].apply(assegna_badge)

    # Ordina per punteggio
    leaderboard = leaderboard.sort_values('punteggio', ascending=False)

    # Rinomina le colonne per chiarezza
    leaderboard = leaderboard.rename(columns={
        'sales_recruiter': 'Sales Recruiter',
        'completati': 'Progetti Completati',
        'tempo_medio': 'Tempo Medio (giorni)',
        'bonus_totale': 'Bonus Recensioni (€)',
        'bonus_completamento': 'Bonus Completamento Rapido (€)',
        'bonus_retenzione': 'Bonus Retenzione (€)',
        'bonus_riunioni': 'Bonus Riunioni (€)',
        'bonus_referrals': 'Bonus Referrals (€)',
        'bonus_formazione': 'Bonus Formazione (€)',
        'punteggio': 'Punteggio Totale',
        'badge': 'Badge'
    })

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

# Carichiamo i riferimenti
settori_db = carica_settori()
pm_db = carica_project_managers()
rec_db = carica_recruiters()

st.title("Gestione Progetti di Recruiting")
st.sidebar.title("Navigazione")
scelta = st.sidebar.radio("Vai a", ["Inserisci Dati", "Dashboard", "Gestisci Opzioni"])

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
        
        data_inizio_str = st.text_input("Data di Inizio (GG/MM/AAAA)", 
                                        value="", 
                                        placeholder="Lascia vuoto se non disponibile")

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
    df_progetti = carica_dati_completo()
    df_candidati = carica_candidati()
    df_riunioni = carica_riunioni()
    df_referrals = carica_referrals()
    df_formazione = carica_formazione()
    
    if df_progetti.empty:
        st.info("Nessun progetto disponibile nel DB.")
    else:
        # Creiamo le Tab
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Panoramica",
            "Carico Proiettato / Previsione",
            "Bonus e Premi",
            "Backup",
            "Classifica"
        ])

        ################################
        # TAB 1: Panoramica
        ################################
        with tab1:
            st.subheader("Tempo Medio Generale e per Recruiter/Settore")

            # Filtro per Anno
            st.markdown("### Filtro per Anno")
            anni_disponibili = sorted(df_progetti['data_inizio_dt'].dt.year.dropna().unique())
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

            df_filtered = df_progetti[
                (df_progetti['data_inizio_dt'] >= pd.Timestamp(start_date)) &
                (df_progetti['data_inizio_dt'] <= pd.Timestamp(end_date))
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
                recruiters_unici = df_progetti['sales_recruiter'].unique()
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
            df_ok = df_progetti[(df_progetti['tempo_previsto'].notna()) & (df_progetti['tempo_previsto'] > 0)]
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
                df_attivi = df_progetti[df_progetti['stato_progetto'].isin(["In corso","Bloccato"])]
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
                Esempio: 4 stelle => 300€, 5 stelle => 500€.
            """)
            st.markdown("### Filtro per Anno")
            anni_disponibili_bonus = sorted(df_progetti['data_inizio_dt'].dt.year.dropna().unique())
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

            # Calcola il punteggio totale considerando i nuovi criteri
            leaderboard_df = calcola_leaderboard_mensile(
                df_progetti=df_progetti,
                df_candidati=df_candidati,
                df_riunioni=df_riunioni,
                df_referrals=df_referrals,
                df_formazione=df_formazione,
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
                    x='Sales Recruiter',
                    y='Punteggio Totale',
                    color='Badge',
                    title='Leaderboard Annuale',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "": "grey"  # Colore di default per badge vuoti
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

                st.markdown("""
                **Formula Punteggio**  
                - +10 punti ogni progetto completato  
                - +50 punti per ogni progetto completato in meno di 60 giorni  
                - +300 punti per ogni candidato che rimane in posizione per almeno 6 mesi  
                - -200 punti per ogni candidato che lascia entro 3 mesi  
                - +500 punti per ogni recensione a 5 stelle  
                - +400 punti per ogni recensione a 4 stelle  
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
            if not leaderboard_df.empty:
                st.subheader("Grafici della Classifica")

                # **1) Leaderboard Totale**
                st.markdown("**1) Leaderboard Totale**")
                fig1 = px.bar(
                    leaderboard_df,
                    x='Sales Recruiter',
                    y='Punteggio Totale',
                    color='Badge',
                    title='Punteggio Totale per Recruiter',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "": "grey"  # Colore di default per badge vuoti
                    }
                )
                st.plotly_chart(fig1, use_container_width=True)

                # **2) Recruiter più veloce (Tempo Medio)**
                st.markdown("**2) Recruiter più veloce (Tempo Medio)**")
                df_comp = df_progetti[
                    (df_progetti['stato_progetto'] == 'Completato') &
                    (df_progetti['data_inizio_dt'] >= pd.Timestamp(start_date_bonus)) &
                    (df_progetti['data_inizio_dt'] <= pd.Timestamp(end_date_bonus))
                ].copy()
                veloce = df_comp.groupby('sales_recruiter')['tempo_totale'].mean().reset_index()
                veloce['tempo_totale'] = veloce['tempo_totale'].fillna(0)
                veloce = veloce.sort_values(by='tempo_totale', ascending=True)
                if veloce.empty:
                    st.info("Nessun progetto completato per calcolare la velocità.")
                else:
                    fig2 = px.bar(
                        veloce,
                        x='tempo_totale',
                        y='sales_recruiter',
                        orientation='h',
                        labels={'tempo_totale': 'Tempo Medio (giorni)', 'sales_recruiter': 'Recruiter'},
                        title='Tempo Medio di Chiusura per Recruiter',
                        color='tempo_totale',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # **3) Recruiter con più Bonus ottenuti** (Recensioni)
                st.markdown("**3) Recruiter con più Bonus ottenuti** (Recensioni)")
                df_bonus = leaderboard_df[['Sales Recruiter', 'Bonus Recensioni (€)']].copy()
                df_bonus = df_bonus.rename(columns={'Sales Recruiter': 'sales_recruiter', 'Bonus Recensioni (€)': 'bonus'})
                df_bonus = df_bonus.sort_values(by='bonus', ascending=False)
                if df_bonus.empty:
                    st.info("Nessun bonus calcolato.")
                else:
                    fig3 = px.bar(
                        df_bonus,
                        x='bonus',
                        y='sales_recruiter',
                        orientation='h',
                        labels={'bonus': 'Bonus Totale (€)', 'sales_recruiter': 'Recruiter'},
                        title='Bonus Totale Ottenuto per Recruiter',
                        color='bonus',
                        color_continuous_scale='Oranges'
                    )
                    st.plotly_chart(fig3, use_container_width=True)

#######################################
# 3. GESTISCI OPZIONI
#######################################
elif scelta == "Gestisci Opzioni":
    st.write("Gestione settori, PM, recruiters e capacity in manage_options.py")
    st.markdown("### Nota")
    st.markdown("""
    La gestione delle opzioni (settori, Project Managers, Recruiters e Capacità) è gestita nel file `manage_options.py`.
    Assicurati di navigare a quella pagina per gestire le tue opzioni.
    """)
