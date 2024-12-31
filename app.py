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
# FUNZIONI DI ACCESSO AL DB (MySQL + pymysql)
#######################################
def get_connection():
    """
    Ritorna una connessione MySQL usando pymysql.
    Sostituisci i valori con i tuoi da Railway:
    """
    return pymysql.connect(
        host="junction.proxy.rlwy.net",  # Public host su Railway
        port=14718,                      # Porta pubblica
        user="root",                     # Username (Railway)
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",  # Tua password
        database="railway"              # Nome DB, di solito 'railway'
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

    # Esegui il backup in locale? Non ha senso con MySQL.
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
    conn.close()

    columns = [
        'id','cliente','settore','project_manager','sales_recruiter',
        'stato_progetto','data_inizio','data_fine','tempo_totale',
        'recensione_stelle','recensione_data','tempo_previsto'
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df

#######################################
# GESTIONE BACKUP
#######################################
def backup_database(max_backups=5):
    """
    Con MySQL, non puoi copiare un file come su SQLite.
    Qui generiamo solo un messaggio d'errore o di info.
    """
    st.info("Backup su MySQL non implementato (nessun file database.db da copiare).")

def check_weekly_backup():
    """
    Inutile in contesto MySQL su Streamlit Cloud.
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
    df_capacity = pd.DataFrame(rows, columns=['sales_recruiter', 'capacity'])
    return df_capacity

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD MENSILE
#######################################
def calcola_leaderboard_mensile(df, start_date, end_date):
    ...
    # Copi e incolli la stessa logica esistente. Lasciata invariata.

# Rimane tutto invariato per le tab, mantenendo la logica

STATI_PROGETTO = ["Completato", "In corso", "Bloccato"]

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
    ...
    # Mantieni identico, 
    # data la logica di caricamento settori/pm/rec, 
    # per poi chiamare inserisci_dati(...).

#######################################
# 2. DASHBOARD
#######################################
elif scelta == "Dashboard":
    st.header("Dashboard di Controllo")
    df = carica_dati_completo()
    ...
    # Rimani identico nel layout e i calcoli (adesso punta a MySQL)
    # Tieni tutto come nel codice che hai fornito.

#######################################
# 3. GESTISCI OPZIONI
#######################################
elif scelta == "Gestisci Opzioni":
    st.write("Gestione settori, PM, recruiters e capacity in manage_options.py")
