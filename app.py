import streamlit as st
import pandas as pd
import os
import time
import base64
from fpdf import FPDF

# 1. CONFIGURAZIONE
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# 2. LOGIN
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown('<h1 style="color: #FFD700; text-align: center;">🔐 Accesso AlPaTest</h1>', unsafe_allow_html=True)
    with st.container():
        codice = st.text_input("Codice di accesso:", type="password", key="login_key").strip()
        if st.button("ENTRA"):
            if codice.lower() in ["open", "studente01"]:
                st.session_state.autenticato = True
                st.rerun()
            else:
                st.error("Codice errato")
    st.stop()

# 3. CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .logo-style { font-size: 3rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.5rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. INIZIALIZZAZIONE STATO
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()

# Caricamento Discipline
if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline").dropna(subset=['Codice', 'Disciplina'])
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except:
        st.session_state.dict_discipline = {}

# 5. FUNZIONI
def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        frames = []
        for i in range(len(st.session_state.dict_discipline)):
            # Leggiamo i valori dai widget usando le chiavi salvate in session_state
            d = st.session_state.get(f"da_{i}", "")
            a = st.session_state.get(f"a_{i}", "")
            if str(d).isdigit() and str(a).isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.fase = "PROVA"
    except Exception as e: st.error(f"Errore Importazione: {e}")

# 6. LAYOUT
if st.session_state.fase == "CONFERMA":
    st.title("🏆 AlPaTest")
    st.warning("### ❓ Vuoi consegnare la prova?")
    if st.button("Sì, CONSEGNA"):
        st.session_state.fase = "CONCLUSIONE"; st.rerun()
    if st.button("No, CONTINUA"):
        st.session_state.fase = "PROVA"; st.rerun()
    st.stop()

if st.session_state.fase == "CONCLUSIONE":
    st.title("🏆 AlPaTest")
    st.success("### Test terminato!")
    if st.button("Ricomincia"):
        st.session_state.fase = "PROVA"
        st.session_state.df_filtrato = pd.DataFrame()
        st.rerun()
    st.stop()

# --- SCHERMATA TEST ---
st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
st.divider()

col_sx, col_ct, col_dx = st.columns([2, 6, 3.5])

with col_sx:
    st.write("### Domande")
    if not st.session_state.df_filtrato.empty:
        lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
        sel = st.radio("Seleziona", lista, index=st.session_state.indice, key="nav_radio")
        st.session_state.indice = lista.index(sel)

with col_ct:
    if not st.session_state.df_filtrato.empty:
        idx = st.session_state.indice
        q = st.session_state.df_filtrato.iloc[idx]
        st.markdown(f'<div class="quesito-style">{idx+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
        
        opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
        
        # Gestione risposta
        r_precedente = st.session_state.risposte_date.get(idx)
        idx_r = ["A","B","C","D"].index(r_precedente) if r_precedente else None
        
        def salva_risposta():
            scelta = st.session_state[f"r_{idx}"]
            st.session_state.risposte_date[idx] = scelta[0]

        st.radio("Risposta:", opts, index=idx_r, key=f"r_{idx}", on_change=salva_risposta)
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ Prec"):
            st.session_state.indice = max(0, idx-1); st.rerun()
        if c2.button("🏁 CONSEGNA", type="primary"):
            st.session_state.fase = "CONFERMA"; st.rerun()
        if c3.button("Succ ➡️"):
            st.session_state.indice = min(len(st.session_state.df_filtrato)-1, idx+1); st.rerun()
    else:
        st.info("Configura le discipline e importa i quesiti.")

with col_dx:
    st.markdown("### Discipline")
    if st.session_state.dict_discipline:
        for i, (cod, testo) in enumerate(st.session_state.dict_discipline.items()):
            st.write(f"**{testo}**")
            c_a, c_b = st.columns(2)
            c_a.text_input("Da", key=f"da_{i}")
            c_b.text_input("A", key=f"a_{i}")
    st.button("📥 Importa Quesiti", on_click=importa_quesiti, use_container_width=True)
