# clienti.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, date, timedelta
import sys
import os
import zipfile
import plotly.express as px
import matplotlib.pyplot as plt

# Aggiungi il percorso per importare utils.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import format_date_display, parse_date

####################################
# FUNZIONI DI ACCESSO AL DB (MySQL)
####################################
def get_connection():
    """Crea e restituisce una connessione al database MySQL."""
    return pymysql.connect(
        host="junction.proxy.rlwy.net",  # Parametri da Railway
        port=14718,
        user="root",
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",
        database="railway",
        cursorclass=pymysql.cursors.DictCursor  # Per ottenere risultati come dizionari
    )

def carica_settori_db():
    """Carica tutti i settori dal database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM settori ORDER BY nome ASC")
    settori = c.fetchall()
    conn.close()
    return settori

def carica_project_managers_db():
    """Carica tutti i project managers dal database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
    pm = c.fetchall()
    conn.close()
    return pm

def carica_recruiters_db():
    """Carica tutti i recruiter dal database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
    rec = c.fetchall()
    conn.close()
    return rec

def carica_clienti_db():
    """Carica tutti i clienti distinti dal database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT cliente, settore_id FROM progetti ORDER BY cliente ASC")
    clienti = c.fetchall()
    conn.close()
    return clienti

def cerca_progetti(id_progetto=None, nome_cliente=None, include_continuativi=True):
    """Cerca progetti nel database. Include o esclude progetti continuativi."""
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT 
            p.id,
            p.cliente,
            p.settore_id,
            p.project_manager_id,
            p.sales_recruiter_id,
            p.stato_progetto,
            p.data_inizio,
            p.data_fine,
            p.start_date,
            p.end_date,
            p.number_recruiters,
            p.recensione_stelle,
            p.recensione_data,
            p.tempo_previsto,
            p.is_continuative
        FROM progetti p
        WHERE 1=1
    """
    params = []
    if id_progetto:
        query += " AND p.id = %s"
        params.append(id_progetto)
    if nome_cliente:
        query += " AND p.cliente LIKE %s"
        params.append(f"%{nome_cliente}%")
    if not include_continuativi:
        query += " AND p.is_continuative = 0"

    c.execute(query, tuple(params))
    risultati = c.fetchall()
    conn.close()
    return risultati

def aggiorna_progetto(
    id_progetto,
    cliente,
    settore_id,
    project_manager_id,
    sales_recruiter_id,
    stato_progetto,
    data_inizio,
    data_fine,
    start_date,
    end_date,
    number_recruiters,
    recensione_stelle,
    recensione_data,
    tempo_previsto
):
    """Aggiorna un progetto nel database."""
    conn = get_connection()
    c = conn.cursor()

    # Calcola tempo_totale solo per progetti una tantum
    tempo_totale = None
    if data_inizio and data_fine and not start_date and not end_date:
        tempo_totale = (data_fine - data_inizio).days

    # Converti le date in stringhe nel formato YYYY-MM-DD
    data_inizio_str = data_inizio.strftime('%Y-%m-%d') if data_inizio else None
    data_fine_str = data_fine.strftime('%Y-%m-%d') if data_fine else None
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None
    recensione_data_str = recensione_data.strftime('%Y-%m-%d') if recensione_data else None

    # Formatta 'stato_progetto' correttamente
    if stato_progetto:
        stato_progetto = stato_progetto.strip()

    query = """
        UPDATE progetti
        SET 
            cliente = %s,
            settore_id = %s,
            project_manager_id = %s,
            sales_recruiter_id = %s,
            stato_progetto = %s,
            data_inizio = %s,
            data_fine = %s,
            start_date = %s,
            end_date = %s,
            number_recruiters = %s,
            recensione_stelle = %s,
            recensione_data = %s,
            tempo_previsto = %s,
            tempo_totale = %s
        WHERE id = %s
    """
    c.execute(query, (
        cliente,
        settore_id,
        project_manager_id,
        sales_recruiter_id,
        stato_progetto,
        data_inizio_str,
        data_fine_str,
        start_date_str,
        end_date_str,
        number_recruiters,
        recensione_stelle,
        recensione_data_str,
        tempo_previsto,
        tempo_totale,
        id_progetto
    ))
    conn.commit()
    conn.close()

def cancella_progetto(id_progetto):
    """Cancella un progetto dal database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM progetti WHERE id = %s", (id_progetto,))
    conn.commit()
    conn.close()

