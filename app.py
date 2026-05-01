import qrcode
import streamlit as st
import pandas as pd
import random
import os
import cv2
import numpy as np

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
            
            # Kod QR dla klienta
            qr_img = qrcode.make(str(kod))
            st.image(qr_img.get_image(), width=150, caption="Pokaż kod przy stoisku")

            
            if not (pd.isna(aktywna) or str(aktywna).strip() == ""):
                st.warning(f"🎫 MASZ AKTYWNE KUPONY: **{aktywna}**")
                st.info("Pokaż kod 5-cyfrowy przy stoisku!")

            st.write("---")
            st.subheader("🎁 Aktywuj nagrodę za punkty:")
            
            oferta_df = load_products()
            
            for index, row in oferta_df.iterrows():
                nagroda = row['Nagroda']
                koszt = row['Koszt']
                sztuk = row['Sztuk']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{nagroda}** ({koszt} Bąbelków)")
                    if sztuk > 0:
                        st.write(f"Zostało: {sztuk} szt.")
                    else:
                        st.write("🔴 BRAK SZTUK")
                        
                with col2:
                    if sztuk > 0:
                        if pkt >= koszt:
                            typ = "primary"
                            tekst = "🟢 Aktywuj"
                        else:
                            typ = "secondary"
                            tekst = "Aktywuj"
                        
                        if st.button(tekst, key=f"kup_{nagroda}", type=typ):
                            if pkt >= koszt:
                                st.session_state.db.loc[idx, 'Punkty'] -= koszt
                                oferta_df.loc[index, 'Sztuk'] -= 1
                                save_products(oferta_df)
                                
                                if pd.isna(aktywna) or str(aktywna).strip() == "":
                                    st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = nagroda
                                else:
                                    st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = f"{aktywna}, {nagroda}"
                                save_data(st.session_state.db)
                                st.success(f"Aktywowano: {nagroda}!")
                                st.rerun()
                            else:
                                st.error("Za mało punktów!")
                    else:
                        st.button("Wyprzedane", key=f"kup_{nagroda}", disabled=True)
            
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
        
        st.subheader("📸 Szybki Skaner QR")
        # Inicjalizacja zmiennej w sesji
        if 'zeskanowany_kod' not in st.session_state:
            st.session_state.zeskanowany_kod = ""
            
        img_file = st.camera_input("Skieruj aparat na kod QR klienta")
        
        if img_file:
            file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
            opencv_image = cv2.imdecode(file_bytes, 1)
            
            detector = cv2.QRCodeDetector()
            data, bbox, straight_qrcode = detector.detectAndDecode(opencv_image)
            
            if data:
                st.session_state.zeskanowany_kod = data
                st.success(f"Odczytano kod: {data}")
        
        st.write("---")
        st.subheader("👥 Obsługa Klienta")
        
        # Kod wstawia się automatycznie ze skanera
        kod_input = st.text_input("Wpisz 5-cyfrowy kod klienta:", value=st.session_state.zeskanowany_kod)
        
        if kod_input:
            user_search = st.session_state.db[st.session_state.db['Kod'] == kod_input]
            if not user_search.empty:
                idx = user_search.index[0]
                klient = user_search['Nazwa'].iloc[0]
                punkty_klienta = user_search['Punkty'].iloc[0]
                kupon = user_search['Aktywna_Nagroda'].iloc[0]
                
                st.write(f"**Klient:** {klient} | **Punkty:** {punkty_klienta}")
                
                kupon_str = str(kupon).strip()
                if kupon_str != "" and not pd.isna(kupon):
                    st.warning(f"🔔 Klient chce odebrać: **{kupon_str}**")
                    lista_kuponow = [k.strip() for k in kupon_str.split(",") if k.strip()]
                    
                    for i, k in enumerate(lista_kuponow):
                        if st.button(f"Wydaj: {k}", key=f"wydaj_{k}_{i}_{idx}"):
                            lista_kuponow.pop(i)
                            nowa_lista = ", ".join(lista_kuponow)
                            st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = nowa_lista
                            save_data(st.session_state.db)
                            st.success(f"Wydano {k}!")
                            st.rerun()
                else:
                    st.info("Brak aktywnych nagród.")
                
                st.write("---")
                ile_pkt = st.number_input("Dodaj punkty za zakupy:", value=10)
                if st.button("DODAJ PUNKTY"):
                    st.session_state.db.loc[idx, 'Punkty'] += ile_pkt
                    save_data(st.session_state.db)
                    st.success(f"Dodano! Klient ma teraz {st.session_state.db.loc[idx, 'Punkty']} pkt.")
                    st.rerun()
            else:
                st.error("Nie znaleziono takiego kodu.")
        
        st.write("---")
        
        st.subheader("🛒 Zarządzanie Ofertą (Magazyn)")
        oferta_df = load_products()
        st.dataframe(oferta_df)
        
        with st.expander("➕ Dodaj lub Edytuj Produkt"):
            p_name = st.text_input("Nazwa nagrody:")
            p_cost = st.number_input("Koszt (Bąbelki):", min_value=1, value=10)
            p_stock = st.number_input("Ilość sztuk:", min_value=0, value=5)
            
            if st.button("Zapisz Produkt w Ofercie"):
                if p_name:
                    if p_name in oferta_df['Nagroda'].values:
                        ofer_idx = oferta_df[oferta_df['Nagroda'] == p_name].index[0]
                        oferta_df.loc[ofer_idx, 'Koszt'] = p_cost
                        oferta_df.loc[ofer_idx, 'Sztuk'] = p_stock
                        st.success(f"Zaktualizowano produkt: {p_name}")
                    else:
                        nowy_p = pd.DataFrame([{'Nagroda': p_name, 'Koszt': p_cost, 'Sztuk': p_stock}])
                        oferta_df = pd.concat([oferta_df, nowy_p], ignore_index=True)
                        st.success(f"Dodano nowy produkt: {p_name}")
                    
                    save_products(oferta_df)
                    st.rerun()
                else:
                    st.warning("Wpisz nazwę nagrody!")
                    
        with st.expander("🗑️ Usuń Produkt z Oferty"):
            delete_name = st.selectbox("Wybierz produkt do usunięcia:", oferta_df['Nagroda'].values)
            if st.button("Usuń trwale ten produkt"):
                oferta_df = oferta_df[oferta_df['Nagroda'] != delete_name]
                save_products(oferta_df)
                st.success(f"Usunięto produkt: {delete_name}")
                st.rerun()
                    
        st.subheader("Baza Klientów")
        st.dataframe(st.session_state.db)

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    # Naturalne wplecenie linku
    st.write("Tworzę rzemieślnicze wypieki i ciekawe aplikacje!")
    st.link_button("🔴 WEJDŹ NA MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")
    st.write("Zostaw subskrypcję, aby wesprzeć moje projekty.")











