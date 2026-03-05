# Alpa2 - Versione Stabile con Logout, Promo e Scudo PDF
import streamlit as st
import pandas as pd
import os
import base64
import time
from fpdf import FPDF

# 1. CONFIGURAZIONE E LARGHEZZA UTILE
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- PROTEZIONE AVANZATA (CSS + JS) ---
# --- PROTEZIONE AVANZATA (CSS + JS) ---
st.markdown("""
    <style>
    [data-testid="stAppViewBlockContainer"] { padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .logo-style { font-family: 'Georgia', serif; font-size: 3.5rem !important; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    
    /* 1. TESTO QUESITO E RISPOSTE */
    .quesito-style { color: #FFEB3B !important; font-size: 2rem !important; font-weight: bold !important; line-height: 1.4 !important; }
    div[data-testid="stRadio"] label p { font-size: 1.5rem !important; color: white !important; }
    
    /* 2. CONFIGURAZIONE (DESTRA) - BOX RIDOTTI IN ALTEZZA */
    .nome-materia { 
        font-size: 1.15rem !important; 
        color: #FFD700 !important; 
        font-weight: bold !important; 
        margin-top: 15px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }
    
    /* Riduzione altezza dei box e della scritta Da/A */
    div[data-testid="stTextInput"] { margin-top: -5px !important; }
    
    div[data-testid="stTextInput"] div[data-baseweb="input"] { 
        min-height: 38px !important; /* Ridotto da 55px */
        height: 38px !important;
        background-color: black !important; 
        border: 2px solid #FFD700 !important;
        border-radius: 8px !important;
    }
    
    /* Scritta interna (Numeri Verdi) proporzionata ai nuovi box */
    div[data-testid="stTextInput"] input { 
        font-size: 1.25rem !important; /* Leggermente più piccola per stare nel box */
        color: #00FF00 !important; 
        font-weight: bold !important;
        text-align: center !important;
        padding: 2px !important;
    }

    /* 3. PULSANTI (Come calibrati prima) */
    .stButton button {
        font-size: 1.25rem !important;
        height: 3.2rem !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }

    /* Tasto Esci/Cambia Accesso */
    div[data-testid="stColumn"]:nth-child(2) .stButton button {
        font-size: 1.4rem !important; 
        color: #FF4B4B !important; 
        border: 2px solid #FF4B4B !important;
    }

    /* BLOCO SELEZIONE TESTO ORIGINALE */
    html, body, [data-testid="stAppViewBlockContainer"], * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
    }
    
    /* AREA PROTEZIONE PDF */
    .container-pdf { position: relative; width: 100%; height: 800px; }
    .overlay-stop-popout { position: absolute; top: 0; right: 0; width: 180px; height: 80px; z-index: 99999; background: transparent; }
    </style>

    <script>
    const doc = window.parent.document;
    doc.addEventListener('contextmenu', e => e.preventDefault(), true);
    doc.addEventListener('keydown', e => {
        if (e.ctrlKey && ['c', 'u', 's', 'p'].includes(e.key)) e.preventDefault();
    }, true);
    </script>
    """, unsafe_allow_html=True)
# --- FUNZIONE RECUPERO DATI GOOGLE SHEETS ---
def get_sheet_data(gid):
    try:
        base_url = st.secrets["gsheets_url"].split("/edit")[0]
        csv_url = f"{base_url}/export?format=csv&gid={gid}"
        return pd.read_csv(csv_url)
    except Exception as e:
        return pd.DataFrame()

# --- INIZIALIZZAZIONE STATO ---
if 'autenticato' not in st.session_state: st.session_state.autenticato = False
if 'is_promo' not in st.session_state: st.session_state.is_promo = False 
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'pdf_id_selezionato' not in st.session_state: st.session_state.pdf_id_selezionato = None
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'punteggi' not in st.session_state: st.session_state.punteggi = {"Corretta": 0.75, "Non Data": 0.0, "Errata": -0.25}
if 'codice_dispense_valido' not in st.session_state: st.session_state.codice_dispense_valido = ""

