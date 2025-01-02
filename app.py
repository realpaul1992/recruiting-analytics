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
    Sostituisci i parametri (host, port, user, password, database)
    con quelli del tuo DB su Railway.
    """
    return pymysql.connect(
        host="junction.proxy.rlwy.net",
        port=14718,
        user="root",
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",
        database="railway"
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
        c = conn.cursor()

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

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD MENSILE
#######################################
def calcola_leaderboard_mensile(df, start_date, end_date):
    df_temp = df.copy()
    df_temp['data_inizio_dt'] = pd.to_datetime(df_temp['data_inizio'], errors='coerce')
    df_temp['recensione_stelle'] = df_temp['recensione_stelle'].fillna(0).astype(int)

    # bonus da recensioni
    def bonus_stelle(stelle):
        if stelle == 4:
            return 300
        elif stelle == 5:
            return 500
        return 0
    
    df_temp['bonus'] = df_temp['recensione_stelle'].apply(bonus_stelle)

    mask = (
        (df_temp['stato_progetto'] == 'Completato') &
        (df_temp['data_inizio_dt'] >= pd.Timestamp(start_date)) &
        (df_temp['data_inizio_dt'] <= pd.Timestamp(end_date))
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
# SISTEMA DI AUTENTICAZIONE
#######################################
# Definisci un dizionario di recruiter con username e password
# In un ambiente di produzione, utilizza metodi di autenticazione sicuri
recruiter_credentials = {
    "Juan.Sebastian": "password1",
    "Paolo.Carnevale": "password2",
    "Daniele.Martignano": "password3"
    "Francesco.Picaro": "password4"
    # Aggiungi altri recruiter qui
}

def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:
        if username in recruiter_credentials and recruiter_credentials[username] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.sidebar.success("Login effettuato con successo!")
            st.experimental_rerun()
        else:
            st.sidebar.error("Username o password errati.")

def logout():
    st.sidebar.button("Logout")
    if 'logout' in st.session_state:
        del st.session_state['logged_in']
        del st.session_state['username']
        st.experimental_rerun()

#######################################
# GESTIONE LOGIN
#######################################
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.stop()

#######################################
# GESTIONE DASHBOARD PERSONALE
#######################################
def recruiter_dashboard_personale(recruiter_username, df):
    df_recruiter = df[df['sales_recruiter'] == recruiter_username]
    
    if df_recruiter.empty:
        st.info("Nessun progetto assegnato a questo recruiter.")
        return
    
    st.header(f"Dashboard di {recruiter_username}")
    
    # Metric: Bonus ricevuti
    df_recruiter['bonus'] = df_recruiter['recensione_stelle'].fillna(0).astype(int).apply(calcola_bonus)
    total_bonus = df_recruiter['bonus'].sum()
    st.metric("Bonus Totale (€)", total_bonus)
    
    # Metric: Tempo medio di chiusura totale
    df_completed = df_recruiter[df_recruiter['stato_progetto'] == 'Completato']
    average_closure_time = df_completed['tempo_totale'].mean() if not df_completed.empty else 0
    st.metric("Tempo Medio di Chiusura Totale (giorni)", round(average_closure_time, 2))
    
    # Metric: Numero di progetti attivi
    active_projects = df_recruiter[df_recruiter['stato_progetto'].isin(["In corso", "Bloccato"])].shape[0]
    st.metric("Numero di Progetti Attivi", active_projects)
    
    # Tempo medio di chiusura per settore
    average_closure_time_sector = df_completed.groupby('settore')['tempo_totale'].mean().reset_index()
    st.subheader("Tempo Medio di Chiusura per Settore")
    if not average_closure_time_sector.empty:
        fig_sector = px.bar(
            average_closure_time_sector,
            x='settore',
            y='tempo_totale',
            labels={'settore': 'Settore', 'tempo_totale': 'Giorni Medi'},
            title='Tempo Medio di Chiusura per Settore'
        )
        st.plotly_chart(fig_sector)
    else:
        st.info("Nessun progetto completato per calcolare il tempo medio per settore.")
    
    # Grafico Bonus per Cliente
    st.subheader("Bonus Ricevuti per Cliente")
    bonus_per_cliente = df_recruiter.groupby('cliente')['bonus'].sum().reset_index()
    fig_bonus_cliente = px.bar(
        bonus_per_cliente,
        x='cliente',
        y='bonus',
        labels={'cliente': 'Cliente', 'bonus': 'Bonus (€)'},
        title='Bonus per Cliente'
    )
    st.plotly_chart(fig_bonus_cliente)
    
    # Grafico Recensioni a 5 Stelle
    st.subheader("Recensioni a 5 Stelle")
    df_recruiter_5 = df_recruiter[df_recruiter['recensione_stelle'] == 5]
    if not df_recruiter_5.empty:
        rec_5_count = df_recruiter_5.groupby('cliente').size().reset_index(name='5_star_reviews')
        fig_rec_5 = px.bar(
            rec_5_count,
            x='cliente',
            y='5_star_reviews',
            labels={'cliente': 'Cliente', '5_star_reviews': 'Recensioni 5 Stelle'},
            title='Recensioni a 5 Stelle per Cliente'
        )
        st.plotly_chart(fig_rec_5)
    else:
        st.info("Nessuna recensione a 5 stelle per questo recruiter.")
    
    # Grafico Avvicinamento al Premio Annuale di 1000€
    st.subheader("Avvicinamento al Premio Annuale di 1000€")
    bonus_rimanente = max(0, 1000 - total_bonus)
    fig_premio = px.bar(
        x=["Bonus Attuale", "Bonus Mancante"],
        y=[total_bonus, bonus_rimanente],
        labels={'x': 'Categoria', 'y': '€'},
        title='Avvicinamento al Premio Annuale di 1000€',
        text=[total_bonus, bonus_rimanente]
    )
    fig_premio.update_traces(textposition='auto', marker_color=['green', 'red'])
    st.plotly_chart(fig_premio)
    
    # Tabella dei Progetti Assegnati
    st.subheader("Progetti Assegnati")
    st.dataframe(df_recruiter[['cliente', 'settore', 'stato_progetto', 'data_inizio', 'recensione_stelle', 'bonus']])

#######################################
# MAIN DASHBOARD
#######################################
def main_dashboard():
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
            "Dashboard Personale",
            "Classifica"
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
                    title='Tempo Medio di Chiusura per Recruiter'
                )
                st.plotly_chart(fig_rec)

                # Tempo medio per settore
                sett_media = df_comp.groupby('settore')['tempo_totale'].mean().reset_index()
                sett_media['tempo_totale'] = sett_media['tempo_totale'].fillna(0).round(2)
                fig_sett = px.bar(
                    sett_media,
                    x='settore',
                    y='tempo_totale',
                    labels={'tempo_totale':'Giorni Medi'},
                    title='Tempo Medio di Chiusura per Settore'
                )
                st.plotly_chart(fig_sett)

                st.subheader("Progetti Attivi (In corso + Bloccato)")
                df_attivi = df_filtered[df_filtered['stato_progetto'].isin(["In corso", "Bloccato"])]
                attivi_count = df_attivi.groupby('sales_recruiter').size().reset_index(name='Progetti Attivi')
                fig_attivi = px.bar(
                    attivi_count,
                    x='sales_recruiter',
                    y='Progetti Attivi',
                    title='Numero di Progetti Attivi per Recruiter'
                )
                st.plotly_chart(fig_attivi)

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
                    title='Capacità di Carico per Recruiter'
                )
                st.plotly_chart(fig_carico)

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
                Esempio: 4 stelle => 300€, 5 stelle => 500€.
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

            # Verifica se 'recensione_data_dt' esiste
            if 'recensione_data_dt' not in df.columns:
                st.error("La colonna 'recensione_data_dt' non esiste nel DataFrame.")
                st.stop()

            df_mese = df[
                (df['recensione_data_dt'] >= pd.Timestamp(start_date_bonus)) & 
                (df['recensione_data_dt'] <= pd.Timestamp(end_date_bonus))
            ]

            st.write(f"Progetti con recensione in questo anno: {len(df_mese)}")

            df_mese['bonus'] = df_mese['recensione_stelle'].fillna(0).astype(int).apply(calcola_bonus)
            bonus_rec = df_mese.groupby('sales_recruiter')['bonus'].sum().reset_index()
            fig_bonus = px.bar(
                bonus_rec,
                x='sales_recruiter',
                y='bonus',
                labels={'bonus':'Bonus (€)'},
                title='Bonus dell\'Anno'
            )
            st.plotly_chart(fig_bonus)

            st.subheader("Premio Annuale (Recensioni a 5 stelle)")
            df_premio_annuale = df_mese[df_mese['recensione_stelle'] == 5]
            rec_5 = df_premio_annuale.groupby('sales_recruiter').size().reset_index(name='cinque_stelle')
            if not rec_5.empty:
                max_num = rec_5['cinque_stelle'].max()
                vincitori = rec_5[rec_5['cinque_stelle'] == max_num]
                if len(vincitori) == 1:
                    st.success(f"Il premio annuale va a {vincitori.iloc[0]['sales_recruiter']} con {max_num} recensioni 5 stelle!")
                else:
                    st.success(f"Premio annuale condiviso tra: {', '.join(vincitori['sales_recruiter'])}, con {max_num} 5 stelle!")
            else:
                st.info("Nessuna recensione a 5 stelle nell'anno selezionato.")

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
        # TAB 5: Dashboard Personale
        ################################
        with tab5:
            st.subheader("Dashboard Personale")
            st.write("Visualizza la tua dashboard personale qui sotto:")

            recruiter_username = st.session_state['username']
            recruiter_dashboard_personale(recruiter_username, df)

        ################################
        # TAB 6: Classifica
        ################################
        with tab6:
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

            leaderboard_df = calcola_leaderboard_mensile(df_leader_filtered, start_date_leader, end_date_leader)
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
                    title='Leaderboard Annuale'
                )
                st.plotly_chart(fig_leader)

                st.markdown("""
                **Formula Punteggio**  
                - +10 punti ogni progetto completato  
                - +bonus (300/500) da recensioni 4/5 stelle  
                - +max(0, 30 - tempo_medio) per invertire la velocità  
                """)
                st.markdown("""
                **Badge**  
                - Bronze = almeno 5 completati  
                - Silver = almeno 10  
                - Gold   = almeno 20  
                """)

            ################################
            # Grafici nella Classifica
            ################################
            st.subheader("Grafici della Classifica")

            # (1) RECRUITER PIÙ VICINO AL PREMIO ANNUALE (5 STELLE)
            st.markdown("**1) Recruiter più vicino al Premio Annuale (5 stelle)**")
            df_premio_annuale = df_leader_filtered[df_leader_filtered['recensione_stelle'] == 5]
            rec_5 = df_premio_annuale.groupby('sales_recruiter').size().reset_index(name='cinque_stelle')
            rec_5 = rec_5.sort_values(by='cinque_stelle', ascending=False)
            if rec_5.empty:
                st.info("Nessuna 5 stelle nell'anno selezionato.")
            else:
                fig1, ax1 = plt.subplots(figsize=(6,4))
                ax1.bar(rec_5['sales_recruiter'], rec_5['cinque_stelle'], color='blue')
                ax1.set_title("N. Recensioni 5 stelle (anno selezionato)")
                ax1.set_xlabel("Recruiter")
                ax1.set_ylabel("Recensioni 5 stelle")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig1)

            # (2) RECRUITER PIÙ VELOCE (TEMPO MEDIO)
            st.markdown("**2) Recruiter più veloce (Tempo Medio)**")
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
                fig2, ax2 = plt.subplots(figsize=(6,4))
                ax2.bar(veloce['sales_recruiter'], veloce['tempo_totale'], color='green')
                ax2.set_title("Tempo Medio (giorni) - Più basso = più veloce")
                ax2.set_xlabel("Recruiter")
                ax2.set_ylabel("Tempo Medio (giorni)")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig2)

            # (3) RECRUITER CON PIÙ BONUS
            st.markdown("**3) Recruiter con più Bonus ottenuti** (4 stelle=300, 5 stelle=500)")
            df_bonus = df_leader_filtered.copy()
            df_bonus['bonus'] = df_bonus['recensione_stelle'].apply(calcola_bonus)
            bonus_df = df_bonus.groupby('sales_recruiter')['bonus'].sum().reset_index()
            bonus_df = bonus_df.sort_values(by='bonus', ascending=False)
            if bonus_df.empty:
                st.info("Nessun bonus calcolato.")
            else:
                fig3, ax3 = plt.subplots(figsize=(6,4))
                ax3.bar(bonus_df['sales_recruiter'], bonus_df['bonus'], color='orange')
                ax3.set_title("Bonus Totale Ottenuto")
                ax3.set_xlabel("Recruiter")
                ax3.set_ylabel("Bonus (€)")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig3)

#######################################
# MAIN APP
#######################################

# Config e layout
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
        settori_nomi = [s[1] for s in settori_db]
        settore_sel = st.selectbox("Settore Cliente", settori_nomi)
        settore_id = None
        for s in settori_db:
            if s[1] == settore_sel:
                settore_id = s[0]
                break
        
        # Project Manager
        pm_nomi = [p[1] for p in pm_db]
        pm_sel = st.selectbox("Project Manager", pm_nomi)
        pm_id = None
        for p in pm_db:
            if p[1] == pm_sel:
                pm_id = p[0]
                break
        
        # Recruiter
        rec_nomi = [r[1] for r in rec_db]
        rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
        rec_id = None
        for r in rec_db:
            if r[1] == rec_sel:
                rec_id = r[0]
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
    main_dashboard()

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

#######################################
# GESTIONE LOGOUT
#######################################
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.experimental_rerun()
