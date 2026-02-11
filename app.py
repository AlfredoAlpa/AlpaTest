import streamlit as st
import pandas as pd
import os
import time
import base64
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- LOGIN ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] > div:has(.titolo-box) {
            border: 3px solid #FFD700 !important;
            border-radius: 20px !important;
            padding: 50px 20px !important;
            background-color: rgba(0, 0, 0, 0.5) !important;
            width: 95% !important; max-width: 550px !important; margin: 40px auto !important; text-align: center !important;
        }
        .titolo-box { color: #FFD700 !important; font-size: 2rem !important; font-weight: 900 !important; }
        </style>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<span class="titolo-box">🔐 Accesso AlPaTest</span>', unsafe_allow_html=True)
        codice = st.text_input("Codice:", type="password", label_visibility="collapsed").strip()
        if st.button("ENTRA"):
            if codice.lower() in ["open", "studente01"]:
                st.session_state.autenticato = True
                st.rerun()
    st.stop()

# --- INIZIALIZZAZIONE ---
if 'vista' not in st.session_state: st.session_state.vista = "TEST"
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        df_disc = df_disc.dropna(subset=['Codice', 'Disciplina'])
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except: st.session_state.dict_discipline = {}

if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None

# --- FUNZIONI NAVIGAZIONE ---
def vai_avanti():
    if st.session_state.indice < len(st.session_state.df_filtrato) - 1:
        st.session_state.indice += 1

def vai_indietro():
    if st.session_state.indice > 0:
        st.session_state.indice -= 1

def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        frames = []
        for i in range(len(st.session_state.dict_discipline)):
            d = st.session_state.get(f"key_da_{i}","")
            a = st.session_state.get(f"key_a_{i}","")
            if str(d).isdigit() and str(a).isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.start_time = time.time()
            st.session_state.fase = "PROVA"
            st.rerun()
    except Exception as e: st.error(f"Errore: {e}")

# --- CSS ---
st.markdown("<style>.stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); color: white; }</style>", unsafe_allow_html=True)

# --- LOGICA NAVIGAZIONE ---
if st.session_state.vista == "TEST":
    
    if st.session_state.fase == "CONFERMA":
        st.markdown("### ❓ Vuoi consegnare la prova?")
        c1, c2 = st.columns(2)
        if c1.button("Sì, CONSEGNA", use_container_width=True):
            st.session_state.fase = "CONCLUSIONE"; st.rerun()
        if c2.button("No, CONTINUA", use_container_width=True):
            st.session_state.fase = "PROVA"; st.rerun()
        st.stop()

    # SCHERMATA TEST
    st.markdown('<h1 style="color:#FFD700;">AlPaTest</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    col_sx, col_centro, col_dx = st.columns([2.5, 6.5, 3])
    
    with col_sx:
        if st.button("📚 VAI ALLE DISPENSE", use_container_width=True):
            st.session_state.vista = "STUDIO"; st.rerun()
        st.write("---")
        if not st.session_state.df_filtrato.empty:
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            # Navigazione tramite lista
            scelta_lista = st.radio("Vai a:", lista, index=st.session_state.indice, key="nav_radio")
            st.session_state.indice = lista.index(scelta_lista)

    with col_centro:
        if not st.session_state.df_filtrato.empty:
            idx = st.session_state.indice
            q = st.session_state.df_filtrato.iloc[idx]
            st.markdown(f"### Domanda {idx+1}")
            st.info(q['Domanda'])
            
            # Opzioni
            opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
            
            # Recupera risposta precedente
            risposta_precedente = st.session_state.risposte_date.get(idx)
            index_radio = ["A", "B", "C", "D"].index(risposta_precedente) if risposta_precedente else None

            def registra_risposta():
                scelta = st.session_state[f"domanda_{idx}"]
                st.session_state.risposte_date[idx] = scelta[0] # Salva solo la lettera

            st.radio("Seleziona la risposta corretta:", opts, index=index_radio, key=f"domanda_{idx}", on_change=registra_risposta)
            
            st.write("---")
            # PULSANTI DI NAVIGAZIONE
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                st.button("⬅️ Precedente", on_click=vai_indietro, use_container_width=True)
            with btn_col2:
                if st.button("🏁 CONSEGNA", type="primary", use_container_width=True):
                    st.session_state.fase = "CONFERMA"; st.rerun()
            with btn_col3:
                st.button("Successivo ➡️", on_click=vai_avanti, use_container_width=True)
        else:
            st.warning("Nessun quesito caricato. Usa il pannello a destra.")

    with col_dx:
        st.markdown("### Configurazione")
        if st.session_state.dict_discipline:
            for i, (cod, testo) in enumerate(st.session_state.dict_discipline.items()):
                st.write(f"<small>{testo}</small>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                st.text_input("Da", key=f"key_da_{i}", label_visibility="collapsed", placeholder="Da")
                st.text_input("A", key=f"key_a_{i}", label_visibility="collapsed", placeholder="A")
        st.button("🚀 IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True)

else:
    # AREA DISPENSE (Logica invariata per continuità)
    st.markdown('<h1 style="color:#FFD700;">AlPaTest - Studio</h1>', unsafe_allow_html=True)
    if st.button("⬅️ TORNA AL TEST", use_container_width=True):
        st.session_state.vista = "TEST"; st.rerun()
    # ... restanti funzioni dispense ...
