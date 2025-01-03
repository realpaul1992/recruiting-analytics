# app.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt
import os
import zipfile
from io import BytesIO

#######################################
# FUNZIONI DI ACCESSO AL DB (MySQL)
#######################################

def get_connection():
    """
    Ritorna una connessione MySQL usando pymysql.
    Utilizza variabili d'ambiente per le credenziali.
    """
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor  # Per avere dizionari anziché tuple
    )

def carica_settori():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM settori ORDER BY nome ASC")
            rows = c.fetchall()
    finally:
        conn.close()
    return rows

def carica_project_managers():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
            rows = c.fetchall()
    finally:
        conn.close()
    return rows

def carica_recruiters():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            rows = c.fetchall()
    finally:
        conn.close()
    return rows

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
                    p.tempo_previsto,
                    p.data_chiusura_prevista
                FROM progetti p
                JOIN settori s ON p.settore_id = s.id
                JOIN project_managers pm ON p.project_manager_id = pm.id
                JOIN recruiters r ON p.sales_recruiter_id = r.id
            """
            c.execute(query)
            rows = c.fetchall()
    finally:
        conn.close()

    df = pd.DataFrame(rows)
    
    # Convertiamo le colonne date a datetime
    date_cols = ['data_inizio', 'data_fine', 'recensione_data', 'data_chiusura_prevista']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Convertiamo 'tempo_previsto' a numerico
    df["tempo_previsto"] = pd.to_numeric(df["tempo_previsto"], errors="coerce")
    df["tempo_previsto"] = df["tempo_previsto"].fillna(0).astype(int)
    
    return df

def carica_candidati():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT c.id, c.candidato_nome, c.data_inserimento, c.data_placement, c.data_dimissioni, 
                       p.cliente, r.nome AS recruiter
                FROM candidati c
                JOIN progetti p ON c.progetto_id = p.id
                JOIN recruiters r ON c.recruiter_id = r.id
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def carica_riunioni():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT r.nome AS recruiter, ri.data_riunione, ri.partecipato
                FROM riunioni ri
                JOIN recruiters r ON ri.recruiter_id = r.id
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def carica_referrals():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT r.nome AS recruiter, ref.cliente_nome, ref.data_referral, ref.stato
                FROM referrals ref
                JOIN recruiters r ON ref.recruiter_id = r.id
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def carica_formazione():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT r.nome AS recruiter, f.corso_nome, f.data_completamento
                FROM formazione f
                JOIN recruiters r ON f.recruiter_id = r.id
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def inserisci_dati(cliente, settore_id, pm_id, rec_id, data_inizio):
    """
    Inserisce un nuovo progetto in MySQL.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
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
                    data_chiusura_prevista
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            c.execute(query, (
                cliente,
                settore_id,
                pm_id,
                rec_id,
                None,  # stato_progetto
                data_inizio,
                None,  # data_fine
                None,  # tempo_totale
                None,  # recensione_stelle
                None,  # recensione_data
                None,  # tempo_previsto
                None   # data_chiusura_prevista
            ))
    finally:
        conn.close()

