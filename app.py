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
    Aggiunge colonne datetime come 'data_inizio_dt', 'start_date_dt', 'recensione_data_dt', e 'data_fine_dt'.
    Crea una colonna 'effective_start_date' che unisce 'data_inizio_dt' e 'start_date_dt'.
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
            p.start_date,
            p.end_date,
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
        'stato_progetto','data_inizio','data_fine','start_date','end_date',
        'tempo_totale','recensione_stelle','recensione_data','tempo_previsto'
    ]
    conn.close()

    df = pd.DataFrame(rows, columns=columns)
    
    # Convertiamo 'tempo_previsto' a numerico
    if "tempo_previsto" in df.columns:
        df["tempo_previsto"] = pd.to_numeric(df["tempo_previsto"], errors="coerce")
        df["tempo_previsto"] = df["tempo_previsto"].fillna(0).astype(int)
    
    # Aggiungi colonne datetime
    df['data_inizio_dt'] = pd.to_datetime(df['data_inizio'], errors='coerce')
    df['start_date_dt'] = pd.to_datetime(df['start_date'], errors='coerce')
    df['recensione_data_dt'] = pd.to_datetime(df['recensione_data'], errors='coerce')
    df['data_fine_dt'] = pd.to_datetime(df['data_fine'], errors='coerce')  # **Aggiunta Necessaria**
    
    # Crea 'effective_start_date' che utilizza 'data_inizio_dt' se presente, altrimenti 'start_date_dt'
    df['effective_start_date'] = df['data_inizio_dt'].combine_first(df['start_date_dt'])
    
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

#######################################
# FUNZIONI PER GESTIONE CANDIDATI  # NUOVO
#######################################

