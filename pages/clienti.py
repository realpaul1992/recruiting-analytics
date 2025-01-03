# clienti.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, date
import sys
import os
import zipfile
from io import BytesIO

# Aggiungi il percorso per importare utils.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM settori ORDER BY nome ASC")
    settori = c.fetchall()
    conn.close()
    return settori

def carica_project_managers_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
    pm = c.fetchall()
    conn.close()
    return pm

def carica_recruiters_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
    rec = c.fetchall()
    conn.close()
    return rec

def carica_clienti_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT cliente, settore_id FROM progetti ORDER BY cliente ASC")
    clienti = c.fetchall()
    conn.close()
    return clienti

def cerca_progetti(id_progetto=None, nome_cliente=None):
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
            p.tempo_totale,
            p.recensione_stelle,
            p.recensione_data,
            p.tempo_previsto,
            p.is_continuative,
            p.number_recruiters,
            p.frequency,
            p.start_date,
            p.end_date
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
    recensione_stelle,
    recensione_data,
    tempo_previsto,
    is_continuative=False,
    number_recruiters=0,
    frequency=None,
    start_date=None,
    end_date=None
):
    conn = get_connection()
    c = conn.cursor()

    if data_inizio and data_fine:
        tempo_totale = (data_fine - data_inizio).days
    else:
        tempo_totale = None

    data_inizio_str = data_inizio.strftime('%Y-%m-%d') if data_inizio else None
    data_fine_str = data_fine.strftime('%Y-%m-%d') if data_fine else None
    recensione_data_str = recensione_data.strftime('%Y-%m-%d') if recensione_data else None

    # Assicurati che 'stato_progetto' sia formattato correttamente
    if stato_progetto:
        stato_progetto = stato_progetto.strip().title()

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
            tempo_totale = %s,
            recensione_stelle = %s,
            recensione_data = %s,
            tempo_previsto = %s,
            is_continuative = %s,
            number_recruiters = %s,
            frequency = %s,
            start_date = %s,
            end_date = %s
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
        tempo_totale,
        recensione_stelle,
        recensione_data_str,
        tempo_previsto,
        is_continuative,
        number_recruiters,
        frequency,
        start_date,
        end_date,
        id_progetto
    ))
    conn.commit()
    conn.close()

def cancella_progetto(id_progetto):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM progetti WHERE id = %s", (id_progetto,))
    conn.commit()
    conn.close()

def carica_dati_completo():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM progetti")
    rows = c.fetchall()
    col_names = [desc[0] for desc in c.description]
    conn.close()

    df = pd.DataFrame(rows, columns=col_names)

    # Converti 'tempo_previsto' a numerico
    if "tempo_previsto" in df.columns:
        df["tempo_previsto"] = pd.to_numeric(df["tempo_previsto"], errors="coerce")
        df["tempo_previsto"] = df["tempo_previsto"].fillna(0).astype(int)

    return df

####################################
# Funzioni per Progetti Continuativi
####################################

def inserisci_progetto_continuativo(
    cliente,
    settore_id,
    project_manager_id,
    sales_recruiter_id,
    stato_progetto,
    data_inizio,
    tempo_previsto,
    is_continuative,
    number_recruiters,
    frequency,
    start_date,
    end_date
):
    conn = get_connection()
    c = conn.cursor()

    # Valori di default
    data_fine = None
    tempo_totale = None
    recensione_stelle = None
    recensione_data = None

    # Assicurati che 'stato_progetto' sia formattato correttamente
    if stato_progetto:
        stato_progetto = stato_progetto.strip().title()

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
            tempo_previsto,
            is_continuative,
            number_recruiters,
            frequency,
            start_date,
            end_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    c.execute(query, (
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
        tempo_previsto,
        is_continuative,
        number_recruiters,
        frequency,
        start_date,
        end_date
    ))
    progetto_id = c.lastrowid  # Ottieni l'ID del progetto appena inserito
    conn.commit()
    conn.close()

    st.success("Progetto continuativo inserito con successo!")

    # Assegna automaticamente i recruiter se necessario
    if is_continuative and number_recruiters > 0:
        assegna_recruiters_a_progetto_continuativo(progetto_id, number_recruiters)

    backup_database()
    return progetto_id

