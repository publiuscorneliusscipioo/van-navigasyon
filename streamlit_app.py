import os
import pandas as pd
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(page_title="Van-Navigasyon", page_icon="📍", layout="centered")

# Özel CSS ile şıklık ve ortalama
st.markdown("""
    <style>
    .login-container {
        max-width: 350px;
        margin: 0 auto;
        padding: 30px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Excel Dosyasını Doğru Yoldan Okuma
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
                print(f"Hata: {e}")
    return None

df = veri_yukle()

# Oturum Durumu
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col1_right = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("static/logo.png"):
            st.image("static/logo.png", width=220)
        elif os.path.exists("logo.png"):
            st.image("logo.png", width=220)
            
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        
        if st.button("GİRİŞ YAP", use_container_width=True):
            if kadi == "admin" and sifre == "admin":
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Hatalı Kullanıcı Adı veya Şifre!")

# --- HARİTA VE ARAMA EKRANI ---
else:
    # Üst Menü
    baslik_col, cikis_col = st.columns([4, 1])
    with baslik_col:
        st.subheader("Van-Navigasyon")
    with cikis_col:
        if st.button("Çıkış", use_container_width=True):
            st.session_state.giris_yapildi = False
            st.rerun()

    st.markdown("---")

    # Arama Alanı
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        tesisat_no = st.text_input("Tesisat No...", label_visibility="collapsed", placeholder="Tesisat No girin...")
    with col_btn:
        ara_clicked = st.button("ARA", use_container_width=True)

    if ara_clicked or tesisat_no:
        if not tesisat_no:
            st.warning("Lütfen bir tesisat numarası yazın.")
        elif df is None or df.empty:
            st.error("⚠️ Tesisatlar.xlsx dosyası bulunamadı! Lütfen GitHub'da dosyanın ana dizinde veya 'data' klasöründe olduğundan emin olun.")
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
                    
                    # Google Maps Yol Tarifi Butonu
                    gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                    st.markdown(
                        f'<a href="{gmaps_url}" target="_blank" style="display:block; text-align:center; background:#2563eb; color:white; padding:10px; border-radius:4px; text-decoration:none; font-weight:bold; font-size:16px; margin-bottom:15px;">🚗 Yol Tarifi</a>',
                        unsafe_allow_html=True
                    )

                    # Haritada Gösterme
                    harita_verisi = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                    st.map(harita_verisi, zoom=15)