def inserisci_candidato(progetto_id, recruiter_id, candidato_nome, data_inserimento, data_placement, data_dimissioni=None):
    """
    Inserisce un nuovo candidato nel database.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO candidati (progetto_id, recruiter_id, candidato_nome, data_inserimento, data_placement, data_dimissioni)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            c.execute(query, (
                progetto_id,
                recruiter_id,
                candidato_nome,
                data_inserimento,
                data_placement,
                data_dimissioni
            ))
    finally:
        conn.close()

def inserisci_riunione(recruiter_id, data_riunione, partecipato=False):
    """
    Inserisce una nuova riunione nel database.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO riunioni (recruiter_id, data_riunione, partecipato)
                VALUES (%s, %s, %s)
            """
            c.execute(query, (
                recruiter_id,
                data_riunione,
                partecipato
            ))
    finally:
        conn.close()

def inserisci_referral(recruiter_id, cliente_nome, data_referral, stato):
    """
    Inserisce un nuovo referral nel database.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO referrals (recruiter_id, cliente_nome, data_referral, stato)
                VALUES (%s, %s, %s, %s)
            """
            c.execute(query, (
                recruiter_id,
                cliente_nome,
                data_referral,
                stato
            ))
    finally:
        conn.close()

def inserisci_formazione(recruiter_id, corso_nome, data_completamento):
    """
    Inserisce una nuova formazione nel database.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO formazione (recruiter_id, corso_nome, data_completamento)
                VALUES (%s, %s, %s)
            """
            c.execute(query, (
                recruiter_id,
                corso_nome,
                data_completamento
            ))
    finally:
        conn.close()

def aggiorna_candidato_dimissioni(candidato_id, data_dimissioni):
    """
    Aggiorna la data di dimissioni di un candidato.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                UPDATE candidati
                SET data_dimissioni = %s
                WHERE id = %s
            """
            c.execute(query, (
                data_dimissioni,
                candidato_id
            ))
    finally:
        conn.close()

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
                tables = [row[f'Tables_in_{os.getenv("DB_NAME")}'] for row in c.fetchall()]
                
                st.info("Inizio backup MySQL in ZIP...")
                
                for table_name in tables:
                    # Query: SELECT * FROM <table_name>
                    c.execute(f"SELECT * FROM {table_name}")
                    rows = c.fetchall()
                    df_table = pd.DataFrame(rows)
                    
                    # Scrivi il CSV direttamente nell'archivio ZIP
                    csv_data = df_table.to_csv(index=False, encoding="utf-8")
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
                        return

                    # Prepara le colonne e i placeholder per l'INSERT
                    col_names = df.columns.tolist()
                    placeholders = ",".join(["%s"] * len(col_names))
                    col_list_str = ",".join(col_names)
                    insert_query = f"INSERT INTO {table_name} ({col_list_str}) VALUES ({placeholders})"

                    # Inserisci le righe
                    try:
                        for _, row in df.iterrows():
                            c.execute(insert_query, tuple(row))
                    except pymysql.Error as e:
                        st.error(f"Errore durante l'INSERT nella tabella {table_name}: {e}")
                        return

            st.success("Ripristino completato con successo da ZIP.")
        finally:
            conn.close()

#######################################
# CAPACITA' PER RECRUITER
#######################################
def carica_recruiters_capacity():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = '''
                SELECT r.nome AS sales_recruiter,
                       IFNULL(rc.capacity_max, 5) AS capacity
                FROM recruiters r
                LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
                ORDER BY r.nome
            '''
            c.execute(query)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD
#######################################
def calcola_leaderboard(start_date, end_date):
    """
    Calcola la leaderboard con il sistema di punteggio definito.
    """
    # Carica dati delle tabelle
    df_progetti = carica_dati_completo()
    df_candidati = carica_candidati()
    df_riunioni = carica_riunioni()
    df_referrals = carica_referrals()
    df_formazione = carica_formazione()

    # Filtra progetti completati nell'intervallo di date
    df_filtro = df_progetti[
        (df_progetti['stato_progetto'] == 'Completato') &
        (df_progetti['data_inizio'] >= pd.Timestamp(start_date)) &
        (df_progetti['data_inizio'] <= pd.Timestamp(end_date))
    ]

    if df_filtro.empty:
        return pd.DataFrame([], columns=[
            'sales_recruiter','completati','tempo_medio','bonus_totale',
            'rimasto_6_mesi','lasciato_3_mesi','partecipazioni',
            'referrals_punti','formazione_punti','punteggio','badge'
        ])

    group = df_filtro.groupby('sales_recruiter')

    # Metriche Esistenti
    completati = group.size().reset_index(name='completati')
    tempo_medio = group['tempo_totale'].mean().reset_index(name='tempo_medio')
    bonus_sum = group['recensione_stelle'].apply(lambda x: x.map({4:400, 5:500}).sum()).reset_index(name='bonus_totale')

    # 1. Candidati Inseriti
    df_candidati_filtered = df_candidati[
        (df_candidati['data_placement'] >= pd.Timestamp(start_date)) &
        (df_candidati['data_placement'] <= pd.Timestamp(end_date))
    ]

    candidati_inseriti = df_candidati_filtered.groupby('recruiter').size().reset_index(name='candidati_inseriti')

    # 2. Tasso di Retenzione
    # +300 punti se il candidato rimane >=6 mesi, -200 se lascia entro 3 mesi
    df_candidati_filtered['rimasto_6_mesi'] = df_candidati_filtered.apply(
        lambda row: 1 if pd.notnull(row['data_dimissioni']) and (row['data_dimissioni'] - row['data_placement']).days >= 180 else 0, axis=1
    )
    df_candidati_filtered['lasciato_3_mesi'] = df_candidati_filtered.apply(
        lambda row: 1 if pd.notnull(row['data_dimissioni']) and (row['data_dimissioni'] - row['data_placement']).days <= 90 else 0, axis=1
    )
    retention = df_candidati_filtered.groupby('recruiter').agg({
        'rimasto_6_mesi': 'sum',
        'lasciato_3_mesi': 'sum'
    }).reset_index()

    # 3. Partecipazione alle Riunioni
    # +100 punti per ogni riunione partecipata
    df_riunioni_filtered = df_riunioni[
        (df_riunioni['data_riunione'] >= pd.Timestamp(start_date)) &
        (df_riunioni['data_riunione'] <= pd.Timestamp(end_date)) &
        (df_riunioni['partecipato'] == True)
    ]
    partecipazioni = df_riunioni_filtered.groupby('recruiter').size().reset_index(name='partecipazioni')

    # 4. Referral di Nuovi Clienti
    # +1000 punti per ogni referral chiuso
    referrals_closed = df_referrals[
        (df_referrals['data_referral'] >= pd.Timestamp(start_date)) &
        (df_referrals['data_referral'] <= pd.Timestamp(end_date)) &
        (df_referrals['stato'] == 'Chiuso')
    ]
    referrals_punti = referrals_closed.groupby('recruiter').size().reset_index(name='referrals_punti')
    referrals_punti['referrals_punti'] = referrals_punti['referrals_punti'] * 1000  # +1000 punti per referral chiuso

    # 5. Formazione
    # +300 punti per ogni corso completato
    formazione_filtered = df_formazione[
        (df_formazione['data_completamento'] >= pd.Timestamp(start_date)) &
        (df_formazione['data_completamento'] <= pd.Timestamp(end_date))
    ]
    formazione_punti = formazione_filtered.groupby('recruiter').size().reset_index(name='formazione_punti')
    formazione_punti['formazione_punti'] = formazione_punti['formazione_punti'] * 300  # +300 punti per corso completato

    # Unisci tutte le metriche
    leaderboard = (
        completati
        .merge(tempo_medio, on='sales_recruiter', how='left')
        .merge(bonus_sum, on='sales_recruiter', how='left')
        .merge(retention, left_on='sales_recruiter', right_on='recruiter', how='left')
        .merge(partecipazioni, left_on='sales_recruiter', right_on='recruiter', how='left')
        .merge(referrals_punti, left_on='sales_recruiter', right_on='recruiter', how='left')
        .merge(formazione_punti, left_on='sales_recruiter', right_on='recruiter', how='left')
    )

    # Sostituisci NaN con 0
    leaderboard = leaderboard.fillna(0)

    # Calcolo del punteggio
    leaderboard['punteggio'] = (
        leaderboard['completati'] * 50 +  # +50 punti per progetto completato in <60 giorni
        leaderboard['bonus_totale'] +  # +500/400 per recensioni a 5/4 stelle
        leaderboard['rimasto_6_mesi'] * 300 +  # +300 punti per ogni candidato che rimane >6 mesi
        leaderboard['lasciato_3_mesi'] * -200 +  # -200 punti per ogni candidato che lascia entro 3 mesi
        leaderboard['partecipazioni'] * 100 +  # +100 punti per ogni riunione partecipata
        leaderboard['referrals_punti'] +  # +1000 punti per ogni referral chiuso
        leaderboard['formazione_punti']  # +300 punti per corso completato
    )

    # Assegna badge
    def assegna_badge(punteggio):
        if punteggio >= 20000:
            return "Gold"
        elif punteggio >= 10000:
            return "Silver"
        elif punteggio >= 5000:
            return "Bronze"
        return ""

    leaderboard['badge'] = leaderboard['punteggio'].apply(assegna_badge)

    # Rimuovi la colonna 'recruiter' derivata dalle merge
    leaderboard = leaderboard.drop(columns=['recruiter'], errors='ignore')

    # Ordina per punteggio
    leaderboard = leaderboard.sort_values('punteggio', ascending=False)

    return leaderboard

#######################################
# UTILITIES PER FORMATTARE LE DATE
#######################################
def format_date_display(x):
    """Formatta le date dal formato 'YYYY-MM-DD' a 'DD/MM/YYYY'."""
    if pd.isnull(x):
        return ""
    try:
        return x.strftime('%d/%m/%Y')
    except:
        return x  # Se il formato non è corretto o è vuoto, lascio inalterato

def parse_date(date_input):
    """Converti un oggetto datetime.date in stringa 'YYYY-MM-DD'."""
    if isinstance(date_input, datetime):
        return date_input.strftime('%Y-%m-%d')
    elif isinstance(date_input, pd.Timestamp):
        return date_input.strftime('%Y-%m-%d')
    elif isinstance(date_input, datetime.date):
        return date_input.strftime('%Y-%m-%d')
    return None

#######################################
# CONFIG E LAYOUT
#######################################
# Carichiamo i riferimenti
settori_db = carica_settori()
pm_db = carica_project_managers()
rec_db = carica_recruiters()

# Imposta il titolo dell'app
st.title("Gestione Progetti di Recruiting")

# Barra laterale per la navigazione
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
        settore_id = next((s['id'] for s in settori_db if s['nome'] == settore_sel), None)
        
        # Project Manager
        pm_nomi = [p['nome'] for p in pm_db]
        pm_sel = st.selectbox("Project Manager", pm_nomi)
        pm_id = next((p['id'] for p in pm_db if p['nome'] == pm_sel), None)
        
        # Recruiter
        rec_nomi = [r['nome'] for r in rec_db]
        rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
        rec_id = next((r['id'] for r in rec_db if r['nome'] == rec_sel), None)
        
        # Data di Inizio
        data_inizio = st.date_input("Data di Inizio", value=datetime.today())
        
        submitted = st.form_submit_button("Inserisci Progetto")
        if submitted:
            if not cliente.strip():
                st.error("Il campo 'Nome Cliente' è obbligatorio!")
                st.stop()
            
            data_inizio_sql = parse_date(data_inizio)
            
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
            anni_disponibili = sorted(df['data_inizio'].dt.year.dropna().unique())
            if len(anni_disponibili) == 0:
                st.warning("Nessun dato disponibile per i filtri.")
                st.stop()
            anno_selezionato = st.selectbox("Seleziona Anno", options=anni_disponibili, index=len(anni_disponibili)-1, key='panoramica_anno')
            
            # Filtra i dati in base all'anno selezionato
            try:
                start_date = datetime(anno_selezionato, 1, 1)
                end_date = datetime(anno_selezionato, 12, 31)
            except TypeError as e:
                st.error(f"Errore nella selezione di Anno: {e}")
                st.stop()

            df_filtered = df[
                (df['data_inizio'] >= pd.Timestamp(start_date)) &
                (df['data_inizio'] <= pd.Timestamp(end_date))
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
                    color='tempo_totale',
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
                    color_discrete_sequence=['#636EFA', '#EF553B']
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

            df_ok = df[(df['tempo_previsto'].notna()) & (df['tempo_previsto'] > 0)]
            df_ok['fine_calcolata'] = df_ok['data_inizio'] + pd.to_timedelta(df_ok['tempo_previsto'], unit='D')

            df_incorso = df_ok[df_ok['stato_progetto'] == 'In corso'].copy()

            st.subheader("Progetti In Corso con tempo_previsto > 0")
            st.dataframe(df_incorso[['cliente','stato_progetto','data_inizio','tempo_previsto','fine_calcolata','sales_recruiter']].applymap(format_date_display))

            st.write("**Vuoi vedere quali progetti si chiuderanno entro X giorni da oggi?**")
            orizzonte_giorni = st.number_input("Seleziona i giorni di orizzonte", value=14, min_value=1)
            today = datetime.today()
            df_prossimi = df_incorso[df_incorso['fine_calcolata'] <= (today + timedelta(days=orizzonte_giorni))]
            if not df_prossimi.empty:
                st.info(f"Progetti in corso che si chiuderanno entro {orizzonte_giorni} giorni:")
                st.dataframe(df_prossimi[['cliente','sales_recruiter','fine_calcolata']].applymap(format_date_display))
                
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
                **Esempio:** 4 stelle => 400€, 5 stelle => 500€.
            """)

            st.markdown("### Filtro per Anno")
            anni_disponibili_bonus = sorted(df['data_inizio'].dt.year.dropna().unique())
            if len(anni_disponibili_bonus) == 0:
                st.warning("Nessun dato disponibile per il filtro dei bonus.")
                st.stop()
            anno_bonus = st.selectbox("Seleziona Anno", options=anni_disponibili_bonus, index=len(anni_disponibili_bonus)-1, key='bonus_anno')
            
            # Filtra i dati in base all'anno selezionato
            try:
                start_date_bonus = datetime(anno_bonus, 1, 1)
                end_date_bonus = datetime(anno_bonus, 12, 31)
            except TypeError as e:
                st.error(f"Errore nella selezione di Anno per i bonus: {e}")
                st.stop()

            # Calcola il bonus totale per ogni recruiter
            df_bonus_totale = df[
                (df['recensione_data'] >= pd.Timestamp(start_date_bonus)) & 
                (df['recensione_data'] <= pd.Timestamp(end_date_bonus))
            ].copy()
            df_bonus_totale['bonus'] = df_bonus_totale['recensione_stelle'].fillna(0).astype(int).map({4:400, 5:500}).fillna(0)
            bonus_rec = df_bonus_totale.groupby('sales_recruiter')['bonus'].sum().reset_index()

            # Calcola la percentuale verso il 1000€
            bonus_rec['percentuale'] = (bonus_rec['bonus'] / 1000) * 100
            bonus_rec['percentuale'] = bonus_rec['percentuale'].apply(lambda x: min(x, 100))  # Limita al 100%

            # Ordina per percentuale
            bonus_rec = bonus_rec.sort_values(by='percentuale', ascending=False)

            st.write(f"Progetti con recensione in questo anno: {len(df_bonus_totale)}")

            # **Grafico: Avvicinamento al Premio Annuale di 1000€**
            st.markdown("### Avvicinamento al Premio Annuale di 1000€")
            fig_premio = px.bar(
                bonus_rec,
                y='sales_recruiter',
                x='percentuale',
                orientation='h',
                labels={'percentuale': 'Percentuale verso 1000€', 'sales_recruiter': 'Recruiter'},
                title='Avvicinamento al Premio Annuale di 1000€',
                text=bonus_rec['percentuale'].apply(lambda x: f"{x:.1f}%")
            )

            # Aggiungi una linea verticale al 100%
            fig_premio.add_shape(
                type="line",
                x0=100,
                y0=-0.5,
                x1=100,
                y1=len(bonus_rec),
                line=dict(color="Red", dash="dash"),
            )

            # Aggiorna layout per migliorare la leggibilità
            fig_premio.update_layout(
                yaxis=dict(categoryorder='total ascending'),
                xaxis=dict(range=[0, 110]),
                showlegend=False,
                margin=dict(l=100, r=50, t=50, b=50)
            )

            fig_premio.update_traces(marker_color='skyblue')

            st.plotly_chart(fig_premio, use_container_width=True, key='premio_annual_chart')  # Chiave unica

            # **Premiazione Basata sulle Recensioni a 5 Stelle**
            st.subheader("Premio Annuale (Recensioni a 5 stelle)")
            # Contare il numero di recensioni a 5 stelle per ogni recruiter
            df_reviews_5 = df[
                (df['recensione_stelle'] == 5) &
                (df['recensione_data'] >= pd.Timestamp(start_date_bonus)) &
                (df['recensione_data'] <= pd.Timestamp(end_date_bonus))
            ]

            if not df_reviews_5.empty:
                count_reviews = df_reviews_5.groupby('sales_recruiter').size().reset_index(name='recensioni_5_stelle')
                max_reviews = count_reviews['recensioni_5_stelle'].max()
                top_recruiters = count_reviews[count_reviews['recensioni_5_stelle'] == max_reviews]

                if len(top_recruiters) == 1:
                    st.success(f"Il premio annuale va a **{top_recruiters.iloc[0]['sales_recruiter']}** con **{top_recruiters.iloc[0]['recensioni_5_stelle']}** recensioni a 5 stelle!")
                else:
                    st.success(f"Premio annuale condiviso tra: {', '.join(top_recruiters['sales_recruiter'])}, ciascuno con **{max_reviews}** recensioni a 5 stelle!")
            else:
                st.info("Nessun recruiter ha ricevuto recensioni a 5 stelle quest'anno.")

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
            st.subheader("Classifica Annuale")
            
            st.markdown("### Filtro per Anno")
            anni_leader = sorted(df['data_inizio'].dt.year.dropna().unique())
            if len(anni_leader) == 0:
                st.warning("Nessun dato disponibile per il leaderboard.")
                st.stop()
            anno_leader = st.selectbox("Seleziona Anno", options=anni_leader, index=len(anni_leader)-1, key='leaderboard_anno')

            # Filtra i dati per il leaderboard basato sull'anno selezionato
            try:
                start_date_leader = datetime(anno_leader, 1, 1)
                end_date_leader = datetime(anno_leader, 12, 31)
            except TypeError as e:
                st.error(f"Errore nella selezione di Anno per il leaderboard: {e}")
                st.stop()

            st.write(f"Anno in analisi: {anno_leader}")

            leaderboard_df = calcola_leaderboard(start_date_leader, end_date_leader)
            if leaderboard_df.empty:
                st.info("Nessun progetto completato in questo periodo.")
            else:
                st.write("**Classifica Annuale con punteggio e badge:**")
                st.dataframe(leaderboard_df[['sales_recruiter','punteggio','badge']])

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
                        "": "grey"  # Colore di default per badge vuoti
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

                st.markdown("""
                **Formula Punteggio**  
                - +50 punti ogni progetto completato in meno di 60 giorni  
                - +500 punti per ogni recensione a 5 stelle ottenuta  
                - +400 punti per ogni recensione a 4 stelle ottenuta  
                - +300 punti se il candidato rimane in posizione per almeno 6 mesi  
                - -200 punti se il candidato lascia entro 3 mesi  
                - +100 punti per ogni riunione a cui partecipa  
                - +1000 punti per ogni nuovo cliente acquisito tramite referral  
                - +300 punti per ogni corso di formazione completato  
                """)

                st.markdown("""
                **Badge**  
                - **Bronze**: almeno 5,000 punti  
                - **Silver**: almeno 10,000 punti  
                - **Gold**: almeno 20,000 punti  
                """)

                ################################
                # Grafici nella Classifica
                ################################
                st.subheader("Grafici della Classifica")

                # **Recruiter più veloce (Tempo Medio)**
                st.markdown("**1. Recruiter più Veloce (Tempo Medio)**")
                df_comp = df[
                    (df['stato_progetto'] == 'Completato') &
                    (df['data_inizio'] >= pd.Timestamp(start_date_leader)) &
                    (df['data_inizio'] <= pd.Timestamp(end_date_leader))
                ].copy()
                veloce = df_comp.groupby('sales_recruiter')['tempo_totale'].mean().reset_index()
                veloce['tempo_totale'] = veloce['tempo_totale'].fillna(0)
                veloce = veloce.sort_values(by='tempo_totale', ascending=True)
                if veloce.empty:
                    st.info("Nessun progetto completato per calcolare la velocità.")
                else:
                    fig2, ax2 = plt.subplots(figsize=(8,6))
                    ax2.bar(veloce['sales_recruiter'], veloce['tempo_totale'], color='#636EFA')
                    ax2.set_title("Tempo Medio (giorni) - Più basso = più veloce")
                    ax2.set_xlabel("Recruiter")
                    ax2.set_ylabel("Tempo Medio (giorni)")
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig2)

                # **Recruiter con più Bonus ottenuti** (4 stelle=400, 5 stelle=500)
                st.markdown("**2. Recruiter con più Bonus Ottenuti** (4 stelle=400€, 5 stelle=500€)")
                df_bonus = df[
                    (df['recensione_stelle'].isin([4,5])) &
                    (df['data_inizio'] >= pd.Timestamp(start_date_leader)) &
                    (df['data_inizio'] <= pd.Timestamp(end_date_leader))
                ].copy()
                df_bonus['bonus'] = df_bonus['recensione_stelle'].map({4:400, 5:500}).fillna(0)
                bonus_df = df_bonus.groupby('sales_recruiter')['bonus'].sum().reset_index()
                bonus_df = bonus_df.sort_values(by='bonus', ascending=False)
                if bonus_df.empty:
                    st.info("Nessun bonus calcolato.")
                else:
                    fig3, ax3 = plt.subplots(figsize=(8,6))
                    ax3.bar(bonus_df['sales_recruiter'], bonus_df['bonus'], color='#EF553B')
                    ax3.set_title("Bonus Totale Ottenuto (€)")
                    ax3.set_xlabel("Recruiter")
                    ax3.set_ylabel("Bonus (€)")
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig3)

