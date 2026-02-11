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

def display_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
        st.download_button(label="📥 SCARICA DISPENSA", data=pdf_data, file_name=os.path.basename(file_path), mime="application/pdf", use_container_width=True)
    except Exception as e: st.error(f"Errore PDF: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, (30 * 60) - (time.time() - st.session_state.start_time))
        minuti, secondi = int(rimanente // 60), int(rimanente % 60)
        colore = "#00FF00" if rimanente > 300 else "#FF0000"
        st.markdown(f'<p style="font-size:2rem; font-weight:bold; text-align:right; color:{colore}">⏱️ {minuti:02d}:{secondi:02d}</p>', unsafe_allow_html=True)
        if rimanente <= 0:
            st.session_state.fase = "CONCLUSIONE"
            st.rerun()

# --- CSS ---
st.markdown("<style>.stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); color: white; }</style>", unsafe_allow_html=True)

# --- LOGICA NAVIGAZIONE ---
if st.session_state.vista == "TEST":
    # GESTIONE FASI FINALI
    if st.session_state.fase == "CONFERMA":
        st.markdown("### ❓ Vuoi consegnare la prova?")
        c1, c2 = st.columns(2)
        if c1.button("Sì, CONSEGNA", use_container_width=True):
            st.session_state.fase = "CONCLUSIONE"; st.rerun()
        if c2.button("No, CONTINUA", use_container_width=True):
            st.session_state.fase = "PROVA"; st.rerun()
        st.stop()
    
    if st.session_state.fase == "CONCLUSIONE":
        st.success("Test terminato! Controlla i tuoi risultati.")
        if st.button("Ricomincia nuovo Test"):
            st.session_state.df_filtrato = pd.DataFrame()
            st.session_state.fase = "PROVA"
            st.rerun()
        st.stop()

    # SCHERMATA TEST ORDINARIA
    t1, t2 = st.columns([7, 3])
    with t1: st.markdown('<h1 style="color:#FFD700; margin-bottom:0;">AlPaTest</h1>', unsafe_allow_html=True)
    with t2: mostra_timer()
    st.markdown("---")
    
    col_sx, col_centro, col_dx = st.columns([2.5, 6.5, 3])
    
    with col_sx:
        if st.button("📚 VAI ALLE DISPENSE", use_container_width=True):
            st.session_state.vista = "STUDIO"; st.rerun()
        st.write("---")
        if not st.session_state.df_filtrato.empty:
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            sel = st.radio("Seleziona Domanda", lista, index=st.session_state.indice, key="nav_main")
            st.session_state.indice = lista.index(sel)

    with col_centro:
        if not st.session_state.df_filtrato.empty:
            q = st.session_state.df_filtrato.iloc[st.session_state.indice]
            st.markdown(f"### {st.session_state.indice+1}. {q['Domanda']}")
            
            # --- SEZIONE RISPOSTE ---
            opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
            ans_prec = st.session_state.risposte_date.get(st.session_state.indice)
            idx_prec = ["A","B","C","D"].index(ans_prec) if ans_prec in ["A","B","C","D"] else None
            
            def salva_risposta():
                val = st.session_state[f"quiz_{st.session_state.indice}"]
                st.session_state.risposte_date[st.session_state.indice] = val[0] # Prende la lettera A, B, C o D

            st.radio("Scegli la risposta:", opts, index=idx_prec, key=f"quiz_{st.session_state.indice}", on_change=salva_risposta)
            
            st.write("---")
            c1, c2, c3 = st.columns(3)
            if c1.button("⬅️ Prec"): 
                st.session_state.indice = max(0, st.session_state.indice-1); st.rerun()
            if c2.button("🏁 CONSEGNA", type="primary"): 
                st.session_state.fase = "CONFERMA"; st.rerun()
            if c3.button("Succ ➡️"): 
                st.session_state.indice = min(len(st.session_state.df_filtrato)-1, st.session_state.indice+1); st.rerun()
        else:
            st.info("Configura le discipline a destra e clicca su 'Importa Quesiti'")

    with col_dx:
        st.markdown("### Discipline")
        if st.session_state.dict_discipline:
            for i, (cod, testo) in enumerate(st.session_state.dict_discipline.items()):
                st.write(f"**{testo}**")
                c1, c2 = st.columns(2)
                st.text_input("Da", key=f"key_da_{i}", label_visibility="collapsed")
                st.text_input("A", key=f"key_a_{i}", label_visibility="collapsed")
        st.checkbox("Simulazione (30 min)", key="simulazione")
        st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True)

else:
    # AREA DISPENSE
    st.markdown('<h1 style="color:#FFD700;">AlPaTest - Studio</h1>', unsafe_allow_html=True)
    if st.button("⬅️ TORNA AL TEST", use_container_width=True):
        st.session_state.vista = "TEST"; st.rerun()
    st.write("---")
    cm, cv = st.columns([3, 7])
    with cm:
        st.subheader("I tuoi PDF")
        if os.path.exists("dispense"):
            lista_pdf = [f for f in os.listdir("dispense") if f.endswith(".pdf")]
            if lista_pdf:
                scelta = st.radio("Seleziona file:", sorted(lista_pdf))
                p_sel = os.path.join("dispense", scelta)
            else: st.warning("Nessun PDF trovato"); p_sel = None
        else: st.error("Cartella 'dispense' mancante"); p_sel = None
    with cv:
        if p_sel: display_pdf(p_sel)
