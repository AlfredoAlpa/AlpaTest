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
if 'punteggi' not in st.session_state: st.session_state.punteggi = {"Corretta": 0.75, "Non Data": 0.0, "Errata": -0.25}

# --- FUNZIONI ---
def pulisci_testo(testo):
    if pd.isna(testo) or testo == "": return " "
    repls = {'’':"'",'‘':"'",'“':'"','”':'"','–':'-','à':'a','è':'e','é':'e','ì':'i','ò':'o','ù':'u'}
    t = str(testo)
    for k,v in repls.items(): t = t.replace(k,v)
    return t.encode('latin-1','replace').decode('latin-1')

def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        frames = []
        for i in range(len(st.session_state.dict_discipline)):
            # MODIFICA: leggiamo dalle chiavi univoche dei widget
            d = st.session_state.get(f"input_da_{i}","")
            a = st.session_state.get(f"input_a_{i}","")
            if d.isdigit() and a.isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.start_time = time.time()
            st.rerun()
    except Exception as e: st.error(f"Errore: {e}")

def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # MODIFICA: Aggiunto #toolbar=0 per forzare il rendering in alcuni browser
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="800" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, (30 * 60) - (time.time() - st.session_state.start_time))
        minuti, secondi = int(rimanente // 60), int(rimanente % 60)
        colore = "#00FF00" if rimanente > 300 else "#FF0000"
        st.markdown(f'<p class="timer-style" style="color:{colore}">⏱️ {minuti:02d}:{secondi:02d}</p>', unsafe_allow_html=True)

# --- CSS ---
st.markdown("""<style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); color: white; }
    .logo-style { font-family: 'Georgia', serif; font-size: 3rem; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.4rem !important; font-weight: bold !important; }
    .timer-style { font-size: 2.5rem; font-weight: bold; text-align: right; }
</style>""", unsafe_allow_html=True)

# --- LOGICA NAVIGAZIONE ---
if st.session_state.vista == "TEST":
    # Layout Test (Identico al tuo, con correzione chiavi discipline)
    t1, t2 = st.columns([7, 3])
    with t1: st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
    with t2: mostra_timer()
    st.markdown("---")
    
    col_sx, col_centro, col_dx = st.columns([2.8, 7, 3.2])
    
    with col_sx:
        if st.button("📚 VAI ALLE DISPENSE", use_container_width=True):
            st.session_state.vista = "STUDIO"; st.rerun()
        st.write("---")
        if not st.session_state.df_filtrato.empty:
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            sel = st.radio("Domande", lista, index=st.session_state.indice, key="nav_main", label_visibility="collapsed")
            st.session_state.indice = lista.index(sel)

    with col_centro:
        if not st.session_state.df_filtrato.empty:
            q = st.session_state.df_filtrato.iloc[st.session_state.indice]
            st.markdown(f'<div class="quesito-style">{st.session_state.indice+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
            # Logica Radio Risposte...
            st.write("---")
            c1, c2, c3 = st.columns(3)
            if c1.button("⬅️ Prec"): st.session_state.indice = max(0, st.session_state.indice-1); st.rerun()
            if c3.button("Succ ➡️"): st.session_state.indice = min(len(st.session_state.df_filtrato)-1, st.session_state.indice+1); st.rerun()
        else: st.info("Configura a destra e premi Importa")

    with col_dx:
        st.markdown('<p style="background:white; color:black; text-align:center; font-weight:bold; border-radius:5px;">Discipline</p>', unsafe_allow_html=True)
        if st.session_state.dict_discipline:
            for i, (cod, testo) in enumerate(st.session_state.dict_discipline.items()):
                if i < 10:
                    c1, c2, c3 = st.columns([6, 2, 2])
                    c1.markdown(f"<small>{testo}</small>", unsafe_allow_html=True)
                    # CORREZIONE CHIAVE: input_da invece di da
                    st.text_input("D", key=f"input_da_{i}", label_visibility="collapsed", placeholder="Da")
                    st.text_input("A", key=f"input_a_{i}", label_visibility="collapsed", placeholder="A")
        st.checkbox("Simulazione (30 min)", key="simulazione")
        st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True)

else:
    # AREA DISPENSE
    st.markdown('<div class="logo-style">AlPaTest - Studio</div>', unsafe_allow_html=True)
    if st.button("⬅️ TORNA AL TEST", use_container_width=True, type="primary"):
        st.session_state.vista = "TEST"; st.rerun()
    st.write("---")
    cm, cv = st.columns([3, 7])
    with cm:
        st.subheader("PDF Disponibili")
        lista_pdf = [f for f in os.listdir("dispense") if f.endswith(".pdf")] if os.path.exists("dispense") else []
        if lista_pdf:
            scelta = st.radio("Seleziona:", sorted(lista_pdf))
            p_sel = os.path.join("dispense", scelta)
        else: st.warning("Nessun PDF trovato"); p_sel = None
    with cv:
        if p_sel:
            st.info(f"Stai leggendo: {scelta}")
            display_pdf(p_sel)