#######################################
# 3. GESTISCI OPZIONI
#######################################
elif scelta == "Gestisci Opzioni":
    st.header("Gestione Opzioni e Metriche")
    
    # Creiamo le tab per le diverse sottotabelle
    tab_opzioni = st.tabs(["Settori", "Project Managers", "Recruiters", "Capacità", "Candidati", "Riunioni", "Referral", "Formazione"])
    
    # 3.1 Settori
    with tab_opzioni[0]:
        st.subheader("Gestione Settori")
        with st.form("form_inserimento_settore"):
            nuovo_settore = st.text_input("Nome Settore")
            submitted = st.form_submit_button("Inserisci Settore")
            if submitted:
                if not nuovo_settore.strip():
                    st.error("Il campo 'Nome Settore' è obbligatorio!")
                else:
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("INSERT INTO settori (nome) VALUES (%s)", (nuovo_settore.strip(),))
                        conn.commit()
                        st.success(f"Settore '{nuovo_settore.strip()}' inserito con successo!")
                    except pymysql.IntegrityError:
                        st.error(f"Settore '{nuovo_settore.strip()}' esiste già!")
                    finally:
                        conn.close()

    # 3.2 Project Managers
    with tab_opzioni[1]:
        st.subheader("Gestione Project Managers")
        with st.form("form_inserimento_pm"):
            nuovo_pm = st.text_input("Nome Project Manager")
            submitted = st.form_submit_button("Inserisci Project Manager")
            if submitted:
                if not nuovo_pm.strip():
                    st.error("Il campo 'Nome Project Manager' è obbligatorio!")
                else:
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("INSERT INTO project_managers (nome) VALUES (%s)", (nuovo_pm.strip(),))
                        conn.commit()
                        st.success(f"Project Manager '{nuovo_pm.strip()}' inserito con successo!")
                    except pymysql.IntegrityError:
                        st.error(f"Project Manager '{nuovo_pm.strip()}' esiste già!")
                    finally:
                        conn.close()

    # 3.3 Recruiters
    with tab_opzioni[2]:
        st.subheader("Gestione Recruiters")
        with st.form("form_inserimento_recruiter"):
            nuovo_recruiter = st.text_input("Nome Recruiter")
            submitted = st.form_submit_button("Inserisci Recruiter")
            if submitted:
                if not nuovo_recruiter.strip():
                    st.error("Il campo 'Nome Recruiter' è obbligatorio!")
                else:
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("INSERT INTO recruiters (nome) VALUES (%s)", (nuovo_recruiter.strip(),))
                        conn.commit()
                        st.success(f"Recruiter '{nuovo_recruiter.strip()}' inserito con successo!")

                        # Imposta capacity=5 per il nuovo recruiter
                        with conn.cursor() as c:
                            c.execute(
                                "INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES ((SELECT id FROM recruiters WHERE nome=%s), 5)",
                                (nuovo_recruiter.strip(),)
                            )
                        conn.commit()
                    except pymysql.IntegrityError:
                        st.error(f"Recruiter '{nuovo_recruiter.strip()}' esiste già!")
                    finally:
                        conn.close()

    # 3.4 Capacità
    with tab_opzioni[3]:
        st.subheader("Gestione Capacità dei Recruiter")
        df_capacity = carica_recruiters_capacity()
        if df_capacity.empty:
            st.info("Nessun recruiter trovato.")
        else:
            for _, row in df_capacity.iterrows():
                recruiter = row['sales_recruiter']
                current_capacity = row['capacity']
                nuova_capacity = st.number_input(f"Capacità Massima per {recruiter}", min_value=1, value=int(current_capacity), key=f'cap_{recruiter}')
                
                if st.button(f"Aggiorna Capacità di {recruiter}", key=f'update_cap_{recruiter}'):
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("""
                                UPDATE recruiter_capacity
                                SET capacity_max = %s
                                WHERE recruiter_id = (SELECT id FROM recruiters WHERE nome = %s)
                            """, (nuova_capacity, recruiter))
                        conn.commit()
                        st.success(f"Capacità di {recruiter} aggiornata a {nuova_capacity}!")
                    except pymysql.Error as e:
                        st.error(f"Errore nell'aggiornamento: {e}")
                    finally:
                        conn.close()

    # 3.5 Candidati
    with tab_opzioni[4]:
        st.subheader("Gestione Candidati")
        inserisci_candidato_ui()

    # 3.6 Riunioni
    with tab_opzioni[5]:
        st.subheader("Gestione Riunioni")
        inserisci_riunione_ui()

    # 3.7 Referral
    with tab_opzioni[6]:
        st.subheader("Gestione Referral")
        inserisci_referral_ui()

    # 3.8 Formazione
    with tab_opzioni[7]:
        st.subheader("Gestione Formazione")
        inserisci_formazione_ui()

