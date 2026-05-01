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
        {'Nagroda': 'Zakwas świeży', 'Koszt': 150, 'Sztuk': 5},
        {'Nagroda': 'Zakwas suszony', 'Koszt': 300, 'Sztuk': 5},
        {'Nagroda': 'Chleb', 'Koszt': 500, 'Sztuk': 5}
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
            l_email = st.text_input("Twój Gmail:", key="l_email")
            l_pass = st.text_input("Hasło:", type="password", key="l_pass")
            if st.button("Zaloguj się"):
                u_row = st.session_state.db[st.session_state.db['Gmail'] == l_email]
                if not u_row.empty:
                    if str(u_row['Haslo'].iloc[0]) == str(l_pass):
                        st.session_state.logged_in_email = l_email
                        st.query_params["user_email"] = l_email
                        st.rerun()
                    else: st.error("Błędne hasło!")
                else: st.error("Brak konta.")
        
        with tab2:
            st.subheader("Nowe konto (+50 Bąbelków!)")
            n_name = st.text_input("Imię:")
            n_email = st.text_input("Gmail:")
            n_pass = st.text_input("Hasło:", type="password")
            if st.button("Zarejestruj mnie"):
                if n_name and n_email and n_pass:
                    if n_email not in st.session_state.db['Gmail'].values:
                        n_kod = str(random.randint(10000, 99999))
                        new_u = pd.DataFrame([{'Nazwa': n_name, 'Gmail': n_email, 'Haslo': str(n_pass), 'Kod': n_kod, 'Punkty': 50, 'Aktywna_Nagroda': ""}])
                        st.session_state.db = pd.concat([st.session_state.db, new_u], ignore_index=True)
                        save_data(st.session_state.db)
                        st.session_state.logged_in_email = n_email
                        st.query_params["user_email"] = n_email
                        st.success("Witaj!"); st.balloons(); st.rerun()
                    else: st.error("E-mail zajęty.")

    else:
        u_row = st.session_state.db[st.session_state.db['Gmail'] == st.session_state.logged_in_email]
        if not u_row.empty:
            idx = u_row.index
            name, kod, pkt, aktywna = u_row['Nazwa'].iloc[0], u_row['Kod'].iloc[0], u_row['Punkty'].iloc[0], u_row['Aktywna_Nagroda'].iloc[0]
            
            st.header(f"Witaj, {name}!")
            c_a, c_b = st.columns(2)
            c_a.metric("Bąbelki", f"{pkt}")
            c_b.metric("Twój Kod", kod)
            
            # QR lokalny
            qr = qrcode.make(str(kod))
            st.image(qr.get_image(), width=180, caption="Pokaż kod przy stoisku")
            
            if aktywna:
                st.warning(f"🎫 MASZ KUPONY: {aktywna}")

            st.write("---")
            st.subheader("🎁 Aktywuj nagrodę:")
            o_df = load_products()
            for i, r in o_df.iterrows():
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{r['Nagroda']}** ({r['Koszt']} pkt)")
                    st.write(f"Sztuk: {r['Sztuk']}" if r['Sztuk'] > 0 else "🔴 BRAK")
                with col2:
                    if r['Sztuk'] > 0:
                        btn_t = "primary" if pkt >= r['Koszt'] else "secondary"
                        if st.button(f"🟢 Aktywuj" if pkt >= r['Koszt'] else "Aktywuj", key=f"k_{r['Nagroda']}", type=btn_t):
                            if pkt >= r['Koszt']:
                                st.session_state.db.loc[idx, 'Punkty'] -= r['Koszt']
                                o_df.loc[i, 'Sztuk'] -= 1
                                save_products(o_df)
                                stara = st.session_state.db.loc[idx, 'Aktywna_Nagroda']
                                st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = r['Nagroda'] if not stara else f"{stara}, {r['Nagroda']}"
                                save_data(st.session_state.db)
                                st.success(f"Aktywowano!"); st.rerun()
                    else: st.button("Wyprzedane", key=f"k_{r['Nagroda']}", disabled=True)
            
            if st.button("Wyloguj"):
                st.session_state.logged_in_email = None
                st.query_params.clear(); st.rerun()

