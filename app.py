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
            width: 95% !important; max-width: 550px !important;
            margin: 40px auto !important; text-align: center !important;
        }
        .titolo-box { color: #FFD700 !important; font-size: 2.3rem !important; font-weight: 900 !important; display: block !important; }
        .istruzione-box { color: white !important; font-size: 1.2rem !important; display: block !important; margin-bottom: 25px !important; }
        div.stButton > button { width: 160px !important; background-color: #FFD700 !important; color: black !important; font-weight: bold !important; }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<span class="titolo-box">🔐 Accesso AlPaTest</span>', unsafe_allow_html=True)
        st.markdown('<span class="istruzione-box">Inserisci il codice di accesso:</span>', unsafe_allow_html=True)
        codice = st.text_input("", type="password", label_visibility="collapsed", key="login_v3").strip()
        if st.button("ENTRA", key="btn_v3"):
            if codice.lower() in ["open", "studente01"]:
                st.session_state.autenticato = True
                st.rerun()
            else:
                st.error("Codice errato")
    st.stop()

# --- CSS GENERALE ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .logo-style { font-family: 'Georgia', serif; font-size: 3.1rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; line-height: 1.0; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.6rem !important; font-weight: bold !important; }
    .stRadio label p { font-size: 1.3rem !important; color: #FFFFFF !important; }
    .timer-style { font-size: 2.6rem; font-weight: bold; text-align: right; }
    p, span, label { font-size: 1.1rem !important; } 
    hr { margin: 10px 0; border-color: rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'pdf_selezionato' not in st.session_state: st.session_state.pdf_selezionato = None

if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        df_disc = df_disc.dropna(subset=['Codice', 'Disciplina'])
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except: st.session_state.dict_discipline = {}

if 'codici_dispense' not in st.session_state:
    try:
        df_cod = pd.read_excel("quiz.xlsx", sheet_name="Dispensecod", header=None)
        st.session_state.codici_dispense = [str(x).strip() for x in df_cod[0].dropna().tolist()]
    except: st.session_state.codici_dispense = []

if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None

# --- FUNZIONI ---
def display_pdf_safe(file_path):
    """Visualizzatore che usa l'oggetto per massima compatibilità"""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    pdf_display = f'''
        <object data="data:application/pdf;base64,{base64_pdf}#toolbar=1" type="application/pdf" width="100%" height="850px">
            <div style="background:white; color:black; padding:30px; text-align:center; border-radius:10px;">
                <h4>Visualizzazione non supportata direttamente</h4>
                <p>Chrome ha bloccato l'anteprima. Clicca qui sotto per leggere:</p>
                <a href="data:application/pdf;base64,{base64_pdf}" download="dispensa.pdf" 
                   style="background-color:#FFD700; color:black; padding:10px 20px; text-decoration:none; font-weight:bold; border-radius:5px;">
                   ⬇️ APRI DISPENSA
                </a>
            </div>
        </object>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)

def pulisci_testo(testo):
    if pd.isna(testo) or testo == "": return " "
    repls = {'’':"'",'‘':"'",'“':'"','”':'"','–':'-','à':'a','è':'e','é':'e','ì':'i','ò':'o','ù':'u'}
    t = str(testo)
    for k,v in repls.items(): t = t.replace(k,v)
    return t.encode('latin-1','replace').decode('latin-1')

def calcola_risultati():
    esatte, errate, non_date = 0, 0, 0
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i)
        if r_u is None: non_date += 1
        elif r_u == str(row['Corretta']).strip(): esatte += 1
        else: errate += 1
    punti = (esatte * 0.75) + (errate * -0.25)
    return esatte, errate, non_date, round(punti, 2)

def genera_report_pdf():
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    lu = 100
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(lu, 10, pulisci_testo("REPORT FINALE - AlPaTest"), ln=True, align='C')
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        pdf.set_font("helvetica", 'B', 10)
        pdf.multi_cell(lu, 6, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"), border=0)
        pdf.set_font("helvetica", '', 10)
        pdf.multi_cell(lu, 6, pulisci_testo(f"Tua: {r_u} | Corretta: {row['Corretta']}"), border=0)
        pdf.ln(2)
    return bytes(pdf.output())

def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        frames = []
        for i in range(9):
            d, a = st.session_state.get(f"da_{i}",""), st.session_state.get(f"a_{i}","")
            if d.strip().isdigit() and a.strip().isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice, st.session_state.risposte_date, st.session_state.start_time = 0, {}, time.time()
            st.rerun()
    except Exception as e: st.error(f"Errore: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time is not None and st.session_state.get("simulazione", False):
        rimanente = max(0, 1800 - (time.time() - st.session_state.start_time))
        m, s = int(rimanente // 60), int(rimanente % 60)
        st.markdown(f'<p class="timer-style" style="color:#00FF00">⏱️ {m:02d}:{s:02d}</p>', unsafe_allow_html=True)

# --- INTERFACCIA ---
t1, t2 = st.columns([7, 3])
with t1: st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
with t2: mostra_timer()
st.markdown("<hr>", unsafe_allow_html=True)

col_sx, col_centro, col_dx = st.columns([2.8, 7, 3.2])

with col_sx:
    st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;border-radius:5px;padding:5px;">Elenco domande</p>', unsafe_allow_html=True)
    if not st.session_state.df_filtrato.empty:
        with st.container(height=300):
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            sel = st.radio("L", lista, index=st.session_state.indice, key=f"n_{st.session_state.indice}", label_visibility="collapsed")
            st.session_state.indice = lista.index(sel)
    
    st.write("---")
    with st.expander("📚 DISPENSE DI STUDIO", expanded=True):
        cod_immesso = st.text_input("Codice + INVIO:", key="cod_dispensa", type="password").strip()
        if cod_immesso != "" and cod_immesso in st.session_state.codici_dispense:
            st.success("Sbloccato!")
            cartella = "static" if os.path.exists("static") else "dispense"
            if os.path.exists(cartella):
                files = [f for f in os.listdir(cartella) if f.endswith(".pdf")]
                files.sort()
                scelta = st.selectbox("Seleziona dispensa:", ["-- Scegli --"] + files, key="select_pdf")
                if scelta != "-- Scegli --":
                    if st.button("📖 LEGGI ORA", use_container_width=True):
                        st.session_state.pdf_selezionato = scelta
                        st.rerun()
                    with open(os.path.join(cartella, scelta), "rb") as f:
                        st.download_button("⬇️ SCARICA PDF", data=f, file_name=scelta, key=f"dl_{scelta}", use_container_width=True)
        elif cod_immesso != "": st.error("Codice errato")

with col_centro:
    if st.session_state.pdf_selezionato:
        st.markdown(f"### 📖 Studio: {st.session_state.pdf_selezionato}")
        if st.button("🔙 CHIUDI E TORNA AL QUIZ", type="primary"):
            st.session_state.pdf_selezionato = None
            st.rerun()
        
        cartella = "static" if os.path.exists("static") else "dispense"
        percorso_pdf = os.path.join(cartella, st.session_state.pdf_selezionato)
        if os.path.exists(percorso_pdf):
            display_pdf_safe(percorso_pdf)
        else:
            st.error("File non trovato.")
    
    elif not st.session_state.df_filtrato.empty:
        q = st.session_state.df_filtrato.iloc[st.session_state.indice]
        st.markdown(f'<div class="quesito-style">{st.session_state.indice + 1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
        if pd.notna(q['Immagine']) and str(q['Immagine']).strip() != "":
            img_path = os.path.join("immagini", str(q['Immagine']))
            if os.path.exists(img_path):
                st.image(img_path, width=450)
        
        opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
        ans_prec = st.session_state.risposte_date.get(st.session_state.indice)
        idx_prec = ["A","B","C","D"].index(ans_prec) if ans_prec in ["A","B","C","D"] else None
        
        def salva_r(): 
            if f"r_{st.session_state.indice}" in st.session_state:
                st.session_state.risposte_date[st.session_state.indice] = st.session_state[f"r_{st.session_state.indice}"][0]

        st.radio("S", opts, key=f"r_{st.session_state.indice}", index=idx_prec, on_change=salva_r, label_visibility="collapsed")
        st.write("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ Prec."):
            if st.session_state.indice > 0: st.session_state.indice -= 1; st.rerun()
        if c2.button("🏁 CONSEGNA", use_container_width=True): st.session_state.fase = "CONCLUSIONE"; st.rerun()
        if c3.button("Succ. ➡️"):
            if st.session_state.indice < len(st.session_state.df_filtrato) - 1: st.session_state.indice += 1; st.rerun()
    else: st.markdown("<h2 style='text-align:center;'><br>Configura e premi Importa</h2>", unsafe_allow_html=True)

with col_dx:
    st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;border-radius:5px;padding:5px;">Discipline</p>', unsafe_allow_html=True)
    for i in range(9):
        nomi = list(st.session_state.dict_discipline.keys())
        cod = nomi[i] if i < len(nomi) else f"G{i+1}"
        testo = st.session_state.dict_discipline.get(cod, f"Gruppo {i+1}")
        c1, c2, c3 = st.columns([6, 2, 2])
        with c1: st.markdown(f"<p style='font-size:0.9rem; color:white;'><b>{cod}</b>: {testo}</p>", unsafe_allow_html=True)
        with c2: st.text_input("D", key=f"da_{i}", placeholder="Da", label_visibility="collapsed")
        with c3: st.text_input("A", key=f"a_{i}", placeholder="A", label_visibility="collapsed")
    st.write("---")
    st.checkbox("Simulazione (30 min)", key="simulazione")
    st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True)

if st.session_state.fase == "CONCLUSIONE":
    esatte, errate, non_date, punti = calcola_risultati()
    st.markdown(f"<div style='background:white;padding:20px;border-radius:10px;color:black;'><h2>Fine! Punti: {punti}</h2></div>", unsafe_allow_html=True)
    st.download_button("Scarica Report", data=genera_report_pdf(), file_name="report.pdf", on_click=lambda: st.session_state.clear())
    st.stop()
