# pages/manage_options.py

import streamlit as st
import pymysql
import pandas as pd

####################################
# Funzione di Connessione
####################################
def get_connection():
    try:
        return pymysql.connect(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets["DB_PORT"]),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            cursorclass=pymysql.cursors.DictCursor  # Per avere dizionari anziché tuple
        )
    except pymysql.err.OperationalError as e:
        st.error("Impossibile connettersi al database. Controlla le credenziali e l'accessibilità del database.")
        st.stop()
    except Exception as e:
        st.error(f"Errore inaspettato: {e}")
        st.stop()

####################################
# GESTIONE SETTORI
####################################
def carica_settori():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM settori ORDER BY nome ASC")
            settori = c.fetchall()
    finally:
        conn.close()
    return settori

def inserisci_settore(nome):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO settori (nome) VALUES (%s)", (nome.strip(),))
        conn.commit()
        st.success(f"Settore '{nome}' inserito con successo!")
    except pymysql.IntegrityError:
        st.error(f"Settore '{nome}' già esistente.")
    except Exception as e:
        st.error(f"Errore nell'inserimento del settore: {e}")
    finally:
        conn.close()

def modifica_settore(settore_id, nuovo_nome):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE settori SET nome = %s WHERE id = %s", (nuovo_nome.strip(), settore_id))
        conn.commit()
        st.success(f"Settore aggiornato a '{nuovo_nome}'!")
    except pymysql.IntegrityError:
        st.error(f"Settore '{nuovo_nome}' già esistente.")
    except Exception as e:
        st.error(f"Errore nell'aggiornamento del settore: {e}")
    finally:
        conn.close()

