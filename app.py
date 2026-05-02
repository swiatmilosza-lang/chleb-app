import streamlit as st
import pandas as pd
import random
import os
import cv2
import numpy as np
import qrcode
from PIL import Image

# Konfiguracja VIP
st.set_page_config(page_title="Bąbelkowa Aplikacja", page_icon="🥖")

# Styl CSS
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
IMG_DIR = "img"

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

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
        {'Nagroda': 'Zakwas świeży', 'Koszt': 150, 'Sztuk': 10},
        {'Nagroda': 'Zakwas suszony', 'Koszt': 300, 'Sztuk': 10},
        {'Nagroda': 'Chleb', 'Koszt': 500, 'Sztuk': 10}
    ])

def save_products(df):
    df.to_csv(PRODUCTS_FILE, index=False)

# Inicjalizacja baz
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
        user_mask = st.session_state.db['Gmail'] == st.session_state.logged_in_email
        if user_mask.any():
            name = st.session_state.db.loc[user_mask, 'Nazwa'].iloc[0]
            kod = st.session_state.db.loc[user_mask, 'Kod'].iloc[0]
            pkt = st.session_state.db.loc[user_mask, 'Punkty'].iloc[0]
            aktywna = st.session_state.db.loc[user_mask, 'Aktywna_Nagroda'].iloc[0]
            
            st.header(f"Witaj, {name}!")
            c_a, c_b = st.columns(2)
            c_a.metric("Bąbelki", f"{pkt}")
            c_b.metric("Twój Kod", kod)
            
            qr = qrcode.make(str(kod))
            st.image(qr.get_image(), width=180)
            
            if aktywna and str(aktywna).strip() != "":
                st.warning(f"🎫 KUPONY: {aktywna}")

            st.write("---")
            st.subheader("🎁 Oferta Inżyniera:")
            o_df = load_products()
            for i, r in o_df.iterrows():
                col_img, col_txt = st.columns(2)
                with col_img:
                    img_path = os.path.join(IMG_DIR, f"{r['Nagroda']}.jpg")
                    if os.path.exists(img_path): st.image(img_path, use_container_width=True)
                    else: st.info("📸")
                with col_txt:
                    st.write(f"**{r['Nagroda']}**")
                    st.write(f"Koszt: {r['Koszt']} pkt | Sztuk: {r['Sztuk']}")
                    btn_t = "primary" if pkt >= r['Koszt'] else "secondary"
                    if st.button(f"🟢 Aktywuj" if pkt >= r['Koszt'] else "Zbieraj dalej", key=f"k_{r['Nagroda']}", type=btn_t):
                        if pkt >= r['Koszt'] and r['Sztuk'] > 0:
                            # Bezpośrednia modyfikacja za pomocą maski, aby uniknąć błędów ValueError
                            st.session_state.db.loc[user_mask, 'Punkty'] -= r['Koszt']
                            o_df.loc[i, 'Sztuk'] -= 1
                            save_products(o_df)
                            
                            stara_n = st.session_state.db.loc[user_mask, 'Aktywna_Nagroda'].iloc[0]
                            nowa_n = r['Nagroda'] if not stara_n else f"{stara_n}, {r['Nagroda']}"
                            st.session_state.db.loc[user_mask, 'Aktywna_Nagroda'] = nowa_n
                            
                            save_data(st.session_state.db)
                            st.success(f"Aktywowano!")
                            st.rerun()
            
            if st.button("Wyloguj"):
                st.session_state.logged_in_email = None
                st.query_params.clear(); st.rerun()

# --- SEKCJA: PANEL SPRZEDAWCY ---
elif menu == "Panel Sprzedawcy":
    st.header("🔐 Autoryzacja")
    pin = st.text_input("Hasło VIP:", type="password")
    
    if pin == "milosz2137":
        of_df = load_products()
        
        st.subheader("📸 Skaner QR")
        if 'last_scan' not in st.session_state: st.session_state.last_scan = ""
        img_cam = st.camera_input("Zeskanuj kod QR klienta")
        if img_cam:
            f_b = np.asarray(bytearray(img_cam.read()), dtype=np.uint8)
            cv_i = cv2.imdecode(f_b, 1)
            val, b, s = cv2.QRCodeDetector().detectAndDecode(cv_i)
            if val: 
                st.session_state.last_scan = val
                st.success(f"Odczytano: {val}")

        st.write("---")
        k_in = st.text_input("Kod klienta:", value=st.session_state.last_scan)
        if k_in:
            search_mask = st.session_state.db['Kod'] == k_in
            if search_mask.any():
                st.write(f"**Klient:** {st.session_state.db.loc[search_mask, 'Nazwa'].iloc[0]} | **Punkty:** {st.session_state.db.loc[search_mask, 'Punkty'].iloc[0]}")
                k_str = str(st.session_state.db.loc[search_mask, 'Aktywna_Nagroda'].iloc[0]).strip()
                
                if k_str and k_str != "nan" and k_str != "":
                    lista = [k.strip() for k in k_str.split(",") if k.strip()]
                    for i, k in enumerate(lista):
                        if st.button(f"Wydaj: {k}", key=f"w_{i}_{k_in}"):
                            lista.pop(i)
                            st.session_state.db.loc[search_mask, 'Aktywna_Nagroda'] = ", ".join(lista)
                            save_data(st.session_state.db); st.rerun()
                
                p_za_zl = 10
                kwota = st.number_input("Kwota (zł):", min_value=1, value=10)
                if st.button("DODAJ PUNKTY"):
                    st.session_state.db.loc[search_mask, 'Punkty'] += (kwota * p_za_zl)
                    save_data(st.session_state.db); st.success("Dodano!"); st.rerun()
            else:
                st.error("Brak kodu!")

        st.write("---")
        st.subheader("🛒 Zarządzanie Magazynem")
        st.dataframe(of_df)
        
        with st.expander("➕ Dodaj Produkt i ZDJĘCIE"):
            n_naz = st.text_input("Nazwa produktu:")
            n_kos = st.number_input("Koszt (pkt):", value=100)
            n_szt = st.number_input("Sztuk:", value=10)
            p_foto = st.file_uploader("Wgraj zdjęcie (JPG)", type=['jpg', 'jpeg', 'png'])
            if st.button("Zapisz"):
                if n_naz:
                    if n_naz in of_df['Nagroda'].values:
                        of_df.loc[of_df['Nagroda'] == n_naz, ['Koszt', 'Sztuk']] = [n_kos, n_szt]
                    else:
                        new_p = pd.DataFrame([{'Nagroda':n_naz, 'Koszt':n_kos, 'Sztuk':n_szt}])
                        of_df = pd.concat([of_df, new_p], ignore_index=True)
                    if p_foto:
                        img = Image.open(p_foto).convert('RGB')
                        img.save(os.path.join(IMG_DIR, f"{n_naz}.jpg"))
                    save_products(of_df); st.rerun()

        with st.expander("🗑️ Usuń produkt"):
            if not of_df.empty:
                del_p = st.selectbox("Co usunąć?", of_df['Nagroda'].values)
                if st.button("Usuń"):
                    of_df = of_df[of_df['Nagroda'] != del_p]
                    save_products(of_df); st.rerun()

        st.write("---")
        st.subheader("👥 Klienci")
        st.dataframe(st.session_state.db)

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    st.link_button("🔴 MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")

















