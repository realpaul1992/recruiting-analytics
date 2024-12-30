# app.py

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import shutil
import os
import matplotlib.pyplot as plt  # <--- Import Matplotlib

#######################################
# FUNZIONI DI ACCESSO AL DB
#######################################
def get_connection():
    conn = sqlite3.connect('database.db')
    return conn

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

    c.execute("""
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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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
    backup_database()

def carica_dati_completo():
    """
    Carica i progetti uniti a settori, pm, recruiters, includendo 'tempo_previsto'.
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
    backup_dir = 'backup'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"database_backup_{stamp}.db"
    backup_path = os.path.join(backup_dir, backup_name)
    
    try:
        shutil.copy('database.db', backup_path)
        st.success(f"Backup eseguito con successo: {backup_name}")
    except Exception as e:
        st.error(f"Errore durante il backup: {e}")
        return
    
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith('.db')],
        key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
        reverse=True
    )
    if len(backups) > max_backups:
        for old_file in backups[max_backups:]:
            try:
                os.remove(os.path.join(backup_dir, old_file))
                st.info(f"Backup obsoleto rimosso: {old_file}")
            except Exception as e:
                st.error(f"Errore rimozione {old_file}: {e}")

def check_weekly_backup():
    last_backup_file = 'last_backup.txt'
    if os.path.exists(last_backup_file):
        with open(last_backup_file, 'r') as f:
            content = f.read()
            try:
                last_backup = datetime.strptime(content, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                last_backup = None
    else:
        last_backup = None
    
    now = datetime.now()
    if last_backup is None or (now - last_backup) >= timedelta(weeks=1):
        backup_database()
        with open(last_backup_file, 'w') as f:
            f.write(now.strftime("%Y-%m-%d %H:%M:%S"))

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
    Ritorna un DataFrame con [sales_recruiter, completati, tempo_medio, bonus_totale, punteggio, badge].
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
        
        data_inizio_str = st.text_input("Data di Inizio (GG/MM/AAAA)", value="", placeholder="Lascia vuoto se non disponibile")

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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Panoramica",
            "Carico Proiettato / Previsione",
            "Bonus e Premi",
            "Backup",
            "Altre Info",
            "Classifica"  # <--- Nuova scheda
        ])

        ################################
        # TAB 1: Panoramica
        ################################
        with tab1:
            st.subheader("Tempo Medio Generale e per Recruiter/Settore")

            df_comp = df[df['stato_progetto'] == 'Completato']
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
            df_attivi = df[df['stato_progetto'].isin(["In corso", "Bloccato"])]
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
            
            df['data_inizio_dt'] = pd.to_datetime(df['data_inizio'], errors='coerce')
            df_ok = df[(df['tempo_previsto'].notna()) & (df['tempo_previsto']>0)]
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
            data_mese = st.date_input("Seleziona un Mese", value=datetime.today())
            import pandas as pd
            mese_inizio = data_mese.replace(day=1)
            mese_fine = (mese_inizio + pd.offsets.MonthEnd(1)).date()

            df['recensione_data_dt'] = pd.to_datetime(df['recensione_data'], errors='coerce')
            df_mese = df[
                (df['recensione_data_dt'] >= pd.Timestamp(mese_inizio)) & 
                (df['recensione_data_dt'] <= pd.Timestamp(mese_fine))
            ]

            st.write(f"Progetti con recensione in questo mese: {len(df_mese)}")

            def calcola_bonus(stelle):
                if stelle == 4:
                    return 300
                elif stelle == 5:
                    return 500
                else:
                    return 0

            df_mese['bonus'] = df_mese['recensione_stelle'].fillna(0).astype(int).apply(calcola_bonus)
            bonus_rec = df_mese.groupby('sales_recruiter')['bonus'].sum().reset_index()
            fig_bonus = px.bar(
                bonus_rec,
                x='sales_recruiter',
                y='bonus',
                labels={'bonus':'Bonus (€)'},
                title='Bonus del Mese'
            )
            st.plotly_chart(fig_bonus)

            st.subheader("Premio Annuale (Recensioni a 5 stelle)")
            oggi = datetime.today().date()
            un_anno_fa = oggi - timedelta(days=365)
            df_ultimo_anno = df[
                (df['recensione_data_dt'] >= pd.Timestamp(un_anno_fa)) &
                (df['recensione_stelle'] == 5)
            ]
            rec_5 = df_ultimo_anno.groupby('sales_recruiter').size().reset_index(name='cinque_stelle')
            if not rec_5.empty:
                max_num = rec_5['cinque_stelle'].max()
                vincitori = rec_5[rec_5['cinque_stelle'] == max_num]
                if len(vincitori) == 1:
                    st.success(f"Il premio annuale va a {vincitori.iloc[0]['sales_recruiter']} con {max_num} recensioni 5 stelle!")
                else:
                    st.success(f"Premio annuale condiviso tra: {', '.join(vincitori['sales_recruiter'])}, con {max_num} 5 stelle!")
            else:
                st.info("Nessuna recensione a 5 stelle nell'ultimo anno.")

        ################################
        # TAB 4: Backup
        ################################
        with tab4:
            st.subheader("Gestione Backup")
            if st.button("Esegui Backup Ora"):
                backup_database()

            backup_dir = 'backup'
            if os.path.exists(backup_dir):
                backup_files = sorted(
                    [f for f in os.listdir(backup_dir) if f.endswith('.db')],
                    key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
                    reverse=True
                )
                if backup_files:
                    for bf in backup_files:
                        path_bf = os.path.join(backup_dir, bf)
                        with open(path_bf, 'rb') as f:
                            st.download_button(
                                label=f"Scarica {bf}",
                                data=f.read(),
                                file_name=bf,
                                mime='application/octet-stream'
                            )
                else:
                    st.info("Nessun backup disponibile.")
            else:
                st.info("La cartella di backup non esiste.")

            st.markdown("---")
            st.write("Ripristina Backup:")
            up_file = st.file_uploader("Carica un file .db per ripristinare", type=['db'])
            if up_file:
                if st.button("Ripristina DB"):
                    try:
                        fname = f"uploaded_{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
                        path_tmp = os.path.join('backup', fname)
                        with open(path_tmp, 'wb') as f:
                            f.write(up_file.getbuffer())
                        shutil.copy(path_tmp, 'database.db')
                        st.success("Backup ripristinato! Ricarica l'app.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Errore ripristino: {e}")

        ################################
        # TAB 5: Altre Info
        ################################
        with tab5:
            st.subheader("Altre Info / Gamification e Strumenti")
            st.write("""
            - Qui puoi mettere info generiche, 
            - Over capacity email, 
            - altre feature.
            """)

        ################################
        # TAB 6: Classifica
        ################################
        with tab6:
            st.subheader("Classifica (Matplotlib)")

            # (1) RECRUITER PIÙ VICINO AL PREMIO ANNUALE (5 STELLE)
            df['recensione_stelle'] = df['recensione_stelle'].fillna(0).astype(int)
            df['recensione_data_dt'] = pd.to_datetime(df['recensione_data'], errors='coerce')

            st.markdown("**1) Recruiter più vicino al Premio Annuale (5 stelle)**")
            oggi = datetime.today().date()
            un_anno_fa = oggi - timedelta(days=365)
            df_ultimo_anno = df[
                (df['recensione_data_dt'] >= pd.Timestamp(un_anno_fa)) &
                (df['recensione_stelle'] == 5)
            ]
            annual_5 = df_ultimo_anno.groupby('sales_recruiter').size().reset_index(name='cinque_stelle')
            annual_5 = annual_5.sort_values(by='cinque_stelle', ascending=False)
            if annual_5.empty:
                st.info("Nessuna 5 stelle nell'ultimo anno.")
            else:
                fig1, ax1 = plt.subplots(figsize=(6,4))
                ax1.bar(annual_5['sales_recruiter'], annual_5['cinque_stelle'], color='blue')
                ax1.set_title("N. Recensioni 5 stelle (ultimo anno)")
                ax1.set_xlabel("Recruiter")
                ax1.set_ylabel("Recensioni 5 stelle")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig1)

            # (2) RECRUITER PIÙ VELOCE (TEMPO MEDIO)
            st.markdown("**2) Recruiter più veloce (Tempo Medio)**")
            df_comp = df[df['stato_progetto'] == 'Completato'].copy()
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
            def calcola_bonus_tmp(stelle):
                if stelle == 4:
                    return 300
                elif stelle == 5:
                    return 500
                else:
                    return 0
            df['bonus'] = df['recensione_stelle'].apply(calcola_bonus_tmp)
            bonus_df = df.groupby('sales_recruiter')['bonus'].sum().reset_index()
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

            # (4) LEADERBOARD MENSILE
            st.markdown("**4) Leaderboard Mensile**")

            # Scegli data di riferimento
            data_riferimento = st.date_input(
                "Seleziona una data del mese da analizzare",
                value=datetime.today()
            )
            mese_inizio = data_riferimento.replace(day=1)
            import pandas as pd
            mese_fine = (mese_inizio + pd.offsets.MonthEnd(1)).date()

            st.write(f"Mese in analisi: {mese_inizio.strftime('%d/%m/%Y')} - {mese_fine.strftime('%d/%m/%Y')}")

            leaderboard_df = calcola_leaderboard_mensile(df, mese_inizio, mese_fine)
            if leaderboard_df.empty:
                st.info("Nessun progetto completato in questo periodo.")
            else:
                st.write("Classifica Mensile con punteggio e badge:")
                st.dataframe(leaderboard_df)

                # Grafico punteggio con Plotly
                fig_leader = px.bar(
                    leaderboard_df,
                    x='sales_recruiter',
                    y='punteggio',
                    color='badge',  # per vedere i diversi badge
                    title='Leaderboard Mensile'
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

#######################################
# 3. GESTISCI OPZIONI
#######################################
elif scelta == "Gestisci Opzioni":
    st.write("Gestione settori, PM, recruiters e capacity in manage_options.py")