def elimina_settore(settore_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM settori WHERE id = %s", (settore_id,))
        conn.commit()
        st.success("Settore eliminato con successo!")
    except pymysql.IntegrityError as e:
        st.error(f"Errore nell'eliminazione del settore: {e}")
    except Exception as e:
        st.error(f"Errore nell'eliminazione del settore: {e}")
    finally:
        conn.close()

####################################
# GESTIONE PM
####################################
def carica_pm():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
            pm = c.fetchall()
    finally:
        conn.close()
    return pm

def inserisci_pm(nome):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO project_managers (nome) VALUES (%s)", (nome.strip(),))
        conn.commit()
        st.success(f"Project Manager '{nome}' inserito con successo!")
    except pymysql.IntegrityError:
        st.error(f"Project Manager '{nome}' già esistente.")
    except Exception as e:
        st.error(f"Errore nell'inserimento del Project Manager: {e}")
    finally:
        conn.close()

def modifica_pm(pm_id, nuovo_nome):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE project_managers SET nome = %s WHERE id = %s", (nuovo_nome.strip(), pm_id))
        conn.commit()
        st.success(f"Project Manager aggiornato a '{nuovo_nome}'!")
    except pymysql.IntegrityError:
        st.error(f"Project Manager '{nuovo_nome}' già esistente.")
    except Exception as e:
        st.error(f"Errore nell'aggiornamento del Project Manager: {e}")
    finally:
        conn.close()

def elimina_pm(pm_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM project_managers WHERE id = %s", (pm_id,))
        conn.commit()
        st.success("Project Manager eliminato con successo!")
    except pymysql.IntegrityError as e:
        st.error(f"Errore nell'eliminazione del PM: {e}")
    except Exception as e:
        st.error(f"Errore nell'eliminazione del PM: {e}")
    finally:
        conn.close()

####################################
# GESTIONE RECRUITERS
####################################
def carica_recruiters():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM recruiters ORDER BY nome ASC")
            recruiters = c.fetchall()
    finally:
        conn.close()
    return recruiters

def inserisci_recruiter(nome):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO recruiters (nome) VALUES (%s)", (nome.strip(),))
        conn.commit()
        st.success(f"Recruiter '{nome}' inserito con successo!")
    except pymysql.IntegrityError:
        st.error(f"Recruiter '{nome}' già esistente.")
    except Exception as e:
        st.error(f"Errore nell'inserimento del Recruiter: {e}")
    finally:
        conn.close()

def modifica_recruiter(rec_id, nuovo_nome):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE recruiters SET nome = %s WHERE id = %s", (nuovo_nome.strip(), rec_id))
        conn.commit()
        st.success(f"Recruiter aggiornato a '{nuovo_nome}'!")
    except pymysql.IntegrityError:
        st.error(f"Recruiter '{nuovo_nome}' già esistente.")
    except Exception as e:
        st.error(f"Errore nell'aggiornamento del Recruiter: {e}")
    finally:
        conn.close()

def elimina_recruiter(rec_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM recruiters WHERE id = %s", (rec_id,))
        conn.commit()
        st.success("Recruiter eliminato con successo!")
    except pymysql.IntegrityError as e:
        st.error(f"Errore nell'eliminazione del Recruiter: {e}")
    except Exception as e:
        st.error(f"Errore nell'eliminazione del Recruiter: {e}")
    finally:
        conn.close()

####################################
# GESTIONE CAPACITA' PER RECRUITER
####################################
def carica_capacity_recruiter():
    """
    Restituisce [(recruiter_id, recruiter_nome, capacity_max), ...]
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute('''
                SELECT r.id, r.nome,
                       IFNULL(rc.capacity_max, 5) AS capacity_max
                FROM recruiters r
                LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
                ORDER BY r.nome
            ''')
            rows = c.fetchall()
    finally:
        conn.close()
    return rows

def aggiorna_capacity_recruiter(recruiter_id, nuova_capacity):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE recruiter_capacity SET capacity_max = %s WHERE recruiter_id = %s", (nuova_capacity, recruiter_id))
            if c.rowcount == 0:
                c.execute("INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (%s, %s)", (recruiter_id, nuova_capacity))
        conn.commit()
        st.success(f"Capacità per Recruiter ID {recruiter_id} aggiornata a {nuova_capacity}.")
    except Exception as e:
        st.error(f"Errore nell'aggiornamento della capacità: {e}")
    finally:
        conn.close()

############################
# LAYOUT DELLA PAGINA
############################

st.title("Gestione Opzioni")

# Carica dati
settori = carica_settori()
pms = carica_pm()
recruiters = carica_recruiters()

# Crea dizionari per mapping
settori_dict = {s['nome']: s['id'] for s in settori}
pms_dict = {pm['nome']: pm['id'] for pm in pms}
recruiters_dict = {r['nome']: r['id'] for r in recruiters}

# Creiamo le Tab
tab1, tab2, tab3, tab4 = st.tabs(["Settori", "Project Managers", "Recruiters", "Capacità Recruiter"])

###################################
# TAB 1: Gestione Settori
###################################
with tab1:
    st.subheader("Gestione Settori")

    with st.form("form_inserisci_settore"):
        nuovo_settore = st.text_input("Nome nuovo Settore")
        sub_settore = st.form_submit_button("Aggiungi Settore")
        if sub_settore:
            if nuovo_settore.strip():
                inserisci_settore(nuovo_settore)
                settori = carica_settori()  # Ricarica i settori aggiornati
                settori_dict = {s['nome']: s['id'] for s in settori}  # Aggiorna il dizionario
            else:
                st.error("Il nome del settore non può essere vuoto.")
    
    st.write("---")
    st.subheader("Modifica / Elimina Settori Esistenti")
    settori = carica_settori()
    if settori:
        for s in settori:
            s_id, s_nome = s['id'], s['nome']
            with st.expander(f"Settore ID {s_id} - {s_nome}", expanded=False):
                col1, col2 = st.columns([2,1])
                with col1:
                    nuovo_nome = st.text_input(f"Nuovo nome per '{s_nome}'", value=s_nome)
                with col2:
                    btn_mod = st.button("Modifica", key=f"mod_settore_{s_id}")
                    btn_del = st.button("Elimina", key=f"del_settore_{s_id}")
                
                if btn_mod:
                    if nuovo_nome.strip():
                        modifica_settore(s_id, nuovo_nome.strip())
                        settori = carica_settori()  # Ricarica i settori aggiornati
                        settori_dict = {s['nome']: s['id'] for s in settori}  # Aggiorna il dizionario
                    else:
                        st.error("Il nome non può essere vuoto.")
                if btn_del:
                    elimina_settore(s_id)
                    settori = carica_settori()  # Ricarica i settori aggiornati
                    settori_dict = {s['nome']: s['id'] for s in settori}  # Aggiorna il dizionario
    else:
        st.info("Nessun settore presente nel DB.")

###################################
# TAB 2: Gestione Project Managers
###################################
with tab2:
    st.subheader("Gestione Project Managers")

    with st.form("form_inserisci_pm"):
        nuovo_pm = st.text_input("Nome nuovo Project Manager")
        sub_pm = st.form_submit_button("Aggiungi Project Manager")
        if sub_pm:
            if nuovo_pm.strip():
                inserisci_pm(nuovo_pm.strip())
                pms = carica_pm()  # Ricarica i PM aggiornati
                pms_dict = {pm['nome']: pm['id'] for pm in pms}  # Aggiorna il dizionario
            else:
                st.error("Il nome del Project Manager non può essere vuoto.")
    
    st.write("---")
    st.subheader("Modifica / Elimina PM Esistenti")
    pms = carica_pm()
    if pms:
        for pm in pms:
            pm_id, pm_nome = pm['id'], pm['nome']
            with st.expander(f"PM ID {pm_id} - {pm_nome}", expanded=False):
                col1, col2 = st.columns([2,1])
                with col1:
                    nuovo_nome_pm = st.text_input(f"Nuovo nome per '{pm_nome}'", value=pm_nome)
                with col2:
                    btn_mod_pm = st.button("Modifica", key=f"mod_pm_{pm_id}")
                    btn_del_pm = st.button("Elimina", key=f"del_pm_{pm_id}")
                
                if btn_mod_pm:
                    if nuovo_nome_pm.strip():
                        modifica_pm(pm_id, nuovo_nome_pm.strip())
                        pms = carica_pm()  # Ricarica i PM aggiornati
                        pms_dict = {pm['nome']: pm['id'] for pm in pms}  # Aggiorna il dizionario
                    else:
                        st.error("Il campo non può essere vuoto.")
                if btn_del_pm:
                    elimina_pm(pm_id)
                    pms = carica_pm()  # Ricarica i PM aggiornati
                    pms_dict = {pm['nome']: pm['id'] for pm in pms}  # Aggiorna il dizionario
    else:
        st.info("Nessun PM presente nel DB.")

###################################
# TAB 3: Gestione Recruiters
###################################
with tab3:
    st.subheader("Gestione Recruiters")

    with st.form("form_inserisci_recruiter"):
        nuovo_rec = st.text_input("Nome nuovo Recruiter")
        sub_rec = st.form_submit_button("Aggiungi Recruiter")
        if sub_rec:
            if nuovo_rec.strip():
                inserisci_recruiter(nuovo_rec.strip())
                recruiters = carica_recruiters()  # Ricarica i recruiters aggiornati
                recruiters_dict = {r['nome']: r['id'] for r in recruiters}  # Aggiorna il dizionario
            else:
                st.error("Il nome del Recruiter non può essere vuoto.")
    
    st.write("---")
    st.subheader("Modifica / Elimina Recruiters Esistenti")
    recruiters = carica_recruiters()
    if recruiters:
        for r in recruiters:
            rec_id, rec_nome = r['id'], r['nome']
            with st.expander(f"Recruiter ID {rec_id} - {rec_nome}", expanded=False):
                col1, col2 = st.columns([2,1])
                with col1:
                    nuovo_nome_rec = st.text_input(f"Nuovo nome per '{rec_nome}'", value=rec_nome)
                with col2:
                    btn_mod_rec = st.button("Modifica", key=f"mod_rec_{rec_id}")
                    btn_del_rec = st.button("Elimina", key=f"del_rec_{rec_id}")
                
                if btn_mod_rec:
                    if nuovo_nome_rec.strip():
                        modifica_recruiter(rec_id, nuovo_nome_rec.strip())
                        recruiters = carica_recruiters()  # Ricarica i recruiters aggiornati
                        recruiters_dict = {r['nome']: r['id'] for r in recruiters}  # Aggiorna il dizionario
                    else:
                        st.error("Il campo non può essere vuoto.")
                if btn_del_rec:
                    elimina_recruiter(rec_id)
                    recruiters = carica_recruiters()  # Ricarica i recruiters aggiornati
                    recruiters_dict = {r['nome']: r['id'] for r in recruiters}  # Aggiorna il dizionario
    else:
        st.info("Nessun Recruiter presente nel DB.")

###################################
# TAB 4: Capacità Recruiter
###################################
with tab4:
    st.subheader("Gestione Capacità per ogni Recruiter")

    rows = carica_capacity_recruiter()
    if not rows:
        st.info("Nessun recruiter presente nel DB.")
    else:
        for rec in rows:
            rec_id, rec_nome, cap_max = rec['id'], rec['nome'], rec['capacity_max']
            with st.expander(f"Recruiter: {rec_nome} (ID: {rec_id}) - Capacità attuale: {cap_max}"):
                with st.form(f"form_capacita_{rec_id}"):
                    nuova_capacity = st.number_input(f"Nuova capacità per {rec_nome}",
                                                     min_value=1, max_value=999,
                                                     value=int(cap_max), step=1)
                    btn_update = st.form_submit_button("Aggiorna Capacità")
                    if btn_update:
                        aggiorna_capacity_recruiter(rec_id, int(nuova_capacity))
                        st.success(f"Capacità per {rec_nome} aggiornata a {nuova_capacity}.")
