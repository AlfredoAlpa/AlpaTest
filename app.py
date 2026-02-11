with st.expander("📚 DISPENSE DI STUDIO", expanded=True):
        cod_immesso = st.text_input("Codice + INVIO:", key="cod_dispensa", type="password").strip()
        if cod_immesso != "" and cod_immesso in st.session_state.codici_dispense:
            try:
                # Carica il foglio Google (Sheet ID corretto)
                df_online = pd.read_csv(f"https://docs.google.com/spreadsheets/d/1WjRbERt91YEr4zVr5ZuRdmlJ85CmHreHHRrlMkyv8zs/gviz/tq?tqx=out:csv&sheet=Dispense_online")
                
                # Pulizia nomi colonne
                df_online.columns = [str(c).strip() for c in df_online.columns]
                
                dispense_nomi = df_online["Titolo Dispensa"].dropna().tolist()
                scelta = st.selectbox("Seleziona dispensa:", ["-- Scegli --"] + dispense_nomi)
                
                if scelta != "-- Scegli --":
                    # Recupera l'ID dalla riga selezionata
                    pdf_id = str(df_online[df_online["Titolo Dispensa"] == scelta]["ID_Drive"].values[0]).strip()
                    
                    if st.button("📖 LEGGI ORA", use_container_width=True):
                        st.session_state.pdf_id_selezionato = pdf_id
                        st.session_state.pdf_titolo_selezionato = scelta
                        st.rerun()
            except Exception as e:
                st.error("Caricamento in corso... se l'errore persiste verifica la connessione.")