def inserisci_progetto_continuativo(
    cliente,
    settore_id,
    project_manager_id,
    sales_recruiter_id,
    stato_progetto,
    start_date,
    end_date,
    number_recruiters
):
    """Inserisce un nuovo progetto continuativo nel database."""
    conn = get_connection()
    c = conn.cursor()

    # Converti le date in stringhe nel formato YYYY-MM-DD
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None

    # Formatta 'stato_progetto' correttamente
    if stato_progetto:
        stato_progetto = stato_progetto.strip()

    query = """
        INSERT INTO progetti (
            cliente,
            settore_id,
            project_manager_id,
            sales_recruiter_id,
            stato_progetto,
            start_date,
            end_date,
            number_recruiters,
            is_continuative
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        # Controllo che settore_id non sia None
        if settore_id is None:
            raise ValueError("settore_id non può essere None. Verifica che il cliente selezionato abbia un settore assegnato.")
        
        c.execute(query, (
            cliente,
            settore_id,
            project_manager_id,
            sales_recruiter_id,
            stato_progetto,
            start_date_str,
            end_date_str,
            number_recruiters,
            1  # is_continuative = True
        ))
        conn.commit()
        st.success("Progetto continuativo inserito con successo!")
    except pymysql.err.IntegrityError as e:
        st.error(f"Errore durante l'inserimento del progetto: {e}")
        conn.rollback()
    except ValueError as ve:
        st.error(f"Errore: {ve}")
        conn.rollback()
    finally:
        conn.close()

def carica_progetti_continuativi_db():
    """Carica i progetti continuativi dal database."""
    return cerca_progetti(include_continuativi=True)

def carica_dati_completo(include_continuativi=True):
    """Carica tutti i progetti dal database. Include o esclude progetti continuativi."""
    risultati = cerca_progetti(include_continuativi=include_continuativi)
    if risultati:
        return pd.DataFrame(risultati)
    else:
        return pd.DataFrame()

def inserisci_candidato(progetto_id, recruiter_id, candidato_nome, data_inserimento, data_dimissioni):
    """Inserisce un nuovo candidato nel database."""
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO candidati (
            progetto_id,
            recruiter_id,
            candidato_nome,
            data_inserimento,
            data_dimissioni,
            data_placement
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        # Imposta 'data_placement' uguale a 'data_inserimento'
        data_placement = data_inserimento.strftime('%Y-%m-%d') if data_inserimento else None
        
        c.execute(query, (
            progetto_id,
            recruiter_id,
            candidato_nome,
            data_inserimento.strftime('%Y-%m-%d') if data_inserimento else None,
            data_dimissioni.strftime('%Y-%m-%d') if data_dimissioni else None,
            data_placement
        ))
        conn.commit()
        st.success("Candidato inserito con successo!")
    except pymysql.Error as e:
        st.error(f"Errore durante l'inserimento del candidato: {e}")
        conn.rollback()
    finally:
        conn.close()

def carica_candidati_progetto(progetto_id):
    """Carica tutti i candidati associati a un progetto specifico."""
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT 
            c.id,
            c.candidato_nome,
            c.data_inserimento,
            c.data_dimissioni,
            c.data_placement
        FROM candidati c
        WHERE c.progetto_id = %s
        ORDER BY c.data_inserimento DESC
    """
    c.execute(query, (progetto_id,))
    candidati = c.fetchall()
    conn.close()
    return candidati

####################################
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
        tables = [list(table.values())[0] for table in c.fetchall()]

        st.info("Inizio backup MySQL in ZIP...")

        for table_name in tables:
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

####################################
# CAPACITA' PER RECRUITER
#######################################
def carica_recruiters_capacity():
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
    df_capacity = pd.DataFrame(rows, columns=['sales_recruiter', 'capacity'])
    conn.close()
    return df_capacity