# --- FUNZIONI UTILI ---
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
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(100, 10, pulisci_testo("REPORT FINALE - AlPaTest"), ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(100, 8, pulisci_testo(f"PUNTEGGIO TOTALE: {punti_tot}"), ln=True, align='C')
    pdf.ln(10)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        r_e = str(row['Corretta']).strip()
        pdf.set_font("helvetica", 'B', 10)
        pdf.multi_cell(100, 6, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"))
        pdf.set_font("helvetica", '', 10)
        pdf.multi_cell(100, 6, pulisci_testo(f"Tua Risposta: {r_u} | Risposta Esatta: {r_e}"))
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 110, pdf.get_y()) 
        pdf.ln(4) 
    return bytes(pdf.output())

# --- LOGIN CON BIVIO PROMO/FULL ---
if not st.session_state.autenticato:
    st.markdown('<div style="border: 3px solid #FFD700; border-radius: 20px; padding: 40px; background-color: rgba(0,0,0,0.6); text-align: center; max-width: 650px; margin: 40px auto;"><h1 style="color: #FFD700; font-size: 2.4rem;">🔐 Accesso AlPaTest</h1><p style="color: white; font-size: 1.25rem;">Benvenuta/o. Scegli come accedere.</p></div>', unsafe_allow_html=True)
    
    col_full, col_promo = st.columns(2)
    
    with col_full:
        st.markdown("<p style='color:white; text-align:center;'>Accesso Utenti Registrati</p>", unsafe_allow_html=True)
        codice = st.text_input("Inserisci codice Full:", type="password", label_visibility="collapsed")
        if st.button("ENTRA (VERSIONE FULL)", use_container_width=True):
            df_codici_access = get_sheet_data("184205490")
            if not df_codici_access.empty and codice in df_codici_access.iloc[:,0].astype(str).values:
                st.session_state.autenticato = True
                st.session_state.is_promo = False
                st.rerun()
            else: st.error("Codice errato")
            
    with col_promo:
        st.markdown("<p style='color:white; text-align:center;'>Vuoi provare il sistema?</p>", unsafe_allow_html=True)
        st.write("") 
        if st.button("🚀 PROVA LA PROMO GRATUITA", use_container_width=True, type="primary"):
            st.session_state.autenticato = True
            st.session_state.is_promo = True
            st.rerun()
            
    st.stop()

# --- CARICAMENTO RISORSE ---
@st.cache_data
def carica_discipline():
    df_d = get_sheet_data("652955788") 
    return pd.Series(df_d.Disciplina.values, index=df_d.Codice.astype(str)).to_dict() if not df_d.empty else {}

dict_discipline = carica_discipline()

@st.cache_data
def carica_codici_dispense():
    df_cod = get_sheet_data("170470777")
    return [str(x).strip().lower() for x in df_cod.iloc[:,0].dropna().tolist()] if not df_cod.empty else []

codici_dispense = carica_codici_dispense()

def importa_quesiti():
    try:
        gid_quesiti = "326583620" if st.session_state.is_promo else "0" 
        df = get_sheet_data(gid_quesiti)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        df_p = get_sheet_data("614003066")
        if not df_p.empty:
            st.session_state.punteggi = {"Corretta": float(df_p.iloc[0,0]), "Non Data": float(df_p.iloc[0,1]), "Errata": float(df_p.iloc[0,2])}
        
        num_discipline = len(dict_discipline)
        frames = [df.iloc[int(st.session_state[f"da_{i}"])-1 : int(st.session_state[f"a_{i}"])] for i in range(num_discipline) if st.session_state.get(f"da_{i}","").isdigit()]
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice, st.session_state.risposte_date, st.session_state.start_time = 0, {}, time.time()
    except Exception as e: st.error(f"Errore caricamento: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, 1800 - (time.time() - st.session_state.start_time))
        st.markdown(f'<p class="timer-style">⏱️ {int(rimanente//60):02d}:{int(rimanente%60):02d}</p>', unsafe_allow_html=True)

# --- VISUALIZZAZIONE ---
if st.session_state.pdf_id_selezionato:
    st.markdown('<style>div.stButton > button:first-child { position: fixed; top: 15px; left: 5%; right: 5%; width: 90%; z-index: 999999; border: 2px solid white !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); } .spacer-pdf { margin-top: 70px; }</style>', unsafe_allow_html=True)
    if st.button("⬅️ CHIUDI DISPENSA E TORNA AI QUESITI", type="primary"): 
        st.session_state.pdf_id_selezionato = None
        st.rerun()
    st.markdown('<div class="spacer-pdf"></div>', unsafe_allow_html=True)
    st.markdown(f'''
        <div class="container-pdf">
            <div class="overlay-stop-popout"></div>
            <iframe src="https://drive.google.com/file/d/{st.session_state.pdf_id_selezionato}/preview" 
                    width="100%" height="800" style="border:none; background:white; border-radius:10px;">
            </iframe>
        </div>
    ''', unsafe_allow_html=True)
else:
    t1, t2 = st.columns([7, 3])
    with t1: 
        titolo_app = "AlPaTest (PROMO)" if st.session_state.is_promo else "AlPaTest"
        st.markdown(f'<div class="logo-style">{titolo_app}</div>', unsafe_allow_html=True)
    with t2: 
        mostra_timer()
        if st.button("🚪 Esci / Cambia Accesso", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.fase == "FINE":
        es, er, nd, pt = calcola_risultati()
        st.success(f"### Punteggio Totale: {pt}")
        c_pdf, c_new = st.columns(2)
        with c_pdf: st.download_button("📥 SCARICA REPORT PDF", genera_report_pdf(), "Report_AlPaTest.pdf", "application/pdf")
        with c_new: 
            if st.button("🔄 NUOVA SIMULAZIONE", use_container_width=True): 
                st.session_state.df_filtrato = pd.DataFrame()
                st.session_state.risposte_date = {}
                st.session_state.fase = "PROVA"
                st.rerun()
        for i, row in st.session_state.df_filtrato.iterrows():
            tua, corr = st.session_state.risposte_date.get(i, "N.D."), str(row['Corretta']).strip()
            colore = "#00FF00" if tua == corr else "#FF4B4B"
            st.markdown(f'<div class="report-card"><p style="color:{colore}; font-weight:bold;">Quesito {i+1}</p><p>{row["Domanda"]}</p><p>Tua: {tua} | Corr: {corr}</p></div>', unsafe_allow_html=True)
    else:
        c_sx, c_ct, c_dx = st.columns([2.8, 7, 3.2])
        with c_sx:
            st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;padding:5px;border-radius:5px;font-size:1.1rem;">Navigazione</p>', unsafe_allow_html=True)
            if not st.session_state.df_filtrato.empty:
                with st.container(height=350):
                    for i in range(len(st.session_state.df_filtrato)):
                        icona = "✅" if i in st.session_state.risposte_date else "⚪"
                        if st.button(f"{icona} Quesito {i+1}", key=f"nav_{i}", use_container_width=True): st.session_state.indice = i; st.rerun()
            st.write("---")
            
            with st.expander("📚 DISPENSE", expanded=True):
                if st.session_state.is_promo:
                    st.info("Modalità Promo: Accesso libero.")
                    df_disp = get_sheet_data("272698671") 
                    if not df_disp.empty:
                        sel = st.selectbox("Seleziona:", df_disp.iloc[:, 0].dropna().tolist(), index=None, placeholder="Scegli...")
                        if sel and st.button("📖 APRI DISPENSA"): 
                            st.session_state.pdf_id_selezionato = str(df_disp[df_disp.iloc[:,0] == sel].iloc[0, 1]).strip()
                            st.rerun()
                else:
                    if st.session_state.codice_dispense_valido == "":
                        cod_s = st.text_input("Codice sblocco Full:", type="password")
                        if cod_s.strip().lower() in codici_dispense: 
                            st.session_state.codice_dispense_valido = cod_s.strip().lower()
                            st.rerun()
                    if st.session_state.codice_dispense_valido != "":
                        df_disp = get_sheet_data("2095138066") 
                        if not df_disp.empty:
                            sel = st.selectbox("Seleziona:", df_disp.iloc[:, 0].dropna().tolist(), index=None, placeholder="Scegli...")
                            if sel and st.button("📖 APRI DISPENSA"): 
                                st.session_state.pdf_id_selezionato = str(df_disp[df_disp.iloc[:,0] == sel].iloc[0, 1]).strip()
                                st.rerun()
        with c_ct:
            if not st.session_state.df_filtrato.empty:
                q = st.session_state.df_filtrato.iloc[st.session_state.indice]
                st.markdown(f'<div class="quesito-style">{st.session_state.indice+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
                if pd.notna(q.get('Immagine')) and str(q['Immagine']).strip():
                    img_path = os.path.join(os.path.dirname(__file__), "immagini", str(q['Immagine']).strip())
                    if os.path.exists(img_path): st.image(img_path, width=450)
                
                st.write("")
                opzioni = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
                idx_sel = ["A","B","C","D"].index(st.session_state.risposte_date.get(st.session_state.indice)) if st.session_state.risposte_date.get(st.session_state.indice) else None
                scelta = st.radio("Scegli la risposta:", opzioni, index=idx_sel, key=f"rad_{st.session_state.indice}")
                if scelta: st.session_state.risposte_date[st.session_state.indice] = scelta[0]
                
                st.write("---")
                b1, b2, b3 = st.columns(3)
                if b1.button("⬅️ Precedente", use_container_width=True) and st.session_state.indice > 0: st.session_state.indice -= 1; st.rerun()
                if b2.button("Successivo ➡️", use_container_width=True) and st.session_state.indice < len(st.session_state.df_filtrato)-1: st.session_state.indice += 1; st.rerun()
                if b3.button("🏁 CONSEGNA", use_container_width=True): st.session_state.fase = "FINE"; st.rerun()
                
                with st.expander("💡 HAI BISOGNO DI AIUTO?"):
                    url_help = "https://drive.google.com/file/d/1XtcQswWHCQvErUJ61OMfF97Psq1UvhKo/preview?authuser=0"
                    st.markdown(f'<iframe src="{url_help}" width="100%" height="700"></iframe>', unsafe_allow_html=True)
            else: 
                st.info("Configura gli intervalli a destra e clicca su 'IMPORTA QUESITI'")
        with c_dx:
            st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;padding:5px;border-radius:5px;font-size:1.1rem;">Configurazione</p>', unsafe_allow_html=True)
            num_discipline = len(dict_discipline)
            for i in range(num_discipline):
                cod_mat = list(dict_discipline.keys())[i]
                st.markdown(f"<p class='nome-materia'>{cod_mat}: {dict_discipline.get(cod_mat)}</p>", unsafe_allow_html=True)
                c_d, c_a = st.columns(2)
                c_d.text_input("da", key=f"da_{i}", label_visibility="collapsed", placeholder="Da")
                c_a.text_input("a", key=f"a_{i}", label_visibility="collapsed", placeholder="A")
            st.write("---")
            st.checkbox("Simulazione (30 min)", key="simulazione")
            st.button("IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True, type="primary")




