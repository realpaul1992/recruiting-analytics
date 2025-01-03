# pages/manage_options.py

import streamlit as st
import pymysql
import pandas as pd

####################################
# Funzione di Connessione
####################################
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
    except pymysql.Error as e:
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
    except pymysql.Error as e:
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
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione del settore: {e}")
    finally:
        conn.close()

####################################
# GESTIONE Project Managers
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
    except pymysql.Error as e:
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
    except pymysql.Error as e:
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
    except pymysql.Error as e:
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
        
        # Imposta capacity=5 per il nuovo recruiter
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES ((SELECT id FROM recruiters WHERE nome=%s), 5)",
                (nome.strip(),)
            )
        conn.commit()
    except pymysql.IntegrityError:
        st.error(f"Recruiter '{nome}' già esistente.")
    except pymysql.Error as e:
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
    except pymysql.Error as e:
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
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione del Recruiter: {e}")
    finally:
        conn.close()

####################################
# GESTIONE CAPACITÀ PER RECRUITER
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
            # Verifica se esiste già una entry per il recruiter
            c.execute("SELECT * FROM recruiter_capacity WHERE recruiter_id = %s", (recruiter_id,))
            exists = c.fetchone()
            if exists:
                # Aggiorna la capacità esistente
                c.execute("UPDATE recruiter_capacity SET capacity_max = %s WHERE recruiter_id = %s", (nuova_capacity, recruiter_id))
            else:
                # Inserisci una nuova capacità
                c.execute("INSERT INTO recruiter_capacity (recruiter_id, capacity_max) VALUES (%s, %s)", (recruiter_id, nuova_capacity))
        conn.commit()
        st.success("Capacità aggiornata con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'aggiornamento della capacità: {e}")
    finally:
        conn.close()

####################################
# GESTIONE CANDIDATI
####################################
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
                ORDER BY c.id DESC
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def inserisci_candidato(progetto_id, recruiter_id, candidato_nome, data_inserimento, data_placement, data_dimissioni=None):
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
        conn.commit()
        st.success("Candidato inserito con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'inserimento del candidato: {e}")
    finally:
        conn.close()

def modifica_candidato(candidato_id, candidato_nome, progetto_id, recruiter_id, data_inserimento, data_placement, data_dimissioni=None):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                UPDATE candidati
                SET candidato_nome = %s,
                    progetto_id = %s,
                    recruiter_id = %s,
                    data_inserimento = %s,
                    data_placement = %s,
                    data_dimissioni = %s
                WHERE id = %s
            """
            c.execute(query, (
                candidato_nome,
                progetto_id,
                recruiter_id,
                data_inserimento,
                data_placement,
                data_dimissioni,
                candidato_id
            ))
        conn.commit()
        st.success("Candidato aggiornato con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'aggiornamento del candidato: {e}")
    finally:
        conn.close()

def elimina_candidato(candidato_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM candidati WHERE id = %s", (candidato_id,))
        conn.commit()
        st.success("Candidato eliminato con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione del candidato: {e}")
    finally:
        conn.close()

####################################
# GESTIONE RIUNIONI
####################################
def carica_riunioni():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT ri.id, r.nome AS recruiter, ri.data_riunione, ri.partecipato
                FROM riunioni ri
                JOIN recruiters r ON ri.recruiter_id = r.id
                ORDER BY ri.id DESC
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def inserisci_riunione(recruiter_id, data_riunione, partecipato=False):
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
        conn.commit()
        st.success("Riunione inserita con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'inserimento della riunione: {e}")
    finally:
        conn.close()

def modifica_riunione(riunione_id, recruiter_id, data_riunione, partecipato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                UPDATE riunioni
                SET recruiter_id = %s,
                    data_riunione = %s,
                    partecipato = %s
                WHERE id = %s
            """
            c.execute(query, (
                recruiter_id,
                data_riunione,
                partecipato,
                riunione_id
            ))
        conn.commit()
        st.success("Riunione aggiornata con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'aggiornamento della riunione: {e}")
    finally:
        conn.close()

