# app.py

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

# Funzioni per Settori
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

# Funzioni per Project Managers
def carica_project_managers():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, nome FROM project_managers ORDER BY nome ASC")
            project_managers = c.fetchall()
    finally:
        conn.close()
    return project_managers

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

# Funzioni per Recruiters
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

# Funzioni per Capacità Recruiter
def carica_capacity_recruiter():
    """
    Restituisce un DataFrame con recruiter e la loro capacità.
    """
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute('''
                SELECT r.id, r.nome AS sales_recruiter,
                       IFNULL(rc.capacity_max, 5) AS capacity_max
                FROM recruiters r
                LEFT JOIN recruiter_capacity rc ON r.id = rc.recruiter_id
                ORDER BY r.nome
            ''')
            rows = c.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=['id', 'sales_recruiter', 'capacity_max'])

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

# Funzioni per Riunioni
def carica_riunioni():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, recruiter_id, data_riunione, partecipato FROM riunioni ORDER BY data_riunione DESC")
            riunioni = c.fetchall()
    except pymysql.err.ProgrammingError as e:
        st.error(f"Errore nella query delle riunioni: {e}")
        riunioni = []
    finally:
        conn.close()
    return riunioni

def inserisci_riunione(recruiter_id, data_riunione, partecipato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO riunioni (recruiter_id, data_riunione, partecipato)
                VALUES (%s, %s, %s)
            """, (recruiter_id, data_riunione, partecipato))
        conn.commit()
        st.success("Riunione inserita con successo!")
    except Exception as e:
        st.error(f"Errore nell'inserimento della riunione: {e}")
    finally:
        conn.close()

def modifica_riunione(riunione_id, recruiter_id, data_riunione, partecipato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                UPDATE riunioni
                SET recruiter_id = %s, data_riunione = %s, partecipato = %s
                WHERE id = %s
            """, (recruiter_id, data_riunione, partecipato, riunione_id))
        conn.commit()
        st.success("Riunione aggiornata con successo!")
    except Exception as e:
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
    except Exception as e:
        st.error(f"Errore nell'eliminazione della riunione: {e}")
    finally:
        conn.close()

# Funzioni per Referrals
def carica_referrals():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, recruiter_id, cliente_nome, data_referral, stato FROM referrals ORDER BY data_referral DESC")
            referrals = c.fetchall()
    finally:
        conn.close()
    return referrals

def inserisci_referral(recruiter_id, cliente_nome, data_referral, stato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO referrals (recruiter_id, cliente_nome, data_referral, stato)
                VALUES (%s, %s, %s, %s)
            """, (recruiter_id, cliente_nome.strip(), data_referral, stato))
        conn.commit()
        st.success("Referral inserito con successo!")
    except Exception as e:
        st.error(f"Errore nell'inserimento del referral: {e}")
    finally:
        conn.close()

def modifica_referral(referral_id, recruiter_id, cliente_nome, data_referral, stato):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                UPDATE referrals
                SET recruiter_id = %s, cliente_nome = %s, data_referral = %s, stato = %s
                WHERE id = %s
            """, (recruiter_id, cliente_nome.strip(), data_referral, stato, referral_id))
        conn.commit()
        st.success("Referral aggiornato con successo!")
    except Exception as e:
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
    except Exception as e:
        st.error(f"Errore nell'eliminazione del referral: {e}")
    finally:
        conn.close()

# Funzioni per Formazione
def carica_formazione():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, recruiter_id, corso_nome, data_completamento FROM formazione ORDER BY data_completamento DESC")
            formazione = c.fetchall()
    finally:
        conn.close()
    return formazione

def inserisci_formazione(recruiter_id, corso_nome, data_completamento):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO formazione (recruiter_id, corso_nome, data_completamento)
                VALUES (%s, %s, %s)
            """, (recruiter_id, corso_nome.strip(), data_completamento))
        conn.commit()
        st.success("Formazione inserita con successo!")
    except Exception as e:
        st.error(f"Errore nell'inserimento della formazione: {e}")
    finally:
        conn.close()

def modifica_formazione(formazione_id, recruiter_id, corso_nome, data_completamento):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                UPDATE formazione
                SET recruiter_id = %s, corso_nome = %s, data_completamento = %s
                WHERE id = %s
            """, (recruiter_id, corso_nome.strip(), data_completamento, formazione_id))
        conn.commit()
        st.success("Formazione aggiornata con successo!")
    except Exception as e:
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
    except Exception as e:
        st.error(f"Errore nell'eliminazione della formazione: {e}")
    finally:
        conn.close()