def assegna_recruiters_a_progetto_continuativo(progetto_id, number_recruiters):
    """
    Assegna automaticamente i recruiter disponibili a un progetto continuativo.
    """
    conn = get_connection()
    c = conn.cursor()

    try:
        # Trova i recruiter con capacità disponibile
        c.execute("""
            SELECT r.id, r.nome, IFNULL(rc.capacity_max, 5) as capacity
            FROM recruiters r
            LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
            WHERE (rc.capacity_max IS NULL OR rc.capacity_max > 0)
            ORDER BY r.nome ASC
            LIMIT %s
        """, (number_recruiters,))
        available_recruiters = c.fetchall()

        if len(available_recruiters) < number_recruiters:
            st.warning("Non ci sono abbastanza recruiter disponibili per assegnare al progetto continuativo.")
        else:
            for rec in available_recruiters:
                rec_id = rec['id']
                # Assegna il recruiter al progetto
                c.execute("""
                    UPDATE progetti
                    SET sales_recruiter_id = %s
                    WHERE id = %s
                """, (rec_id, progetto_id))

                # Aggiorna la capacità
                c.execute("""
                    UPDATE recruiter_capacity
                    SET capacity_max = capacity_max - 1
                    WHERE recruiter_id = %s
                """, (rec_id,))

            conn.commit()
            st.success(f"{len(available_recruiters)} recruiter assegnati al progetto continuativo.")
    except pymysql.Error as e:
        conn.rollback()
        st.error(f"Errore durante l'assegnazione dei recruiter: {e}")
    finally:
        conn.close()

