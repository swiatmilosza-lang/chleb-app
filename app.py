import streamlit as st
import pandas as pd
import random
import os
import cv2
import numpy as np
import qrcode

# Konfiguracja VIP
st.set_page_config(page_title="Bąbelkowa Aplikacja", page_icon="🥖")

# Styl CSS dla zielonych przycisków
st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "baza_inzynier.csv"
PRODUCTS_FILE = "oferta_inzynier.csv"

# --- FUNKCJE BAZY DANYCH ---
def load_data():
    kolumny = ['Nazwa', 'Gmail', 'Haslo', 'Kod', 'Punkty', 'Aktywna_Nagroda']
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype={'Kod': str, 'Haslo': str, 'Aktywna_Nagroda': str})
        for col in kolumny:
            if col not in df.columns:
                df[col] = "" if col == 'Aktywna_Nagroda' else (0 if col == 'Punkty' else "")
        df['Aktywna_Nagroda'] = df['Aktywna_Nagroda'].fillna("")
        return df[kolumny]
    return pd.DataFrame(columns=kolumny)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        return pd.read_csv(PRODUCTS_FILE)
    return pd.DataFrame([
        {'Nagroda': 'Mini Pizza', 'Koszt': 30, 'Sztuk': 5},
        {'Nagroda': 'Zakwas', 'Koszt': 50, 'Sztuk': 5},
        {'Nagroda': 'Chleb', 'Koszt': 70, 'Sztuk': 5}
    ])

def save_products(df):
    df.to_csv(PRODUCTS_FILE, index=False)

if 'db' not in st.session_state:
    st.session_state.db = load_data()

# Logika automatycznego logowania
if "user_email" in st.query_params:
    email_z_linku = st.query_params["user_email"]
    if email_z_linku in st.session_state.db['Gmail'].values:
        st.session_state.logged_in_email = email_z_linku
    else:
        st.session_state.logged_in_email = None
        st.query_params.clear()
elif "logged_in_email" not in st.session_state:
    st.session_state.logged_in_email = None

# Menu boczne
st.title("🥖 Bąbelkowa Aplikacja")
menu = st.sidebar.radio("Menu", ["Mój Profil", "Panel Sprzedawcy", "YouTube & Info"])

# --- SEKCJA: MÓJ PROFIL ---
if menu == "Mój Profil":
    if st.session_state.logged_in_email is None:
        st.header("Zaloguj się lub załóż konto")
        tab1, tab2 = st.tabs(["Logowanie", "Rejestracja"])
        
        with tab1:
            st.subheader("Zaloguj się")
            login_email = st.text_input("Twój Gmail:", key="login_email")
            login_pass = st.text_input("Hasło:", type="password", key="login_pass")
            
            if st.button("Zaloguj się"):
                user_row = st.session_state.db[st.session_state.db['Gmail'] == login_email]
                if not user_row.empty:
                    poprawne_haslo = str(user_row['Haslo'].iloc[0])
                    if poprawne_haslo == str(login_pass):
                        st.session_state.logged_in_email = login_email
                        st.query_params["user_email"] = login_email
                        st.rerun()
                    else:
                        st.error("Błędne hasło!")
                else:
                    st.error("Nie znaleziono konta.")
        
        with tab2:
            st.subheader("Załóż nowe konto")
            st.warning("⚠️ NIE wpisuj tu prawdziwego hasła do Gmaila!")
            new_name = st.text_input("Twoje Imię:")
            new_email = st.text_input("Twój Gmail:")
            new_pass = st.text_input("Hasło do apki:", type="password")
            
            if st.button("Zarejestruj mnie (+5 pkt!)"):
                if new_name and new_email and new_pass:
                    if new_email not in st.session_state.db['Gmail'].values:
                        nowy_kod = str(random.randint(10000, 99999))
                        nowy_user = pd.DataFrame([{
                            'Nazwa': new_name, 'Gmail': new_email, 'Haslo': str(new_pass), 
                            'Kod': nowy_kod, 'Punkty': 5, 'Aktywna_Nagroda': ""
                        }])
                        st.session_state.db = pd.concat([st.session_state.db, nowy_user], ignore_index=True)
                        save_data(st.session_state.db)
                        
                        st.session_state.logged_in_email = new_email
                        st.query_params["user_email"] = new_email
                        st.success("Witaj w klubie!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Ten adres Gmail jest już zajęty.")
                else:
                    st.warning("Wypełnij wszystkie pola!")

    else:
        user_row = st.session_state.db[st.session_state.db['Gmail'] == st.session_state.logged_in_email]
        if not user_row.empty:
            idx = user_row.index[0]
            name = user_row['Nazwa'].iloc[0]
            kod = user_row['Kod'].iloc[0]
            pkt = user_row['Punkty'].iloc[0]
            aktywna = user_row['Aktywna_Nagroda'].iloc[0]
            
            st.header(f"Witaj, {name}!")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Twoje Zapasy", f"{pkt} Bąbelków")
            with col_b:
                st.metric("Twój Kod", kod)
            
            # Kod QR wygenerowany lokalnie
            qr = qrcode.make(str(kod))
            st.image(qr.get_image(), width=180, caption="Pokaż kod przy stoisku")
            
            if not (pd.isna(aktywna) or str(aktywna).strip() == ""):
                st.warning(f"🎫 MASZ AKTYWNE KUPONY: **{aktywna}**")
                st.info("Pokaż kod powyżej przy stoisku, aby odebrać nagrodę!")

            st.write("---")
            st.subheader("🎁 Aktywuj nagrodę za punkty:")
            
            oferta_df = load_products()
            for index, row in oferta_df.iterrows():
                nagroda = row['Nagroda']
                koszt = row['Koszt']
                s_sztuk = row['Sztuk']
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**{nagroda}** ({koszt} pkt)")
                    st.write(f"Sztuk: {s_sztuk}" if s_sztuk > 0 else "🔴 BRAK")
                with c2:
                    if s_sztuk > 0:
                        btn_typ = "primary" if pkt >= koszt else "secondary"
                        if st.button(f"🟢 Aktywuj" if pkt >= koszt else "Aktywuj", key=f"k_{nagroda}", type=btn_typ):
                            if pkt >= koszt:
                                st.session_state.db.loc[idx, 'Punkty'] -= koszt
                                oferta_df.loc[index, 'Sztuk'] -= 1
                                save_products(oferta_df)
                                stara_n = st.session_state.db.loc[idx, 'Aktywna_Nagroda']
                                st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = nagroda if not stara_n else f"{stara_n}, {nagroda}"
                                save_data(st.session_state.db)
                                st.success(f"Aktywowano {nagroda}!")
                                st.rerun()
                            else:
                                st.error("Brak punktów!")
                    else:
                        st.button("Wyprzedane", key=f"k_{nagroda}", disabled=True)
            
            st.write("---")
            if st.button("Wyloguj"):
                st.session_state.logged_in_email = None
                st.query_params.clear()
                st.rerun()