# Funzioni per Leaderboard Settings (opzionale, se vuoi gestire pesi dinamici)
def get_leaderboard_settings():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT setting_name, setting_value FROM leaderboard_settings")
            settings = c.fetchall()
        settings_dict = {setting['setting_name']: setting['setting_value'] for setting in settings}
    finally:
        conn.close()
    return settings_dict

def update_leaderboard_setting(setting_name, setting_value):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO leaderboard_settings (setting_name, setting_value)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """, (setting_name, setting_value))
        conn.commit()
        st.success(f"Impostazione '{setting_name}' aggiornata a {setting_value}.")
    except Exception as e:
        st.error(f"Errore nell'aggiornamento della impostazione: {e}")
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
                tables = c.fetchall()

                st.info("Inizio backup MySQL in ZIP...")

                for table in tables:
                    table_name = list(table.values())[0]
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

        except pymysql.Error as e:
            st.error(f"Errore durante il backup: {e}")
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

        except pymysql.Error as e:
            st.error(f"Errore nel ripristino del database: {e}")
            conn.rollback()
        finally:
            conn.commit()
            conn.close()
    
    st.success("Ripristino completato con successo da ZIP.")

#######################################
# FUNZIONE PER CALCOLARE LEADERBOARD MENSILE
#######################################
def calcola_leaderboard_mensile(df, start_date, end_date, settings):
    """
    Calcola la leaderboard basata su vari criteri di punteggio.
    Utilizza i settings forniti per i pesi e le soglie.
    """
    # Filtra i progetti completati nel periodo
    df_temp = df.copy()
    df_temp['data_inizio_dt'] = pd.to_datetime(df_temp['data_inizio'], errors='coerce')
    df_temp['recensione_stelle'] = df_temp['recensione_stelle'].fillna(0).astype(int)

    # Bonus da recensioni
    df_temp['bonus_recensione'] = df_temp['recensione_stelle'].apply(
        lambda x: settings.get('points_per_bonus_review_5', 500) if x == 5 else (
            settings.get('points_per_bonus_review_4', 300) if x == 4 else 0
        )
    )

    # Punti per progetto completato
    df_temp['punti_completato'] = settings.get('points_per_project_completed', 10)

    # Punti per completamento rapido
    df_temp['giorni_completamento'] = (pd.to_datetime(df_temp['data_fine']) - df_temp['data_inizio_dt']).dt.days
    df_temp['bonus_completamento'] = df_temp['giorni_completamento'].apply(
        lambda x: settings.get('points_per_fast_completion', 50) if x < 60 else 0
    )

    # Filtro progetti completati nel periodo
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

    # Calcola completati e tempo medio
    group = df_filtro.groupby('sales_recruiter')
    completati = group.size().reset_index(name='completati')
    tempo_medio = group['tempo_totale'].mean().reset_index(name='tempo_medio')
    bonus_recensione = group['bonus_recensione'].sum().reset_index(name='bonus_totale')
    bonus_completamento = group['bonus_completamento'].sum().reset_index(name='bonus_completamento')

    # Merge tutti i bonus
    leaderboard = completati.merge(tempo_medio, on='sales_recruiter', how='left')
    leaderboard = leaderboard.merge(bonus_recensione, on='sales_recruiter', how='left')
    leaderboard = leaderboard.merge(bonus_completamento, on='sales_recruiter', how='left')

    # Calcola punteggio totale
    leaderboard['punteggio'] = (
        leaderboard['completati'] * settings.get('points_per_project_completed', 10) +
        leaderboard['bonus_totale'] +
        leaderboard['bonus_completamento']
    )

    # Assegna badge
    def assegna_badge(punteggio):
        if punteggio >= settings.get('badge_gold_threshold', 10000):
            return "Gold"
        elif punteggio >= settings.get('badge_silver_threshold', 5000):
            return "Silver"
        elif punteggio >= settings.get('badge_bronze_threshold', 2000):
            return "Bronze"
        return "Grey"

    leaderboard['badge'] = leaderboard['punteggio'].apply(assegna_badge)

    # Ordina per punteggio
    leaderboard = leaderboard.sort_values('punteggio', ascending=False)

    return leaderboard

#######################################
# CONFIG E LAYOUT
#######################################
STATO_REFERRAL_OPTIONS = ["In Attesa", "Accettato", "Rifiutato"]
PARTICIPATO_OPTIONS = [True, False]

STATO_PROGETTO = ["Completato", "In corso", "Bloccato"]

# Carichiamo i riferimenti
settori_db = carica_settori()
pm_db = carica_project_managers()
rec_db = carica_recruiters()

st.title("Gestione Progetti di Recruiting")
st.sidebar.title("Navigazione")
scelta = st.sidebar.radio("Vai a", ["Inserisci Dati", "Dashboard", "Gestisci Opzioni", "Gestisci Classifica"])

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
        
        # Data di Inizio
        data_inizio_str = st.text_input("Data di Inizio (GG/MM/AAAA)", 
                                        value="", 
                                        placeholder="Lascia vuoto se non disponibile")

        # Tempo Previsto
        tempo_previsto = st.number_input("Tempo Previsto (giorni)", min_value=0, step=1, value=0)

        # Pulsante di Submit
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
                    title='Tempo Medio di Chiusura per Recruiter',
                    color='tempo_totale',  # Aggiunta di colore per stile
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
                df_capacity = carica_capacity_recruiter()
                recruiters_unici = df['sales_recruiter'].unique()
                cap_df = pd.DataFrame({'sales_recruiter': recruiters_unici})
                cap_df = cap_df.merge(attivi_count, on='sales_recruiter', how='left').fillna(0)
                cap_df = cap_df.merge(df_capacity, on='sales_recruiter', how='left').fillna(5)
                cap_df['capacity_max'] = cap_df['capacity_max'].astype(int)
                cap_df['Progetti Attivi'] = cap_df['Progetti Attivi'].astype(int)
                cap_df['Capacità Disponibile'] = cap_df['capacity_max'] - cap_df['Progetti Attivi']
                cap_df.loc[cap_df['Capacità Disponibile'] < 0, 'Capacità Disponibile'] = 0

                overcap = cap_df[cap_df['Capacità Disponibile'] == 0]
                if not overcap.empty:
                    st.warning("Attenzione! I seguenti Recruiter sono a capacità 0:")
                    st.write(overcap[['sales_recruiter','Progetti Attivi','capacity_max','Capacità Disponibile']])

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
                df_capacity = carica_capacity_recruiter()
                df_attivi = df[df['stato_progetto'].isin(["In corso","Bloccato"])]
                attivi_count = df_attivi.groupby('sales_recruiter').size().reset_index(name='Progetti Attivi')

                rec_df = df_capacity.merge(attivi_count, on='sales_recruiter', how='left').fillna(0)
                rec_df['Progetti Attivi'] = rec_df['Progetti Attivi'].astype(int)
                rec_df = rec_df.merge(closings, on='sales_recruiter', how='left').fillna(0)
                rec_df['progetti_che_chiudono'] = rec_df['progetti_che_chiudono'].astype(int)

                rec_df['Nuovi Attivi'] = rec_df['Progetti Attivi'] - rec_df['progetti_che_chiudono']
                rec_df.loc[rec_df['Nuovi Attivi'] < 0, 'Nuovi Attivi'] = 0
                rec_df['Capacità Disponibile'] = rec_df['capacity_max'] - rec_df['Nuovi Attivi']
                rec_df.loc[rec_df['Capacità Disponibile'] < 0, 'Capacità Disponibile'] = 0

                st.dataframe(rec_df[['sales_recruiter','capacity_max','Progetti Attivi','progetti_che_chiudono','Nuovi Attivi','Capacità Disponibile']])
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

            # Calcola il bonus totale per ogni recruiter
            settings = get_leaderboard_settings()
            leaderboard_df = calcola_leaderboard_mensile(
                df=df,
                start_date=start_date_bonus,
                end_date=end_date_bonus,
                settings=settings
            )

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
                    title='Leaderboard Annuale',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "Grey": "grey"  # Colore di default per badge vuoti
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

                st.markdown("""
                **Formula Punteggio**  
                - +10 punti ogni progetto completato  
                - +300 punti per ogni recensione a 4 stelle  
                - +500 punti per ogni recensione a 5 stelle  
                - +50 punti per ogni progetto completato in meno di 60 giorni  
                """)

                st.markdown("""
                **Badge**  
                - **Gold:** Punteggio >= 10000  
                - **Silver:** Punteggio >= 5000  
                - **Bronze:** Punteggio >= 2000  
                - **Grey:** Altri punteggi  
                """)

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

            # Recupera le impostazioni correnti
            settings = get_leaderboard_settings()

            leaderboard_df = calcola_leaderboard_mensile(
                df=df_leader_filtered,
                start_date=start_date_leader,
                end_date=end_date_leader,
                settings=settings
            )
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
                    title='Leaderboard Annuale',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "Grey": "grey"
                    }
                )
                st.plotly_chart(fig_leader, use_container_width=True)

                st.markdown("""
                **Formula Punteggio**  
                - +10 punti ogni progetto completato  
                - +300 punti per ogni recensione a 4 stelle  
                - +500 punti per ogni recensione a 5 stelle  
                - +50 punti per ogni progetto completato in meno di 60 giorni  
                """)

                st.markdown("""
                **Badge**  
                - **Gold:** Punteggio >= 10000  
                - **Silver:** Punteggio >= 5000  
                - **Bronze:** Punteggio >= 2000  
                - **Grey:** Altri punteggi  
                """)

            ################################
            # Grafici nella Classifica
            ################################
            if not leaderboard_df.empty:
                st.subheader("Grafici della Classifica")

                # **1) Leaderboard Totale**
                st.markdown("**1) Leaderboard Totale**")
                fig1 = px.bar(
                    leaderboard_df,
                    x='sales_recruiter',
                    y='punteggio',
                    color='badge',
                    title='Punteggio Totale per Recruiter',
                    color_discrete_map={
                        "Gold": "gold",
                        "Silver": "silver",
                        "Bronze": "brown",
                        "Grey": "grey"
                    }
                )
                st.plotly_chart(fig1, use_container_width=True)

                # **2) Recruiter più veloce (Tempo Medio)**
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
                    fig2 = px.bar(
                        veloce,
                        x='tempo_totale',
                        y='sales_recruiter',
                        orientation='h',
                        labels={'tempo_totale': 'Tempo Medio (giorni)', 'sales_recruiter': 'Recruiter'},
                        title='Tempo Medio di Chiusura per Recruiter',
                        color='tempo_totale',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # **3) Recruiter con più Bonus ottenuti** (Recensioni)
                st.markdown("**3) Recruiter con più Bonus ottenuti** (Recensioni)")
                df_bonus = df_leader_filtered.copy()
                df_bonus['bonus'] = df_bonus['recensione_stelle'].apply(lambda x: calcola_bonus(x))
                bonus_df = df_bonus.groupby('sales_recruiter')['bonus'].sum().reset_index()
                bonus_df = bonus_df.sort_values(by='bonus', ascending=False)
                if bonus_df.empty:
                    st.info("Nessun bonus calcolato.")
                else:
                    fig3 = px.bar(
                        bonus_df,
                        x='bonus',
                        y='sales_recruiter',
                        orientation='h',
                        labels={'bonus': 'Bonus Totale (€)', 'sales_recruiter': 'Recruiter'},
                        title='Bonus Totale Ottenuto per Recruiter',
                        color='bonus',
                        color_continuous_scale='Oranges'
                    )
                    st.plotly_chart(fig3, use_container_width=True)

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
# 4. GESTISCI CLASSIFICA (OPZIONALE)
#######################################
# Puoi implementare una sezione separata per gestire le impostazioni della classifica
# Se desideri mantenere questa funzionalità nel `app.py`, puoi aggiungerla qui

#######################################
# 5. GESTIONE AVANZATA (Nuova Sezione "Gestione")
#######################################
elif scelta == "Gestisci Classifica":
    st.header("Gestione Classifica (Leaderboard)")

    # Recupera le impostazioni attuali
    settings = get_leaderboard_settings()
    
    st.subheader("Impostazioni Correnti")
    for key, value in settings.items():
        st.write(f"**{key.replace('_', ' ').capitalize()}**: {value}")
    
    st.write("---")
    st.subheader("Aggiorna Impostazioni della Classifica")
    
    # Form per aggiornare le impostazioni
    with st.form("form_gestisci_leaderboard"):
        points_per_project_completed = st.number_input(
            "Punti per Progetto Completato",
            min_value=0,
            step=1,
            value=float(settings.get('points_per_project_completed', 10))
        )
        
        points_per_bonus_review_4 = st.number_input(
            "Punti per Recensione a 4 Stelle",
            min_value=0,
            step=100,
            value=float(settings.get('points_per_bonus_review_4', 300))
        )
        
        points_per_bonus_review_5 = st.number_input(
            "Punti per Recensione a 5 Stelle",
            min_value=0,
            step=100,
            value=float(settings.get('points_per_bonus_review_5', 500))
        )
        
        points_per_fast_completion = st.number_input(
            "Punti per Completamento Rapido (<60 giorni)",
            min_value=0,
            step=10,
            value=float(settings.get('points_per_fast_completion', 50))
        )
        
        badge_gold_threshold = st.number_input(
            "Soglia per Badge Gold",
            min_value=0,
            step=1000,
            value=float(settings.get('badge_gold_threshold', 10000))
        )
        
        badge_silver_threshold = st.number_input(
            "Soglia per Badge Silver",
            min_value=0,
            step=500,
            value=float(settings.get('badge_silver_threshold', 5000))
        )
        
        badge_bronze_threshold = st.number_input(
            "Soglia per Badge Bronze",
            min_value=0,
            step=500,
            value=float(settings.get('badge_bronze_threshold', 2000))
        )
        
        submit_settings = st.form_submit_button("Aggiorna Impostazioni")
        if submit_settings:
            update_leaderboard_setting('points_per_project_completed', points_per_project_completed)
            update_leaderboard_setting('points_per_bonus_review_4', points_per_bonus_review_4)
            update_leaderboard_setting('points_per_bonus_review_5', points_per_bonus_review_5)
            update_leaderboard_setting('points_per_fast_completion', points_per_fast_completion)
            update_leaderboard_setting('badge_gold_threshold', badge_gold_threshold)
            update_leaderboard_setting('badge_silver_threshold', badge_silver_threshold)
            update_leaderboard_setting('badge_bronze_threshold', badge_bronze_threshold)

#######################################
# 6. GESTIONE AVANZATA: "Gestione" per Riunioni, Referrals e Formazione
#######################################
# Aggiungiamo una nuova opzione nella sidebar per "Gestione"
elif scelta == "Gestisci Classifica":
    st.header("Gestione Classifica (Leaderboard)")

elif scelta == "Gestisci Riunioni, Referrals e Formazione":
    st.header("Gestione Avanzata")
    
    # Creiamo le Tab per Riunioni, Referrals, Formazione
    tab_riunioni, tab_referrals, tab_formazione = st.tabs(["Riunioni", "Referrals", "Formazione"])
    
    ###################################
    # TAB: Riunioni
    ###################################
    with tab_riunioni:
        st.subheader("Gestione Riunioni")
        
        # Form per inserire una nuova riunione
        with st.form("form_inserisci_riunione"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            data_riunione = st.date_input("Data Riunione", value=datetime.today())
            partecipato = st.selectbox("Partecipato", PARTICIPATO_OPTIONS)
            
            submit_riunione = st.form_submit_button("Inserisci Riunione")
            if submit_riunione:
                inserisci_riunione(recruiter_id, data_riunione, partecipato)
        
        st.write("---")
        st.subheader("Modifica / Elimina Riunioni Esistenti")
        riunioni = carica_riunioni()
        if riunioni:
            for riunione in riunioni:
                ri_id = riunione['id']
                recruiter_id = riunione['recruiter_id']
                data_riunione = riunione['data_riunione']
                partecipato = riunione['partecipato']
                
                with st.expander(f"Riunione ID {ri_id} - {data_riunione}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox("Recruiter", recruiter_nomi, index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)), key=f"recruiter_{ri_id}")
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    data_riunione_new = st.date_input("Data Riunione", value=datetime.strptime(data_riunione, '%Y-%m-%d').date(), key=f"data_riunione_{ri_id}")
                    partecipato_new = st.selectbox("Partecipato", PARTICIPATO_OPTIONS, index=int(partecipato), key=f"partecipato_{ri_id}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod = st.button("Modifica", key=f"mod_riunione_{ri_id}")
                    with col2:
                        btn_del = st.button("Elimina", key=f"del_riunione_{ri_id}")
                    
                    if btn_mod:
                        modifica_riunione(ri_id, recruiter_id_new, data_riunione_new, partecipato_new)
                    
                    if btn_del:
                        elimina_riunione(ri_id)
        else:
            st.info("Nessuna riunione presente nel DB.")

    ###################################
    # TAB: Referrals
    ###################################
    with tab_referrals:
        st.subheader("Gestione Referrals")
        
        # Form per inserire un nuovo referral
        with st.form("form_inserisci_referral"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            cliente_nome = st.text_input("Nome Cliente")
            data_referral = st.date_input("Data Referral", value=datetime.today())
            stato_referral = st.selectbox("Stato Referral", STATO_REFERRAL_OPTIONS)
            
            submit_referral = st.form_submit_button("Inserisci Referral")
            if submit_referral:
                if not cliente_nome.strip():
                    st.error("Il campo 'Nome Cliente' è obbligatorio!")
                else:
                    inserisci_referral(recruiter_id, cliente_nome, data_referral, stato_referral)
        
        st.write("---")
        st.subheader("Modifica / Elimina Referrals Esistenti")
        referrals = carica_referrals()
        if referrals:
            for referral in referrals:
                ref_id = referral['id']
                recruiter_id = referral['recruiter_id']
                cliente_nome = referral['cliente_nome']
                data_referral = referral['data_referral']
                stato = referral['stato']
                
                with st.expander(f"Referral ID {ref_id} - {cliente_nome}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox("Recruiter", recruiter_nomi, index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)), key=f"recruiter_ref_{ref_id}")
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    cliente_nome_new = st.text_input("Nome Cliente", value=cliente_nome, key=f"cliente_ref_{ref_id}")
                    data_referral_new = st.date_input("Data Referral", value=datetime.strptime(data_referral, '%Y-%m-%d').date(), key=f"data_referral_{ref_id}")
                    stato_referral_new = st.selectbox("Stato Referral", STATO_REFERRAL_OPTIONS, index=STATO_REFERRAL_OPTIONS.index(stato), key=f"stato_referral_{ref_id}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_ref = st.button("Modifica", key=f"mod_referral_{ref_id}")
                    with col2:
                        btn_del_ref = st.button("Elimina", key=f"del_referral_{ref_id}")
                    
                    if btn_mod_ref:
                        if not cliente_nome_new.strip():
                            st.error("Il campo 'Nome Cliente' è obbligatorio!")
                        else:
                            modifica_referral(ref_id, recruiter_id_new, cliente_nome_new, data_referral_new, stato_referral_new)
                    
                    if btn_del_ref:
                        elimina_referral(ref_id)
        else:
            st.info("Nessun referral presente nel DB.")

    ###################################
    # TAB: Formazione
    ###################################
    with tab_formazione:
        st.subheader("Gestione Formazione")
        
        # Form per inserire una nuova formazione
        with st.form("form_inserisci_formazione"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            corso_nome = st.text_input("Nome Corso")
            data_completamento = st.date_input("Data Completamento", value=datetime.today())
            
            submit_formazione = st.form_submit_button("Inserisci Formazione")
            if submit_formazione:
                if not corso_nome.strip():
                    st.error("Il campo 'Nome Corso' è obbligatorio!")
                else:
                    inserisci_formazione(recruiter_id, corso_nome, data_completamento)
        
        st.write("---")
        st.subheader("Modifica / Elimina Formazione Esistenti")
        formazioni = carica_formazione()
        if formazioni:
            for formazione in formazioni:
                form_id = formazione['id']
                recruiter_id = formazione['recruiter_id']
                corso_nome = formazione['corso_nome']
                data_completamento = formazione['data_completamento']
                
                with st.expander(f"Formazione ID {form_id} - {corso_nome}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox("Recruiter", recruiter_nomi, index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)), key=f"recruiter_formazione_{form_id}")
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    corso_nome_new = st.text_input("Nome Corso", value=corso_nome, key=f"corso_formazione_{form_id}")
                    data_completamento_new = st.date_input("Data Completamento", value=datetime.strptime(data_completamento, '%Y-%m-%d').date(), key=f"data_completamento_formazione_{form_id}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_form = st.button("Modifica", key=f"mod_formazione_{form_id}")
                    with col2:
                        btn_del_form = st.button("Elimina", key=f"del_formazione_{form_id}")
                    
                    if btn_mod_form:
                        if not corso_nome_new.strip():
                            st.error("Il campo 'Nome Corso' è obbligatorio!")
                        else:
                            modifica_formazione(form_id, recruiter_id_new, corso_nome_new, data_completamento_new)
                    
                    if btn_del_form:
                        elimina_formazione(form_id)
        else:
            st.info("Nessuna formazione presente nel DB.")

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
# 4. GESTISCI LEADERBOARD
#######################################
elif scelta == "Gestisci Classifica":
    st.header("Gestione Classifica (Leaderboard)")

    # Recupera le impostazioni attuali
    settings = get_leaderboard_settings()
    
    st.subheader("Impostazioni Correnti")
    for key, value in settings.items():
        st.write(f"**{key.replace('_', ' ').capitalize()}**: {value}")
    
    st.write("---")
    st.subheader("Aggiorna Impostazioni della Classifica")
    
    # Form per aggiornare le impostazioni
    with st.form("form_gestisci_leaderboard"):
        points_per_project_completed = st.number_input(
            "Punti per Progetto Completato",
            min_value=0,
            step=1,
            value=float(settings.get('points_per_project_completed', 10))
        )
        
        points_per_bonus_review_4 = st.number_input(
            "Punti per Recensione a 4 Stelle",
            min_value=0,
            step=100,
            value=float(settings.get('points_per_bonus_review_4', 300))
        )
        
        points_per_bonus_review_5 = st.number_input(
            "Punti per Recensione a 5 Stelle",
            min_value=0,
            step=100,
            value=float(settings.get('points_per_bonus_review_5', 500))
        )
        
        points_per_fast_completion = st.number_input(
            "Punti per Completamento Rapido (<60 giorni)",
            min_value=0,
            step=10,
            value=float(settings.get('points_per_fast_completion', 50))
        )
        
        badge_gold_threshold = st.number_input(
            "Soglia per Badge Gold",
            min_value=0,
            step=1000,
            value=float(settings.get('badge_gold_threshold', 10000))
        )
        
        badge_silver_threshold = st.number_input(
            "Soglia per Badge Silver",
            min_value=0,
            step=500,
            value=float(settings.get('badge_silver_threshold', 5000))
        )
        
        badge_bronze_threshold = st.number_input(
            "Soglia per Badge Bronze",
            min_value=0,
            step=500,
            value=float(settings.get('badge_bronze_threshold', 2000))
        )
        
        submit_settings = st.form_submit_button("Aggiorna Impostazioni")
        if submit_settings:
            update_leaderboard_setting('points_per_project_completed', points_per_project_completed)
            update_leaderboard_setting('points_per_bonus_review_4', points_per_bonus_review_4)
            update_leaderboard_setting('points_per_bonus_review_5', points_per_bonus_review_5)
            update_leaderboard_setting('points_per_fast_completion', points_per_fast_completion)
            update_leaderboard_setting('badge_gold_threshold', badge_gold_threshold)
            update_leaderboard_setting('badge_silver_threshold', badge_silver_threshold)
            update_leaderboard_setting('badge_bronze_threshold', badge_bronze_threshold)

#######################################
# 5. GESTIONE AVANZATA: Riunioni, Referrals, Formazione
#######################################
elif scelta == "Gestisci Classifica":
    st.header("Gestione Classifica (Leaderboard)")
    
else:
    st.error("Sezione non riconosciuta. Ricarica l'applicazione.")

#######################################
# 6. Sezione "Gestione" per Riunioni, Referrals e Formazione
#######################################
# Aggiungiamo una nuova opzione nella sidebar per "Gestione Avanzata"
# Modifica la radio nella sidebar per includere "Gestisci Avanzato"
# Aggiorniamo la scelta per includere la nuova opzione

# Aggiornamento della barra laterale di navigazione
st.sidebar.title("Navigazione")
scelta = st.sidebar.radio("Vai a", ["Inserisci Dati", "Dashboard", "Gestisci Opzioni", "Gestisci Classifica", "Gestisci Avanzato"])

if scelta == "Gestisci Avanzato":
    st.header("Gestione Avanzata")
    
    # Creiamo le Tab per Riunioni, Referrals, Formazione
    tab_riunioni, tab_referrals, tab_formazione = st.tabs(["Riunioni", "Referrals", "Formazione"])
    
    ###################################
    # TAB: Riunioni
    ###################################
    with tab_riunioni:
        st.subheader("Gestione Riunioni")
        
        # Form per inserire una nuova riunione
        with st.form("form_inserisci_riunione"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            data_riunione = st.date_input("Data Riunione", value=datetime.today())
            partecipato = st.selectbox("Partecipato", PARTICIPATO_OPTIONS)
            
            submit_riunione = st.form_submit_button("Inserisci Riunione")
            if submit_riunione:
                inserisci_riunione(recruiter_id, data_riunione, partecipato)
        
        st.write("---")
        st.subheader("Modifica / Elimina Riunioni Esistenti")
        riunioni = carica_riunioni()
        if riunioni:
            for riunione in riunioni:
                ri_id = riunione['id']
                recruiter_id = riunione['recruiter_id']
                data_riunione = riunione['data_riunione']
                partecipato = riunione['partecipato']
                
                with st.expander(f"Riunione ID {ri_id} - {data_riunione}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox("Recruiter", recruiter_nomi, index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)), key=f"recruiter_{ri_id}")
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    data_riunione_new = st.date_input("Data Riunione", value=datetime.strptime(data_riunione, '%Y-%m-%d').date(), key=f"data_riunione_{ri_id}")
                    partecipato_new = st.selectbox("Partecipato", PARTICIPATO_OPTIONS, index=int(partecipato), key=f"partecipato_{ri_id}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod = st.button("Modifica", key=f"mod_riunione_{ri_id}")
                    with col2:
                        btn_del = st.button("Elimina", key=f"del_riunione_{ri_id}")
                    
                    if btn_mod:
                        modifica_riunione(ri_id, recruiter_id_new, data_riunione_new, partecipato_new)
                    
                    if btn_del:
                        elimina_riunione(ri_id)
        else:
            st.info("Nessuna riunione presente nel DB.")

    ###################################
    # TAB: Referrals
    ###################################
    with tab_referrals:
        st.subheader("Gestione Referrals")
        
        # Form per inserire un nuovo referral
        with st.form("form_inserisci_referral"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            cliente_nome = st.text_input("Nome Cliente")
            data_referral = st.date_input("Data Referral", value=datetime.today())
            stato_referral = st.selectbox("Stato Referral", STATO_REFERRAL_OPTIONS)
            
            submit_referral = st.form_submit_button("Inserisci Referral")
            if submit_referral:
                if not cliente_nome.strip():
                    st.error("Il campo 'Nome Cliente' è obbligatorio!")
                else:
                    inserisci_referral(recruiter_id, cliente_nome, data_referral, stato_referral)
        
        st.write("---")
        st.subheader("Modifica / Elimina Referrals Esistenti")
        referrals = carica_referrals()
        if referrals:
            for referral in referrals:
                ref_id = referral['id']
                recruiter_id = referral['recruiter_id']
                cliente_nome = referral['cliente_nome']
                data_referral = referral['data_referral']
                stato = referral['stato']
                
                with st.expander(f"Referral ID {ref_id} - {cliente_nome}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox("Recruiter", recruiter_nomi, index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)), key=f"recruiter_ref_{ref_id}")
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    cliente_nome_new = st.text_input("Nome Cliente", value=cliente_nome, key=f"cliente_ref_{ref_id}")
                    data_referral_new = st.date_input("Data Referral", value=datetime.strptime(data_referral, '%Y-%m-%d').date(), key=f"data_referral_{ref_id}")
                    stato_referral_new = st.selectbox("Stato Referral", STATO_REFERRAL_OPTIONS, index=STATO_REFERRAL_OPTIONS.index(stato), key=f"stato_referral_{ref_id}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_ref = st.button("Modifica", key=f"mod_referral_{ref_id}")
                    with col2:
                        btn_del_ref = st.button("Elimina", key=f"del_referral_{ref_id}")
                    
                    if btn_mod_ref:
                        if not cliente_nome_new.strip():
                            st.error("Il campo 'Nome Cliente' è obbligatorio!")
                        else:
                            modifica_referral(ref_id, recruiter_id_new, cliente_nome_new, data_referral_new, stato_referral_new)
                    
                    if btn_del_ref:
                        elimina_referral(ref_id)
        else:
            st.info("Nessun referral presente nel DB.")

    ###################################
    # TAB: Formazione
    ###################################
    with tab_formazione:
        st.subheader("Gestione Formazione")
        
        # Form per inserire una nuova formazione
        with st.form("form_inserisci_formazione"):
            recruiters = carica_recruiters()
            recruiter_nomi = [r['nome'] for r in recruiters]
            recruiter_sel = st.selectbox("Recruiter", recruiter_nomi)
            recruiter_id = None
            for r in recruiters:
                if r['nome'] == recruiter_sel:
                    recruiter_id = r['id']
                    break
            
            corso_nome = st.text_input("Nome Corso")
            data_completamento = st.date_input("Data Completamento", value=datetime.today())
            
            submit_formazione = st.form_submit_button("Inserisci Formazione")
            if submit_formazione:
                if not corso_nome.strip():
                    st.error("Il campo 'Nome Corso' è obbligatorio!")
                else:
                    inserisci_formazione(recruiter_id, corso_nome, data_completamento)
        
        st.write("---")
        st.subheader("Modifica / Elimina Formazione Esistenti")
        formazioni = carica_formazione()
        if formazioni:
            for formazione in formazioni:
                form_id = formazione['id']
                recruiter_id = formazione['recruiter_id']
                corso_nome = formazione['corso_nome']
                data_completamento = formazione['data_completamento']
                
                with st.expander(f"Formazione ID {form_id} - {corso_nome}"):
                    recruiters = carica_recruiters()
                    recruiter_nomi = [r['nome'] for r in recruiters]
                    recruiter_sel = st.selectbox("Recruiter", recruiter_nomi, index=recruiter_nomi.index(next(r['nome'] for r in recruiters if r['id'] == recruiter_id)), key=f"recruiter_formazione_{form_id}")
                    recruiter_id_new = None
                    for r in recruiters:
                        if r['nome'] == recruiter_sel:
                            recruiter_id_new = r['id']
                            break
                    
                    corso_nome_new = st.text_input("Nome Corso", value=corso_nome, key=f"corso_formazione_{form_id}")
                    data_completamento_new = st.date_input("Data Completamento", value=datetime.strptime(data_completamento, '%Y-%m-%d').date(), key=f"data_completamento_formazione_{form_id}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        btn_mod_form = st.button("Modifica", key=f"mod_formazione_{form_id}")
                    with col2:
                        btn_del_form = st.button("Elimina", key=f"del_formazione_{form_id}")
                    
                    if btn_mod_form:
                        if not corso_nome_new.strip():
                            st.error("Il campo 'Nome Corso' è obbligatorio!")
                        else:
                            modifica_formazione(form_id, recruiter_id_new, corso_nome_new, data_completamento_new)
                    
                    if btn_del_form:
                        elimina_formazione(form_id)
        else:
            st.info("Nessuna formazione presente nel DB.")

#######################################
# 7. FINE DEL CODICE
#######################################
