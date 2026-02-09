import streamlit as st
import pandas as pd
import os
import time
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- LOGIN (Versione Centrata) ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown("""
        <style>
        /* Centra il titolo principale */
        .centered-title { 
            text-align: center; 
            color: #FFD700; 
            font-size: 3.5rem; 
            font-weight: bold; 
            margin-bottom: 2rem; 
        }
        
        /* Centra la casella di input e ne definisce la larghezza */
        div[data-testid="stTextInput"] { 
            width: 450px !important; 
            margin: 0 auto !important; 
        }
        
        /* Stile del testo dentro l'input */
        div[data-testid="stTextInput"] input { 
            height: 70px !important; 
            font-size: 2.5rem !important; 
            text-align: center !important; 
        }
        
        /* Centra l'etichetta sopra l'input */
        div[data-testid="stTextInput"] label { 
            display: flex !important; 
            justify-content: center !important; 
            margin-bottom: 10px !important; 
        }
        div[data-testid="stTextInput"] label p { 
            font-size: 1.6rem !important; 
            color: #FFD700 !important; 
            font-weight: bold !important; 
        }

        /* Stile del pulsante: larghezza 100% rispetto alla sua colonna */
        div.stButton > button { 
            width: 100% !important; 
            height: 65px !important; 
            font-size: 2.2rem !important; 
            background-color: #FFD700 !important; 
            color: black !important; 
            border-radius: 10px !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="centered-title">🔐 Accesso AlPaTest</p>', unsafe_allow_html=True)
    
    # Campo di input centrato dal CSS
    codice = st.text_input("Inserisci il codice di accesso:", type="password").strip()

    # --- CENTRATURA PULSANTE TRAMITE COLONNE ---
    # Creiamo 3 colonne: le laterali vuote spingono quella centrale (larghezza 300px circa)
    col_l, col_btn, col_r = st.columns([1, 1, 1]) 

    with col_btn:
        if st.button("Entra"):
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
    .block-container { padding-top: 4rem !important; padding-bottom: 0rem !important; }
    .logo-style { font-family: 'Georgia', serif; font-size: 3rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; line-height: 1.0; margin-bottom: -10px; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.5rem !important; font-weight: bold !important; line-height: 1.2; }
    .stRadio label p { font-size: 1.2rem !important; color: #FFFFFF !important; font-weight: 500 !important; }
    div[data-testid="stRadio"] > div { align-items: flex-start !important; color: white !important; }
    .timer-style { font-size: 2.5rem; font-weight: bold; text-align: right; }
    .risultato-box { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; color: white; border: 2px solid #FFD700; text-align: center; }
    hr { margin-top: 0.5rem !important; margin-bottom: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'punteggi' not in st.session_state: st.session_state.punteggi = {"Corretta": 0.75, "Non Data": 0.0, "Errata": -0.25}

# --- CARICAMENTO DISCIPLINE ---
if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        df_disc = df_disc.dropna(subset=['Codice', 'Disciplina'])
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except:
        st.session_state.dict_discipline = {}

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
    pdf = FPDF(); pdf.add_page(); pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "REPORT FINALE - AlPaTest", ln=True, align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.cell(190, 10, f"Punteggio: {punti_tot} | Esatte: {esatte} | Errate: {errate} | N.D.: {non_date}", ln=True, align='C')
    pdf.ln(10)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        pdf.set_font("helvetica", 'B', 10)
        pdf.multi_cell(190, 6, pulisci_testo(f"{i+1}. {row['Domanda']}"))
        pdf.set_font("helvetica", '', 10)
        pdf.cell(190, 6, pulisci_testo(f"Tua: {r_u} | Esatta: {row['Corretta']}"), ln=True)
        pdf.ln(2)
    return bytes(pdf.output())

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

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, (30 * 60) - (time.time() - st.session_state.start_time))
        minuti, secondi = int(rimanente // 60), int(rimanente % 60)
        st.markdown(f'<p class="timer-style" style="color:{"#00FF00" if rimanente > 300 else "#FF0000"}">⏱️ {minuti:02d}:{secondi:02d}</p>', unsafe_allow_html=True)
        if rimanente <= 0:
            st.session_state.fase = "CONCLUSIONE"
            st.rerun()

# --- LOGICA DI CONTROLLO FASI (SISTEMA LO SCHERMO BIANCO) ---
if st.session_state.fase in ["CONFERMA", "CONCLUSIONE"]:
    st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
    st.write("---")
    if st.session_state.fase == "CONFERMA":
        st.markdown("<div class="risultato-box"><h2>❓ Vuoi consegnare la prova?</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ SÌ, CONSEGNA", use_container_width=True):
                st.session_state.fase = "CONCLUSIONE"; st.rerun()
        with c2:
            if st.button("❌ NO, CONTINUA", use_container_width=True):
                st.session_state.fase = "PROVA"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        esatte, errate, non_date, punti_tot = calcola_risultati()
        st.markdown(f"""
            <div class="risultato-box">
                <h2>✅ Esame completato!</h2>
                <p style="font-size:2rem;">Punteggio: <b>{punti_tot}</b></p>
                <p>Esatte: {esatte} | Errate: {errate} | N.D.: {non_date}</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.download_button("📩 SCARICA REPORT E CHIUDI", data=genera_report_pdf(), file_name="esito.pdf", on_click=lambda: st.session_state.clear(), use_container_width=True)
    st.stop()

# --- LAYOUT PRINCIPALE ---
t1, t2 = st.columns([7, 3])
with t1: st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
with t2: mostra_timer()
st.markdown("<hr>", unsafe_allow_html=True)

col_sx, col_centro, col_dx = st.columns([2.8, 7, 3.2])

with col_sx:
    st.markdown('<p style="background:#FFF;color:000;text-align:center;font-weight:bold;border-radius:5px;">Elenco domande</p>', unsafe_allow_html=True)
    if not st.session_state.df_filtrato.empty:
        with st.container(height=500):
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            sel = st.radio("Lista", lista, index=st.session_state.indice, label_visibility="collapsed", key=f"nav_{st.session_state.indice}")
            st.session_state.indice = lista.index(sel)

with col_centro:
    if not st.session_state.df_filtrato.empty:
        q = st.session_state.df_filtrato.iloc[st.session_state.indice]
        st.markdown(f'<div class="quesito-style">{st.session_state.indice + 1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
        if pd.notna(q['Immagine']) and str(q['Immagine']).strip() != "":
            img_path = os.path.join("immagini", str(q['Immagine']).strip())
            if os.path.exists(img_path): st.image(img_path, use_container_width=True)
        
        opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
        ans_prec = st.session_state.risposte_date.get(st.session_state.indice)
        idx_prec = ["A","B","C","D"].index(ans_prec) if ans_prec in ["A","B","C","D"] else None
        
        chiave_r = f"r_{st.session_state.indice}"
        def salva_r():
            if chiave_r in st.session_state and st.session_state[chiave_r]:
                st.session_state.risposte_date[st.session_state.indice] = st.session_state[chiave_r][0]

        st.radio("Scelte", opts, key=chiave_r, index=idx_prec, on_change=salva_r, label_visibility="collapsed")
        st.write("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⬅️ Precedente", use_container_width=True):
                if st.session_state.indice > 0: st.session_state.indice -= 1; st.rerun()
        with c2:
            if st.button("Successivo ➡️", use_container_width=True):
                if st.session_state.indice < len(st.session_state.df_filtrato)-1: st.session_state.indice += 1; st.rerun()
        with c3:
            if st.button("🏁 CONSEGNA", use_container_width=True):
                st.session_state.fase = "CONFERMA"; st.rerun()
    else: st.markdown("<h2 style='text-align:center; color:white;'>Configura e premi Importa</h2>", unsafe_allow_html=True)

with col_dx:
    st.markdown('<p style="background:#FFF;color:000;text-align:center;font-weight:bold;border-radius:5px;">Discipline</p>', unsafe_allow_html=True)
    if st.session_state.dict_discipline:
        chiavi = list(st.session_state.dict_discipline.keys())[:9]
        for i, cod in enumerate(chiavi):
            c1, c2, c3 = st.columns([6, 2, 2])
            c1.markdown(f"<p style='font-size:0.8rem; color:white;'><b>{cod}</b></p>", unsafe_allow_html=True)
            st.session_state[f"da_{i}"] = c2.text_input("D", key=f"d_{i}", label_visibility="collapsed")
            st.session_state[f"a_{i}"] = c3.text_input("A", key=f"al_{i}", label_visibility="collapsed")
    st.write("---")
    st.checkbox("Simulazione (30 min)", key="simulazione")
    st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True)

