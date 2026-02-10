
# --- LOGIN PROTETTO: BOX RESTRINTO E PULSANTE CENTRATO ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown("""
        <style>
        /* 1. Restringiamo il Box a 550px */
        .login-box-centrale {
            border: 3px solid #FFD700 !important;
            border-radius: 20px;
            padding: 30px;
            width: 550px; 
            margin: 50px auto !important;
            text-align: center;
            background-color: rgba(0, 0, 0, 0.5);
        }

        .titolo-login {
            color: #FFD700 !important;
            font-size: 2.2rem !important;
            font-weight: 900 !important;
            white-space: nowrap !important;
            margin-bottom: 20px !important;
        }

        .istruzione-codice {
            color: #FFFFFF !important;
            font-size: 1.3rem !important;
            font-weight: bold !important;
            margin-bottom: 20px !important;
        }

        /* Il campo di testo rimane come lo hai visto, ma lo centriamo nel box */
        div[data-testid="stTextInput"] {
            width: 90% !important;
            margin: 0 auto !important;
        }

        /* 2. CENTRATURA PULSANTE: Forza il posizionamento al centro */
        div.stButton {
            text-align: center;
            width: 100%;
        }
        
        div.stButton > button {
            width: 200px !important; /* Larghezza fissa per non farlo gigante */
            height: 55px !important;
            background-color: #FFD700 !important;
            color: black !important;
            font-size: 1.6rem !important;
            font-weight: bold !important;
            border-radius: 10px !important;
            margin: 20px auto !important;
            display: block !important; /* Fondamentale per la centratura */
        }
        </style>
    """, unsafe_allow_html=True)

    # Apertura del Box
    st.markdown('<div class="login-box-centrale">', unsafe_allow_html=True)
    st.markdown('<div class="titolo-login">🔐 Accesso AlPaTest</div>', unsafe_allow_html=True)
    st.markdown('<div class="istruzione-codice">Inserisci il codice di accesso:</div>', unsafe_allow_html=True)

    # Campo di testo
    codice = st.text_input("", type="password", label_visibility="collapsed", key="pwd_center").strip()
    
    # Pulsante (ora centrato grazie al display:block e margin:auto)
    if st.button("ENTRA"):
        if codice.lower() in ["open", "studente01"]:
            st.session_state.autenticato = True
            st.rerun()
        else:
            st.error("Codice errato")

    # Chiusura del Box
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
    # --- ELEMENTI DELLA PAGINA ---
    st.markdown('<p class="centered-title">🔐 Accesso AlPaTest</p>', unsafe_allow_html=True)
    
    codice = st.text_input("Inserisci il codice di accesso:", type="password").strip()
    
    if st.button("Entra"):
        if codice.lower() in ["open", "studente01"]:
            st.session_state.autenticato = True
            st.rerun()
        else:
            st.error("Codice errato")
    st.stop()

# --- CSS GENERALE (Applicato dopo il login) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .block-container { padding-top: 4rem !important; padding-bottom: 0rem !important; }
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
    div[data-testid="stRadio"] > div { align-items: flex-start !important; color: white !important; }
    .timer-style { font-size: 2.5rem; font-weight: bold; text-align: right; }
    .stButton>button { height: 50px !important; font-weight: bold !important; }
    .risultato-box { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; color: white; border: 1px solid #FFD700; }
    hr { margin-top: 0.5rem !important; margin-bottom: 1rem !important; }
    .stAlert p { font-size: 0.9rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"

# --- CARICAMENTO DISCIPLINE DA EXCEL (Con pulizia nan) ---
if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        # Rimuove righe vuote o con nan
        df_disc = df_disc.dropna(subset=['Codice', 'Disciplina'])
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except Exception as e:
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
    esatte = 0
    errate = 0
    non_date = 0
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
    larghezza_utile = 100 
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(larghezza_utile, 10, pulisci_testo("REPORT FINALE - AlPaTest"), ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(larghezza_utile, 8, pulisci_testo(f"PUNTEGGIO TOTALE: {punti_tot}"), ln=True, align='C')
    pdf.set_font("helvetica", '', 10)
    pdf.cell(larghezza_utile, 6, pulisci_testo(f"Esatte: {esatte} | Errate: {errate} | Non date: {non_date}"), ln=True, align='C')
    pdf.ln(10)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        r_e = str(row['Corretta']).strip()
        pdf.set_font("helvetica", 'B', 11)
        pdf.multi_cell(larghezza_utile, 7, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"), border=0, align='L')
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(larghezza_utile, 7, pulisci_testo(f"Tua Risposta: {r_u} | Risposta Esatta: {r_e}"), border=0, align='L')
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5) 
    return bytes(pdf.output())

def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        try:
            df_p = pd.read_excel("quiz.xlsx", sheet_name="Punteggi")
            st.session_state.punteggi["Corretta"] = float(df_p.iloc[0, 0])
            st.session_state.punteggi["Non Data"] = float(df_p.iloc[0, 1])
            st.session_state.punteggi["Errata"] = float(df_p.iloc[0, 2])
        except:
            st.warning("Foglio 'Punteggi' non trovato. Uso valori predefiniti.")
        frames = []
        # Legge fino a 9 righe (compatibile con la colonna dx)
        for i in range(len(st.session_state.dict_discipline)):
            d, a = st.session_state.get(f"da_{i}",""), st.session_state.get(f"a_{i}","")
            if d.isdigit() and a.isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.start_time = time.time()
    except Exception as e:
        st.error(f"Errore caricamento Excel: {e}")

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

# --- LOGICA NAVIGAZIONE ---
if st.session_state.fase in ["CONFERMA", "CONCLUSIONE"]:
    st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
    if st.session_state.fase == "CONFERMA":
        with st.container(border=True):
            st.write("## ❓ Vuoi consegnare la prova?")
            c1, c2 = st.columns(2)
            if c1.button("Sì, CONSEGNA", use_container_width=True):
                st.session_state.fase = "CONCLUSIONE"
                st.rerun()
            if c2.button("No, CONTINUA", use_container_width=True):
                st.session_state.fase = "PROVA"
                st.rerun()
    else:
        esatte, errate, non_date, punti_tot = calcola_risultati()
        st.markdown(f"""
            <div class="risultato-box">
                <h2>✅ Esame completato!</h2>
                <p style="font-size:1.5rem;">Punteggio Totale: <b>{punti_tot}</b></p>
                <p>Risposte Esatte: {esatte} | Errate: {errate} | Non date: {non_date}</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("📩 SCARICA REPORT E CHIUDI", 
                           data=genera_report_pdf(), 
                           file_name="esito_esame.pdf", 
                           on_click=lambda: st.session_state.clear(), 
                           use_container_width=True)
    st.stop()

