# pages/Recruiter_Dashboard.py

import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt
import urllib.parse

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

# Leggi i parametri della query
query_params = st.experimental_get_query_params()
st.write("Parametri della Query:", query_params)  # Debugging: Mostra i parametri ricevuti
if 'recruiter_id' in query_params:
    recruiter_id = query_params['recruiter_id'][0]
    # Decodifica eventuali caratteri speciali
    recruiter_id = urllib.parse.unquote(recruiter_id)
    # Optionally, sanitizza recruiter_id o convertila in int se necessario
else:
    st.error("Nessun recruiter specificato. Accesso non autorizzato.")
    st.stop()

# Carica i dati
df = carica_dati_completo()

# Verifica che il recruiter esista
if recruiter_id not in df['sales_recruiter'].unique():
    st.error("Recruiter non trovato.")
    st.stop()

# Filtra i dati per il recruiter
df_recruiter = df[df['sales_recruiter'] == recruiter_id]

if df_recruiter.empty:
    st.info("Nessun progetto assegnato a questo recruiter.")
    st.stop()

st.title(f"Dashboard di {recruiter_id}")

# Metric: Bonus ricevuti
df_recruiter['bonus'] = df_recruiter['recensione_stelle'].fillna(0).astype(int).apply(calcola_bonus)
total_bonus = df_recruiter['bonus'].sum()

# Metric: Tempo medio di chiusura totale
df_completed = df_recruiter[df_recruiter['stato_progetto'] == 'Completato']
average_closure_time = df_completed['tempo_totale'].mean() if not df_completed.empty else 0

# Metric: Numero di progetti attivi
active_projects = df_recruiter[df_recruiter['stato_progetto'].isin(["In corso", "Bloccato"])].shape[0]

# Metric: Tempo medio di chiusura per settore
average_closure_time_sector = df_completed.groupby('settore')['tempo_totale'].mean().reset_index()

# Graph: Chi si sta avvicinando di più al premio annuale (tipo a forma di scala)
# Assumiamo che "avvicinarsi al premio" significhi avere più recensioni a 5 stelle
df_all = df.copy()
df_all_5 = df_all[df_all['recensione_stelle'] == 5]
rec_5_reviews = df_all_5.groupby('sales_recruiter').size().reset_index(name='5_star_reviews')
rec_5_reviews = rec_5_reviews.sort_values(by='5_star_reviews', ascending=False)

# Current recruiter's 5-star reviews
current_recruiter_reviews = rec_5_reviews[rec_5_reviews['sales_recruiter'] == recruiter_id]
current_recruiter_reviews = current_recruiter_reviews['5_star_reviews'].values[0] if not current_recruiter_reviews.empty else 0

# Plot a bar chart showing all recruiters and highlighting the current recruiter
fig_award = px.bar(
    rec_5_reviews,
    x='sales_recruiter',
    y='5_star_reviews',
    title='Recensioni a 5 Stelle per Recruiter',
    labels={'sales_recruiter': 'Recruiter', '5_star_reviews': 'Recensioni 5 Stelle'},
    height=400
)

# Evidenzia il recruiter corrente
fig_award.add_trace(
    px.bar(
        rec_5_reviews[rec_5_reviews['sales_recruiter'] == recruiter_id],
        x='sales_recruiter',
        y='5_star_reviews'
    ).data[0]
)

# Aggiorna i colori per evidenziare il recruiter corrente
fig_award.update_traces(marker_color=['orange' if r == recruiter_id else 'blue' for r in rec_5_reviews['sales_recruiter']])
st.plotly_chart(fig_award)

# Metric: Tempo medio di chiusura totale
st.metric("Tempo Medio di Chiusura Totale (giorni)", round(average_closure_time, 2))

# Metric: Numero di progetti attivi
st.metric("Numero di Progetti Attivi", active_projects)

# Display Tempo medio di chiusura per settore
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

# Display Bonus ricevuti
st.subheader("Bonus Ricevuti")
st.metric("Bonus Totale (€)", total_bonus)

# Optionally, display a table of projects
st.subheader("Progetti Assegnati")
st.dataframe(df_recruiter[['cliente', 'settore', 'stato_progetto', 'data_inizio', 'recensione_stelle', 'bonus']])
