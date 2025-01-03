# pages/manage_options.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime

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

def carica_progetti():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, cliente FROM progetti ORDER BY cliente ASC")
            progetti = c.fetchall()
    finally:
        conn.close()
    return progetti

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
            c.execute("""
                SELECT 
                    c.id,
                    c.candidato_nome,
                    c.data_inserimento,
                    c.data_placement,
                    c.data_dimissioni,
                    c.progetto_id,
                    r.nome AS recruiter_nome,
                    p.cliente AS progetto_cliente
                FROM candidati c
                JOIN recruiters r ON c.recruiter_id = r.id
                JOIN progetti p ON c.progetto_id = p.id
                ORDER BY c.candidato_nome ASC
            """)
            candidati = c.fetchall()
    finally:
        conn.close()
    return candidati

def inserisci_candidato(recruiter_id, candidato_nome, data_inserimento, data_placement, data_dimissioni, progetto_id):
    """
    Inserisce un nuovo candidato in MySQL.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO candidati (
                    recruiter_id,
                    candidato_nome,
                    data_inserimento,
                    data_placement,
                    data_dimissioni,
                    progetto_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            c.execute(query, (
                recruiter_id,
                candidato_nome,
                data_inserimento,
                data_placement,
                data_dimissioni,
                progetto_id
            ))
        conn.commit()
    except pymysql.Error as e:
        st.error(f"Errore nell'inserimento del candidato: {e}")
    finally:
        conn.close()

def aggiorna_candidato(candidato_id, recruiter_id, candidato_nome, data_inserimento, data_placement, data_dimissioni, progetto_id):
    """
    Aggiorna un candidato esistente in MySQL.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                UPDATE candidati
                SET recruiter_id = %s,
                    candidato_nome = %s,
                    data_inserimento = %s,
                    data_placement = %s,
                    data_dimissioni = %s,
                    progetto_id = %s
                WHERE id = %s
            """
            c.execute(query, (
                recruiter_id,
                candidato_nome,
                data_inserimento,
                data_placement,
                data_dimissioni,
                progetto_id,
                candidato_id
            ))
        conn.commit()
    except pymysql.Error as e:
        st.error(f"Errore nell'aggiornamento del candidato: {e}")
    finally:
        conn.close()

def elimina_candidato(candidato_id):
    """
    Elimina un candidato da MySQL.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM candidati WHERE id = %s", (candidato_id,))
        conn.commit()
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione del candidato: {e}")
    finally:
        conn.close()

def carica_progetti_dict():
    progetti = carica_progetti()
    progetti_dict = {p['cliente']: p['id'] for p in progetti}
    return progetti_dict

def carica_recruiters_dict():
    recruiters = carica_recruiters()
    recruiters_dict = {r['nome']: r['id'] for r in recruiters}
    return recruiters_dict

def parse_date_input(date_str):
    """Converti una stringa di data in formato 'GG/MM/AAAA' a 'YYYY-MM-DD'."""
    if not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        st.error("Formato data non valido. Usa GG/MM/AAAA.")
        st.stop()

st.title("Gestione Opzioni")

# Carica dati
progetti = carica_progetti()
recruiters = carica_recruiters()
candidati = carica_candidati()

# Crea dizionari per mapping
progetti_dict = carica_progetti_dict()
recruiters_dict = carica_recruiters_dict()

# Creiamo le Tab
tab1, tab2, tab3, tab4 = st.tabs(["Settori", "Project Managers", "Recruiters", "Candidati"])

################################
# TAB 1: Settori
################################
with tab1:
    st.header("Gestione Settori")
    st.write("Funzionalità da implementare.")
    # Puoi implementare la gestione dei settori qui, simile a come gestisci i candidati.

################################
# TAB 2: Project Managers
################################
with tab2:
    st.header("Gestione Project Managers")
    st.write("Funzionalità da implementare.")
    # Puoi implementare la gestione dei Project Managers qui.

################################
# TAB 3: Recruiters
################################
with tab3:
    st.header("Gestione Recruiters")
    st.write("Funzionalità da implementare.")
    # Puoi implementare la gestione dei Recruiters qui.

