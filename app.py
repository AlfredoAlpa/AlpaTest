import streamlit as st
import pandas as pd
import os
import time
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# Parametri Google Sheets (Il tuo foglio specifico)
SHEET_ID = "1WjRbERt91YEr4zVr5ZuRdmlJ85CmHreHHRrlMkyv8zs"
# Usiamo gid=0 per essere sicuri di prendere il primo foglio indipendentemente dal nome
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

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
        codice = st.text_input("", type="password", label_visibility="collapsed", key="login_main").strip()
        if st.button("ENTRA"):
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
    .logo-style { font-family: 'Georgia', serif; font-size: 3.1rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.6rem !important; font-weight: bold !important; }
    .timer-style { font-size: 2.6rem; font-weight: bold; text-align: right; color: #00FF00; }
    hr { border-color: rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE DATI ---
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'pdf_id_selezionato' not in st.session_state: st.session_state.pdf_id_selezionato = None
if 'pdf_titolo_selezionato' not in st.session_state: st.session_state.pdf_titolo_selezionato = None
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()

# Caricamento Discipline e Codici Dispense da quiz.xlsx
@st.cache_data
def carica_risorse_locali():
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        d_disc = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
        df_cod = pd.read_excel("quiz.xlsx", sheet_name="Dispensecod", header=None)
        c_disp = [str(x).strip() for x in df_cod[0].dropna().tolist()]
        return d_disc, c_disp
    except:
        return {}, []

dict_discipline, codici_dispense = carica_risorse_locali()

# --- FUNZIONI ---
def display_google_pdf(file_id):
    """Visualizzatore PDF tramite iframe di Google Drive"""
    url = f"https://drive.google.com/file/d/{file_id}/preview"
    st.markdown(f'<iframe src="{url}" width="100%" height="800" style="border:none; background:white; border-radius:10px;"></iframe>', unsafe_allow_html=True)

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
    except Exception as e: st.error(f"Errore nel file Excel: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time is not None and st.session_state.get("simulazione", False):
        rimanente = max(0, 1800 - (time.time() - st.session_state.start_time))
        m, s = int(rimanente // 60), int(rimanente % 60)
        st.markdown(f'<p class="timer-style">⏱️ {m:02d}:{s:02d}</p>', unsafe_allow_html=True)

# --- LAYOUT PRINCIPALE ---
t1, t2 = st.columns([7, 3])
with t1: st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
with t2: mostra_timer()
st.markdown("<hr>", unsafe_allow_html=True)

col_sx, col_centro, col_dx = st.columns([2.8, 7, 3.2])

# --- COLONNA SINISTRA: NAVIGATION & DISPENSE ---
with col_sx:
    st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;border-radius:5px;padding:5px;">Navigazione</p>', unsafe_allow_html=True)
    if not st.session_state.df_filtrato.empty:
        with st.container(height=300):
            for i in range(len(st.session_state.df_filtrato)):
                icona = "✅" if i in st.session_state.risposte_date else "⚪"
                if st.button(f"{icona} Quesito {i+1}", key=f"nav_{i}", use_container_width=True):
                    st.session_state.indice = i
                    st.rerun()
    
    st.write("---")
    with st.expander("📚 DISPENSE DI STUDIO", expanded=True):
        cod_immesso = st.text_input("Codice Sblocco:", type="password", key="lock").strip()
        if cod_immesso in codici_dispense and cod_immesso != "":
            try:
                # Lettura remota da Google Sheets
                df_online = pd.read_csv(SHEET_URL)
                df_online.columns = [str(c).strip() for c in df_online.columns]
                
                # Usa gli indici delle colonne (1 per titolo, 2 per ID) per massima sicurezza
                titoli = df_online.iloc[:, 1].dropna().tolist()
                scelta = st.selectbox("Scegli dispensa:", ["-- Seleziona --"] + titoli)
                
                if scelta != "-- Seleziona --":
                    # Estrae l'ID corrispondente
                    raw_id = str(df_online[df_online.iloc[:, 1] == scelta].iloc[0, 2]).strip()
                    if st.button("📖 APRI DISPENSA", use_container_width=True):
                        st.session_state.pdf_id_selezionato = raw_id
                        st.session_state.pdf_titolo_selezionato = scelta
                        st.rerun()
            except:
                st.error("Errore di collegamento al database dispense.")
        elif cod_immesso != "":
            st.error("Codice non valido")

# --- COLONNA CENTRALE: QUIZ O PDF ---
with col_centro:
    if st.session_state.pdf_id_selezionato:
        st.markdown(f"### 📖 Studio: {st.session_state.pdf_titolo_selezionato}")
        if st.button("🔙 CHIUDI E TORNA AI QUIZ", type="primary"):
            st.session_state.pdf_id_selezionato = None
            st.rerun()
        display_google_pdf(st.session_state.pdf_id_selezionato)
    
    elif not st.session_state.df_filtrato.empty:
        q = st.session_state.df_filtrato.iloc[st.session_state.indice]
        st.markdown(f'<div class="quesito-style">{st.session_state.indice + 1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
        
        if pd.notna(q['Immagine']) and str(q['Immagine']).strip() != "":
            img_path = os.path.join("immagini", str(q['Immagine']))
            if os.path.exists(img_path): st.image(img_path, width=500)
        
        opzioni = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
        risposta_prec = st.session_state.risposte_date.get(st.session_state.indice)
        idx_selezione = ["A","B","C","D"].index(risposta_prec) if risposta_prec else None
        
        scelta_u = st.radio("Seleziona la risposta:", opzioni, index=idx_selezione, key=f"quiz_{st.session_state.indice}")
        
        if scelta_u:
            st.session_state.risposte_date[st.session_state.indice] = scelta_u[0]

        st.write("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ Precedente") and st.session_state.indice > 0:
            st.session_state.indice -= 1
            st.rerun()
        if c2.button("🏁 CONSEGNA", use_container_width=True):
            st.session_state.fase = "FINE"
            st.rerun()
        if c3.button("Successivo ➡️") and st.session_state.indice < len(st.session_state.df_filtrato) - 1:
            st.session_state.indice += 1
            st.rerun()
    else:
        st.markdown("<h2 style='text-align:center;'><br>Configura i gruppi a destra e premi Importa</h2>", unsafe_allow_html=True)

# --- COLONNA DESTRA: CONFIGURAZIONE ---
with col_dx:
    st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;border-radius:5px;padding:5px;">Configura Test</p>', unsafe_allow_html=True)
    for i in range(9):
        cod = list(dict_discipline.keys())[i] if i < len(dict_discipline) else f"G{i+1}"
        nome = dict_discipline.get(cod, f"Gruppo {i+1}")
        c_a, c_b, c_c = st.columns([5, 2.5, 2.5])
        with c_a: st.markdown(f"<p style='font-size:0.85rem; color:white;'>{cod}: {nome}</p>", unsafe_allow_html=True)
        with c_b: st.text_input("Da", key=f"da_{i}", label_visibility="collapsed", placeholder="Da")
        with c_c: st.text_input("A", key=f"a_{i}", label_visibility="collapsed", placeholder="A")
    
    st.write("---")
    st.checkbox("Modalità Simulazione (30 min)", key="simulazione")
    st.button("IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True, type="primary")

# --- SCHERMATA FINALE ---
if st.session_state.fase == "FINE":
    st.balloons()
    esatte = sum(1 for i, r in st.session_state.risposte_date.items() if r == str(st.session_state.df_filtrato.iloc[i]['Corretta']).strip())
    totali = len(st.session_state.df_filtrato)
    st.success(f"### Test Completato! \n\n Risposte esatte: {esatte} su {totali}")
    if st.button("Ricomincia"):
        st.session_state.clear()
        st.rerun()