# --- LAYOUT PRINCIPALE ---
t1, t2 = st.columns([7, 3])
with t1: st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
with t2: mostra_timer()

st.markdown("<hr style='border:1px solid rgba(255,255,255,0.1)'>", unsafe_allow_html=True)

col_sx, col_centro, col_dx = st.columns([2.8, 7, 3.2])

with col_sx:
    st.markdown('<p style="background:#FFFFFF;color:black;text-align:center;font-weight:bold;border-radius:5px;padding:3px;margin-bottom:10px;">Elenco domande</p>', unsafe_allow_html=True)
    if not st.session_state.df_filtrato.empty:
        with st.container(height=550, border=False):
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            sel = st.radio("Lista", lista, index=st.session_state.indice, label_visibility="collapsed", key=f"nav_{st.session_state.indice}")
            st.session_state.indice = lista.index(sel)

with col_centro:
    if not st.session_state.df_filtrato.empty:
        q = st.session_state.df_filtrato.iloc[st.session_state.indice]
        st.markdown(f'<div class="quesito-style">{st.session_state.indice + 1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        
        if pd.notna(q['Immagine']) and str(q['Immagine']).strip() != "":
            img_nome = str(q['Immagine']).strip()
            percorso_img = os.path.join("immagini", img_nome)
            if os.path.exists(percorso_img):
                sx, centro, dx = st.columns([1, 4, 1]) 
                with centro:
                    st.image(percorso_img, use_container_width=True)
            else:
                st.info(f"Immagine {img_nome} non trovata.")
        
        opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
        ans_prec = st.session_state.risposte_date.get(st.session_state.indice)
        idx_prec = ["A","B","C","D"].index(ans_prec) if ans_prec in ["A","B","C","D"] else None
        
        def salva_r(): 
            chiave = f"r_{st.session_state.indice}"
            if chiave in st.session_state and st.session_state[chiave]:
                st.session_state.risposte_date[st.session_state.indice] = st.session_state[chiave][0]

        st.radio("Scelte", opts, key=f"r_{st.session_state.indice}", index=idx_prec, on_change=salva_r, label_visibility="collapsed")
        
        st.write("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ Precedente"):
            if st.session_state.indice > 0:
                st.session_state.indice -= 1
                st.rerun()
        if c2.button("🏁 CONSEGNA", use_container_width=True):
            st.session_state.fase = "CONFERMA"
            st.rerun()
        if c3.button("Successivo ➡️"):
            if st.session_state.indice < len(st.session_state.df_filtrato) - 1:
                st.session_state.indice += 1
                st.rerun()
    else:
        st.markdown("<h2 style='color:white;text-align:center;'><br>Configura e premi Importa</h2>", unsafe_allow_html=True)

with col_dx:
    st.markdown('<p style="background:#FFFFFF;color:black;text-align:center;font-weight:bold;border-radius:5px;padding:3px;margin-bottom:10px;">Discipline e Gruppi</p>', unsafe_allow_html=True)
    
    if st.session_state.dict_discipline:
        # Mostriamo fino a 9 righe basandoci sulle chiavi del dizionario caricato
        chiavi = list(st.session_state.dict_discipline.keys())[:9]
        
        for i, cod in enumerate(chiavi):
            testo = st.session_state.dict_discipline[cod]
            # Colonne: testo largo, input "Da" stretto, input "A" stretto
            c1, c2, c3 = st.columns([6, 2, 2])
            
            with c1:
                st.markdown(f"<p style='font-size:0.85rem; color:white; margin-top:5px; line-height:1.2;'><b>{cod}</b>: {testo}</p>", unsafe_allow_html=True)
            
            with c2:
                st.text_input("Dal", key=f"da_{i}", placeholder="Da", label_visibility="collapsed", max_chars=6)
            
            with c3:
                st.text_input("Al", key=f"a_{i}", placeholder="A", label_visibility="collapsed", max_chars=6)
    
    st.write("---")
    st.checkbox("Simulazione (30 min)", key="simulazione")
    st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True, disabled=not st.session_state.df_filtrato.empty)






