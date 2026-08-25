import os
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Van-Navigasyon", page_icon="📍", layout="wide")

@st.cache_data
def veri_yukle():
    yol = "Tesisatlar.xlsx"
    if os.path.exists(yol):
        try:
            df = pd.read_excel(yol, dtype={"Tesisat": str})
            df.columns = df.columns.astype(str).str.strip()
            df["Tesisat"] = df["Tesisat"].astype(str).str.strip()
            return df
        except Exception as e:
            st.error(f"Excel okuma hatası: {e}")
    return None

df = veri_yukle()

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# Kalıcı konum hafızası için session_state tanımları
if "son_lat" not in st.session_state:
    st.session_state.son_lat = 38.5
if "son_lon" not in st.session_state:
    st.session_state.son_lon = 43.4
if "son_zoom" not in st.session_state:
    st.session_state.son_zoom = 12
if "aktif_tesisat" not in st.session_state:
    st.session_state.aktif_tesisat = None
if "hata_mesaji" not in st.session_state:
    st.session_state.hata_mesaji = None

# --- GİRİŞ ---
if not st.session_state.giris_yapildi:
    st.title("📍 Van-Navigasyon")
    with st.form("login_form"):
        kadi = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password", placeholder="Şifre")
        giris = st.form_submit_button("GİRİŞ YAP")
        if giris:
            if kadi == "admin" and sifre == "admin":
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Hatalı Kullanıcı Adı veya Şifre!")

# --- HARİTA ---
else:
    st.markdown("### 🔎 Tesisat Arama")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        tesisat_no = st.text_input("Tesisat No", placeholder="Tesisat No...", value=st.session_state.aktif_tesisat if st.session_state.aktif_tesisat else "")
    with col2:
        ara_clicked = st.button("ARA", use_container_width=True)
    with col3:
        if st.button("Çıkış", use_container_width=True):
            st.session_state.giris_yapildi = False
            st.session_state.aktif_tesisat = None
            st.rerun()

    st.markdown("---")

    if df is None or df.empty:
        st.error("⚠️ Tesisatlar.xlsx dosyası bulunamadı! Ana dizine yükleyin.")
    else:
        # Butona basıldığında veya arama kutusuna yeni değer girildiğinde arama yap
        if ara_clicked and tesisat_no:
            bulunan = df[df["Tesisat"] == tesisat_no.strip()]
            if bulunan.empty:
                st.session_state.hata_mesaji = "Bu tesisat numarası bulunamadı!"
                st.session_state.aktif_tesisat = None
            else:
                row = bulunan.iloc[0]
                lat, lon = None, None
                for l_col, b_col in [("Enlem.1", "Boylam.1"), ("Enlem", "Boylam")]:
                    try:
                        val_lat = float(str(row[l_col]).replace(",", "."))
                        val_lon = float(str(row[b_col]).replace(",", "."))
                        if val_lat != 0 and val_lon != 0:
                            lat, lon = val_lat, val_lon
                            break
                    except:
                        pass

                if lat and lon:
                    st.session_state.son_lat = lat
                    st.session_state.son_lon = lon
                    st.session_state.son_zoom = 16
                    st.session_state.aktif_tesisat = tesisat_no.strip()
                    st.session_state.hata_mesaji = None
                else:
                    st.session_state.hata_mesaji = "Bu tesisata ait geçerli koordinat bulunamadı!"
                    st.session_state.aktif_tesisat = None

        # Hata veya başarı mesajlarını ekranda tutma
        if st.session_state.hata_mesaji:
            st.error(st.session_state.hata_mesaji)
        elif st.session_state.aktif_tesisat:
            st.success(f"Tesisat Bulundu: {st.session_state.aktif_tesisat}")

        # Folium Haritasını Oluşturma
        m = folium.Map(location=[st.session_state.son_lat, st.session_state.son_lon], zoom_start=st.session_state.son_zoom)

        # Eğer aktif bir tesisat varsa haritaya kalıcı marker ekle
        if st.session_state.aktif_tesisat:
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={st.session_state.son_lat},{st.session_state.son_lon}"
            popup_html = f"""
            <b>Tesisat:</b> {st.session_state.aktif_tesisat}<br><br>
            <a href='{gmaps_url}' target='_blank'
               style='background:#2563eb; color:white; padding:6px 12px;
                      text-decoration:none; border-radius:4px;
                      display:inline-block; font-weight:bold; font-size:13px;'>
                 Yol Tarifi Al
            </a>
            """
            folium.Marker([st.session_state.son_lat, st.session_state.son_lon], popup=popup_html).add_to(m)

        # Haritayı ekrana bas
        st_folium(m, width=900, height=500)