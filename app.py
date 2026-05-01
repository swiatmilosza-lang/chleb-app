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
        df['Aktywna_Nagroda'] = df['Aktywna_Nagroda'].fillna("")
        return df
    return pd.DataFrame(columns=kolumny)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        return pd.read_csv(PRODUCTS_FILE)
    return pd.DataFrame(columns=['Nagroda', 'Koszt', 'Sztuk'])

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
        st.header("Zaloguj się")
        tab1, tab2 = st.tabs(["Logowanie", "Rejestracja"])
        with tab1:
            l_email = st.text_input("Gmail:")
            l_pass = st.text_input("Hasło:", type="password")
            if st.button("Zaloguj"):
                u_row = st.session_state.db[st.session_state.db['Gmail'] == l_email]
                if not u_row.empty and str(u_row['Haslo'].iloc[0]) == str(l_pass):
                    st.session_state.logged_in_email = l_email
                    st.query_params["user_email"] = l_email
                    st.rerun()
                else: st.error("Błąd danych")
        with tab2:
            n_name = st.text_input("Imię:")
            n_email = st.text_input("Gmail:")
            n_pass = st.text_input("Hasło:", type="password")
            if st.button("Zarejestruj (+50 pkt)"):
                if n_name and n_email and n_pass:
                    n_kod = str(random.randint(10000, 99999))
                    new_u = pd.DataFrame([{'Nazwa': n_name, 'Gmail': n_email, 'Haslo': str(n_pass), 'Kod': n_kod, 'Punkty': 50, 'Aktywna_Nagroda': ""}])
                    st.session_state.db = pd.concat([st.session_state.db, new_u], ignore_index=True)
                    save_data(st.session_state.db)
                    st.session_state.logged_in_email = n_email
                    st.query_params["user_email"] = n_email
                    st.success("Witaj!"); st.rerun()
    else:
        u_row = st.session_state.db[st.session_state.db['Gmail'] == st.session_state.logged_in_email]
        idx = u_row.index
        st.header(f"Witaj, {u_row['Nazwa'].iloc[0]}!")
        c_a, c_b = st.columns(2)
        c_a.metric("Bąbelki", int(u_row['Punkty'].iloc[0]))
        c_b.metric("Kod", u_row['Kod'].iloc[0])
        
        qr = qrcode.make(str(u_row['Kod'].iloc[0]))
        st.image(qr.get_image(), width=150, caption="Twój kod do skanowania")

        st.write("---")
        st.subheader("🎁 Oferta Inżyniera:")
        o_df = load_products()
        for i, r in o_df.iterrows():
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                img_path = os.path.join(IMG_DIR, f"{r['Nagroda']}.jpg")
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else: st.info("Brak foto")
            with col_txt:
                st.subheader(r['Nagroda'])
                st.write(f"Koszt: {r['Koszt']} pkt | Sztuk: {r['Sztuk']}")
                if st.button(f"Aktywuj", key=f"btn_{i}", type="primary" if u_row['Punkty'].iloc[0] >= r['Koszt'] else "secondary"):
                    if u_row['Punkty'].iloc[0] >= r['Koszt'] and r['Sztuk'] > 0:
                        st.session_state.db.loc[idx, 'Punkty'] -= r['Koszt']
                        o_df.loc[i, 'Sztuk'] -= 1
                        save_products(o_df)
                        save_data(st.session_state.db)
                        st.success("Aktywowano!"); st.rerun()

# --- SEKCJA: PANEL SPRZEDAWCY ---
elif menu == "Panel Sprzedawcy":
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "milosz2137":
        st.subheader("🛒 Zarządzanie Magazynem")
        of_df = load_products()
        
        with st.expander("➕ DODAJ PRODUKT I ZDJĘCIE"):
            p_nazwa = st.text_input("Nazwa produktu:")
            p_koszt = st.number_input("Koszt (pkt):", value=100)
            p_sztuk = st.number_input("Ilość sztuk:", value=10)
            
            # TO JEST PRZYCISK DO WYBIERANIA ZDJĘCIA Z KOMPUTERA
            p_foto = st.file_uploader("Wybierz zdjęcie z komputera (JPG)", type=['jpg', 'jpeg', 'png'])
            
            if st.button("ZAPISZ PRODUKT"):
                if p_nazwa:
                    new_p = pd.DataFrame([{'Nagroda':p_nazwa, 'Koszt':p_koszt, 'Sztuk':p_sztuk}])
                    of_df = pd.concat([of_df, new_p], ignore_index=True)
                    save_products(of_df)
                    if p_foto:
                        img = Image.open(p_foto).convert('RGB')
                        img.save(os.path.join(IMG_DIR, f"{p_nazwa}.jpg"))
                    st.success(f"Dodano {p_nazwa}!"); st.rerun()

        st.dataframe(of_df)
        
        st.write("---")
        st.subheader("👥 Obsługa Klienta (Punkty)")
        # Skaner i dodawanie punktów (1zł = 10pkt)
        kwota = st.number_input("Kwota zakupu (zł):", min_value=0)
        kod_k = st.text_input("Kod klienta (5 cyfr):")
        if st.button("DODAJ PUNKTY (10 pkt za 1 zł)"):
            if kod_k in st.session_state.db['Kod'].values:
                idx_k = st.session_state.db[st.session_state.db['Kod'] == kod_k].index
                st.session_state.db.loc[idx_k, 'Punkty'] += (kwota * 10)
                save_data(st.session_state.db)
                st.success(f"Dodano {kwota*10} pkt!"); st.rerun()

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    st.link_button("🔴 MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")















