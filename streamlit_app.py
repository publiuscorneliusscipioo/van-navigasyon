import os
import pandas as pd
import streamlit as st

# Sayfa Yapılandırması ve Geniş Mod
st.set_page_config(page_title="Van-Navigasyon", page_icon="📍", layout="wide")

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
    st.markdown("""
        <style>
        .stApp { background-color: #f4f6f8; }
        .login-card {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            width: 320px;
            margin: 80px auto;
            text-align: center;
        }
        .login-card img {
            max-width: 180px;
            height: auto;
            margin: 0 auto 15px auto;
            display: block;
        }
        .login-title {
            color: #0f766e;
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        </style>
        
        <div class="login-card">
    """, unsafe_allow_html=True)

    if os.path.exists("static/logo.png"):
        st.image("static/logo.png", width=180)
    elif os.path.exists("logo.png"):
        st.image("logo.png", width=180)

    st.markdown('<div class="login-title">Van-Navigasyon</div>', unsafe_allow_html=True)

    kadi = st.text_input("Kullanıcı Adı", key="kadi_input", placeholder="Kullanıcı Adı")
    sifre = st.text_input("Şifre", type="password", key="sifre_input", placeholder="Şifre")

    if st.button("GİRİŞ YAP", use_container_width=True):
        if kadi == "admin" and sifre == "admin":
            st.session_state.giris_yapildi = True
            st.rerun()
        else:
            st.error("Hatalı Kullanıcı Adı veya Şifre!")

    st.markdown("</div>", unsafe_allow_html=True)

# --- HARİTA VE ARAMA EKRANI ---
else:
    # Üst Menü Tasarımı
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .top-bar {
            background: #0f766e;
            padding: 10px 15px;
            border-radius: 4px;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    col_title, col_input, col_ara, col_cikis = st.columns([2.5, 3, 1, 1])
    
    with col_title:
        st.markdown("<h3 style='color: #0f766e; margin: 0; padding-top: 5px;'>Van-Navigasyon</h3>", unsafe_allow_html=True)
    
    with col_input:
        tesisat_no = st.text_input("Tesisat No", label_visibility="collapsed", placeholder="Tesisat No...")
    
    with col_ara:
        ara_clicked = st.button("ARA", use_container_width=True)
        
    with col_cikis:
        cikis_clicked = st.button("Çıkış", use_container_width=True)
        if cikis_clicked:
            st.session_state.giris_yapildi = False
            st.rerun()

    st.markdown("---")

    # Arama ve Leaflet Harita Entegrasyonu
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
                    
                    gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                    
                    # Flask'teki gibi tam fonksiyonel Leaflet Haritası HTML kodu
                    leaflet_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8" />
                        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                        <style>
                            #map {{ width: 100%; height: 450px; border-radius: 8px; }}
                        </style>
                    </head>
                    <body>
                        <div id="map"></div>
                        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                        <script>
                            var map = L.map('map').setView([{lat}, {lon}], 16);
                            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                                maxZoom: 19,
                                attribution: '© OpenStreetMap'
                            }}).addTo(map);

                            var marker = L.marker([{lat}, {lon}]).addTo(map);
                            var popupContent = "<b>Tesisat:</b> {tesisat_no}<br><br>" +
                                               "<a href='{gmaps_url}' target='_blank' style='background:#2563eb; color:white; padding:6px 12px; text-decoration:none; border-radius:4px; display:inline-block; font-weight:bold; font-size:13px;'>Yol Tarifi</a>";
                            marker.bindPopup(popupContent).openPopup();
                        </script>
                    </body>
                    </html>
                    """
                    
                    # Haritayı ekrana basma
                    from streamlit.components.v1 import html
                    html(leaflet_html, height=470)