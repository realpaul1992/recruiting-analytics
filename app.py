# app.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import plotly.express as px
import shutil
import os
import matplotlib.pyplot as plt  # <--- Import Matplotlib

#######################################
# FUNZIONI DI ACCESSO AL DB (MySQL)
#######################################
def get_connection():
    """
    Ritorna una connessione MySQL usando pymysql.
    Sostituisci i parametri con i tuoi valori Railway.
    """
    return pymysql.connect(
        host="junction.proxy.rlwy.net",  # Public host
        port=14718,                      # Porta pubblica
        user="root",                     # Username
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",  # Password
        database="railway"               # Nome DB
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
    conn = get_connection()
    c = conn.cursor()

    # Stato e date di default
    stato_progetto = None
    data_fine = None
    tempo_totale = None
    recensione_stelle = None
    recensione_data = None
    tempo_previsto = None  # Gestito in "clienti.py"

    # Inserimento
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
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    # Backup su MySQL non è un semplice copia-file
    backup_database()

def carica_dati_completo():
    """
    Carica i progetti uniti a settori, pm, recruiters, 
    includendo la colonna 'tempo_previsto'.
    """
    conn = get_connection()
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
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#######################################
# GESTIONE BACKUP
#######################################
def backup_database(max_backups=5):
    """
    Con MySQL non possiamo semplicemente copiare un file .db come in SQLite.
    Quindi qui ci limitiamo a mostrare un messaggio informativo.
    """
    st.info("Backup non implementato su MySQL (nessun file database.db da copiare).")

def check_weekly_backup():
    """
    In contesto MySQL su hosting, 
    il backup periodico non è implementato in questo codice.
    """
    pass

check_weekly_backup()

#######################################
# CAPACITA' PER RECRUITER
#######################################
def carica_recruiters_capacity():
    """
    Restituisce un DF con [sales_recruiter, capacity].
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT r.nome AS sales_recruiter,
               IFNULL(rc.capacity_max, 5) AS capacity
        FROM recruiters r
        LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
        ORDER BY r.nome
    ''')
    rows = c.fetchall()
    conn.close()
    df_capacity = pd.DataFrame(rows, columns=['sales_recruiter', 'capacity'])
    return df_capacity

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD MENSILE
#######################################
def calcola_leaderboard_mensile(df, start_date, end_date):
    """
    Filtra i progetti completati (stato_progetto='Completato')
    con data_inizio compresa in [start_date, end_date].
    
    Calcola:
      - completati = n. progetti completati nel periodo
      - tempo_medio = tempo medio di chiusura
      - bonus_totale = somma bonus (4 stelle=300, 5 stelle=500)
      - punteggio = completati*10 + bonus_totale + max(0, 30 - tempo_medio)
      - badge = 'Bronze' (>=5), 'Silver' (>=10), 'Gold' (>=20)

    Ritorna un DataFrame con:
      [sales_recruiter, completati, tempo_medio, bonus_totale, punteggio, badge].
    """
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

    # punteggio
    leaderboard['punteggio'] = (
        leaderboard['completati'] * 10
        + leaderboard['bonus_totale']
        + leaderboard['tempo_medio'].apply(lambda x: max(0, 30 - x))
    )

    # badge
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
# CONFIG E LAYOUT
#######################################
STATI_PROGETTO = ["Completato", "In corso", "Bloccato"]

# Caricamento dei dati delle tabelle
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
        settori_nomi = [s[1] for s in settori_db]
        settore_sel = st.selectbox("Settore Cliente", settori_nomi)
        settore_id = next(s[0] for s in settori_db if s[1] == settore_sel)
        
        # Project Manager
        pm_nomi = [p[1] for p in pm_db]
        pm_sel = st.selectbox("Project Manager", pm_nomi)
        pm_id = next(p[0] for p in pm_db if p[1] == pm_sel)
        
        # Recruiter
        rec_nomi = [r[1] for r in rec_db]
        rec_sel = st.selectbox("Sales Recruiter", rec_nomi)
        rec_id = next(r[0] for r in rec_db if r[1] == rec_sel)
        
        data_inizio_str = st.text_input("Data di Inizio (GG/MM/AAAA)", value="", 
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
    
    if df.empty:
        st.info("Nessun progetto disponibile nel DB.")
    else:
        # Definisci le tab
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Panoramica",
            "Carico Proiettato / Previsione",
            "Bonus e Premi",
            "Backup",
            "Altre Info",
            "Classifica"
        ])

        #
        # Resto del codice identico (Panoramica, Carico Proiettato, etc.)
        # Basta copiare esattamente ciò che hai già fornito e che stava funzionando
        #

        with tab1:
            ...
            # etc.

        # e così via per tab2, tab3, ...

#######################################
# 3. GESTISCI OPZIONI
#######################################
elif scelta == "Gestisci Opzioni":
    st.write("Gestione settori, PM, recruiters e capacity in manage_options.py")
