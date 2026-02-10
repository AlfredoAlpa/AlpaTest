import streamlit as st
import pandas as pd
import os
import time
import base64
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- LOGIN ROBUSTO E RESPONSIVE ---
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
            width: 95% !important;
            max-width: 550px !important;
            margin: 40px auto !important;
            text-align: center !important;
        }
        .titolo-box {
            color: #FFD700 !important;
            font-size: clamp(1.5rem, 6vw, 2.2rem) !important;
            font-weight: 900 !important;
            display: block !important;
            margin-bottom: 10px !important;
        }
        .istruzione-box {
            color: white !important;
            font-size: 1.1rem !important;
            display: block !important;
            margin-bottom: 25px !important;
        }
        div[data-testid="stTextInput"] {
            width: 80% !important;
            margin: 0 auto !important;
        }
        div.stButton > button {
            width: 160px !important;
            background-color: #FFD700 !important;
            color: black !important;
            font-weight: bold !important;
            margin: 25px auto !important;
            display: block !important;
        }
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
    .logo-style { 
        font-family: 'Georgia', serif; 
        font-size: 3rem; 
        font-weight: bold; 
        color: #FFD700; 
        text-shadow: 2px 2px 4px #000;
        line-height: 1.0; 
        margin-bottom: -10px; 
    }
    .quesito-style { color: #FFEB3B !important; font-size: 1.5rem !important; font-weight: bold !important; line-height: 1.2; }
    .stRadio label p { font-size: 1.2rem !important; color: #FFFFFF !important; font-weight: 500 !important; }
    .timer-style { font-size: 2.5rem; font-weight: bold; text-align: right; }
    .risultato-box { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; color: white; border: 1px solid #FFD700; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if 'vista' not in st.session_state: st.session_state.vista = "TEST"
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        df_disc = df_disc.dropna(subset=['Codice', 'Disciplina'])
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except:
        st.session_state.dict_discipline = {}

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

def calcola_risultati():
    esatte, errate, non_date = 0, 0, 0
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i)
        r_e = str(row['Corretta']).strip()
        if r_u is None: non_date += 1
        elif r_u == r_e: esatte += 1
        else: errate += 1
    punti = (esatte * st.session_state.punteggi["Corretta"]) + (non_date * st.session_state.punteggi["Non Data"]) + (errate * st.session_state.punteggi["Errata"])
    return esatte, errate, non_date, round(punti, 2)

def genera_report_pdf():
    esatte, errate, non_date, punti_tot = calcola_risultati()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, pulisci_testo("REPORT FINALE - AlPaTest"), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, pulisci_testo(f"PUNTEGGIO TOTALE: {punti_tot}"), ln=True)
    pdf.set_font("Arial", '', 11)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        r_e = str(row['Corretta']).strip()
        pdf.multi_cell(190, 7, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"))
        pdf.multi_cell(190, 7, pulisci_testo(f"Tua: {r_u} | Esatta: {r_e}"))
        pdf.ln(2)
    return bytes(pdf.output(dest='S'))

def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        frames = []
        for i in range(len(st.session_state.dict_discipline)):
            d, a = st.session_state.get(f"da_{i}",""), st.session_state.get(f"a_{i}","")
            if d.isdigit() and a.isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.start_time = time.time()
    except Exception as e: st.error(f"Errore: {e}")

def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, (30 * 60) - (time.time() - st.session_state.start_time))
        minuti, secondi = int(rimanente // 60), int(rimanente % 60)
        colore = "#00FF00" if rimanente > 300 else "#FF0000"
        st.markdown(f'<p class="timer-style" style="color:{colore}">⏱️ {minuti:02d}:{secondi:02d}</p>', unsafe_allow_html=True)
        if rimanente <= 0:
            st.session_state.fase = "CONCLUSIONE"
            st.rerun()

# --- LOGICA NAVIGAZIONE (VIGILE) ---
if st.session_state.vista == "TEST":
    # SCHERMATA FINALE
    if st.session_state.fase in ["CONFERMA", "CONCLUSIONE"]:
        st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
        if st.session_state.fase == "CONFERMA":
            with st.container(border=True):
                st.write("## ❓ Vuoi consegnare la prova?")
                c1, c2 = st.columns(2)
                if c1.button("Sì, CONSEGNA", use_container_width=True):
                    st.session_state.fase = "CONCLUSIONE"; st.rerun()
                if c2.button("No, CONTINUA", use_container_width=True):
                    st.session_state.fase = "PROVA"; st.rerun()
        else:
            esatte, errate, non_date, punti_tot = calcola_risultati()
            st.markdown(f'<div class="risultato-box"><h2>✅ Completato! Punti: {punti_tot}</h2></div>', unsafe_allow_html=True)
            st.download_button("📩 REPORT", data=genera_report_pdf(), file_name="esito.pdf", on_click=lambda: st.session_state.clear())
        st.stop()

    # LAYOUT TEST
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
            with st.container(height=550, border=False):
                lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
                sel = st.radio("L", lista, index=st.session_state.indice, label_visibility="collapsed", key="nav_main")
                st.session_state.indice = lista.index(sel)

    with col_centro:
        if not st.session_state.df_filtrato.empty:
            q = st.session_state.df_filtrato.iloc[st.session_state.indice]
            st.markdown(f'<div class="quesito-style">{st.session_state.indice+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
            if pd.notna(q['Immagine']) and str(q['Immagine']).strip() != "":
                path_img = os.path.join("immagini", str(q['Immagine']).strip())
                if os.path.exists(path_img): st.image(path_img, width=450)
            
            opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
            ans_prec = st.session_state.risposte_date.get(st.session_state.indice)
            idx_prec = ["A","B","C","D"].index(ans_prec) if ans_prec in ["A","B","C","D"] else None
            
            def salva_r():
                chiave = f"r_{st.session_state.indice}"
                if chiave in st.session_state: st.session_state.risposte_date[st.session_state.indice] = st.session_state[chiave][0]

            st.radio("S", opts, key=f"r_{st.session_state.indice}", index=idx_prec, on_change=salva_r, label_visibility="collapsed")
            st.write("---")
            c1, c2, c3 = st.columns(3)
            if c1.button("⬅️ Prec"): st.session_state.indice = max(0, st.session_state.indice-1); st.rerun()
            if c2.button("🏁 CONSEGNA"): st.session_state.fase = "CONFERMA"; st.rerun()
            if c3.button("Succ ➡️"): st.session_state.indice = min(len(st.session_state.df_filtrato)-1, st.session_state.indice+1); st.rerun()
        else: st.info("Configura a destra e premi Importa")

    with col_dx:
        st.markdown('<p style="background:white; color:black; text-align:center; font-weight:bold; border-radius:5px; padding:3px;">Discipline</p>', unsafe_allow_html=True)
        if st.session_state.dict_discipline:
            for i, (cod, testo) in enumerate(st.session_state.dict_discipline.items()):
                if i < 9:
                    c1, c2, c3 = st.columns([6, 2, 2])
                    c1.markdown(f"<small>{cod}: {testo}</small>", unsafe_allow_html=True)
                    st.session_state[f"da_{i}"] = c2.text_input("D", key=f"da_{i}", label_visibility="collapsed")
                    st.session_state[f"a_{i}"] = c3.text_input("A", key=f"a_{i}", label_visibility="collapsed")
        st.checkbox("Simulazione (30 min)", key="simulazione")
        st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True, disabled=not st.session_state.df_filtrato.empty)

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
        else: st.warning("Nessun PDF trovato nella cartella"); p_sel = None
    with cv:
        if p_sel: display_pdf(p_sel)
