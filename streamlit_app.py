import os
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# Sayfa Yapılandırması
st.set_page_config(page_title="Van-Navigasyon", page_icon="📍", layout="wide")

# Excel Dosyası Yükleme
@st.cache_data
def veri_yukle():
    yollar = [
        os.path.join("data", "Tesisatlar.xlsx"),
        "Tesisatlar.xlsx"
    ]
    for yol in yollar:
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

# Oturum Durumu
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
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

# --- HARİTA VE ARAMA EKRANI ---
else:
    st.markdown("### 🔎 Tesisat Arama")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        tesisat_no = st.text_input("Tesisat No", placeholder="Tesisat No...")
    with col2:
        ara_clicked = st.button("ARA")
    with col3:
        if st.button("Çıkış"):
            st.session_state.giris_yapildi = False
            st.rerun()

    st.markdown("---")

    if ara_clicked:
        if not tesisat_no:
            st.warning("Lütfen bir tesisat numarası yazın.")
        elif df is None or df.empty:
            st.error("⚠️ Tesisatlar.xlsx dosyası bulunamadı! Lütfen 'data' klasörüne ekleyin.")
        else:
            bulunan = df[df["Tesisat"] == tesisat_no.strip()]
            if bulunan.empty:
                st.error("Bu tesisat numarası bulunamadı!")
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

                if lat is None or lon is None:
                    st.error("Bu tesisata ait geçerli koordinat bulunamadı!")
                else:
                    st.success(f"Tesisat Bulundu: {tesisat_no}")

                    # Folium Haritası
                    m = folium.Map(location=[lat, lon], zoom_start=16)
                    folium.Marker(
                        [lat, lon],
                        popup=f"Tesisat: {tesisat_no}<br><a href='https://www.google.com/maps/dir/?api=1&destination={lat},{lon}' target='_blank'>Yol Tarifi</a>"
                    ).add_to(m)

                    st_folium(m, width=700, height=500)