def carica_candidati_completo():
    """
    Carica tutti i candidati dal database.
    """
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT
            c.id,
            c.progetto_id,
            c.recruiter_id,
            c.candidato_nome,
            c.data_inserimento,
            c.data_dimissioni,
            c.data_placement
        FROM candidati c
    """
    c.execute(query)
    rows = c.fetchall()
    columns = ['id','progetto_id','recruiter_id','candidato_nome','data_inserimento','data_dimissioni','data_placement']
    conn.close()
    df = pd.DataFrame(rows, columns=columns)
    
    # Convertiamo le date
    df['data_inserimento_dt'] = pd.to_datetime(df['data_inserimento'], errors='coerce')
    df['data_dimissioni_dt'] = pd.to_datetime(df['data_dimissioni'], errors='coerce')
    df['data_placement_dt'] = pd.to_datetime(df['data_placement'], errors='coerce')
    
    # Calcoliamo la durata in giorni se 'data_dimissioni' è presente
    df['durata_giorni'] = (df['data_dimissioni_dt'] - df['data_inserimento_dt']).dt.days
    
    return df

def calcola_durata_media(df_candidati):
    """
    Calcola la durata media dei venditori per progetto.
    """
    df_valid = df_candidati.dropna(subset=['durata_giorni'])
    if df_valid.empty:
        return pd.DataFrame()
    durata_media = df_valid.groupby(['recruiter_id', 'progetto_id'])['durata_giorni'].mean().reset_index()
    return durata_media

def conta_dimissioni_per_recruiter(df_candidati):
    """
    Conta quante volte un venditore è stato inserito e ha lasciato un progetto per recruiter.
    """
    inserimenti = df_candidati.groupby('recruiter_id').size().reset_index(name='inserimenti')
    dimissioni = df_candidati.dropna(subset=['data_dimissioni_dt']).groupby('recruiter_id').size().reset_index(name='dimissioni')
    conta = inserimenti.merge(dimissioni, on='recruiter_id', how='left').fillna(0)
    conta['dimissioni'] = conta['dimissioni'].astype(int)
    return conta

def recruiter_piu_dimissioni(df_candidati):
    """
    Trova il recruiter con il maggior numero di venditori che hanno lasciato i progetti.
    """
    dimissioni = df_candidati.dropna(subset=['data_dimissioni_dt'])
    if dimissioni.empty:
        return None
    recruiter_count = dimissioni.groupby('recruiter_id').size().reset_index(name='dimissioni')
    max_dimissioni = recruiter_count['dimissioni'].max()
    top_recruiters = recruiter_count[recruiter_count['dimissioni'] == max_dimissioni]
    return top_recruiters

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
# Aggiorna la lista delle tab includendo "Recruiters"
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
    df = carica_dati_completo()
    
    # Carica dati candidati per la scheda Retention
    df_candidati = carica_candidati_completo()
    
    if df.empty:
        st.info("Nessun progetto disponibile nel DB.")
    else:
        # Creiamo le Tab, includendo "Recruiters"
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Panoramica",
            "Carico Proiettato / Previsione",
            "Bonus e Premi",
            "Backup",
            "Retention",  # Scheda Retention
            "Classifica",
            "Recruiters"  # Nuova scheda Recruiters
        ])

        ################################
        # TAB 1: Panoramica
        ################################
        with tab1:
            st.subheader("Tempo Medio Generale e per Recruiter/Settore")

            # Filtro per Anno
            st.markdown("### Filtro per Anno")
            anni_disponibili = sorted(df['effective_start_date'].dt.year.dropna().unique())
            anni_disponibili = [int(y) for y in anni_disponibili]
            anni_opzioni = ["Tutti"] + anni_disponibili
            anno_selezionato = st.selectbox(
                "Seleziona Anno",
                options=anni_opzioni,
                index=0,  # Imposta di default su "Tutti"
                key='panoramica_anno'
            )
            
            # Filtra i dati in base alla selezione
            if anno_selezionato != "Tutti":
                try:
                    start_date = datetime(anno_selezionato, 1, 1)
                    end_date = datetime(anno_selezionato, 12, 31)
                except TypeError as e:
                    st.error(f"Errore nella selezione di Anno: {e}")
                    st.stop()

                # Filtraggio per progetti attivi durante l'anno selezionato
                df_filtered = df[
                    (df['effective_start_date'] >= pd.Timestamp(start_date)) &
                    (df['effective_start_date'] <= pd.Timestamp(end_date))
                ]
            else:
                # Usa tutti i dati
                df_filtered = df.copy()

            if df_filtered.empty:
                st.info("Nessun dato disponibile per la selezione.")
            else:
                # Filtra solo i progetti completati e una tantum
                df_comp = df_filtered[
                    (df_filtered['stato_progetto'] == 'Completato') &
                    (df_filtered['start_date_dt'].isna())  # Escludi progetti continuativi
                ]
                if df_comp.empty:
                    st.info("Nessun progetto una tantum completato nella selezione.")
                else:
                    # Tempo Medio Globale (Solo Progetti Una Tantum)
                    tempo_medio_globale = df_comp['tempo_totale'].dropna().mean() or 0
                    st.metric("Tempo Medio Globale (giorni)", round(tempo_medio_globale,2))

                    # Tempo medio per recruiter (Solo Progetti Una Tantum)
                    rec_media = df_comp.groupby('sales_recruiter')['tempo_totale'].mean().reset_index(name='tempo_medio')
                    rec_media['tempo_medio'] = rec_media['tempo_medio'].fillna(0).round(2)
                    fig_rec = px.bar(
                        rec_media,
                        x='sales_recruiter',
                        y='tempo_medio',
                        labels={'tempo_medio':'Giorni Medi'},
                        title='Tempo Medio di Chiusura per Recruiter (Progetti Una Tantum)',
                        color='tempo_medio',  # Aggiunta di colore per stile
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig_rec, use_container_width=True)

                    # Tempo medio per settore (Solo Progetti Una Tantum)
                    sett_media = df_comp.groupby('settore')['tempo_totale'].mean().reset_index(name='tempo_medio')
                    sett_media['tempo_medio'] = sett_media['tempo_medio'].fillna(0).round(2)
                    fig_sett = px.bar(
                        sett_media,
                        x='settore',
                        y='tempo_medio',
                        labels={'tempo_medio':'Giorni Medi'},
                        title='Tempo Medio di Chiusura per Settore (Progetti Una Tantum)',
                        color='tempo_medio',
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
                Calcoliamo la data di fine calcolata = effective_start_date + tempo_previsto (giorni) per i progetti continuativi.
                Per i progetti una tantum, calcoliamo fine_calcolata = oggi + tempo_previsto.
            """)

            # Filtra i progetti con tempo_previsto > 0
            df_ok = df[(df['tempo_previsto'].notna()) & (df['tempo_previsto'] > 0)]

            # Calcola 'fine_calcolata' differenziando tra progetti continuativi e una tantum
            today = datetime.today()
            df_ok['fine_calcolata'] = df_ok.apply(
                lambda row: row['effective_start_date'] + pd.to_timedelta(row['tempo_previsto'], unit='D') 
                if pd.notna(row['start_date_dt']) else today + pd.to_timedelta(row['tempo_previsto'], unit='D'),
                axis=1
            )

            # Filtra i progetti in corso
            df_incorso = df_ok[df_ok['stato_progetto'] == 'In corso'].copy()

            st.subheader("Mostriamo i Progetti In Corso con tempo_previsto > 0")
            st.dataframe(df_incorso[['cliente','stato_progetto','effective_start_date','tempo_previsto','fine_calcolata','sales_recruiter']])

            st.write("**Vuoi vedere quali progetti si chiuderanno entro X giorni da oggi?**")
            orizzonte_giorni = st.number_input("Seleziona i giorni di orizzonte", value=14, min_value=1)
            today_plus_orizzonte = today + timedelta(days=orizzonte_giorni)
            df_prossimi = df_incorso[df_incorso['fine_calcolata'] <= today_plus_orizzonte]
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
            anni_disponibili_bonus = sorted(df['recensione_data_dt'].dt.year.dropna().unique())
            anni_disponibili_bonus = [int(y) for y in anni_disponibili_bonus]
            anni_opzioni_bonus = ["Tutti"] + anni_disponibili_bonus
            anno_bonus = st.selectbox(
                "Seleziona Anno",
                options=anni_opzioni_bonus,
                index=0,  # Imposta di default su "Tutti"
                key='bonus_anno'
            )
            
            # Filtra i dati in base alla selezione
            if anno_bonus != "Tutti":
                try:
                    start_date_bonus = datetime(anno_bonus, 1, 1)
                    end_date_bonus = datetime(anno_bonus, 12, 31)
                except TypeError as e:
                    st.error(f"Errore nella selezione di Anno per i bonus: {e}")
                    st.stop()
                
                # Filtra i dati per l'anno selezionato
                df_bonus_totale = df[
                    (df['recensione_data_dt'] >= pd.Timestamp(start_date_bonus)) & 
                    (df['recensione_data_dt'] <= pd.Timestamp(end_date_bonus))
                ].copy()
            else:
                # Usa tutti i dati
                df_bonus_totale = df.copy()
            
            # Verifica la presenza della colonna 'recensione_stelle'
            if 'recensione_stelle' not in df_bonus_totale.columns:
                st.error("'recensione_stelle' non è presente nei dati filtrati.")
                st.stop()
            
            # Calcola il premio annuale basato su recensioni a 5 stelle **prima** di aggregare
            df_reviews_5 = df_bonus_totale[df_bonus_totale['recensione_stelle'] == 5]
            
            # Calcola il bonus totale per ogni recruiter **dopo** aver filtrato 'df_reviews_5'
            df_bonus_totale['bonus'] = df_bonus_totale['recensione_stelle'].fillna(0).astype(int).apply(calcola_bonus)
            df_bonus_totale = df_bonus_totale.groupby('sales_recruiter')['bonus'].sum().reset_index(name='bonus_totale')

            # Calcola la percentuale verso il 1000€
            df_bonus_totale['percentuale'] = (df_bonus_totale['bonus_totale'] / 1000) * 100
            df_bonus_totale['percentuale'] = df_bonus_totale['percentuale'].apply(lambda x: min(x, 100))  # Limita al 100%

            # Ordina per percentuale
            df_bonus_totale = df_bonus_totale.sort_values(by='percentuale', ascending=False)

            st.write(f"Progetti con recensione in questo anno: {len(df_bonus_totale)}")

            # **Grafico: Avvicinamento al Premio Annuale di 1000€**
            st.markdown("### Avvicinamento al Premio Annuale di 1000€")
            fig_premio = px.bar(
                df_bonus_totale,
                y='sales_recruiter',
                x='percentuale',
                orientation='h',
                labels={'percentuale': 'Percentuale verso 1000€', 'sales_recruiter': 'Recruiter'},
                title='Avvicinamento al Premio Annuale di 1000€',
                text=df_bonus_totale['percentuale'].apply(lambda x: f"{x:.1f}%")
            )

            # Aggiungi una linea verticale al 100%
            fig_premio.add_shape(
                type="line",
                x0=100,
                y0=-0.5,
                x1=100,
                y1=len(df_bonus_totale),
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
            
            if not df_reviews_5.empty:
                count_reviews = df_reviews_5.groupby('sales_recruiter').size().reset_index(name='recensioni_5_stelle')
                max_reviews = count_reviews['recensioni_5_stelle'].max()
                top_recruiters = count_reviews[count_reviews['recensioni_5_stelle'] == max_reviews]

                if len(top_recruiters) == 1:
                    st.success(f"Il premio annuale va a {top_recruiters.iloc[0]['sales_recruiter']} con {top_recruiters.iloc[0]['recensioni_5_stelle']} recensioni a 5 stelle!")
                else:
                    st.success(f"Premio annuale condiviso tra: {', '.join(top_recruiters['sales_recruiter'])}, ciascuno con {max_reviews} recensioni a 5 stelle!")
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
        # TAB 5: Retention
        ################################
        with tab5:
            st.subheader("Analisi della Retention")

            if df_candidati.empty:
                st.info("Nessun dato sui candidati disponibile.")
            else:
                # Carica i dati dei recruiter
                df_recruiters = carica_recruiters()
                recruiters_dict = {row['id']: row['nome'] for row in df_recruiters}

                # Seleziona un intervallo di date per l'analisi
                st.markdown("### Filtro per Intervallo di Date")
                with st.form("form_retention_filter_dashboard"):
                    start_date_retention = st.date_input("Data Inizio", value=datetime.today().date().replace(year=datetime.today().year -1))
                    end_date_retention = st.date_input("Data Fine", value=datetime.today().date())
                    submit_retention = st.form_submit_button("Calcola Retention")
                
                if submit_retention:
                    if start_date_retention > end_date_retention:
                        st.error("La Data Inizio non può essere successiva alla Data Fine.")
                    else:
                        # Filtra i candidati inseriti nell'intervallo
                        df_filtered_retention = df_candidati[
                            (df_candidati['data_inserimento_dt'] >= pd.Timestamp(start_date_retention)) &
                            (df_candidati['data_inserimento_dt'] <= pd.Timestamp(end_date_retention))
                        ]

                        total_candidati = len(df_filtered_retention)
                        total_dimissioni = df_filtered_retention['data_dimissioni_dt'].notna().sum()

                        st.metric("Totale Candidati Inseriti", total_candidati)
                        st.metric("Totale Dimissioni", total_dimissioni)

                        # Durata Media dei Venditori per Progetto
                        durata_media = calcola_durata_media(df_filtered_retention)
                        if durata_media.empty:
                            st.info("Nessun venditore ha lasciato un progetto in questo intervallo.")
                        else:
                            # Aggiungi nomi dei recruiter e progetti
                            df_recruiters = carica_recruiters()
                            recruiters_dict = {row['id']: row['nome'] for row in df_recruiters}

                            # Carica i nomi dei progetti
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute("SELECT id, cliente FROM progetti")
                            progetti = c.fetchall()
                            progetti_dict = {row['id']: row['cliente'] for row in progetti}
                            conn.close()

                            durata_media['recruiter'] = durata_media['recruiter_id'].map(recruiters_dict)
                            durata_media['progetto'] = durata_media['progetto_id'].map(progetti_dict)
                            durata_media = durata_media.dropna(subset=['recruiter', 'progetto'])

                            st.markdown("#### Durata Media dei Venditori per Progetto")
                            st.dataframe(durata_media[['recruiter', 'progetto', 'durata_giorni']].rename(columns={
                                'recruiter': 'Recruiter',
                                'progetto': 'Progetto',
                                'durata_giorni': 'Durata Media (giorni)'
                            }))

                            # Grafico: Durata Media per Recruiter
                            fig_durata = px.bar(
                                durata_media,
                                x='recruiter',
                                y='durata_giorni',
                                color='progetto',
                                labels={'recruiter': 'Recruiter', 'durata_giorni': 'Durata Media (giorni)', 'progetto': 'Progetto'},
                                title='Durata Media dei Venditori per Recruiter e Progetto'
                            )
                            st.plotly_chart(fig_durata, use_container_width=True)

                        # Numero di Inserimenti e Dimissioni per Recruiter
                        conta_dimissioni = conta_dimissioni_per_recruiter(df_filtered_retention)
                        conta_dimissioni['recruiter'] = conta_dimissioni['recruiter_id'].map(recruiters_dict)
                        conta_dimissioni = conta_dimissioni.dropna(subset=['recruiter'])

                        st.markdown("#### Numero di Inserimenti e Dimissioni per Recruiter")
                        st.dataframe(conta_dimissioni[['recruiter', 'inserimenti', 'dimissioni']].rename(columns={
                            'recruiter': 'Recruiter',
                            'inserimenti': 'Inserimenti',
                            'dimissioni': 'Dimissioni'
                        }))

                        # Grafico: Inserimenti vs Dimissioni per Recruiter
                        fig_inserimenti = px.bar(
                            conta_dimissioni,
                            x='recruiter',
                            y=['inserimenti', 'dimissioni'],
                            barmode='group',
                            labels={'recruiter': 'Recruiter', 'value': 'Numero'},
                            title='Inserimenti vs Dimissioni per Recruiter',
                            color_discrete_sequence=['#636EFA', '#EF553B']
                        )
                        st.plotly_chart(fig_inserimenti, use_container_width=True)

                        # Recruiter con più venditori andati via
                        top_recruiters = recruiter_piu_dimissioni(df_filtered_retention)
                        if top_recruiters is not None and not top_recruiters.empty:
                            top_recruiters['recruiter'] = top_recruiters['recruiter_id'].map(recruiters_dict)
                            top_recruiters = top_recruiters.dropna(subset=['recruiter'])
                            max_dimissioni = top_recruiters['dimissioni'].max()
                            st.markdown("#### Recruiter con più Venditori Andati Via")
                            st.dataframe(top_recruiters[['recruiter', 'dimissioni']].rename(columns={
                                'recruiter': 'Recruiter',
                                'dimissioni': 'Dimissioni Totali'
                            }))
                            
                            # Grafico: Top Recruiter Dimissioni
                            fig_top_rec = px.bar(
                                top_recruiters,
                                x='recruiter',
                                y='dimissioni',
                                labels={'recruiter': 'Recruiter', 'dimissioni': 'Dimissioni Totali'},
                                title='Recruiter con più Venditori Andati Via',
                                color='dimissioni',
                                color_continuous_scale='Reds'
                            )
                            st.plotly_chart(fig_top_rec, use_container_width=True)
                        else:
                            st.info("Nessun recruiter ha venditori andati via in questo intervallo.")

        ################################
        # TAB 6: Classifica
        ################################
        with tab6:
            st.subheader("Classifica")

            st.markdown("### Filtro per Anno")
            anni_leader = sorted(df['effective_start_date'].dt.year.dropna().unique())
            anni_leader = [int(y) for y in anni_leader]
            anni_opzioni_leader = ["Tutti"] + anni_leader
            anno_leader = st.selectbox(
                "Seleziona Anno",
                options=anni_opzioni_leader,
                index=0,  # Imposta di default su "Tutti"
                key='leaderboard_anno'
            )

            # Filtra i dati per il leaderboard basato sulla selezione
            if anno_leader != "Tutti":
                try:
                    start_date_leader = datetime(anno_leader, 1, 1)
                    end_date_leader = datetime(anno_leader, 12, 31)
                except TypeError as e:
                    st.error(f"Errore nella selezione di Anno per il leaderboard: {e}")
                    st.stop()
                
                df_leader_filtered = df[
                    (df['effective_start_date'] >= pd.Timestamp(start_date_leader)) &
                    (df['effective_start_date'] <= pd.Timestamp(end_date_leader))
                ]
            else:
                # Usa tutti i dati
                df_leader_filtered = df.copy()

            # Filtra solo i progetti completati e una tantum
            df_leader_comp = df_leader_filtered[
                (df_leader_filtered['stato_progetto'] == 'Completato') &
                (df_leader_filtered['start_date_dt'].isna())  # Solo progetti una tantum
            ].copy()

            st.write(f"Anno in analisi: {anno_leader}")

            # Definisci le date minime e massime se "Tutti" è selezionato
            if anno_leader == "Tutti":
                start_date_leader = df_leader_filtered['effective_start_date'].min()
                end_date_leader = df_leader_filtered['effective_start_date'].max()

            leaderboard_df = calcola_leaderboard_mensile(df_leader_comp, start_date_leader, end_date_leader)
            if leaderboard_df.empty:
                st.info("Nessun progetto completato una tantum in questo periodo.")
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
                        "": "grey"  # Colore di default per badge vuoti
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

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

            # **2) Recruiter più veloce (Tempo Medio)**
            st.markdown("**2) Recruiter più veloce (Tempo Medio)**")
            df_comp_leader = df_leader_comp.copy()
            veloce = df_comp_leader.groupby('sales_recruiter')['tempo_totale'].mean().reset_index()
            veloce['tempo_totale'] = veloce['tempo_totale'].fillna(0)
            veloce = veloce.sort_values(by='tempo_totale', ascending=True)
            if veloce.empty:
                st.info("Nessun progetto completato una tantum per calcolare la velocità.")
            else:
                fig2, ax2 = plt.subplots(figsize=(8,6))
                ax2.bar(veloce['sales_recruiter'], veloce['tempo_totale'], color='#636EFA')  # Colore simile al grafico avvicinamento
                ax2.set_title("Tempo Medio (giorni) - Più basso = più veloce")
                ax2.set_xlabel("Recruiter")
                ax2.set_ylabel("Tempo Medio (giorni)")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig2)

            # **3) Recruiter con più Bonus ottenuti** (4 stelle=300, 5 stelle=500)
            st.markdown("**3) Recruiter con più Bonus ottenuti** (4 stelle=300, 5 stelle=500)")
            df_bonus = df_leader_comp.copy()
            if 'recensione_stelle' in df_bonus.columns:
                df_bonus['bonus'] = df_bonus['recensione_stelle'].apply(calcola_bonus)
                bonus_df = df_bonus.groupby('sales_recruiter')['bonus'].sum().reset_index()
                bonus_df = bonus_df.sort_values(by='bonus', ascending=False)
                if bonus_df.empty:
                    st.info("Nessun bonus calcolato.")
                else:
                    fig3, ax3 = plt.subplots(figsize=(8,6))
                    ax3.bar(bonus_df['sales_recruiter'], bonus_df['bonus'], color='#EF553B')  # Colore simile al grafico avvicinamento
                    ax3.set_title("Bonus Totale Ottenuto")
                    ax3.set_xlabel("Recruiter")
                    ax3.set_ylabel("Bonus (€)")
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig3)
            else:
                st.warning("'recensione_stelle' non è presente nei dati filtrati.")

        ################################
        # TAB 7: Recruiters
        ################################
        with tab7:
            st.subheader("Recruiters")

            # Filtro per Anno
            st.markdown("### Filtro per Anno")
            anni_disponibili_recr = sorted(df['effective_start_date'].dt.year.dropna().unique())
            anni_disponibili_recr = [int(y) for y in anni_disponibili_recr]
            anni_opzioni_recr = ["Tutti"] + anni_disponibili_recr
            anno_recr = st.selectbox(
                "Seleziona Anno",
                options=anni_opzioni_recr,
                index=0,  # Imposta di default su "Tutti"
                key='recruiters_anno'
            )

            # Menu a tendina per tutti i Recruiters con indicatore di stato
            st.markdown("### Seleziona Recruiter")
            # Carica tutti i recruiters
            all_recruiters = [r['nome'] for r in rec_db]
            all_recruiters = sorted(all_recruiters)
            
            # Ottieni l'elenco dei recruiters con progetti attivi
            df_active_recr = df[df['stato_progetto'].isin(['In corso', 'Bloccato'])]
            active_recruiters_set = set(df_active_recr['sales_recruiter'].unique())
            
            # Crea una lista di tuples con nome e stato attivo
            recruiters_with_status = [
                (recruiter, "Attivo" if recruiter in active_recruiters_set else "Inattivo") 
                for recruiter in all_recruiters
            ]
            
            # Visualizza il menu a tendina con status
            rec_sel_recr = st.selectbox(
                "Seleziona Recruiter",
                options=recruiters_with_status,
                format_func=lambda x: f"{x[0]} ({x[1]})",
                index=0,
                key='recruiters_selezionato'
            )
            
            # Estrai solo il nome del recruiter selezionato
            selected_recruiter_name = rec_sel_recr[0]

            # Filtra i dati in base alla selezione
            if anno_recr != "Tutti":
                try:
                    start_date_recr = datetime(anno_recr, 1, 1)
                    end_date_recr = datetime(anno_recr, 12, 31)
                    df_filtered_recr = df[
                        (df['effective_start_date'] >= pd.Timestamp(start_date_recr)) &
                        (df['effective_start_date'] <= pd.Timestamp(end_date_recr)) &
                        (df['sales_recruiter'] == selected_recruiter_name)
                    ]
                except TypeError as e:
                    st.error(f"Errore nella selezione di Anno: {e}")
                    st.stop()
            else:
                # Usa tutti i dati per il recruiter selezionato
                df_filtered_recr = df[df['sales_recruiter'] == selected_recruiter_name].copy()

            if df_filtered_recr.empty:
                st.info("Nessun dato disponibile per la selezione.")
            else:
                #############################################
                # 1. Tempo Medio di Chiusura
                #############################################
                # Tempo Medio di Chiusura
                df_closed_recr = df_filtered_recr[df_filtered_recr['stato_progetto'] == 'Completato']
                if df_closed_recr.empty:
                    st.info("Nessun progetto completato per questo recruiter e anno.")
                else:
                    tempo_medio = df_closed_recr['tempo_totale'].dropna().mean() or 0
                    st.metric("Tempo Medio di Chiusura (giorni)", round(tempo_medio,2))

                    # Tempo Medio di Chiusura per Settore del Recruiter
                    tempo_medio_sett_recr = df_closed_recr.groupby('settore')['tempo_totale'].mean().reset_index(name='tempo_medio')
                    tempo_medio_sett_recr['tempo_medio'] = tempo_medio_sett_recr['tempo_medio'].fillna(0).round(2)
                    fig_sett_recr = px.bar(
                        tempo_medio_sett_recr,
                        x='settore',
                        y='tempo_medio',
                        labels={'tempo_medio':'Giorni Medi'},
                        title=f'Tempo Medio di Chiusura per Settore - {selected_recruiter_name}',
                        color='tempo_medio',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig_sett_recr, use_container_width=True)

                #############################################
                # 2. Progetti Attivi
                #############################################
                # Progetti Attivi
                df_attivi_recr = df_filtered_recr[df_filtered_recr['stato_progetto'].isin(["In corso", "Bloccato"])]
                progetti_attivi_recr = len(df_attivi_recr)
                st.metric("Progetti Attivi", progetti_attivi_recr)

                #############################################
                # 3. Capacità di Carico
                #############################################
                # Capacità di Carico
                df_capacity = carica_recruiters_capacity()
                recruiter_capacity = df_capacity[df_capacity['sales_recruiter'] == selected_recruiter_name]
                if not recruiter_capacity.empty:
                    capacity_max_recr = int(recruiter_capacity['capacity'].iloc[0])
                else:
                    capacity_max_recr = 5  # default as per existing code
                capacità_disponibile_recr = capacity_max_recr - progetti_attivi_recr
                capacità_disponibile_recr = max(capacità_disponibile_recr, 0)
                st.metric("Capacità Disponibile", capacità_disponibile_recr)

                # Grafico Capacità di Carico
                fig_capacity_recr = px.bar(
                    x=['Progetti Attivi', 'Capacità Disponibile'],
                    y=[progetti_attivi_recr, capacità_disponibile_recr],
                    labels={'x': 'Categoria', 'y': 'Numero'},
                    title=f'Capacità di Carico - {selected_recruiter_name}',
                    color=['Progetti Attivi', 'Capacità Disponibile'],
                    color_discrete_sequence=['#636EFA', '#EF553B']
                )
                st.plotly_chart(fig_capacity_recr, use_container_width=True)

                #############################################
                # 4. Numero di Inserimenti e Dimissioni
                #############################################
                st.markdown("### Numero di Inserimenti e Dimissioni")
                if df_candidati.empty:
                    st.info("Nessun dato sui candidati disponibile.")
                else:
                    # Filtra i candidati per il recruiter selezionato e l'anno (se selezionato)
                    if anno_recr != "Tutti":
                        df_candidati_filtered = df_candidati[
                            (df_candidati['recruiter_id'] == rec_sel_recr[0]) &
                            (df_candidati['data_inserimento_dt'] >= pd.Timestamp(start_date_recr)) &
                            (df_candidati['data_inserimento_dt'] <= pd.Timestamp(end_date_recr))
                        ]
                    else:
                        df_candidati_filtered = df_candidati[df_candidati['recruiter_id'] == rec_sel_recr[0]].copy()

                    # Numero di Inserimenti
                    inserimenti = df_candidati_filtered.shape[0]

                    # Numero di Dimissioni
                    dimissioni = df_candidati_filtered['data_dimissioni_dt'].notna().sum()

                    # Display delle metriche
                    col_inserimenti, col_dimissioni = st.columns(2)
                    col_inserimenti.metric("Numero di Inserimenti", inserimenti)
                    col_dimissioni.metric("Numero di Dimissioni", dimissioni)

                    # Grafico Inserimenti e Dimissioni
                    st.markdown("#### Inserimenti vs Dimissioni")
                    df_ins_dim = pd.DataFrame({
                        'Categoria': ['Inserimenti', 'Dimissioni'],
                        'Conteggio': [inserimenti, dimissioni]
                    })
                    fig_ins_dim = px.bar(
                        df_ins_dim,
                        x='Categoria',
                        y='Conteggio',
                        labels={'Conteggio': 'Numero', 'Categoria': 'Categoria'},
                        title='Inserimenti vs Dimissioni',
                        color='Categoria',
                        color_discrete_sequence=['#636EFA', '#EF553B']
                    )
                    st.plotly_chart(fig_ins_dim, use_container_width=True)

                #############################################
                # 5. Bonus Ottenuti
                #############################################
                st.markdown("### Bonus Ottenuti")
                if df_closed_recr.empty:
                    st.info("Nessun progetto completato per calcolare i bonus.")
                else:
                    # Calcola il bonus per ogni progetto completato
                    df_closed_recr['bonus'] = df_closed_recr['recensione_stelle'].fillna(0).astype(int).apply(calcola_bonus)
                    bonus_totale = df_closed_recr['bonus'].sum()

                    # Display della metrica
                    st.metric("Bonus Ottenuti (€)", bonus_totale)

                    # Grafico Bonus per Progetto
                    st.markdown("#### Bonus per Progetto Completato")
                    bonus_per_progetto = df_closed_recr.groupby('cliente')['bonus'].sum().reset_index()
                    fig_bonus_progetto = px.bar(
                        bonus_per_progetto,
                        x='cliente',
                        y='bonus',
                        labels={'bonus': 'Bonus (€)', 'cliente': 'Cliente'},
                        title='Bonus Totale per Progetto',
                        color='bonus',
                        color_continuous_scale='Greens'
                    )
                    st.plotly_chart(fig_bonus_progetto, use_container_width=True)

                #############################################
                # 6. Altre Metriche Suggerite
                #############################################
                st.markdown("### Altre Metriche")
                # Numero Totale di Progetti Gestiti
                num_progetti_gestiti = df_filtered_recr.shape[0]
                st.metric("Numero Totale di Progetti Gestiti", num_progetti_gestiti)

                # Conversion Rate (Inserimenti a Placement)
                if inserimenti > 0:
                    placements = df_candidati_filtered['data_placement_dt'].notna().sum()
                    conversion_rate = (placements / inserimenti) * 100
                    st.metric("Conversion Rate (%)", f"{conversion_rate:.2f}%")
                else:
                    st.metric("Conversion Rate (%)", "N/A")

                # Tempo Medio di Inserimento
                df_placements = df_candidati_filtered.dropna(subset=['data_placement_dt'])
                if not df_placements.empty:
                    df_placements['tempo_inserimento'] = (df_placements['data_placement_dt'] - df_placements['data_inserimento_dt']).dt.days
                    tempo_medio_inserimento = df_placements['tempo_inserimento'].mean()
                    st.metric("Tempo Medio di Inserimento (giorni)", round(tempo_medio_inserimento,2))
                else:
                    st.metric("Tempo Medio di Inserimento (giorni)", "N/A")

                # Retention Rate (opzionale)
                if inserimenti > 0:
                    retention = ((inserimenti - dimissioni) / inserimenti) * 100
                    st.metric("Retention Rate (%)", f"{retention:.2f}%")
                else:
                    st.metric("Retention Rate (%)", "N/A")

                # Grafico Conversion Rate
                if inserimenti > 0:
                    df_conversion = pd.DataFrame({
                        'Categoria': ['Inserimenti', 'Placements'],
                        'Conteggio': [inserimenti, placements]
                    })
                    fig_conversion = px.bar(
                        df_conversion,
                        x='Categoria',
                        y='Conteggio',
                        labels={'Conteggio': 'Numero', 'Categoria': 'Categoria'},
                        title='Inserimenti vs Placements',
                        color='Categoria',
                        color_discrete_sequence=['#636EFA', '#EF553B']
                    )
                    st.plotly_chart(fig_conversion, use_container_width=True)

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
