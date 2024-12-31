# clienti.py

import streamlit as st
import pandas as pd
import pymysql  # <--- sostituisce sqlite3
from datetime import datetime

# Se utils.py è fuori dalla cartella pages, facciamo:
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import format_date_display, parse_date

# ===============================
# Funzioni per Interagire con il Database (MySQL)
# ===============================

def get_connection():
    """Crea e restituisce una connessione al database MySQL."""
    return pymysql.connect(
        host="junction.proxy.rlwy.net",  # Esempio di parametri da Railway
        port=14718,
        user="root",
        password="GoHrUNytXgoikyAkbwYQpYLnfuQVQdBM",
        database="railway"
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

def cerca_progetti(id_progetto=None, nome_cliente=None):
    """
    Cerca progetti nel database, inclusa la colonna tempo_previsto.
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
            p.tempo_previsto
        FROM progetti p
        WHERE 1=1
    """
    params = []
    # Filtri opzionali
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
    tempo_previsto
):
    """
    Aggiorna i campi di un progetto esistente, inclusa la parte di recensioni
    e il 'tempo_previsto'. Se data_fine è None, la cancelliamo (NULL).
    """
    conn = get_connection()
    c = conn.cursor()

    # Calcolo tempo_totale se entrambe le date ci sono
    if data_inizio and data_fine:
        tempo_totale = (data_fine - data_inizio).days
    else:
        tempo_totale = None

    # Converto le date in stringhe SQL
    data_inizio_str = data_inizio.strftime('%Y-%m-%d') if data_inizio else None
    data_fine_str   = data_fine.strftime('%Y-%m-%d') if data_fine else None
    recensione_data_str = recensione_data.strftime('%Y-%m-%d') if recensione_data else None

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
            tempo_previsto = %s
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
        id_progetto
    ))
    conn.commit()
    conn.close()