# --- SEKCJA: PANEL SPRZEDAWCY ---
elif menu == "Panel Sprzedawcy":
    st.header("Panel Admina")
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "milosz2137":
        # Skaner
        if 'last_scan' not in st.session_state: st.session_state.last_scan = ""
        img = st.camera_input("Zeskanuj kod QR")
        if img:
            f_b = np.asarray(bytearray(img.read()), dtype=np.uint8)
            cv_i = cv2.imdecode(f_b, 1)
            val, b, s = cv2.QRCodeDetector().detectAndDecode(cv_i)
            if val: 
                st.session_state.last_scan = val
                st.success(f"Odczytano: {val}")

        st.write("---")
        k_in = st.text_input("Kod klienta:", value=st.session_state.last_scan)
        if k_in:
            search = st.session_state.db[st.session_state.db['Kod'] == k_in]
            if not search.empty:
                s_idx = search.index
                st.write(f"**Klient:** {search['Nazwa'].iloc[0]} | **Punkty:** {search['Punkty'].iloc[0]}")
                
                # Wydawanie
                k_str = str(search['Aktywna_Nagroda'].iloc[0]).strip()
                if k_str:
                    lista = [k.strip() for k in k_str.split(",") if k.strip()]
                    for i, k in enumerate(lista):
                        if st.button(f"Wydaj: {k}", key=f"w_{i}_{k_in}"):
                            lista.pop(i)
                            st.session_state.db.loc[s_idx, 'Aktywna_Nagroda'] = ", ".join(lista)
                            save_data(st.session_state.db); st.rerun()
                
                # Punkty (1zł = 10pkt)
                st.write("---")
                p_za_zl = 10
                kwota = st.number_input("Kwota (zł):", min_value=1, value=10)
                st.info(f"Doda: **{kwota * p_za_zl} Bąbelków**")
                if st.button("DODAJ PUNKTY"):
                    st.session_state.db.loc[s_idx, 'Punkty'] += (kwota * p_za_zl)
                    save_data(st.session_state.db); st.success("Dodano!"); st.rerun()

        st.write("---")
        st.subheader("🛒 Magazyn i Oferta")
        of_df = load_products()
        st.dataframe(of_df)
        with st.expander("➕ Edytuj ofertę"):
            n_naz = st.text_input("Produkt:")
            n_kos = st.number_input("Koszt:", value=100)
            n_szt = st.number_input("Sztuk:", value=10)
            if st.button("Zapisz produkt"):
                if n_naz in of_df['Nagroda'].values:
                    of_df.loc[of_df['Nagroda'] == n_naz, ['Koszt', 'Sztuk']] = [n_kos, n_szt]
                else:
                    of_df = pd.concat([of_df, pd.DataFrame([{'Nagroda':n_naz,'Koszt':n_kos,'Sztuk':n_szt}])])
                save_products(of_df); st.rerun()
        with st.expander("🗑️ Usuń produkt"):
            if not of_df.empty:
                del_p = st.selectbox("Co usunąć?", of_df['Nagroda'].values)
                if st.button("Potwierdź usunięcie produktu"):
                    of_df = of_df[of_df['Nagroda'] != del_p]
                    save_products(of_df); st.rerun()

        st.write("---")
        st.subheader("👥 Zarządzanie Klientami")
        st.dataframe(st.session_state.db)
        with st.expander("👤 Usuń konto klienta"):
            if not st.session_state.db.empty:
                del_user = st.selectbox("Wybierz konto do skasowania:", st.session_state.db['Nazwa'].values)
                if st.button("USUŃ KONTO NA ZAWSZE"):
                    st.session_state.db = st.session_state.db[st.session_state.db['Nazwa'] != del_user]
                    save_data(st.session_state.db)
                    st.success(f"Usunięto konto: {del_user}"); st.rerun()

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    st.link_button("🔴 MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")