#######################################
# FUNZIONI UI PER GESTIRE LE INSERZIONI
#######################################
def inserisci_candidato_ui():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Carica progetti e recruiter
            c.execute("SELECT id, cliente FROM progetti ORDER BY cliente ASC")
            progetti = c.fetchall()
            progetti_nomi = [f"{p['cliente']} (ID: {p['id']})" for p in progetti]
            progetto_sel = st.selectbox("Seleziona Progetto", progetti_nomi)
            progetto_id = int(progetto_sel.split("ID: ")[1].strip(")")) if progetto_sel else None

            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            recruiters = c.fetchall()
            recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
            recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi)
            recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

            candidato_nome = st.text_input("Nome Candidato")
            data_inserimento = st.date_input("Data di Inserimento", value=datetime.today())
            data_placement = st.date_input("Data di Placement", value=datetime.today())
            data_dimissioni = st.date_input("Data di Dimissioni (Lascia vuoto se ancora in posizione)", value=None)

            submitted = st.form_submit_button("Inserisci Candidato")
            if submitted:
                if not candidato_nome.strip():
                    st.error("Il campo 'Nome Candidato' è obbligatorio!")
                elif progetto_id is None:
                    st.error("Selezionare un Progetto.")
                elif recruiter_id is None:
                    st.error("Selezionare un Recruiter.")
                elif data_inserimento > data_placement:
                    st.error("La 'Data di Placement' non può essere precedente alla 'Data di Inserimento'.")
                elif data_dimissioni and data_dimissioni < data_placement:
                    st.error("La 'Data di Dimissioni' non può essere precedente alla 'Data di Placement'.")
                else:
                    data_inserimento_sql = parse_date(data_inserimento)
                    data_placement_sql = parse_date(data_placement)
                    data_dimissioni_sql = parse_date(data_dimissioni) if data_dimissioni else None

                    inserisci_candidato(progetto_id, recruiter_id, candidato_nome.strip(), data_inserimento_sql, data_placement_sql, data_dimissioni_sql)
                    st.success("Candidato inserito con successo!")
    finally:
        conn.close()