def elimina_riunione(riunione_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM riunioni WHERE id = %s", (riunione_id,))
        conn.commit()
        st.success("Riunione eliminata con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione della riunione: {e}")
    finally:
        conn.close()

####################################
# GESTIONE REFERRALS
####################################
def carica_referrals():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT ref.id, r.nome AS recruiter, ref.cliente_nome, ref.data_referral, ref.stato
                FROM referrals ref
                JOIN recruiters r ON ref.recruiter_id = r.id
                ORDER BY ref.id DESC
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def inserisci_referral(recruiter_id, cliente_nome, data_referral, stato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO referrals (recruiter_id, cliente_nome, data_referral, stato)
                VALUES (%s, %s, %s, %s)
            """
            c.execute(query, (
                recruiter_id,
                cliente_nome.strip(),
                data_referral,
                stato
            ))
        conn.commit()
        st.success("Referral inserito con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'inserimento del referral: {e}")
    finally:
        conn.close()

def modifica_referral(referral_id, recruiter_id, cliente_nome, data_referral, stato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                UPDATE referrals
                SET recruiter_id = %s,
                    cliente_nome = %s,
                    data_referral = %s,
                    stato = %s
                WHERE id = %s
            """
            c.execute(query, (
                recruiter_id,
                cliente_nome.strip(),
                data_referral,
                stato,
                referral_id
            ))
        conn.commit()
        st.success("Referral aggiornato con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'aggiornamento del referral: {e}")
    finally:
        conn.close()

def elimina_referral(referral_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM referrals WHERE id = %s", (referral_id,))
        conn.commit()
        st.success("Referral eliminato con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione del referral: {e}")
    finally:
        conn.close()

####################################
# GESTIONE FORMAZIONE
####################################
def carica_formazione():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT f.id, r.nome AS recruiter, f.corso_nome, f.data_completamento
                FROM formazione f
                JOIN recruiters r ON f.recruiter_id = r.id
                ORDER BY f.id DESC
            """)
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows)

def inserisci_formazione(recruiter_id, corso_nome, data_completamento):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                INSERT INTO formazione (recruiter_id, corso_nome, data_completamento)
                VALUES (%s, %s, %s)
            """
            c.execute(query, (
                recruiter_id,
                corso_nome.strip(),
                data_completamento
            ))
        conn.commit()
        st.success("Formazione inserita con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'inserimento della formazione: {e}")
    finally:
        conn.close()

def modifica_formazione(formazione_id, recruiter_id, corso_nome, data_completamento):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            query = """
                UPDATE formazione
                SET recruiter_id = %s,
                    corso_nome = %s,
                    data_completamento = %s
                WHERE id = %s
            """
            c.execute(query, (
                recruiter_id,
                corso_nome.strip(),
                data_completamento,
                formazione_id
            ))
        conn.commit()
        st.success("Formazione aggiornata con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'aggiornamento della formazione: {e}")
    finally:
        conn.close()

def elimina_formazione(formazione_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM formazione WHERE id = %s", (formazione_id,))
        conn.commit()
        st.success("Formazione eliminata con successo!")
    except pymysql.Error as e:
        st.error(f"Errore nell'eliminazione della formazione: {e}")
    finally:
        conn.close()

####################################
# LAYOUT DELLA PAGINA
####################################
st.title("Gestione Opzioni e Metriche")

# Creiamo le Tab per ogni sezione di gestione
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Settori",
    "Project Managers",
    "Recruiters",
    "Capacità Recruiter",
    "Candidati",
    "Riunioni",
    "Referrals",
    "Formazione"
])

####################################
# TAB 1: Gestione Settori
####################################
with tab1:
    st.subheader("Gestione Settori")

    # Form per inserire un nuovo settore
    with st.form("form_inserisci_settore"):
        nuovo_settore = st.text_input("Nome nuovo Settore")
        sub_settore = st.form_submit_button("Aggiungi Settore")
        if sub_settore:
            if nuovo_settore.strip():
                inserisci_settore(nuovo_settore)
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
                    nuovo_nome = st.text_input(f"Nuovo nome per '{s_nome}'", value=s_nome, key=f"settore_{s_id}")
                with col2:
                    btn_mod = st.button("Modifica", key=f"mod_settore_{s_id}")
                    btn_del = st.button("Elimina", key=f"del_settore_{s_id}")

                if btn_mod:
                    if nuovo_nome.strip():
                        modifica_settore(s_id, nuovo_nome.strip())
                    else:
                        st.error("Il nome non può essere vuoto.")
                if btn_del:
                    elimina_settore(s_id)
    else:
        st.info("Nessun settore presente nel DB.")

####################################
# TAB 2: Gestione Project Managers
####################################
with tab2:
    st.subheader("Gestione Project Managers")

    # Form per inserire un nuovo Project Manager
    with st.form("form_inserisci_pm"):
        nuovo_pm = st.text_input("Nome nuovo Project Manager")
        sub_pm = st.form_submit_button("Aggiungi Project Manager")
        if sub_pm:
            if nuovo_pm.strip():
                inserisci_pm(nuovo_pm.strip())
            else:
                st.error("Il nome del Project Manager non può essere vuoto.")

    st.write("---")
    st.subheader("Modifica / Elimina Project Managers Esistenti")
    pms = carica_pm()
    if pms:
        for pm in pms:
            pm_id, pm_nome = pm['id'], pm['nome']
            with st.expander(f"PM ID {pm_id} - {pm_nome}", expanded=False):
                col1, col2 = st.columns([2,1])
                with col1:
                    nuovo_nome_pm = st.text_input(f"Nuovo nome per '{pm_nome}'", value=pm_nome, key=f"pm_{pm_id}")
                with col2:
                    btn_mod_pm = st.button("Modifica", key=f"mod_pm_{pm_id}")
                    btn_del_pm = st.button("Elimina", key=f"del_pm_{pm_id}")

                if btn_mod_pm:
                    if nuovo_nome_pm.strip():
                        modifica_pm(pm_id, nuovo_nome_pm.strip())
                    else:
                        st.error("Il campo non può essere vuoto.")
                if btn_del_pm:
                    elimina_pm(pm_id)
    else:
        st.info("Nessun Project Manager presente nel DB.")

####################################
# TAB 3: Gestione Recruiters
####################################
with tab3:
    st.subheader("Gestione Recruiters")

    # Form per inserire un nuovo Recruiter
    with st.form("form_inserisci_recruiter"):
        nuovo_rec = st.text_input("Nome nuovo Recruiter")
        sub_rec = st.form_submit_button("Aggiungi Recruiter")
        if sub_rec:
            if nuovo_rec.strip():
                inserisci_recruiter(nuovo_rec.strip())
            else:
                st.error("Il nome del Recruiter non può essere vuoto.")

    st.write("---")
    st.subheader("Modifica / Elimina Recruiters Esistenti")
    rec_list = carica_recruiters()
    if rec_list:
        for r in rec_list:
            rec_id, rec_nome = r['id'], r['nome']
            with st.expander(f"Recruiter ID {rec_id} - {rec_nome}", expanded=False):
                col1, col2 = st.columns([2,1])
                with col1:
                    nuovo_nome_rec = st.text_input(f"Nuovo nome per '{rec_nome}'", value=rec_nome, key=f"rec_{rec_id}")
                with col2:
                    btn_mod_rec = st.button("Modifica", key=f"mod_rec_{rec_id}")
                    btn_del_rec = st.button("Elimina", key=f"del_rec_{rec_id}")

                if btn_mod_rec:
                    if nuovo_nome_rec.strip():
                        modifica_recruiter(rec_id, nuovo_nome_rec.strip())
                    else:
                        st.error("Il campo non può essere vuoto.")
                if btn_del_rec:
                    elimina_recruiter(rec_id)
    else:
        st.info("Nessun Recruiter presente nel DB.")

####################################
# TAB 4: Gestione Capacità Recruiter
####################################
with tab4:
    st.subheader("Gestione Capacità per ogni Recruiter")

    rows = carica_capacity_recruiter()
    if not rows:
        st.info("Nessun recruiter presente nel DB.")
    else:
        for row in rows:
            rec_id, rec_nome, cap_max = row['id'], row['nome'], row['capacity_max']
            with st.expander(f"Recruiter: {rec_nome} (ID: {rec_id}) - Capacità attuale: {cap_max}"):
                with st.form(f"form_capacita_{rec_id}"):
                    nuova_capacity = st.number_input(
                        f"Nuova capacità per {rec_nome}",
                        min_value=1,
                        max_value=999,
                        value=int(cap_max),
                        step=1,
                        key=f"cap_input_{rec_id}"
                    )
                    btn_update = st.form_submit_button("Aggiorna Capacità")
                    if btn_update:
                        aggiorna_capacity_recruiter(rec_id, int(nuova_capacity))

####################################
# TAB 5: Gestione Candidati
####################################
with tab5:
    st.subheader("Gestione Candidati")

    # Form per inserire un nuovo candidato
    with st.form("form_inserisci_candidato"):
        # Carica progetti
        conn = get_connection()
        try:
            with conn.cursor() as c:
                c.execute("SELECT id, cliente FROM progetti ORDER BY cliente ASC")
                progetti = c.fetchall()
        finally:
            conn.close()

        progetti_nomi = [f"{p['cliente']} (ID: {p['id']})" for p in progetti]
        progetto_sel = st.selectbox("Seleziona Progetto", progetti_nomi, key="candidato_progetto")
        progetto_id = int(progetto_sel.split("ID: ")[1].strip(")")) if progetto_sel else None

        # Carica recruiters
        recruiters = carica_recruiters()
        recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
        recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi, key="candidato_recruiter")
        recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

        candidato_nome = st.text_input("Nome Candidato", key="candidato_nome")
        data_inserimento = st.date_input("Data di Inserimento", value=pd.to_datetime("today"), key="candidato_data_inserimento")
        data_placement = st.date_input("Data di Placement", value=pd.to_datetime("today"), key="candidato_data_placement")
        data_dimissioni = st.date_input("Data di Dimissioni (Lascia vuoto se ancora in posizione)", value=None, key="candidato_data_dimissioni")

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
                data_inserimento_sql = data_inserimento.strftime('%Y-%m-%d')
                data_placement_sql = data_placement.strftime('%Y-%m-%d')
                data_dimissioni_sql = data_dimissioni.strftime('%Y-%m-%d') if data_dimissioni else None

                inserisci_candidato(progetto_id, recruiter_id, candidato_nome.strip(), data_inserimento_sql, data_placement_sql, data_dimissioni_sql)

    st.write("---")
    st.subheader("Modifica / Elimina Candidati Esistenti")
    candidati_df = carica_candidati()
    if not candidati_df.empty:
        st.dataframe(candidati_df)
        st.write("**Attenzione:** Per modificare o eliminare un candidato, cerca l'ID corrispondente.")

        candidato_id = st.number_input("Inserisci ID del Candidato da Modificare/Eliminare", min_value=1, step=1, key="candidato_id_input")
        azione_candidato = st.selectbox("Seleziona Azione", ["Modifica", "Elimina"], key="candidato_azione")

        if azione_candidato == "Modifica":
            # Trova il candidato
            candidato = candidati_df[candidati_df['id'] == candidato_id]
            if not candidato.empty:
                candidato = candidato.iloc[0]
                with st.form("form_modifica_candidato"):
                    nuovo_nome = st.text_input("Nome Candidato", value=candidato['candidato_nome'], key="mod_candidato_nome")
                    
                    # Carica progetti
                    progetti_nomi_mod = [f"{p['cliente']} (ID: {p['id']})" for p in progetti]
                    progetto_sel_mod = st.selectbox("Seleziona Progetto", progetti_nomi_mod, index=[p['id'] for p in progetti].index(candidato['progetto_id']), key="mod_candidato_progetto")
                    progetto_id_mod = int(progetto_sel_mod.split("ID: ")[1].strip(")")) if progetto_sel_mod else None

                    # Carica recruiters
                    recruiter_sel_mod = st.selectbox("Seleziona Recruiter", recruiter_nomi, index=[r['id'] for r in recruiters].index(candidato['recruiter_id']), key="mod_candidato_recruiter")
                    recruiter_id_mod = int(recruiter_sel_mod.split("ID: ")[1].strip(")")) if recruiter_sel_mod else None

                    data_inserimento_mod = st.date_input("Data di Inserimento", value=pd.to_datetime(candidato['data_inserimento']), key="mod_candidato_data_inserimento")
                    data_placement_mod = st.date_input("Data di Placement", value=pd.to_datetime(candidato['data_placement']), key="mod_candidato_data_placement")
                    data_dimissioni_mod = st.date_input("Data di Dimissioni (Lascia vuoto se ancora in posizione)", value=pd.to_datetime(candidato['data_dimissioni']) if pd.notnull(candidato['data_dimissioni']) else None, key="mod_candidato_data_dimissioni")

                    submitted_mod = st.form_submit_button("Aggiorna Candidato")
                    if submitted_mod:
                        if not nuovo_nome.strip():
                            st.error("Il campo 'Nome Candidato' è obbligatorio!")
                        elif progetto_id_mod is None:
                            st.error("Selezionare un Progetto.")
                        elif recruiter_id_mod is None:
                            st.error("Selezionare un Recruiter.")
                        elif data_inserimento_mod > data_placement_mod:
                            st.error("La 'Data di Placement' non può essere precedente alla 'Data di Inserimento'.")
                        elif data_dimissioni_mod and data_dimissioni_mod < data_placement_mod:
                            st.error("La 'Data di Dimissioni' non può essere precedente alla 'Data di Placement'.")
                        else:
                            data_inserimento_sql_mod = data_inserimento_mod.strftime('%Y-%m-%d')
                            data_placement_sql_mod = data_placement_mod.strftime('%Y-%m-%d')
                            data_dimissioni_sql_mod = data_dimissioni_mod.strftime('%Y-%m-%d') if data_dimissioni_mod else None

                            modifica_candidato(
                                candidato_id,
                                nuovo_nome.strip(),
                                progetto_id_mod,
                                recruiter_id_mod,
                                data_inserimento_sql_mod,
                                data_placement_sql_mod,
                                data_dimissioni_sql_mod
                            )
            else:
                st.error(f"Nessun candidato trovato con ID {candidato_id}.")
        elif azione_candidato == "Elimina":
            conferma = st.checkbox(f"Sei sicuro di voler eliminare il candidato con ID {candidato_id}?", key="conferma_elimina_candidato")
            if conferma:
                elimina_candidato(candidato_id)
    else:
        st.info("Nessun candidato presente nel DB.")

####################################
# TAB 6: Gestione Riunioni
####################################
with tab6:
    st.subheader("Gestione Riunioni")

    # Form per inserire una nuova riunione
    with st.form("form_inserisci_riunione"):
        recruiters = carica_recruiters()
        recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
        recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi, key="riunione_recruiter")
        recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

        data_riunione = st.date_input("Data della Riunione", value=pd.to_datetime("today"), key="riunione_data")
        partecipato = st.checkbox("Ha partecipato", key="riunione_partecipato")

        submitted = st.form_submit_button("Inserisci Riunione")
        if submitted:
            if recruiter_id is None:
                st.error("Selezionare un Recruiter.")
            elif not data_riunione:
                st.error("Il campo 'Data della Riunione' è obbligatorio!")
            else:
                data_riunione_sql = data_riunione.strftime('%Y-%m-%d')
                inserisci_riunione(recruiter_id, data_riunione_sql, partecipato)

    st.write("---")
    st.subheader("Modifica / Elimina Riunioni Esistenti")
    riunioni_df = carica_riunioni()
    if not riunioni_df.empty:
        st.dataframe(riunioni_df)
        st.write("**Attenzione:** Per modificare o eliminare una riunione, cerca l'ID corrispondente.")

        riunione_id = st.number_input("Inserisci ID della Riunione da Modificare/Eliminare", min_value=1, step=1, key="riunione_id_input")
        azione_riunione = st.selectbox("Seleziona Azione", ["Modifica", "Elimina"], key="riunione_azione")

        if azione_riunione == "Modifica":
            # Trova la riunione
            riunione = riunioni_df[riunioni_df['id'] == riunione_id]
            if not riunione.empty:
                riunione = riunione.iloc[0]
                with st.form("form_modifica_riunione"):
                    # Carica recruiters
                    recruiter_sel_mod = st.selectbox("Seleziona Recruiter", recruiter_nomi, index=[r['id'] for r in recruiters].index(riunione['recruiter_id']), key="mod_riunione_recruiter")
                    recruiter_id_mod = int(recruiter_sel_mod.split("ID: ")[1].strip(")")) if recruiter_sel_mod else None

                    data_riunione_mod = st.date_input("Data della Riunione", value=pd.to_datetime(riunione['data_riunione']), key="mod_riunione_data")
                    partecipato_mod = st.checkbox("Ha partecipato", value=riunione['partecipato'], key="mod_riunione_partecipato")

                    submitted_mod = st.form_submit_button("Aggiorna Riunione")
                    if submitted_mod:
                        if recruiter_id_mod is None:
                            st.error("Selezionare un Recruiter.")
                        elif not data_riunione_mod:
                            st.error("Il campo 'Data della Riunione' è obbligatorio!")
                        else:
                            data_riunione_sql_mod = data_riunione_mod.strftime('%Y-%m-%d')
                            modifica_riunione(
                                riunione_id,
                                recruiter_id_mod,
                                data_riunione_sql_mod,
                                partecipato_mod
                            )
            else:
                st.error(f"Nessuna riunione trovata con ID {riunione_id}.")
        elif azione_riunione == "Elimina":
            conferma = st.checkbox(f"Sei sicuro di voler eliminare la riunione con ID {riunione_id}?", key="conferma_elimina_riunione")
            if conferma:
                elimina_riunione(riunione_id)
    else:
        st.info("Nessuna riunione presente nel DB.")