####################################
# FUNZIONE PER CALCOLARE LEADERBOARD MENSILE
#######################################
def calcola_leaderboard_mensile(df, start_date, end_date):
    df_temp = df.copy()
    df_temp['recensione_stelle'] = df_temp['recensione_stelle'].fillna(0).astype(int)

    # bonus da recensioni
    def bonus_stelle(stelle):
        if stelle == 4:
            return 300
        elif stelle == 5:
            return 500
        return 0
    
    df_temp['bonus'] = df_temp['recensione_stelle'].apply(bonus_stelle)

    # Filtra solo i progetti completati e una tantum
    mask = (
        (df_temp['stato_progetto'] == 'Completato') &
        (df_temp['effective_start_date'] >= pd.Timestamp(start_date)) &
        (df_temp['effective_start_date'] <= pd.Timestamp(end_date)) &
        (df_temp['start_date_dt'].isna())  # Escludi progetti continuativi
    )
    df_filtro = df_temp[mask].copy()

    if df_filtro.empty:
        return pd.DataFrame([], columns=[
            'sales_recruiter','completati','tempo_medio','bonus_totale','punteggio','badge'
        ])

    group = df_filtro.groupby('sales_recruiter')
    completati = group.size().reset_index(name='completati')
    tempo_medio = group['tempo_totale'].mean().reset_index(name='tempo_medio')
    bonus_sum = group['bonus'].sum().reset_index(name='bonus_totale')

    leaderboard = (
        completati
        .merge(tempo_medio, on='sales_recruiter', how='left')
        .merge(bonus_sum, on='sales_recruiter', how='left')
    )

    leaderboard['tempo_medio'] = leaderboard['tempo_medio'].fillna(0)
    leaderboard['bonus_totale'] = leaderboard['bonus_totale'].fillna(0)
    leaderboard['punteggio'] = (
        leaderboard['completati'] * 10
        + leaderboard['bonus_totale']
        + leaderboard['tempo_medio'].apply(lambda x: max(0, 30 - x))
    )

    def assegna_badge(n):
        if n >= 20:
            return "Gold"
        elif n >= 10:
            return "Silver"
        elif n >= 5:
            return "Bronze"
        return ""
    
    leaderboard['badge'] = leaderboard['completati'].apply(assegna_badge)
    leaderboard = leaderboard.sort_values('punteggio', ascending=False)
    return leaderboard

####################################
# FUNZIONI DI RETENTION
####################################
def calcola_retention(df, start_date, end_date):
    """
    Calcola la retention dei clienti nell'intervallo di date specificato.
    """
    df_temp = df.copy()
    
    # Assicurati che 'effective_start_date' sia datetime
    df_temp['effective_start_date'] = pd.to_datetime(df_temp['effective_start_date'], errors='coerce')
    
    # Filtra i progetti completati
    df_completati = df_temp[df_temp['stato_progetto'] == 'Completato']
    
    # Crea un dataframe con i clienti e la prima data di progetto completato
    first_projects = df_completati.groupby('cliente')['effective_start_date'].min().reset_index()
    first_projects.rename(columns={'effective_start_date': 'first_project_date'}, inplace=True)
    
    # Unisci con il dataframe originale
    df_completati = df_completati.merge(first_projects, on='cliente', how='left')
    
    # Calcola il numero di clienti che hanno completato almeno un progetto nell'intervallo
    df_interval = df_completati[
        (df_completati['first_project_date'] >= pd.Timestamp(start_date)) &
        (df_completati['first_project_date'] <= pd.Timestamp(end_date))
    ]
    
    total_new_clients = df_interval['cliente'].nunique()
    
    # Calcola la retention per ogni mese
    df_completati['year_month'] = df_completati['effective_start_date'].dt.to_period('M')
    retention = df_completati.groupby(['year_month', 'cliente']).size().reset_index(name='count')
    retention['retained'] = 1
    retention_summary = retention.groupby('year_month')['retained'].sum().reset_index(name='retained_clients')
    
    retention_summary['total_new_clients'] = total_new_clients
    retention_summary['retention_rate'] = (retention_summary['retained_clients'] / retention_summary['total_new_clients']) * 100
    retention_summary = retention_summary.sort_values('year_month')
    
    return retention_summary

####################################
# CONFIG E LAYOUT
####################################
# Lista degli stati progetto con "In corso" correttamente capitalizzato
STATI_PROGETTO = ["Completato", "In corso", "Bloccato"]

# Carichiamo i riferimenti
settori_db = carica_settori_db()
project_managers_db = carica_project_managers_db()
recruiters_db = carica_recruiters_db()
clienti_db = carica_clienti_db()

settori_dict = {row['id']: row['nome'] for row in settori_db}
settori_dict_reverse = {v: k for k, v in settori_dict.items()}

project_managers_dict = {row['id']: row['nome'] for row in project_managers_db}
project_managers_dict_reverse = {v: k for k, v in project_managers_dict.items()}

recruiters_dict = {row['id']: row['nome'] for row in recruiters_db}
recruiters_dict_reverse = {v: k for k, v in recruiters_dict.items()}

if 'progetto_selezionato' not in st.session_state:
    st.session_state.progetto_selezionato = None

if 'show_confirm_delete' not in st.session_state:
    st.session_state.show_confirm_delete = False

st.title("Gestione Clienti")

# Creiamo le Tabs per differenziare le sezioni
tab1, tab2, tab3 = st.tabs(["Gestione Progetti", "Gestione Progetti Continuativi", "Retention"])