################################
# TAB 4: Candidati
################################
with tab4:
    st.header("Gestione Candidati")

    # Sottotab: Inserisci o Modifica
    subtab1, subtab2 = st.tabs(["Inserisci Candidato", "Modifica Candidato"])

    # Sottotab 1: Inserisci Candidato
    with subtab1:
        st.subheader("Inserisci Nuovo Candidato")
        with st.form("form_inserisci_candidato"):
            # Recruiter
            recruiters_nomi = list(recruiters_dict.keys())
            recruiter_sel = st.selectbox("Recruiter", recruiters_nomi)
            recruiter_id = recruiters_dict.get(recruiter_sel)

            # Nome Candidato
            candidato_nome = st.text_input("Nome Candidato")

            # Data di Inserimento
            data_inserimento_str = st.text_input("Data di Inserimento (GG/MM/AAAA)", 
                                                value="", 
                                                placeholder="Lascia vuoto se non disponibile")

            # Data di Placement
            data_placement_str = st.text_input("Data di Placement (GG/MM/AAAA)", 
                                               value="", 
                                               placeholder="Lascia vuoto se non disponibile")

            # Data di Dimissioni
            data_dimissioni_str = st.text_input("Data di Dimissioni (GG/MM/AAAA)", 
                                                value="", 
                                                placeholder="Lascia vuoto se non disponibile")

            # Seleziona Progetto
            progetti_nomi = list(progetti_dict.keys())
            progetto_sel = st.selectbox("Seleziona Progetto", progetti_nomi)
            progetto_id = progetti_dict.get(progetto_sel)

            # Pulsante di Submit
            submitted = st.form_submit_button("Inserisci Candidato")
            if submitted:
                if not candidato_nome.strip():
                    st.error("Il campo 'Nome Candidato' è obbligatorio!")
                    st.stop()
                
                # Parsing delle date
                data_inserimento_sql = parse_date_input(data_inserimento_str)
                data_placement_sql = parse_date_input(data_placement_str)
                data_dimissioni_sql = parse_date_input(data_dimissioni_str)

                inserisci_candidato(
                    recruiter_id=recruiter_id,
                    candidato_nome=candidato_nome.strip(),
                    data_inserimento=data_inserimento_sql,
                    data_placement=data_placement_sql,
                    data_dimissioni=data_dimissioni_sql,
                    progetto_id=progetto_id
                )
                st.success("Candidato inserito con successo!")

    # Sottotab 2: Modifica Candidato
    with subtab2:
        st.subheader("Modifica Candidato Esistente")
        if not candidati:
            st.info("Nessun candidato disponibile da modificare.")
        else:
            # Seleziona Candidato da Modificare
            candidati_nomi = [f"{c['candidato_nome']} ({c['recruiter_nome']})" for c in candidati]
            candidato_sel = st.selectbox("Seleziona Candidato da Modificare", candidati_nomi)
            candidato_index = candidati_nomi.index(candidato_sel)
            candidato = candidati[candidato_index]

            with st.form("form_modifica_candidato"):
                # Recruiter
                recruiters_nomi = list(recruiters_dict.keys())
                recruiter_sel_mod = st.selectbox("Recruiter", recruiters_nomi, index=recruiters_nomi.index(candidato['recruiter_nome']))
                recruiter_id_mod = recruiters_dict.get(recruiter_sel_mod)

                # Nome Candidato
                candidato_nome_mod = st.text_input("Nome Candidato", value=candidato['candidato_nome'])

                # Data di Inserimento
                if pd.notna(candidato['data_inserimento']):
                    data_inserimento_val = candidato['data_inserimento'].strftime('%d/%m/%Y')
                else:
                    data_inserimento_val = ""
                data_inserimento_mod = st.text_input("Data di Inserimento (GG/MM/AAAA)", 
                                                    value=data_inserimento_val, 
                                                    placeholder="Lascia vuoto se non disponibile")

                # Data di Placement
                if pd.notna(candidato['data_placement']):
                    data_placement_val = candidato['data_placement'].strftime('%d/%m/%Y')
                else:
                    data_placement_val = ""
                data_placement_mod = st.text_input("Data di Placement (GG/MM/AAAA)", 
                                                   value=data_placement_val, 
                                                   placeholder="Lascia vuoto se non disponibile")

                # Data di Dimissioni
                if pd.notna(candidato['data_dimissioni']):
                    data_dimissioni_val = candidato['data_dimissioni'].strftime('%d/%m/%Y')
                else:
                    data_dimissioni_val = ""
                data_dimissioni_mod = st.text_input("Data di Dimissioni (GG/MM/AAAA)", 
                                                    value=data_dimissioni_val, 
                                                    placeholder="Lascia vuoto se non disponibile")

                # Seleziona Progetto
                progetti_nomi_mod = list(progetti_dict.keys())
                progetto_sel_mod = st.selectbox("Seleziona Progetto", progetti_nomi_mod, index=progetti_nomi_mod.index(candidato['progetto_cliente']))
                progetto_id_mod = progetti_dict.get(progetto_sel_mod)

                # Pulsante di Submit
                submitted_mod = st.form_submit_button("Aggiorna Candidato")
                if submitted_mod:
                    if not candidato_nome_mod.strip():
                        st.error("Il campo 'Nome Candidato' è obbligatorio!")
                        st.stop()
                    
                    # Parsing delle date
                    data_inserimento_sql_mod = parse_date_input(data_inserimento_mod)
                    data_placement_sql_mod = parse_date_input(data_placement_mod)
                    data_dimissioni_sql_mod = parse_date_input(data_dimissioni_mod)

                    aggiorna_candidato(
                        candidato_id=candidato['id'],
                        recruiter_id=recruiter_id_mod,
                        candidato_nome=candidato_nome_mod.strip(),
                        data_inserimento=data_inserimento_sql_mod,
                        data_placement=data_placement_sql_mod,
                        data_dimissioni=data_dimissioni_sql_mod,
                        progetto_id=progetto_id_mod
                    )
                    st.success("Candidato aggiornato con successo!")

            # Elimina Candidato
            st.markdown("---")
            st.subheader("Elimina Candidato")
            with st.form("form_elimina_candidato"):
                conferma = st.checkbox("Confermi di voler eliminare questo candidato?", key="conferma_elimina")
                submitted_del = st.form_submit_button("Elimina Candidato")
                if submitted_del:
                    if conferma:
                        elimina_candidato(candidato['id'])
                        st.success("Candidato eliminato con successo!")
                        # Aggiorna la lista dei candidati
                        candidati = carica_candidati()
                        st.experimental_rerun()
                    else:
                        st.error("Devi confermare l'eliminazione del candidato.")
