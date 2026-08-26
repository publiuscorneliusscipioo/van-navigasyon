import os
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from io import BytesIO

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

# --- SESSION STATE TANIMLAMALARI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_rolu" not in st.session_state:
    st.session_state.kullanici_rolu = None

# Admin Hafızası
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

# Demo / Rota Hafızası
if "demo_yuklenenler" not in st.session_state:
    st.session_state.demo_yuklenenler = [] # Haritada olanlar
if "demo_secilenler" not in st.session_state:
    st.session_state.demo_secilenler = [] # Sağ panelde birikenler (havuz)

st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.title("Van-Navigasyon Giriş")
    with st.form("login_form"):
        kadi = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password", placeholder="Şifre")
        giris = st.form_submit_button("GİRİŞ YAP", use_container_width=True)
        if giris:
            if kadi == "admin" and sifre == "admin":
                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "admin"
                st.rerun()
            elif kadi == "demo" and sifre == "demo":
                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "demo"
                st.rerun()
            else:
                st.error("Hatalı Kullanıcı Adı veya Şifre! (Admin için: admin/admin, Demo için: demo/demo)")

# --- 1. ADMIN PANELİ ---
elif st.session_state.kullanici_rolu == "admin":
    col_baslik, col_cikis = st.columns([8, 1])
    with col_baslik:
        st.markdown("### Van Navigasyon - Admin Paneli")
    with col_cikis:
        if st.button("Çıkış Yap"):
            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None
            st.rerun()

    with st.form("arama_formu"):
        tesisat_no = st.text_input("Tesisat No", placeholder="Tesisat No girin...", value=st.session_state.aktif_tesisat if st.session_state.aktif_tesisat else "")
        ara_submitted = st.form_submit_button("ARA", use_container_width=True)

    if ara_submitted:
        if not tesisat_no:
            st.session_state.hata_mesaji = "Lütfen bir tesisat numarası yazın."
            st.session_state.aktif_tesisat = None
        else:
            if df is None or df.empty:
                st.session_state.hata_mesaji = "⚠️ Tesisatlar.xlsx dosyası bulunamadı!"
                st.session_state.aktif_tesisat = None
            else:
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
                        st.session_state.son_zoom = 17
                        st.session_state.aktif_tesisat = tesisat_no.strip()
                        st.session_state.hata_mesaji = None
                    else:
                        st.session_state.hata_mesaji = "Bu tesisata ait geçerli koordinat bulunamadı!"
                        st.session_state.aktif_tesisat = None

    if st.session_state.hata_mesaji:
        st.error(st.session_state.hata_mesaji)
    elif st.session_state.aktif_tesisat:
        st.success(f"Tesisat Bulundu: {st.session_state.aktif_tesisat}")

    m = folium.Map(
        location=[st.session_state.son_lat, st.session_state.son_lon], 
        zoom_start=st.session_state.son_zoom
    )

    if st.session_state.aktif_tesisat:
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={st.session_state.son_lat},{st.session_state.son_lon}"
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 140px;">
            <b>Tesisat:</b> {st.session_state.aktif_tesisat}<br><br>
            <a href='{gmaps_url}' target='_blank'
               style='background:#2563eb; color:white; padding:6px 12px;
                      text-decoration:none; border-radius:4px;
                      display:inline-block; font-weight:bold; font-size:13px;'>
                 Yol Tarifi Al
            </a>
        </div>
        """
        folium.CircleMarker(
            location=[st.session_state.son_lat, st.session_state.son_lon],
            radius=12,
            color="#0f766e",
            fill=True,
            fill_color="#14b8a6",
            fill_opacity=0.95,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    st_folium(m, use_container_width=True, height=500)

# --- 2. DEMO / ROTA PLANLAMA PANELİ (SOL: HARİTA, SAĞ: HAVUZ VE YÜKLEME) ---
elif st.session_state.kullanici_rolu == "demo":
    col_baslik, col_cikis = st.columns([8, 1])
    with col_baslik:
        st.markdown("### 🗺️ Demo Rota Planlama Paneli (Masaüstü)")
    with col_cikis:
        if st.button("Çıkış Yap"):
            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None
            st.rerun()

    # Sol ve Sağ Sütunlar (Sol: Harita, Sağ: Yükleme ve Havuz)
    col_sol_harita, col_sag_panel = st.columns([7, 3])

    with col_sag_panel:
        st.markdown("#### 📥 Toplu Tesisat Yükleme")
        toplu_input = st.text_area("Alt alta tesisat numaralarını girin:", height=110, placeholder="1001\n1002\n1003...")
        
        if st.button("Tesisatları Haritaya Yükle", use_container_width=True):
            if df is None:
                st.error("Tesisatlar.xlsx dosyası bulunamadı!")
            else:
                girilen_liste = [t.strip() for t in toplu_input.split("\n") if t.strip()]
                bulunanlar = []
                for t_no in girilen_liste:
                    eksik_mi = not any(item["tesisat"] == t_no for item in st.session_state.demo_yuklenenler + st.session_state.demo_secilenler)
                    if eksik_mi:
                        match = df[df["Tesisat"] == t_no]
                        if not match.empty:
                            row = match.iloc[0]
                            lat, lon = None, None
                            for l_col, b_col in [("Enlem.1", "Boylam.1"), ("Enlem", "Boylam")]:
                                try:
                                    v_lat = float(str(row[l_col]).replace(",", "."))
                                    v_lon = float(str(row[b_col]).replace(",", "."))
                                    if v_lat != 0 and v_lon != 0:
                                        lat, lon = v_lat, v_lon
                                        break
                                except:
                                    pass
                            if lat and lon:
                                bulunanlar.append({"tesisat": t_no, "lat": lat, "lon": lon})
                
                st.session_state.demo_yuklenenler.extend(bulunanlar)
                st.success(f"{len(bulunanlar)} adet tesisat haritaya eklendi.")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 📌 Rota Havuzu (Sağ Panel)")
        
        rota_adi = st.text_input("Rota Adı", value="Rota 1")

        if st.session_state.demo_secilenler:
            st.info(f"Havuzdaki Toplam Tesisat: {len(st.session_state.demo_secilenler)}")
            st.markdown("<small>Havuzdan çıkarmak ve haritaya döndürmek için tıklayın:</small>", unsafe_allow_html=True)
            
            for idx, item in enumerate(st.session_state.demo_secilenler):
                if st.button(f"↩️ {item['tesisat']} (Haritaya Geri Gönder)", key=f"cikar_{idx}", use_container_width=True):
                    st.session_state.demo_secilenler.pop(idx)
                    st.session_state.demo_yuklenenler.append(item)
                    st.rerun()

            # Excel'e İndir Butonu
            excel_df = pd.DataFrame([{ "Rota Adı": rota_adi, "Tesisat": i["tesisat"], "Enlem": i["lat"], "Boylam": i["lon"] } for i in st.session_state.demo_secilenler])
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                excel_df.to_excel(writer, index=False, sheet_name='Rota')
            processed_data = output.getvalue()

            st.download_button(
                label="📊 Rota Excel Dosyasını İndir",
                data=processed_data,
                file_name=f"{rota_adi}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.markdown("_Henüz havuzda tesisat yok. Haritadaki noktalara tıklayarak buraya alabilirsiniz._")

        st.markdown("---")
        if st.button("Tümünü Temizle", use_container_width=True):
            st.session_state.demo_yuklenenler = []
            st.session_state.demo_secilenler = []
            st.rerun()

    with col_sol_harita:
        st.markdown("#### Harita Görünümü (Haritadaki noktalara tıklayarak sağ havuza alabilirsiniz)")
        
        harita_merkez = [38.5, 43.4]
        if st.session_state.demo_yuklenenler:
            harita_merkez = [st.session_state.demo_yuklenenler[0]["lat"], st.session_state.demo_yuklenenler[0]["lon"]]
        elif st.session_state.demo_secilenler:
            harita_merkez = [st.session_state.demo_secilenler[0]["lat"], st.session_state.demo_secilenler[0]["lon"]]

        m_demo = folium.Map(location=harita_merkez, zoom_start=13)

        for item in st.session_state.demo_yuklenenler:
            t_no = item["tesisat"]
            folium.Marker(
                location=[item["lat"], item["lon"]],
                popup=folium.Popup(f"<b>Tesisat: {t_no}</b>", max_width=200),
                tooltip=f"Tesisat: {t_no} (Havuza almak için tıklayın)",
                icon=folium.Icon(color="green", icon="info-sign")
            ).add_to(m_demo)

        map_data = st_folium(m_demo, use_container_width=True, height=600)

        # Haritada tıklanan koordinatı yüklenen tesisatlarla eşleştirip sağ havuza atma
        if map_data and map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"]["lat"]
            click_lon = map_data["last_clicked"]["lng"]
            
            for item in list(st.session_state.demo_yuklenenler):
                # Yaklaşık 50 metre (0.0005) tolerans ile tıklanan noktayı bulur
                if abs(item["lat"] - click_lat) < 0.0005 and abs(item["lon"] - click_lon) < 0.0005:
                    st.session_state.demo_yuklenenler.remove(item)
                    if item not in st.session_state.demo_secilenler:
                        st.session_state.demo_secilenler.append(item)
                    st.rerun()

        # Alternatif pratik yönetim: Harita tıklaması tarayıcıda gecikirse diye harita altı hızlı seçim kutusu da ekleyebiliriz
        if st.session_state.demo_yuklenenler:
            st.markdown("---")
            st.markdown("##### ⚡ Hızlı Havuz İşlemi (Haritaya tıklamakta zorlanırsanız buradan seçin):")
            secilen_hizli = st.selectbox("Havuza eklenecek tesisatı seçin:", ["Seçiniz..."] + [i["tesisat"] for i in st.session_state.demo_yuklenenler])
            if secilen_hizli != "Seçiniz...":
                for item in list(st.session_state.demo_yuklenenler):
                    if item["tesisat"] == secilen_hizli:
                        st.session_state.demo_yuklenenler.remove(item)
                        st.session_state.demo_secilenler.append(item)
                        st.rerun()