####################################
# TAB 1: Gestione Progetti (Tutti i Progetti)
####################################
with tab1:
    st.header("Cerca Progetto")

    with st.form("form_cerca_progetto"):
        id_progetto_str = st.text_input("ID Progetto (lascia vuoto se non vuoi specificare)")
        nome_cliente = st.text_input("Nome Cliente")
        submit_cerca = st.form_submit_button("Cerca")

    if submit_cerca:
        if not id_progetto_str and not nome_cliente:
            st.error("Inserisci almeno l'ID o il nome del cliente per la ricerca.")
        else:
            id_progetto = int(id_progetto_str) if id_progetto_str.isdigit() else None
            risultati = cerca_progetti(id_progetto=id_progetto, nome_cliente=nome_cliente.strip() or None, include_continuativi=True)
            if not risultati:
                st.info("Nessun progetto trovato con i criteri inseriti.")
            else:
                df_risultati = pd.DataFrame(risultati)

                # Mappa ID -> nomi
                df_risultati['settore'] = df_risultati['settore_id'].map(settori_dict)
                df_risultati['project_manager'] = df_risultati['project_manager_id'].map(project_managers_dict)
                df_risultati['sales_recruiter'] = df_risultati['sales_recruiter_id'].map(recruiters_dict)

                # Format date
                for col in ['data_inizio', 'data_fine', 'recensione_data', 'start_date', 'end_date']:
                    if col in df_risultati.columns:
                        df_risultati[col] = df_risultati[col].apply(format_date_display)

                df_risultati['stato_progetto'] = df_risultati['stato_progetto'].fillna("")
                df_risultati['recensione_stelle'] = df_risultati['recensione_stelle'].fillna(0).astype(int)
                df_risultati['tempo_previsto'] = df_risultati['tempo_previsto'].fillna(0).astype(int)

                st.write("**Dati recuperati:**")
                st.dataframe(df_risultati)

                st.header("Aggiorna Progetto Selezionato")
                progetto_scelto = st.selectbox(
                    "Seleziona ID Progetto da Aggiornare",
                    options=df_risultati['id'].tolist()
                )
                st.session_state.progetto_selezionato = progetto_scelto

    st.header("Aggiorna / Elimina Progetto Selezionato")
    if st.session_state.progetto_selezionato:
        row_list = cerca_progetti(id_progetto=st.session_state.progetto_selezionato, include_continuativi=True)
        if not row_list:
            st.error("Progetto non trovato. Forse è stato eliminato?")
            st.session_state.progetto_selezionato = None
        else:
            progetto = row_list[0]

            cliente_attuale = progetto['cliente']
            settore_attuale = settori_dict.get(progetto['settore_id'], "Sconosciuto")
            pm_attuale = project_managers_dict.get(progetto['project_manager_id'], "Sconosciuto")
            rec_attuale = recruiters_dict.get(progetto['sales_recruiter_id'], "Sconosciuto")
            stato_attuale = progetto['stato_progetto'] if progetto['stato_progetto'] else STATI_PROGETTO[0]

            # Correggi la capitalizzazione se necessario
            if stato_attuale.lower() == "in corso":
                stato_attuale = "In corso"

            # Preleva le date esistenti
            data_inizio_existing = progetto['data_inizio']
            data_inizio_formatted = format_date_display(data_inizio_existing) if data_inizio_existing else ""

            data_fine_existing = progetto['data_fine']
            data_fine_formatted = format_date_display(data_fine_existing) if data_fine_existing else ""

            start_date_existing = progetto['start_date']
            start_date_formatted = format_date_display(start_date_existing) if start_date_existing else ""

            end_date_existing = progetto['end_date']
            end_date_formatted = format_date_display(end_date_existing) if end_date_existing else ""

            number_recruiters_existing = progetto['number_recruiters'] if progetto['number_recruiters'] else 0

            # Ripristinare recensione_stelle, recensione_data e tempo_previsto
            recensione_stelle_existing = progetto['recensione_stelle'] if progetto['recensione_stelle'] else 0
            recensione_data_existing = progetto['recensione_data']
            tempo_previsto_existing = progetto['tempo_previsto'] if progetto['tempo_previsto'] else 0

            with st.form("form_aggiorna_progetto"):
                st.subheader("Aggiorna Progetto")

                # Nome Cliente
                cliente_agg = st.text_input("Nome Cliente", value=cliente_attuale)

                # Settore Cliente
                settori_nomi = [s['nome'] for s in settori_db]
                settore_scelto = st.selectbox(
                    "Settore Cliente",
                    options=settori_nomi,
                    index=settori_nomi.index(settore_attuale) if settore_attuale in settori_nomi else 0
                )
                settore_id_agg = settori_dict_reverse.get(settore_scelto, None)

                # Project Manager
                pm_nomi = [p['nome'] for p in project_managers_db]
                pm_sel = st.selectbox(
                    "Project Manager",
                    options=pm_nomi,
                    index=pm_nomi.index(pm_attuale) if pm_attuale in pm_nomi else 0
                )
                pm_id_agg = project_managers_dict_reverse.get(pm_sel, None)

                # Sales Recruiter
                rec_nomi = [r['nome'] for r in recruiters_db]
                rec_sel = st.selectbox(
                    "Sales Recruiter",
                    options=rec_nomi,
                    index=rec_nomi.index(rec_attuale) if rec_attuale in rec_nomi else 0
                )
                rec_id_agg = recruiters_dict_reverse.get(rec_sel, None)

                # Stato Progetto
                stato_agg = st.selectbox(
                    "Stato Progetto",
                    [""] + STATI_PROGETTO,
                    index=STATI_PROGETTO.index(stato_attuale) + 1 if stato_attuale in STATI_PROGETTO else 0
                )
                if stato_agg == "":
                    stato_agg = None

                st.write("**Lascia vuoto per cancellare la data.**")

                # Data Inizio
                data_inizio_agg = st.text_input("Data Inizio (GG/MM/AAAA)", value=data_inizio_formatted)

                # Data Fine
                data_fine_agg = st.text_input("Data Fine (GG/MM/AAAA)", value=data_fine_formatted)

                # Data Inizio Continuativo
                data_inizio_continuativo = st.text_input("Data Inizio Continuativo (GG/MM/AAAA)", value=start_date_formatted)

                # Data Fine Continuativo
                data_fine_continuativo = st.text_input("Data Fine Continuativo (GG/MM/AAAA)", value=end_date_formatted)

                # Numero di Venditori da Inserire
                numero_venditori = st.number_input("Numero di Venditori da Inserire", min_value=0, value=int(number_recruiters_existing))

                # Recensione (Stelle)
                rec_stelle_agg = st.selectbox("Recensione (Stelle)", [0,1,2,3,4,5], index=int(recensione_stelle_existing))

                # Data Recensione
                if rec_stelle_agg > 0:
                    if recensione_data_existing:
                        rec_data_val = parse_date(recensione_data_existing)
                        if not rec_data_val:
                            rec_data_val = datetime.today().date()
                    else:
                        rec_data_val = datetime.today().date()
                    rec_data_input = st.date_input("Data Recensione", value=rec_data_val)
                else:
                    rec_data_input = None

                # Tempo Previsto
                tempo_previsto_agg = st.number_input("Tempo Previsto (giorni)", value=int(tempo_previsto_existing), min_value=0)

                # Pulsanti
                submit_update = st.form_submit_button("Aggiorna Progetto")
                submit_delete = st.form_submit_button("Elimina Progetto")

                if submit_update:
                    # Validazione delle date
                    data_inizio_parsed = None
                    data_fine_parsed = None
                    start_date_parsed = None
                    end_date_parsed = None

                    if data_inizio_agg.strip():
                        data_inizio_parsed = parse_date(data_inizio_agg.strip())
                        if not data_inizio_parsed:
                            st.error("Data Inizio non valida (GG/MM/AAAA).")
                            st.stop()

                    if data_fine_agg.strip():
                        data_fine_parsed = parse_date(data_fine_agg.strip())
                        if not data_fine_parsed:
                            st.error("Data Fine non valida (GG/MM/AAAA).")
                            st.stop()

                    if data_inizio_parsed and data_fine_parsed:
                        if data_fine_parsed < data_inizio_parsed:
                            st.error("Data Fine non può essere precedente a Data Inizio.")
                            st.stop()

                    if data_inizio_continuativo.strip():
                        start_date_parsed = parse_date(data_inizio_continuativo.strip())
                        if not start_date_parsed:
                            st.error("Data Inizio Continuativo non valida (GG/MM/AAAA).")
                            st.stop()

                    if data_fine_continuativo.strip():
                        end_date_parsed = parse_date(data_fine_continuativo.strip())
                        if not end_date_parsed:
                            st.error("Data Fine Continuativo non valida (GG/MM/AAAA).")
                            st.stop()

                    # Validazione della recensione
                    if rec_stelle_agg > 0 and not rec_data_input:
                        st.error("Se hai inserito stelle > 0, devi specificare la data recensione.")
                        st.stop()

                    # Validazione dei campi selezionati
                    if settore_id_agg is None:
                        st.error(f"Settore '{settore_scelto}' non esiste nei dizionari.")
                        st.stop()
                    if pm_id_agg is None:
                        st.error(f"Project Manager '{pm_sel}' non esiste nei dizionari.")
                        st.stop()
                    if rec_id_agg is None:
                        st.error(f"Sales Recruiter '{rec_sel}' non esiste nei dizionari.")
                        st.stop()

                    # Aggiornamento del progetto
                    aggiorna_progetto(
                        id_progetto=st.session_state.progetto_selezionato,
                        cliente=cliente_agg.strip(),
                        settore_id=settore_id_agg,
                        project_manager_id=pm_id_agg,
                        sales_recruiter_id=rec_id_agg,
                        stato_progetto=stato_agg,
                        data_inizio=data_inizio_parsed,
                        data_fine=data_fine_parsed,
                        start_date=start_date_parsed,
                        end_date=end_date_parsed,
                        number_recruiters=numero_venditori,
                        recensione_stelle=rec_stelle_agg,
                        recensione_data=rec_data_input,
                        tempo_previsto=tempo_previsto_agg
                    )
                    st.success(f"Progetto ID {st.session_state.progetto_selezionato} aggiornato con successo!")
                    st.session_state.progetto_selezionato = None

                if submit_delete:
                    st.session_state.show_confirm_delete = True

    # Conferma eliminazione
    if st.session_state.show_confirm_delete and st.session_state.progetto_selezionato:
        st.warning("Sei sicuro di voler eliminare questo progetto? Questa azione è irreversibile.")
        conferma_delete = st.button("Conferma Eliminazione")
        if conferma_delete:
            cancella_progetto(st.session_state.progetto_selezionato)
            st.success(f"Progetto ID {st.session_state.progetto_selezionato} eliminato con successo!")
            st.session_state.progetto_selezionato = None
            st.session_state.show_confirm_delete = False

    st.header("Tutti i Clienti Gestiti")

    if st.button("Mostra Tutti i Clienti"):
        df_tutti_clienti = carica_dati_completo(include_continuativi=True)
        if df_tutti_clienti.empty:
            st.info("Nessun progetto presente nel DB.")
        else:
            df_tutti_clienti['settore'] = df_tutti_clienti['settore_id'].map(settori_dict).fillna("Sconosciuto")
            df_tutti_clienti['project_manager'] = df_tutti_clienti['project_manager_id'].map(project_managers_dict).fillna("Sconosciuto")
            df_tutti_clienti['sales_recruiter'] = df_tutti_clienti['sales_recruiter_id'].map(recruiters_dict).fillna("Sconosciuto")

            # Format date
            for col in ['data_inizio', 'data_fine', 'recensione_data', 'start_date', 'end_date']:
                if col in df_tutti_clienti.columns:
                    df_tutti_clienti[col] = df_tutti_clienti[col].apply(format_date_display)

            df_tutti_clienti['stato_progetto'] = df_tutti_clienti['stato_progetto'].fillna("")
            df_tutti_clienti['recensione_stelle'] = df_tutti_clienti['recensione_stelle'].fillna(0).astype(int)
            df_tutti_clienti['tempo_previsto'] = df_tutti_clienti['tempo_previsto'].fillna(0).astype(int)

            st.write("**Tutti i Clienti Gestiti:**")
            st.dataframe(df_tutti_clienti)

            st.download_button(
                label="Scarica Tutti i Clienti in CSV",
                data=df_tutti_clienti.to_csv(index=False).encode('utf-8'),
                file_name="tutti_clienti.csv",
                mime="text/csv"
            )