####################################
# TAB 7: Gestione Referrals
####################################
with tab7:
    st.subheader("Gestione Referrals")

    # Form per inserire un nuovo referral
    with st.form("form_inserisci_referral"):
        recruiters = carica_recruiters()
        recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
        recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi, key="referral_recruiter")
        recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

        cliente_nome = st.text_input("Nome del Nuovo Cliente", key="referral_cliente")
        data_referral = st.date_input("Data del Referral", value=pd.to_datetime("today"), key="referral_data")
        stato = st.selectbox("Stato del Referral", ["In corso", "Chiuso"], key="referral_stato")

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
                data_referral_sql = data_referral.strftime('%Y-%m-%d')
                inserisci_referral(recruiter_id, cliente_nome.strip(), data_referral_sql, stato)

    st.write("---")
    st.subheader("Modifica / Elimina Referrals Esistenti")
    referrals_df = carica_referrals()
    if not referrals_df.empty:
        st.dataframe(referrals_df)
        st.write("**Attenzione:** Per modificare o eliminare un referral, cerca l'ID corrispondente.")

        referral_id = st.number_input("Inserisci ID del Referral da Modificare/Eliminare", min_value=1, step=1, key="referral_id_input")
        azione_referral = st.selectbox("Seleziona Azione", ["Modifica", "Elimina"], key="referral_azione")

        if azione_referral == "Modifica":
            # Trova il referral
            referral = referrals_df[referrals_df['id'] == referral_id]
            if not referral.empty:
                referral = referral.iloc[0]
                with st.form("form_modifica_referral"):
                    # Carica recruiters
                    recruiter_sel_mod = st.selectbox("Seleziona Recruiter", recruiter_nomi, index=[r['id'] for r in recruiters].index(referral['recruiter_id']), key="mod_referral_recruiter")
                    recruiter_id_mod = int(recruiter_sel_mod.split("ID: ")[1].strip(")")) if recruiter_sel_mod else None

                    cliente_nome_mod = st.text_input("Nome del Nuovo Cliente", value=referral['cliente_nome'], key="mod_referral_cliente")
                    data_referral_mod = st.date_input("Data del Referral", value=pd.to_datetime(referral['data_referral']), key="mod_referral_data")
                    stato_mod = st.selectbox("Stato del Referral", ["In corso", "Chiuso"], index=["In corso", "Chiuso"].index(referral['stato']), key="mod_referral_stato")

                    submitted_mod = st.form_submit_button("Aggiorna Referral")
                    if submitted_mod:
                        if recruiter_id_mod is None:
                            st.error("Selezionare un Recruiter.")
                        elif not cliente_nome_mod.strip():
                            st.error("Il campo 'Nome del Nuovo Cliente' è obbligatorio!")
                        elif not data_referral_mod:
                            st.error("Il campo 'Data del Referral' è obbligatorio!")
                        elif not stato_mod:
                            st.error("Il campo 'Stato del Referral' è obbligatorio!")
                        else:
                            data_referral_sql_mod = data_referral_mod.strftime('%Y-%m-%d')
                            modifica_referral(
                                referral_id,
                                recruiter_id_mod,
                                cliente_nome_mod.strip(),
                                data_referral_sql_mod,
                                stato_mod
                            )
            else:
                st.error(f"Nessun referral trovato con ID {referral_id}.")
        elif azione_referral == "Elimina":
            conferma = st.checkbox(f"Sei sicuro di voler eliminare il referral con ID {referral_id}?", key="conferma_elimina_referral")
            if conferma:
                elimina_referral(referral_id)
    else:
        st.info("Nessun referral presente nel DB.")

