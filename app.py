import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# 1. CONFIGURAZIONE PAGINA (Larghezza massima per evitare che il report esca fuori)
st.set_page_config(page_title="AlPaTest - Quiz Online", layout="wide")

# 2. FUNZIONE PER GESTIRE LE IMMAGINI
def mostra_immagine(nome_file):
    # Cerca l'immagine nella cartella 'immagini'
    percorso = os.path.join("immagini", nome_file)
    if os.path.exists(percorso):
        st.image(percorso, width=500)
    else:
        st.info(f"Nota: L'immagine {nome_file} verrà visualizzata qui appena caricata nella cartella 'immagini'.")

# --- 3. SISTEMA DI LOGIN ---
if 'autenticato' not in st.session_state:
    st.session_state['autenticato'] = False

if not st.session_state['autenticato']:
    st.title("🔐 Accesso AlPaTest")
    st.write("Inserisci uno dei codici autorizzati per iniziare il quiz.")
    
    # .strip() rimuove spazi vuoti digitati per errore
    codice_inserito = st.text_input("Codice di accesso:", type="password").strip()
    
    # I TUOI CODICI DEFINITIVI
    codici_validi = ["Open", "Studente01"]
    
    if st.button("Accedi"):
        if codice_inserito in codici_validi:
            st.session_state['autenticato'] = True
            st.rerun()
        else:
            st.error("Codice non valido. Riprova o contatta l'amministratore.")
    st.stop()

# --- 4. INTERFACCIA QUIZ (Dopo il Login) ---
st.title("📝 AlPaTest - Sessione Quiz Concorso")
st.success(f"Accesso effettuato con successo!")

# ESEMPIO DI DOMANDA CON IMMAGINE (Domanda 15)
st.markdown("---")
st.subheader("Domanda n. 15")
st.write("Analizza la figura sottostante e seleziona la risposta corretta:")

# Richiamo l'immagine q15.jpg dalla cartella immagini
mostra_immagine("q15.jpg")

risposta_15 = st.radio("Scegli un'opzione:", ["Opzione A", "Opzione B", "Opzione C", "Opzione D"], key="q15")

# --- 5. GENERAZIONE REPORT PDF (Larghezza utile 100%) ---
st.markdown("---")
if st.button("🏁 Concludi Quiz e Genera Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Titolo Report
    pdf.cell(190, 10, "Report Finale AlPaTest", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    # Tabella con larghezza 190mm (il massimo per un foglio A4)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(95, 10, "Riferimento Domanda", border=1, fill=True)
    pdf.cell(95, 10, "Risposta Data", border=1, fill=True, ln=True)
    
    # Dati della risposta
    pdf.cell(95, 10, "Domanda n. 15", border=1)
    pdf.cell(95, 10, str(risposta_15), border=1, ln=True)
    
    # Salvataggio e Download
    pdf_file = "Report_AlPaTest.pdf"
    pdf.output(pdf_file)
    
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📥 Scarica il tuo Report (PDF)",
            data=f,
            file_name="Risultati_AlPaTest.pdf",
            mime="application/pdf"
        )