####################################
# TAB 2: Gestione Progetti Continuativi
####################################
with tab2:
    st.header("Gestione Progetti Continuativi")

    st.subheader("Inserisci Nuovo Progetto Continuativo")
    with st.form("form_inserisci_progetto_continuativo"):
        # Nome Cliente: selezionato dalla lista esistente
        clienti_db = carica_clienti_db()
        if clienti_db:
            client_names = [c['cliente'] for c in clienti_db]
            cliente_sel = st.selectbox("Nome Cliente", options=client_names)
        else:
            st.error("Nessun cliente disponibile. Aggiungi un cliente prima di inserire un progetto continuativo.")
            st.stop()

        # Ottieni settore_id basato sul cliente selezionato
        settore_id = None
        for c in clienti_db:
            if c['cliente'] == cliente_sel:
                settore_id = c['settore_id']  # Utilizza direttamente settore_id
                break

        # Verifica che settore_id sia stato trovato
        if settore_id is None:
            st.error("Errore: settore_id non trovato per il cliente selezionato.")
            st.stop()

        # Project Manager
        pm_nomi = [p['nome'] for p in project_managers_db]
        pm_sel = st.selectbox("Project Manager", pm_nomi)
        pm_id = project_managers_dict_reverse.get(pm_sel, None)

        # Recruiter
        rec_nomi = [r['nome'] for r in recruiters_db]
        rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
        rec_id = recruiters_dict_reverse.get(rec_sel, None)

        # Stato Progetto
        stato_progetto = st.selectbox("Stato Progetto", [""] + STATI_PROGETTO, index=0)
        if stato_progetto == "":
            stato_progetto = None

        # Data Inizio Continuativo (start_date)
        start_date_continuativo = st.date_input("Data Inizio Continuativo", value=datetime.today().date())

        # Data Fine Continuativo opzionale
        data_fine_continuativo = st.text_input("Data Fine Continuativo (GG/MM/AAAA, opzionale)", value="")
        if data_fine_continuativo.strip():
            data_fine_parsed = parse_date(data_fine_continuativo.strip())
            if data_fine_parsed is None:
                st.error("Data Fine Continuativo non valida (GG/MM/AAAA).")
                st.stop()
        else:
            data_fine_parsed = None

        # Numero di Venditori da Inserire
        numero_venditori = st.number_input("Numero di Venditori da Inserire", min_value=1, value=1)

        # Rimosso Recensione (Stelle) e Data Recensione

        # Pulsante di invio
        submit_continuative = st.form_submit_button("Inserisci Progetto Continuativo")

        if submit_continuative:
            if not cliente_sel.strip():
                st.error("Il campo 'Nome Cliente' è obbligatorio!")
                st.stop()
            if not pm_id:
                st.error("Project Manager selezionato non valido.")
                st.stop()
            if not rec_id:
                st.error("Sales Recruiter selezionato non valido.")
                st.stop()

            # Formatta 'stato_progetto' correttamente
            if stato_progetto:
                stato_progetto = stato_progetto.strip()

            inserisci_progetto_continuativo(
                cliente=cliente_sel.strip(),
                settore_id=settore_id,
                project_manager_id=pm_id,
                sales_recruiter_id=rec_id,
                stato_progetto=stato_progetto,
                start_date=start_date_continuativo,
                end_date=data_fine_parsed,
                number_recruiters=numero_venditori
            )
            st.session_state.progetto_selezionato = None  # Reset dello stato di selezione

    st.write("---")
    st.subheader("Visualizza Progetti Continuativi Esistenti")
    if st.button("Mostra Progetti Continuativi"):
        progetti_continuativi = carica_dati_completo(include_continuativi=True)
        progetti_continuativi = progetti_continuativi[progetti_continuativi['is_continuative'] == 1]
        if progetti_continuativi.empty:
            st.info("Nessun progetto continuativo presente nel DB.")
        else:
            df_continuativi = progetti_continuativi.copy()
            df_continuativi['settore'] = df_continuativi['settore_id'].map(settori_dict).fillna("Sconosciuto")
            df_continuativi['project_manager'] = df_continuativi['project_manager_id'].map(project_managers_dict).fillna("Sconosciuto")
            df_continuativi['sales_recruiter'] = df_continuativi['sales_recruiter_id'].map(recruiters_dict).fillna("Sconosciuto")

            # Format date
            for col in ['data_inizio', 'data_fine', 'recensione_data', 'start_date', 'end_date']:
                if col in df_continuativi.columns:
                    df_continuativi[col] = df_continuativi[col].apply(format_date_display)

            df_continuativi['stato_progetto'] = df_continuativi['stato_progetto'].fillna("")
            df_continuativi['recensione_stelle'] = df_continuativi['recensione_stelle'].fillna(0).astype(int)
            df_continuativi['tempo_previsto'] = df_continuativi['tempo_previsto'].fillna(0).astype(int)
            df_continuativi['number_recruiters'] = df_continuativi['number_recruiters'].fillna(0).astype(int)

            # Rimuovi eventuali duplicati nella lista di stati_progetto
            df_continuativi['stato_progetto'] = df_continuativi['stato_progetto'].apply(lambda x: "In corso" if x.lower() == "in corso" else x.title())

            st.write("**Progetti Continuativi Esistenti:**")
            st.dataframe(df_continuativi[['id', 'cliente', 'settore', 'project_manager', 'sales_recruiter', 'stato_progetto', 'data_inizio', 'data_fine', 'start_date', 'end_date', 'number_recruiters', 'recensione_stelle', 'tempo_previsto']])

            st.download_button(
                label="Scarica Progetti Continuativi in CSV",
                data=df_continuativi.to_csv(index=False).encode('utf-8'),
                file_name="progetti_continuativi.csv",
                mime="text/csv"
            )