def carica_progetti_continuativi_db():
    """
    Carica i progetti continuativi dal database.
    """
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
            p.tempo_totale,
            p.recensione_stelle,
            p.recensione_data,
            p.tempo_previsto,
            p.is_continuative,
            p.number_recruiters,
            p.frequency,
            p.start_date,
            p.end_date
        FROM progetti p
        WHERE p.is_continuative = TRUE
    """
    c.execute(query)
    risultati = c.fetchall()
    conn.close()
    return risultati

####################################
# DEFINIZIONE DELLE FUNZIONI CRUD
####################################

# (Le funzioni CRUD per Riunioni, Referrals, Formazione e Candidati rimangono invariate)

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
    """
    Restituisce un DataFrame con recruiter e la loro capacità.
    """
    conn = get_connection()
    c = conn.cursor()
    query = '''
        SELECT r.id, r.nome AS sales_recruiter,
               IFNULL(rc.capacity_max, 5) AS capacity
        FROM recruiters r
        LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
        ORDER BY r.nome
    '''
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return pd.DataFrame(rows, columns=['id', 'sales_recruiter', 'capacity'])

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

####################################
# CONFIG E LAYOUT
#######################################

STATI_PROGETTO = ["Completato", "In corso", "Bloccato"]

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

st.title("Gestione Clienti")

# Creiamo le Tabs per differenziare le sezioni
tab1, tab2 = st.tabs(["Gestione Progetti", "Gestione Progetti Continuativi"])

####################################
# TAB 1: Gestione Progetti
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
            risultati = cerca_progetti(id_progetto=id_progetto, nome_cliente=nome_cliente.strip() or None)
            if risultati:
                columns = [
                    'id','cliente','settore_id','project_manager_id','sales_recruiter_id',
                    'stato_progetto','data_inizio','data_fine','tempo_totale',
                    'recensione_stelle','recensione_data','tempo_previsto',
                    'is_continuative','number_recruiters','frequency','start_date','end_date'
                ]
                df_risultati = pd.DataFrame(risultati, columns=columns)

                # Mappa ID -> nomi
                df_risultati['settore'] = df_risultati['settore_id'].map(settori_dict)
                df_risultati['project_manager'] = df_risultati['project_manager_id'].map(project_managers_dict)
                df_risultati['sales_recruiter'] = df_risultati['sales_recruiter_id'].map(recruiters_dict)

                # Format date
                df_risultati['data_inizio'] = df_risultati['data_inizio'].apply(format_date_display)
                df_risultati['data_fine']   = df_risultati['data_fine'].apply(format_date_display)
                df_risultati['recensione_data'] = df_risultati['recensione_data'].apply(format_date_display)
                df_risultati['start_date'] = df_risultati['start_date'].apply(format_date_display)
                df_risultati['end_date'] = df_risultati['end_date'].apply(format_date_display)

                df_risultati['stato_progetto'] = df_risultati['stato_progetto'].fillna("")
                df_risultati['recensione_stelle'] = df_risultati['recensione_stelle'].fillna(0).astype(int)
                df_risultati['tempo_previsto'] = df_risultati['tempo_previsto'].fillna(0).astype(int)
                df_risultati['number_recruiters'] = df_risultati['number_recruiters'].fillna(0).astype(int)

                st.write("**Dati recuperati:**")
                st.dataframe(df_risultati)

                st.header("Aggiorna Progetto Selezionato")
                progetto_scelto = st.selectbox(
                    "Seleziona ID Progetto da Aggiornare",
                    options=df_risultati['id'].tolist()
                )
                st.session_state.progetto_selezionato = progetto_scelto
            else:
                st.info("Nessun progetto trovato con i criteri inseriti.")

    if st.session_state.progetto_selezionato:
        row_list = cerca_progetti(id_progetto=st.session_state.progetto_selezionato)
        if not row_list:
            st.error("Progetto non trovato. Forse è stato eliminato?")
            st.session_state.progetto_selezionato = None
        else:
            progetto = row_list[0]

            st.header("Aggiorna / Elimina Progetto")

            settore_attuale = settori_dict.get(progetto['settore_id'], "Sconosciuto")
            pm_attuale = project_managers_dict.get(progetto['project_manager_id'], "Sconosciuto")
            rec_attuale = recruiters_dict.get(progetto['sales_recruiter_id'], "Sconosciuto")

            col_upd, col_del = st.columns([3,1])
            with col_upd:
                with st.form("form_aggiorna_progetto"):
                    # Nome Cliente: selezionato dalla lista esistente
                    clienti = carica_clienti_db()
                    client_names = [c['cliente'] for c in clienti]
                    cliente_sel = st.selectbox("Nome Cliente", options=client_names, index=client_names.index(progetto['cliente']) if progetto['cliente'] in client_names else 0)

                    # Ottieni settore_id basato sul cliente selezionato
                    settore_id_agg = None
                    for c in clienti:
                        if c['cliente'] == cliente_sel:
                            settore_id_agg = c['settore_id']
                            break

                    # Project Manager
                    pm_nomi = [p['nome'] for p in project_managers_db]
                    pm_sel = st.selectbox(
                        "Project Manager",
                        options=pm_nomi,
                        index=pm_nomi.index(pm_attuale) if pm_attuale in pm_nomi else 0
                    )
                    pm_id_agg = project_managers_dict_reverse.get(pm_sel, None)

                    # Recruiter
                    rec_nomi = [r['nome'] for r in recruiters_db]
                    rec_sel = st.selectbox(
                        "Sales Recruiter",
                        options=rec_nomi,
                        index=rec_nomi.index(rec_attuale) if rec_attuale in rec_nomi else 0
                    )
                    rec_id_agg = recruiters_dict_reverse.get(rec_sel, None)

                    # Stato Progetto: lasciare vuoto per permettere selezione
                    stato_attuale = progetto['stato_progetto'] if progetto['stato_progetto'] else ""
                    stato_agg = st.selectbox(
                        "Stato Progetto",
                        [""] + STATI_PROGETTO,
                        index=STATI_PROGETTO.index(stato_attuale) if stato_attuale in STATI_PROGETTO else 0
                    )
                    if stato_agg == "":
                        stato_agg = None

                    # Numero di venditori da inserire
                    numero_venditori_agg = st.number_input("Numero di Venditori da Inserire", min_value=1, value=int(progetto['number_recruiters']) if progetto['number_recruiters'] else 1)

                    # Data inizio continuativo
                    data_inizio_existing = parse_date(progetto['start_date'])
                    data_inizio_str = data_inizio_existing.strftime('%d/%m/%Y') if data_inizio_existing else ""
                    data_inizio_agg = st.text_input("Data Inizio Continuativo (GG/MM/AAAA)", value=data_inizio_str)

                    # Data fine continuativo opzionale
                    data_fine_existing = parse_date(progetto['end_date'])
                    data_fine_str = data_fine_existing.strftime('%d/%m/%Y') if data_fine_existing else ""
                    data_fine_agg = st.text_input("Data Fine Continuativo (GG/MM/AAAA, opzionale)", value=data_fine_str)

                    tempo_previsto_existing = progetto['tempo_previsto'] if progetto['tempo_previsto'] else 0
                    tempo_previsto_agg = st.number_input("Tempo Previsto (giorni)",
                                                        value=int(tempo_previsto_existing),
                                                        min_value=0)

                    # Data recensione solo se stelle > 0
                    rec_stelle_attuale = progetto['recensione_stelle'] or 0
                    rec_stelle_agg = st.selectbox("Recensione (Stelle)", [0,1,2,3,4,5], index=rec_stelle_attuale)
                    
                    if rec_stelle_agg > 0:
                        rec_data_existing = parse_date(progetto['recensione_data'])
                        if rec_data_existing:
                            rec_data_val = rec_data_existing
                        else:
                            rec_data_val = datetime.today().date()
                        rec_data_input = st.date_input("Data Recensione", value=rec_data_val)
                    else:
                        rec_data_input = None

                    sub_update = st.form_submit_button("Aggiorna Progetto")

                    if sub_update:
                        # Validazione dei campi
                        if data_inizio_agg.strip():
                            try:
                                data_inizio_parsed = datetime.strptime(data_inizio_agg.strip(), '%d/%m/%Y').date()
                            except ValueError:
                                st.error("Data inizio non valida (GG/MM/AAAA).")
                                st.stop()
                        else:
                            data_inizio_parsed = None

                        if data_fine_agg.strip():
                            try:
                                data_fine_parsed = datetime.strptime(data_fine_agg.strip(), '%d/%m/%Y').date()
                            except ValueError:
                                st.error("Data fine non valida (GG/MM/AAAA).")
                                st.stop()
                        else:
                            data_fine_parsed = None

                        if data_inizio_parsed and data_fine_parsed:
                            if data_fine_parsed < data_inizio_parsed:
                                st.error("Data fine non può essere precedente a data inizio.")
                                st.stop()

                        if rec_stelle_agg > 0 and not rec_data_input:
                            st.error("Se hai messo stelle > 0, devi specificare la data recensione.")
                            st.stop()

                        if settore_id_agg is None:
                            st.error(f"Settore associato al cliente '{cliente_sel}' non trovato.")
                            st.stop()
                        if pm_id_agg is None:
                            st.error(f"Project Manager '{pm_sel}' non esiste nei dizionari.")
                            st.stop()
                        if rec_id_agg is None:
                            st.error(f"Recruiter '{rec_sel}' non esiste nei dizionari.")
                            st.stop()

                        aggiorna_progetto(
                            id_progetto=st.session_state.progetto_selezionato,
                            cliente=cliente_sel.strip(),
                            settore_id=settore_id_agg,
                            project_manager_id=pm_id_agg,
                            sales_recruiter_id=rec_id_agg,
                            stato_progetto=stato_agg,
                            data_inizio=data_inizio_parsed,
                            data_fine=data_fine_parsed,
                            recensione_stelle=rec_stelle_agg,
                            recensione_data=rec_data_input,
                            tempo_previsto=tempo_previsto_agg,
                            is_continuative=True,
                            number_recruiters=numero_venditori_agg,
                            frequency=None,
                            start_date=data_inizio_parsed.strftime('%Y-%m-%d') if data_inizio_parsed else None,
                            end_date=data_fine_parsed.strftime('%Y-%m-%d') if data_fine_parsed else None
                        )
                        st.success(f"Progetto {st.session_state.progetto_selezionato} aggiornato con successo!")
                        st.session_state.progetto_selezionato = None  # Reset dello stato di selezione

            with col_del:
                st.write("**Attenzione:**")
                st.write("Eliminando il progetto, i dati spariranno definitivamente.")
                elimina_button = st.button("Elimina Progetto")
                if elimina_button:
                    cancella_progetto(st.session_state.progetto_selezionato)
                    st.success(f"Progetto ID {st.session_state.progetto_selezionato} eliminato con successo!")
                    st.session_state.progetto_selezionato = None  # Reset dello stato di selezione

    st.header("Tutti i Clienti Gestiti")

    if st.button("Mostra Tutti i Clienti"):
        df_tutti_clienti = carica_dati_completo()
        if df_tutti_clienti.empty:
            st.info("Nessun progetto presente nel DB.")
        else:
            df_tutti_clienti['settore'] = df_tutti_clienti['settore_id'].map(settori_dict).fillna("Sconosciuto")
            df_tutti_clienti['project_manager'] = df_tutti_clienti['project_manager_id'].map(project_managers_dict).fillna("Sconosciuto")
            df_tutti_clienti['sales_recruiter'] = df_tutti_clienti['sales_recruiter_id'].map(recruiters_dict).fillna("Sconosciuto")

            df_tutti_clienti['data_inizio'] = df_tutti_clienti['data_inizio'].apply(format_date_display)
            df_tutti_clienti['data_fine'] = df_tutti_clienti['data_fine'].apply(format_date_display)
            df_tutti_clienti['recensione_data'] = df_tutti_clienti['recensione_data'].apply(format_date_display)
            df_tutti_clienti['start_date'] = df_tutti_clienti['start_date'].apply(format_date_display)
            df_tutti_clienti['end_date'] = df_tutti_clienti['end_date'].apply(format_date_display)

            df_tutti_clienti['stato_progetto'] = df_tutti_clienti['stato_progetto'].fillna("")
            df_tutti_clienti['recensione_stelle'] = df_tutti_clienti['recensione_stelle'].fillna(0).astype(int)
            df_tutti_clienti['tempo_previsto'] = df_tutti_clienti['tempo_previsto'].fillna(0).astype(int)
            df_tutti_clienti['number_recruiters'] = df_tutti_clienti['number_recruiters'].fillna(0).astype(int)

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

    # Form per inserire un nuovo progetto continuativo
    with st.form("form_inserisci_progetto_continuativo"):
        st.subheader("Inserisci Nuovo Progetto Continuativo")

        # Nome Cliente: selezionato dalla lista esistente
        clienti = carica_clienti_db()
        client_names = [c['cliente'] for c in clienti]
        cliente_sel = st.selectbox("Nome Cliente", options=client_names)
        
        # Ottieni settore_id basato sul cliente selezionato
        settore_id = None
        for c in clienti:
            if c['cliente'] == cliente_sel:
                settore_id = c['settore_id']
                break

        # Project Manager
        pm_nomi = [p['nome'] for p in project_managers_db]
        pm_sel = st.selectbox("Project Manager", pm_nomi)
        pm_id = project_managers_dict_reverse.get(pm_sel, None)

        # Recruiter
        rec_nomi = [r['nome'] for r in recruiters_db]
        rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
        rec_id = recruiters_dict_reverse.get(rec_sel, None)

        # Stato Progetto: lasciare vuoto per permettere selezione
        stato_progetto = st.selectbox("Stato Progetto", [""] + STATI_PROGETTO, index=0)
        if stato_progetto == "":
            stato_progetto = None

        # Numero di venditori da inserire
        numero_venditori = st.number_input("Numero di Venditori da Inserire", min_value=1, value=1)

        # Data inizio continuativo
        data_inizio_continuativo = st.date_input("Data Inizio Continuativo", value=datetime.today().date())

        # Data fine continuativo opzionale
        data_fine_continuativo = st.text_input("Data Fine Continuativo (GG/MM/AAAA, opzionale)", value="")
        if data_fine_continuativo.strip():
            try:
                data_fine_parsed = datetime.strptime(data_fine_continuativo.strip(), '%d/%m/%Y').date()
            except ValueError:
                st.error("Data fine non valida (GG/MM/AAAA).")
                st.stop()
        else:
            data_fine_parsed = None

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

            # Assicurati che 'stato_progetto' sia formattato correttamente
            if stato_progetto:
                stato_progetto = stato_progetto.strip().title()

            inserisci_progetto_continuativo(
                cliente=cliente_sel.strip(),
                settore_id=settore_id,
                project_manager_id=pm_id,
                sales_recruiter_id=rec_id,
                stato_progetto=stato_progetto,
                data_inizio=data_inizio_continuativo.strftime('%Y-%m-%d') if data_inizio_continuativo else None,
                tempo_previsto=0,  # o un valore di default appropriato
                is_continuative=True,
                number_recruiters=numero_venditori,
                frequency=None,
                start_date=data_inizio_continuativo.strftime('%Y-%m-%d') if data_inizio_continuativo else None,
                end_date=data_fine_parsed.strftime('%Y-%m-%d') if data_fine_parsed else None
            )
            st.success("Progetto continuativo inserito con successo!")
            st.session_state.progetto_selezionato = None  # Reset dello stato di selezione

    st.write("---")
    st.subheader("Visualizza Progetti Continuativi Esistenti")
    progetti_continuativi = carica_progetti_continuativi_db()
    if progetti_continuativi:
        df_continuativi = pd.DataFrame(progetti_continuativi)
        df_continuativi['settore'] = df_continuativi['settore_id'].map(settori_dict)
        df_continuativi['project_manager'] = df_continuativi['project_manager_id'].map(project_managers_dict)
        df_continuativi['sales_recruiter'] = df_continuativi['sales_recruiter_id'].map(recruiters_dict)

        # Format date con funzione aggiornata
        df_continuativi['data_inizio'] = df_continuativi['data_inizio'].apply(format_date_display)
        df_continuativi['data_fine']   = df_continuativi['data_fine'].apply(format_date_display)
        df_continuativi['recensione_data'] = df_continuativi['recensione_data'].apply(format_date_display)
        df_continuativi['start_date'] = df_continuativi['start_date'].apply(format_date_display)
        df_continuativi['end_date'] = df_continuativi['end_date'].apply(format_date_display)

        df_continuativi['stato_progetto'] = df_continuativi['stato_progetto'].fillna("")
        df_continuativi['recensione_stelle'] = df_continuativi['recensione_stelle'].fillna(0).astype(int)
        df_continuativi['tempo_previsto'] = df_continuativi['tempo_previsto'].fillna(0).astype(int)
        df_continuativi['number_recruiters'] = df_continuativi['number_recruiters'].fillna(0).astype(int)

        st.dataframe(df_continuativi[['id', 'cliente', 'settore', 'project_manager', 'sales_recruiter', 'stato_progetto', 'data_inizio', 'tempo_previsto', 'is_continuative', 'number_recruiters', 'start_date', 'end_date']])

        st.download_button(
            label="Scarica Progetti Continuativi in CSV",
            data=df_continuativi.to_csv(index=False).encode('utf-8'),
            file_name="progetti_continuativi.csv",
            mime="text/csv"
        )
    else:
        st.info("Nessun progetto continuativo presente nel DB.")

####################################
# OPZIONI AGGIUNTIVE (GESTIONE RECRUITERS, PROJECT MANAGERS, SETTORI)
#######################################

# Scheda aggiuntiva per la gestione dei Recruiters
tab3 = st.sidebar.selectbox("Seleziona Sezione", ["Gestione Progetti", "Gestione Progetti Continuativi", "Gestione Recruiters"])

if tab3 == "Gestione Recruiters":
    st.header("Gestione Recruiters")

    # Mostra la lista dei recruiter
    df_recruiters = carica_recruiters_capacity()
    st.subheader("Lista dei Recruiters e le loro Capacità")
    st.dataframe(df_recruiters)

    # Form per aggiornare la capacità di un recruiter
    st.subheader("Aggiorna Capacità Recruiter")
    with st.form("form_aggiorna_capacity"):
        recruiter_sel = st.selectbox("Seleziona Recruiter", options=df_recruiters['sales_recruiter'].tolist())
        recruiter_id = df_recruiters[df_recruiters['sales_recruiter'] == recruiter_sel]['id'].values[0]
        nuova_capacity = st.number_input("Nuova Capacità", min_value=0, value=int(df_recruiters[df_recruiters['sales_recruiter'] == recruiter_sel]['capacity'].values[0]))
        submit_capacity = st.form_submit_button("Aggiorna Capacità")

        if submit_capacity:
            aggiorna_capacity_recruiter(recruiter_id, nuova_capacity)

    # Visualizza le capacità aggiornate
    st.subheader("Capacità Aggiornate dei Recruiters")
    df_recruiters_updated = carica_recruiters_capacity()
    st.dataframe(df_recruiters_updated)

    # Opzione per aggiungere un nuovo recruiter
    st.subheader("Aggiungi Nuovo Recruiter")
    with st.form("form_aggiungi_recruiter"):
        nuovo_recruiter = st.text_input("Nome Recruiter")
        submit_nuovo_recruiter = st.form_submit_button("Aggiungi Recruiter")

        if submit_nuovo_recruiter:
            if nuovo_recruiter.strip():
                conn = get_connection()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO recruiters (nome) VALUES (%s)", (nuovo_recruiter.strip(),))
                    # Imposta la capacità iniziale a 5
                    rec_id = c.lastrowid
                    c.execute("INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (%s, 5)", (rec_id,))
                    conn.commit()
                    st.success(f"Recruiter '{nuovo_recruiter}' aggiunto con capacità iniziale di 5.")
                except pymysql.IntegrityError:
                    st.error("Il recruiter esiste già.")
                finally:
                    conn.close()
                backup_database()
            else:
                st.error("Il nome del recruiter non può essere vuoto.")

    # Opzione per eliminare un recruiter
    st.subheader("Elimina Recruiter")
    with st.form("form_elimina_recruiter"):
        recruiter_elim = st.selectbox("Seleziona Recruiter da Eliminare", options=df_recruiters['sales_recruiter'].tolist())
        submit_elimina_recruiter = st.form_submit_button("Elimina Recruiter")

        if submit_elimina_recruiter:
            recruiter_id = df_recruiters[df_recruiters['sales_recruiter'] == recruiter_elim]['id'].values[0]
            conn = get_connection()
            c = conn.cursor()
            try:
                # Verifica se il recruiter è assegnato a qualche progetto
                c.execute("SELECT COUNT(*) as count FROM progetti WHERE sales_recruiter_id = %s", (recruiter_id,))
                count = c.fetchone()['count']
                if count > 0:
                    st.error("Impossibile eliminare il recruiter poiché è assegnato a uno o più progetti.")
                else:
                    c.execute("DELETE FROM recruiters WHERE id = %s", (recruiter_id,))
                    c.execute("DELETE FROM recruiter_capacity WHERE recruiter_id = %s", (recruiter_id,))
                    conn.commit()
                    st.success(f"Recruiter '{recruiter_elim}' eliminato con successo.")
            except pymysql.Error as e:
                st.error(f"Errore durante l'eliminazione del recruiter: {e}")
            finally:
                conn.close()
            backup_database()