# --- SEKCJA: PANEL SPRZEDAWCY ---
elif menu == "Panel Sprzedawcy":
    st.header("Panel Admina")
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "milosz2137":
        
        # SKANER
        if 'last_scan' not in st.session_state: st.session_state.last_scan = ""
        img = st.camera_input("Zeskanuj kod QR klienta")
        if img:
            f_bytes = np.asarray(bytearray(img.read()), dtype=np.uint8)
            cv_img = cv2.imdecode(f_bytes, 1)
            det = cv2.QRCodeDetector()
            val, b, s = det.detectAndDecode(cv_img)
            if val: 
                st.session_state.last_scan = val
                st.success(f"Skan OK: {val}")

        st.write("---")
        kod_in = st.text_input("Kod klienta:", value=st.session_state.last_scan)
        
        if kod_in:
            search = st.session_state.db[st.session_state.db['Kod'] == kod_in]
            if not search.empty:
                s_idx = search.index[0]
                st.write(f"**Klient:** {search['Nazwa'].iloc[0]} | **Punkty:** {search['Punkty'].iloc[0]}")
                
                # Wydawanie nagród
                kupony = str(search['Aktywna_Nagroda'].iloc[0]).strip()
                if kupony:
                    st.warning(f"Kupony: {kupony}")
                    lista = [k.strip() for k in kupony.split(",") if k.strip()]
                    for i, k in enumerate(lista):
                        if st.button(f"Wydaj: {k}", key=f"w_{i}_{kod_in}"):
                            lista.pop(i)
                            st.session_state.db.loc[s_idx, 'Aktywna_Nagroda'] = ", ".join(lista)
                            save_data(st.session_state.db)
                            st.rerun()
                
                # DODAWANIE PUNKTÓW Z PRZELICZNIKIEM
                st.write("---")
                p_za_zl = 2 # PRZELICZNIK: 2 pkt za 1 zł
                kwota = st.number_input("Kwota zakupu (zł):", min_value=1, value=10)
                obliczone = kwota * p_za_zl
                st.info(f"Doda: **{obliczone} Bąbelków**")
                
                if st.button("DODAJ PUNKTY"):
                    st.session_state.db.loc[s_idx, 'Punkty'] += obliczone
                    save_data(st.session_state.db)
                    st.success("Dodano!")
                    st.rerun()
            else:
                st.error("Brak kodu!")

        st.write("---")
        # ZARZĄDZANIE MAGAZYNEM
        st.subheader("🛒 Magazyn i Oferta")
        of_df = load_products()
        st.dataframe(of_df)
        with st.expander("Edytuj produkt"):
            n_nazwa = st.text_input("Nazwa:")
            n_koszt = st.number_input("Koszt (pkt):", value=10)
            n_sztuk = st.number_input("Sztuk:", value=5)
            if st.button("Zapisz"):
                if n_nazwa in of_df['Nagroda'].values:
                    of_df.loc[of_df['Nagroda'] == n_nazwa, ['Koszt', 'Sztuk']] = [n_koszt, n_sztuk]
                else:
                    of_df = pd.concat([of_df, pd.DataFrame([{'Nagroda':n_nazwa,'Koszt':n_koszt,'Sztuk':n_sztuk}])])
                save_products(of_df); st.rerun()

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    st.link_button("🔴 MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")












