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
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Usiamo un iframe che è più compatibile con i browser moderni
        pdf_display = f'''
            <iframe src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" height="800" type="application/pdf" 
            style="border:none;"></iframe>
        '''
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Aggiungiamo un link di emergenza sotto il riquadro
        st.markdown(f"**Problemi di visualizzazione?** [Clicca qui per scaricare il file](data:application/pdf;base64,{base64_pdf})", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Errore nella visualizzazione del PDF: {e}")

# --- PARTE FINALE DEL CODICE (Sostituisci il blocco 'else' finale) ---
else:
    # AREA DISPENSE
    st.markdown('<div class="logo-style">AlPaTest - Studio</div>', unsafe_allow_html=True)
    if st.button("⬅️ TORNA AL TEST", use_container_width=True, type="primary"):
        st.session_state.vista = "TEST"; st.rerun()
    st.write("---")
    cm, cv = st.columns([3, 7])
    with cm:
        st.subheader("PDF Disponibili")
        # Controlliamo se la cartella esiste prima di leggere
        if not os.path.exists("dispense"):
            os.makedirs("dispense")
            st.warning("Cartella 'dispense' creata. Carica i file PDF su GitHub.")
        
        lista_pdf = [f for f in os.listdir("dispense") if f.endswith(".pdf")]
        if lista_pdf:
            scelta = st.radio("Seleziona la dispensa da studiare:", sorted(lista_pdf))
            p_sel = os.path.join("dispense", scelta)
        else: 
            st.warning("Nessun PDF trovato nella cartella 'dispense'.")
            p_sel = None
            
    with cv:
        if p_sel:
            st.info(f"📖 Lettura in corso: **{scelta}**")
            display_pdf(p_sel)