####################################
# TAB 8: Gestione Formazione
####################################
with tab8:
    st.subheader("Gestione Formazione")

    # Form per inserire una nuova formazione
    with st.form("form_inserisci_formazione"):
        recruiters = carica_recruiters()
        recruiter_nomi = [f"{r['nome']} (ID: {r['id']})" for r in recruiters]
        recruiter_sel = st.selectbox("Seleziona Recruiter", recruiter_nomi, key="formazione_recruiter")
        recruiter_id = int(recruiter_sel.split("ID: ")[1].strip(")")) if recruiter_sel else None

        corso_nome = st.text_input("Nome del Corso", key="formazione_corso")
        data_completamento = st.date_input("Data di Completamento", value=pd.to_datetime("today"), key="formazione_data")

        submitted = st.form_submit_button("Inserisci Formazione")
        if submitted:
            if recruiter_id is None:
                st.error("Selezionare un Recruiter.")
            elif not corso_nome.strip():
                st.error("Il campo 'Nome del Corso' è obbligatorio!")
            elif not data_completamento:
                st.error("Il campo 'Data di Completamento' è obbligatorio!")
            else:
                data_completamento_sql = data_completamento.strftime('%Y-%m-%d')
                inserisci_formazione(recruiter_id, corso_nome.strip(), data_completamento_sql)

    st.write("---")
    st.subheader("Modifica / Elimina Formazioni Esistenti")
    formazione_df = carica_formazione()
    if not formazione_df.empty:
        st.dataframe(formazione_df)
        st.write("**Attenzione:** Per modificare o eliminare una formazione, cerca l'ID corrispondente.")

        formazione_id = st.number_input("Inserisci ID della Formazione da Modificare/Eliminare", min_value=1, step=1, key="formazione_id_input")
        azione_formazione = st.selectbox("Seleziona Azione", ["Modifica", "Elimina"], key="formazione_azione")

        if azione_formazione == "Modifica":
            # Trova la formazione
            formazione = formazione_df[formazione_df['id'] == formazione_id]
            if not formazione.empty:
                formazione = formazione.iloc[0]
                with st.form("form_modifica_formazione"):
                    # Carica recruiters
                    recruiter_sel_mod = st.selectbox("Seleziona Recruiter", recruiter_nomi, index=[r['id'] for r in recruiters].index(formazione['recruiter_id']), key="mod_formazione_recruiter")
                    recruiter_id_mod = int(recruiter_sel_mod.split("ID: ")[1].strip(")")) if recruiter_sel_mod else None

                    corso_nome_mod = st.text_input("Nome del Corso", value=formazione['corso_nome'], key="mod_formazione_corso")
                    data_completamento_mod = st.date_input("Data di Completamento", value=pd.to_datetime(formazione['data_completamento']), key="mod_formazione_data")

                    submitted_mod = st.form_submit_button("Aggiorna Formazione")
                    if submitted_mod:
                        if recruiter_id_mod is None:
                            st.error("Selezionare un Recruiter.")
                        elif not corso_nome_mod.strip():
                            st.error("Il campo 'Nome del Corso' è obbligatorio!")
                        elif not data_completamento_mod:
                            st.error("Il campo 'Data di Completamento' è obbligatorio!")
                        else:
                            data_completamento_sql_mod = data_completamento_mod.strftime('%Y-%m-%d')
                            modifica_formazione(
                                formazione_id,
                                recruiter_id_mod,
                                corso_nome_mod.strip(),
                                data_completamento_sql_mod
                            )
            else:
                st.error(f"Nessuna formazione trovata con ID {formazione_id}.")
        elif azione_formazione == "Elimina":
            conferma = st.checkbox(f"Sei sicuro di voler eliminare la formazione con ID {formazione_id}?", key="conferma_elimina_formazione")
            if conferma:
                elimina_formazione(formazione_id)
    else:
        st.info("Nessuna formazione presente nel DB.")
