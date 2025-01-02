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
# DASHBOARD PER ADMIN
#######################################
def admin_dashboard(df):
    st.header("Dashboard Amministratore")
    
    # Creiamo le Tab
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Panoramica",
        "Carico Proiettato / Previsione",
        "Bonus e Premi",
        "Backup",
        "Altre Info",
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

    #######################################
    # DASHBOARD PERSONALE PER RECRUITER
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
# SISTEMA DI AUTENTICAZIONE
#######################################
# Definisci un dizionario di utenti con username, password e ruolo
# In un ambiente di produzione, utilizza metodi di autenticazione sicuri
user_credentials = {
    "admin": {"password": "adminpass", "role": "admin"},
    "Juan.Sebastian": {"password": "password1", "role": "recruiter"},
    "luca.bianchi": {"password": "password2", "role": "recruiter"},
    "giulia.verdi": {"password": "password3", "role": "recruiter"},
    # Aggiungi altri recruiter qui
}

def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")
    
    if login_button:
        if username in user_credentials and user_credentials[username]["password"] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['role'] = user_credentials[username]["role"]
            st.sidebar.success("Login effettuato con successo!")
        else:
            st.sidebar.error("Username o password errati.")

#######################################
# GESTIONE LOGIN E LOGOUT
#######################################
# Inizializzazione dello stato della sessione
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# Se non loggato, mostra il form di login e interrompi l'esecuzione
if not st.session_state['logged_in']:
    login()
    st.stop()

# Una volta loggato, mostra il pulsante di logout
if st.sidebar.button("Logout", key="unique_logout_button"):
    for key in ['logged_in', 'username', 'role']:
        if key in st.session_state:
            del st.session_state[key]
    st.sidebar.success("Sei stato disconnesso.")
    st.stop()  # Interrompi l'esecuzione dopo il logout

#######################################
# GESTIONE NAVIGAZIONE BASATA SUL RUOLO
#######################################
if st.session_state['role'] == "admin":
    scelta = st.sidebar.radio("Vai a", ["Inserisci Dati", "Dashboard", "Gestisci Opzioni"], key='admin_nav')

    #######################################
    # 1. INSERISCI DATI (solo admin)
    #######################################
    if scelta == "Inserisci Dati":
        st.header("Inserimento Nuovo Progetto")
        
        with st.form("form_inserimento_progetto"):
            cliente = st.text_input("Nome Cliente")
            
            # Settore
            settori_nomi = [s[1] for s in carica_settori()]
            settore_sel = st.selectbox("Settore Cliente", settori_nomi)
            settore_id = None
            for s in carica_settori():
                if s[1] == settore_sel:
                    settore_id = s[0]
                    break
            
            # Project Manager
            pm_nomi = [p[1] for p in carica_project_managers()]
            pm_sel = st.selectbox("Project Manager", pm_nomi)
            pm_id = None
            for p in carica_project_managers():
                if p[1] == pm_sel:
                    pm_id = p[0]
                    break
            
            # Recruiter
            rec_nomi = [r[1] for r in carica_recruiters()]
            rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
            rec_id = None
            for r in carica_recruiters():
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
    # 2. DASHBOARD (admin)
    #######################################
    elif scelta == "Dashboard":
        df = carica_dati_completo()
        if df.empty:
            st.info("Nessun progetto disponibile nel DB.")
        else:
            admin_dashboard(df)

    #######################################
    # 3. GESTISCI OPZIONI (admin)
    #######################################
    elif scelta == "Gestisci Opzioni":
        st.write("Gestione settori, PM, recruiters e capacity in manage_options.py")
        st.markdown("### Nota")
        st.markdown("""
        La gestione delle opzioni (settori, Project Managers, Recruiters e Capacità) è gestita nel file `manage_options.py`.
        Assicurati di navigare a quella pagina per gestire le tue opzioni.
        """)

elif st.session_state['role'] == "recruiter":
    scelta_recruiter = st.sidebar.radio("Vai a", ["Dashboard Personale"], key='recruiter_nav')

    #######################################
    # DASHBOARD PERSONALE (recruiter)
    #######################################
    if scelta_recruiter == "Dashboard Personale":
        recruiter_username = st.session_state['username']
        df = carica_dati_completo()
        recruiter_dashboard_personale(recruiter_username, df)