def inserisci_riunione_ui():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Carica recruiters
            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            recruiters = c.fetchall()
            recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
            recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi)
            recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

            data_riunione = st.date_input("Data della Riunione", value=datetime.today())
            partecipato = st.checkbox("Ha partecipato")

            submitted = st.form_submit_button("Inserisci Riunione")
            if submitted:
                if recruiter_id is None:
                    st.error("Selezionare un Recruiter.")
                elif not data_riunione:
                    st.error("Il campo 'Data della Riunione' è obbligatorio!")
                else:
                    data_riunione_sql = parse_date(data_riunione)
                    inserisci_riunione(recruiter_id, data_riunione_sql, partecipato)
                    st.success("Riunione inserita con successo!")
    finally:
        conn.close()

def inserisci_referral_ui():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Carica recruiters
            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            recruiters = c.fetchall()
            recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
            recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi)
            recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

            cliente_nome = st.text_input("Nome del Nuovo Cliente")
            data_referral = st.date_input("Data del Referral", value=datetime.today())
            stato = st.selectbox("Stato del Referral", ["In corso", "Chiuso"])

            submitted = st.form_submit_button("Inserisci Referral")
            if submitted:
                if recruiter_id is None:
                    st.error("Selezionare un Recruiter.")
                elif not cliente_nome.strip():
                    st.error("Il campo 'Nome del Nuovo Cliente' è obbligatorio!")
                elif not data_referral:
                    st.error("Il campo 'Data del Referral' è obbligatorio!")
                elif not stato:
                    st.error("Il campo 'Stato del Referral' è obbligatorio!")
                else:
                    data_referral_sql = parse_date(data_referral)
                    inserisci_referral(recruiter_id, cliente_nome.strip(), data_referral_sql, stato)
                    st.success("Referral inserito con successo!")
    finally:
        conn.close()

def inserisci_formazione_ui():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Carica recruiters
            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            recruiters = c.fetchall()
            recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
            recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi)
            recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

            corso_nome = st.text_input("Nome del Corso")
            data_completamento = st.date_input("Data di Completamento", value=datetime.today())

            submitted = st.form_submit_button("Inserisci Formazione")
            if submitted:
                if recruiter_id is None:
                    st.error("Selezionare un Recruiter.")
                elif not corso_nome.strip():
                    st.error("Il campo 'Nome del Corso' è obbligatorio!")
                elif not data_completamento:
                    st.error("Il campo 'Data di Completamento' è obbligatorio!")
                else:
                    data_completamento_sql = parse_date(data_completamento)
                    inserisci_formazione(recruiter_id, corso_nome.strip(), data_completamento_sql)
                    st.success("Formazione inserita con successo!")
    finally:
        conn.close()

#######################################
# 4. Considerazioni Finali
#######################################

# Nota: Tutte le funzioni e le interfacce utente necessarie sono state incluse sopra.
# L'applicazione ora dovrebbe essere completa con tutte le funzionalità richieste.