####################################
# TAB 3: Retention
####################################
with tab3:
    st.header("Gestione Candidati")

    st.subheader("Aggiungi Candidato a un Progetto")
    with st.form("form_inserisci_candidato"):
        # Seleziona Progetto
        progetti = carica_dati_completo(include_continuativi=False)
        progetti = progetti[progetti['is_continuative'] == 0]  # Escludi progetti continuativi
        if progetti.empty:
            st.error("Nessun progetto disponibile. Inserisci un progetto prima di aggiungere candidati.")
            st.stop()
        else:
            progetti_nomi = progetti['cliente'].tolist()
            progetto_selezionato_nome = st.selectbox("Seleziona Progetto", options=progetti_nomi)
            # Ottieni il progetto_id e recruiter_id basato sul nome selezionato
            progetto_selezionato = progetti[progetti['cliente'] == progetto_selezionato_nome].iloc[0]
            progetto_id = progetto_selezionato['id']
            recruiter_id = progetto_selezionato['sales_recruiter_id']

        # Visualizza il recruiter associato
        recruiter_nome = recruiters_dict.get(recruiter_id, "Sconosciuto")
        st.write(f"**Recruiter Associato:** {recruiter_nome}")

        # Inserisci Nome e Cognome Candidato
        candidato_nome = st.text_input("Nome e Cognome Candidato")

        # Inserisci Data Inserimento Candidato
        data_inserimento_candidato = st.date_input("Data Inserimento Candidato", value=datetime.today().date())

        # Inserisci Data Dimissioni (opzionale)
        data_dimissioni_candidato = st.date_input("Data Dimissioni Candidato (se applicabile)", value=None, key="dimissioni_candidato")
        # Permetti di lasciare vuoto
        if not st.session_state.get("dimissioni_candidato"):
            data_dimissioni_candidato = None
        else:
            data_dimissioni_candidato = st.session_state.dimissioni_candidato

        # Pulsante di invio
        submit_candidato = st.form_submit_button("Aggiungi Candidato")

        if submit_candidato:
            if not candidato_nome.strip():
                st.error("Il campo 'Nome e Cognome Candidato' è obbligatorio.")
            else:
                inserisci_candidato(
                    progetto_id=progetto_id,
                    recruiter_id=recruiter_id,
                    candidato_nome=candidato_nome.strip(),
                    data_inserimento=data_inserimento_candidato,
                    data_dimissioni=data_dimissioni_candidato
                )

    st.write("---")
    st.subheader("Visualizza Candidati di un Progetto")
    with st.form("form_visualizza_candidati"):
        progetto_visualizza_nome = st.selectbox("Seleziona Progetto per Visualizzare Candidati", options=progetti_nomi)
        submit_visualizza = st.form_submit_button("Visualizza Candidati")

    if submit_visualizza:
        progetto_visualizza = progetti[progetti['cliente'] == progetto_visualizza_nome].iloc[0]
        progetto_visualizza_id = progetto_visualizza['id']
        candidati = carica_candidati_progetto(progetto_visualizza_id)
        if not candidati:
            st.info("Nessun candidato associato a questo progetto.")
        else:
            df_candidati = pd.DataFrame(candidati)
            # Format date
            df_candidati['data_inserimento'] = df_candidati['data_inserimento'].apply(format_date_display)
            df_candidati['data_dimissioni'] = df_candidati['data_dimissioni'].apply(format_date_display)
            df_candidati['data_placement'] = df_candidati['data_placement'].apply(format_date_display)
            st.write(f"**Candidati per il Progetto: {progetto_visualizza_nome}**")
            st.dataframe(df_candidati[['id', 'candidato_nome', 'data_inserimento', 'data_dimissioni', 'data_placement']])

    # Rimuovere l'Analisi della Retention dei Clienti
    # Tutto ciò che era precedentemente nella scheda Retention relativo all'analisi viene rimosso.

####################################
# CODICE PER GESTIONE CLIENTI E PROGETTI CONTINUATIVI
#######################################

# Il resto del codice rimane invariato...

# Se desideri aggiungere ulteriori funzionalità alla scheda Retention o altre schede, puoi estendere le funzioni sopra o aggiungere nuovi componenti all'interno delle rispettive schede.