def cancella_progetto(id_progetto):
    """Elimina il progetto con ID corrispondente dalla tabella 'progetti'."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM progetti WHERE id = %s", (id_progetto,))
    conn.commit()
    conn.close()

def carica_dati_completo():
    """
    Carica tutti i dati dalla tabella 'progetti' (senza join),
    includendo la colonna tempo_previsto.
    """
    conn = get_connection()
    c = conn.cursor()
    # Selezioniamo tutte le colonne della tabella 'progetti'
    c.execute("SELECT * FROM progetti")
    rows = c.fetchall()
    col_names = [desc[0] for desc in c.description]  # nome colonna da c.description
    conn.close()

    # Creiamo il DataFrame con le stesse colonne della tabella
    df = pd.DataFrame(rows, columns=col_names)
    return df

# ======================================
# Definizione delle Opzioni / Dizionari
# ======================================

STATI_PROGETTO = ["Completato", "In corso", "Bloccato"]

settori_db = carica_settori_db()
project_managers_db = carica_project_managers_db()
recruiters_db = carica_recruiters_db()

# Dizionari per mappare id -> nome
settori_dict = {row[0]: row[1] for row in settori_db}
settori_dict_reverse = {v: k for k, v in settori_dict.items()}

project_managers_dict = {row[0]: row[1] for row in project_managers_db}
project_managers_dict_reverse = {v: k for k, v in project_managers_dict.items()}

recruiters_dict = {row[0]: row[1] for row in recruiters_db}
recruiters_dict_reverse = {v: k for k, v in recruiters_dict.items()}

# Variabile di stato
if 'progetto_selezionato' not in st.session_state:
    st.session_state.progetto_selezionato = None

# ======================================
# Layout della Pagina
# ======================================
st.title("Gestione Clienti")

st.header("Cerca Progetto")

# Form di ricerca
with st.form("form_cerca_progetto"):
    id_progetto_str = st.text_input("ID Progetto (lascia vuoto se non vuoi specificare)")
    nome_cliente = st.text_input("Nome Cliente")
    submit_cerca = st.form_submit_button("Cerca")

if submit_cerca:
    if not id_progetto_str and not nome_cliente:
        st.error("Inserisci almeno l'ID o il nome del cliente per la ricerca.")
    else:
        # Converte id_progetto_str in int se possibile
        id_progetto = int(id_progetto_str) if id_progetto_str.isdigit() else None
        risultati = cerca_progetti(id_progetto=id_progetto, nome_cliente=nome_cliente.strip() or None)
        if risultati:
            # Creiamo un DataFrame con i campi selezionati
            columns = [
                'id','cliente','settore_id','project_manager_id','sales_recruiter_id',
                'stato_progetto','data_inizio','data_fine','tempo_totale',
                'recensione_stelle','recensione_data','tempo_previsto'
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
        else:
            st.info("Nessun progetto trovato con i criteri inseriti.")

# Se abbiamo selezionato un progetto da aggiornare
if st.session_state.progetto_selezionato:
    row_list = cerca_progetti(id_progetto=st.session_state.progetto_selezionato)
    if not row_list:
        st.error("Progetto non trovato. Forse è stato eliminato?")
        st.stop()

    progetto = row_list[0]  # Primo record

    st.header("Aggiorna / Elimina Progetto")

    # Nomi attuali (id -> nome)
    settore_attuale = settori_dict.get(progetto[2], None)  # p.settore_id = progetto[2]
    pm_attuale = project_managers_dict.get(progetto[3], None)
    rec_attuale = recruiters_dict.get(progetto[4], None)

    col_upd, col_del = st.columns([3,1])
    with col_upd:
        with st.form("form_aggiorna_progetto"):
            # Nome Cliente
            cliente_agg = st.text_input("Nome Cliente", value=progetto[1])  # p.cliente = progetto[1]

            # Settore
            settori_nomi = [s[1] for s in settori_db]
            if settore_attuale and settore_attuale not in settori_nomi:
                settori_nomi.append(settore_attuale)
            if not settore_attuale:
                settore_attuale = settori_nomi[0]

            settore_scelto = st.selectbox(
                "Settore Cliente",
                options=settori_nomi,
                index=settori_nomi.index(settore_attuale) if settore_attuale in settori_nomi else 0
            )
            settore_id_agg = settori_dict_reverse.get(settore_scelto, None)

            # Project Manager
            pm_nomi = [p[1] for p in project_managers_db]
            if pm_attuale and pm_attuale not in pm_nomi:
                pm_nomi.append(pm_attuale)
            if not pm_attuale:
                pm_attuale = pm_nomi[0]

            pm_scelto = st.selectbox(
                "Project Manager",
                options=pm_nomi,
                index=pm_nomi.index(pm_attuale) if pm_attuale in pm_nomi else 0
            )
            pm_id_agg = project_managers_dict_reverse.get(pm_scelto, None)

            # Recruiter
            rec_nomi = [r[1] for r in recruiters_db]
            if rec_attuale and rec_attuale not in rec_nomi:
                rec_nomi.append(rec_attuale)
            if not rec_attuale:
                rec_attuale = rec_nomi[0]

            rec_scelto = st.selectbox(
                "Sales Recruiter",
                options=rec_nomi,
                index=rec_nomi.index(rec_attuale) if rec_attuale in rec_nomi else 0
            )
            rec_id_agg = recruiters_dict_reverse.get(rec_scelto, None)

            # Stato Progetto
            stato_attuale = progetto[5] if progetto[5] else STATI_PROGETTO[0]
            if stato_attuale not in STATI_PROGETTO:
                stato_attuale = STATI_PROGETTO[0]
            stato_agg = st.selectbox(
                "Stato Progetto",
                STATI_PROGETTO,
                index=STATI_PROGETTO.index(stato_attuale) if stato_attuale in STATI_PROGETTO else 0
            )

            st.write("**Lascia vuoto per cancellare la data.**")

            # Data Inizio / Data Fine
            data_inizio_existing = parse_date(progetto[6])  # p.data_inizio
            data_fine_existing   = parse_date(progetto[7])  # p.data_fine

            data_inizio_str = data_inizio_existing.strftime('%d/%m/%Y') if data_inizio_existing else ""
            data_fine_str   = data_fine_existing.strftime('%d/%m/%Y') if data_fine_existing else ""

            data_inizio_agg = st.text_input("Data Inizio (GG/MM/AAAA)", value=data_inizio_str)
            data_fine_agg   = st.text_input("Data Fine (GG/MM/AAAA)",  value=data_fine_str)

            # Recensione
            rec_stelle_attuale = progetto[9] or 0  # p.recensione_stelle = [9]
            rec_stelle_agg = st.selectbox("Recensione (Stelle)", [0,1,2,3,4,5], index=rec_stelle_attuale)

            rec_data_existing = parse_date(progetto[10])  # p.recensione_data
            if rec_stelle_agg > 0:
                rec_data_val = rec_data_existing if rec_data_existing else datetime.today().date()
                rec_data_input = st.date_input("Data Recensione", value=rec_data_val)
            else:
                rec_data_input = None

            # tempo_previsto
            tempo_previsto_existing = progetto[11] if progetto[11] else 0
            tempo_previsto_agg = st.number_input("Tempo Previsto (giorni)", 
                                                value=int(tempo_previsto_existing),
                                                min_value=0)

            sub_update = st.form_submit_button("Aggiorna Progetto")
            if sub_update:
                # parse data_inizio
                if data_inizio_agg.strip():
                    try:
                        data_inizio_parsed = datetime.strptime(data_inizio_agg.strip(), '%d/%m/%Y').date()
                    except ValueError:
                        st.error("Data inizio non valida (GG/MM/AAAA).")
                        st.stop()
                else:
                    data_inizio_parsed = None

                # parse data_fine
                if data_fine_agg.strip():
                    try:
                        data_fine_parsed = datetime.strptime(data_fine_agg.strip(), '%d/%m/%Y').date()
                    except ValueError:
                        st.error("Data fine non valida (GG/MM/AAAA).")
                        st.stop()
                else:
                    data_fine_parsed = None

                # Controllo data
                if data_inizio_parsed and data_fine_parsed:
                    if data_fine_parsed < data_inizio_parsed:
                        st.error("Data fine non può essere precedente a data inizio.")
                        st.stop()

                if rec_stelle_agg > 0 and not rec_data_input:
                    st.error("Se hai messo stelle>0, devi specificare la data recensione.")
                    st.stop()

                # Validazione dizionari
                if settore_id_agg is None:
                    st.error(f"Settore '{settore_scelto}' non esiste nei dizionari.")
                    st.stop()
                if pm_id_agg is None:
                    st.error(f"PM '{pm_scelto}' non esiste nei dizionari.")
                    st.stop()
                if rec_id_agg is None:
                    st.error(f"Recruiter '{rec_scelto}' non esiste nei dizionari.")
                    st.stop()

                aggiorna_progetto(
                    id_progetto=st.session_state.progetto_selezionato,
                    cliente=cliente_agg.strip(),
                    settore_id=settore_id_agg,
                    project_manager_id=pm_id_agg,
                    sales_recruiter_id=rec_id_agg,
                    stato_progetto=stato_agg,
                    data_inizio=data_inizio_parsed,
                    data_fine=data_fine_parsed,
                    recensione_stelle=rec_stelle_agg,
                    recensione_data=rec_data_input,
                    tempo_previsto=tempo_previsto_agg
                )
                st.success(f"Progetto {st.session_state.progetto_selezionato} aggiornato con successo!")
                st.session_state.progetto_selezionato = None

    # Colonna per Eliminare
    with col_del:
        st.write("**Attenzione:**")
        st.write("Eliminando il progetto, i dati spariranno definitivamente.")
        elimina_button = st.button("Elimina Progetto")
        if elimina_button:
            cancella_progetto(st.session_state.progetto_selezionato)
            st.success(f"Progetto ID {st.session_state.progetto_selezionato} eliminato con successo!")
            st.session_state.progetto_selezionato = None

# ======================================
# Sezione "Tutti i Clienti Gestiti"
# ======================================
st.header("Tutti i Clienti Gestiti")

if st.button("Mostra Tutti i Clienti"):
    df_tutti_clienti = carica_dati_completo()
    if df_tutti_clienti.empty:
        st.info("Nessun progetto presente nel DB.")
    else:
        # Mappa ID -> nome
        df_tutti_clienti['settore'] = df_tutti_clienti['settore_id'].map(settori_dict).fillna("Sconosciuto")
        df_tutti_clienti['project_manager'] = df_tutti_clienti['project_manager_id'].map(project_managers_dict).fillna("Sconosciuto")
        df_tutti_clienti['sales_recruiter'] = df_tutti_clienti['sales_recruiter_id'].map(recruiters_dict).fillna("Sconosciuto")

        # Format date
        df_tutti_clienti['data_inizio'] = df_tutti_clienti['data_inizio'].apply(format_date_display)
        df_tutti_clienti['data_fine'] = df_tutti_clienti['data_fine'].apply(format_date_display)
        df_tutti_clienti['recensione_data'] = df_tutti_clienti['recensione_data'].apply(format_date_display)

        df_tutti_clienti['stato_progetto'] = df_tutti_clienti['stato_progetto'].fillna("")
        df_tutti_clienti['recensione_stelle'] = df_tutti_clienti['recensione_stelle'].fillna(0).astype(int)

        # Se la colonna tempo_previsto esiste, la convertiamo in int con fillna(0).
        if 'tempo_previsto' in df_tutti_clienti.columns:
            df_tutti_clienti['tempo_previsto'] = df_tutti_clienti['tempo_previsto'].fillna(0).astype(int)

        st.dataframe(df_tutti_clienti)

        st.download_button(
            label="Scarica Tutti i Clienti in CSV",
            data=df_tutti_clienti.to_csv(index=False).encode('utf-8'),
            file_name="tutti_clienti.csv",
            mime="text/csv"
        )
