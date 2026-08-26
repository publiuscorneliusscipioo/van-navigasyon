import os
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(
    page_title="Van-Navigasyon",
    page_icon="📍",
    layout="wide"
)


# =========================================================
# EXCEL VERİSİ
# =========================================================

@st.cache_data
def veri_yukle():
    yol = "Tesisatlar.xlsx"

    if os.path.exists(yol):
        try:
            df = pd.read_excel(yol, dtype={"Tesisat": str})

            df.columns = df.columns.astype(str).str.strip()

            if "Tesisat" in df.columns:
                df["Tesisat"] = df["Tesisat"].astype(str).str.strip()

            return df

        except Exception as e:
            st.error(f"Excel okuma hatası: {e}")

    return None


df = veri_yukle()


# =========================================================
# SESSION STATE
# =========================================================

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if "kullanici_rolu" not in st.session_state:
    st.session_state.kullanici_rolu = None


# ---------------- ADMIN ----------------

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


# ---------------- DEMO ----------------

# Haritada bulunan tesisatlar
if "demo_yuklenenler" not in st.session_state:
    st.session_state.demo_yuklenenler = []


# Rota havuzuna alınan tesisatlar
if "demo_secilenler" not in st.session_state:
    st.session_state.demo_secilenler = []


# Rota adı
if "demo_rota_adi" not in st.session_state:
    st.session_state.demo_rota_adi = "Rota 1"


# =========================================================
# SAYFA CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

.rota-item {
    padding: 8px;
    margin-bottom: 5px;
    border: 1px solid #ddd;
    border-radius: 6px;
    background-color: #f8f9fa;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# GİRİŞ
# =========================================================

if not st.session_state.giris_yapildi:

    st.title("📍 Van-Navigasyon Giriş")

    with st.form("login_form"):

        kadi = st.text_input(
            "Kullanıcı Adı",
            placeholder="Kullanıcı Adı"
        )

        sifre = st.text_input(
            "Şifre",
            type="password",
            placeholder="Şifre"
        )

        giris = st.form_submit_button(
            "GİRİŞ YAP",
            use_container_width=True
        )

        if giris:

            # ADMIN
            if kadi == "admin" and sifre == "admin":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "admin"

                st.rerun()


            # DEMO
            elif kadi == "demo" and sifre == "demo":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "demo"

                # Demo ekranı temiz başlasın
                st.session_state.demo_yuklenenler = []
                st.session_state.demo_secilenler = []

                st.rerun()


            else:

                st.error(
                    "Hatalı Kullanıcı Adı veya Şifre!"
                )


# =========================================================
# ADMIN PANELİ
# =========================================================

elif st.session_state.kullanici_rolu == "admin":

    col_baslik, col_cikis = st.columns([8, 1])

    with col_baslik:

        st.markdown(
            "### Van Navigasyon - Admin Paneli"
        )

    with col_cikis:

        if st.button("Çıkış Yap"):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.rerun()


    # -----------------------------------------
    # ARAMA
    # -----------------------------------------

    with st.form("arama_formu"):

        tesisat_no = st.text_input(
            "Tesisat No",
            placeholder="Tesisat No girin...",
            value=(
                st.session_state.aktif_tesisat
                if st.session_state.aktif_tesisat
                else ""
            )
        )

        ara_submitted = st.form_submit_button(
            "ARA",
            use_container_width=True
        )


    if ara_submitted:

        if not tesisat_no:

            st.session_state.hata_mesaji = (
                "Lütfen bir tesisat numarası yazın."
            )

            st.session_state.aktif_tesisat = None

        else:

            if df is None or df.empty:

                st.session_state.hata_mesaji = (
                    "⚠️ Tesisatlar.xlsx dosyası bulunamadı!"
                )

                st.session_state.aktif_tesisat = None

            else:

                bulunan = df[
                    df["Tesisat"] == tesisat_no.strip()
                ]


                if bulunan.empty:

                    st.session_state.hata_mesaji = (
                        "Bu tesisat numarası bulunamadı!"
                    )

                    st.session_state.aktif_tesisat = None

                else:

                    row = bulunan.iloc[0]

                    lat, lon = None, None


                    for l_col, b_col in [
                        ("Enlem.1", "Boylam.1"),
                        ("Enlem", "Boylam")
                    ]:

                        try:

                            val_lat = float(
                                str(row[l_col]).replace(",", ".")
                            )

                            val_lon = float(
                                str(row[b_col]).replace(",", ".")
                            )

                            if val_lat != 0 and val_lon != 0:

                                lat = val_lat
                                lon = val_lon

                                break

                        except:

                            pass


                    if lat is not None and lon is not None:

                        st.session_state.son_lat = lat
                        st.session_state.son_lon = lon
                        st.session_state.son_zoom = 17

                        st.session_state.aktif_tesisat = (
                            tesisat_no.strip()
                        )

                        st.session_state.hata_mesaji = None

                    else:

                        st.session_state.hata_mesaji = (
                            "Bu tesisata ait geçerli koordinat bulunamadı!"
                        )

                        st.session_state.aktif_tesisat = None


    # -----------------------------------------
    # MESAJ
    # -----------------------------------------

    if st.session_state.hata_mesaji:

        st.error(
            st.session_state.hata_mesaji
        )

    elif st.session_state.aktif_tesisat:

        st.success(
            f"Tesisat Bulundu: "
            f"{st.session_state.aktif_tesisat}"
        )


    # -----------------------------------------
    # ADMIN HARİTA
    # -----------------------------------------

    m = folium.Map(
        location=[
            st.session_state.son_lat,
            st.session_state.son_lon
        ],
        zoom_start=st.session_state.son_zoom
    )


    if st.session_state.aktif_tesisat:

        gmaps_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&destination="
            f"{st.session_state.son_lat},"
            f"{st.session_state.son_lon}"
        )


        popup_html = f"""
        <div style="font-family:sans-serif;min-width:140px;">

            <b>Tesisat:</b>
            {st.session_state.aktif_tesisat}

            <br><br>

            <a href="{gmaps_url}"
               target="_blank"
               style="
               background:#2563eb;
               color:white;
               padding:6px 12px;
               text-decoration:none;
               border-radius:4px;
               display:inline-block;
               font-weight:bold;
               font-size:13px;
               ">

               Yol Tarifi Al

            </a>

        </div>
        """


        folium.CircleMarker(

            location=[
                st.session_state.son_lat,
                st.session_state.son_lon
            ],

            radius=12,

            color="#0f766e",

            fill=True,

            fill_color="#14b8a6",

            fill_opacity=0.95,

            popup=folium.Popup(
                popup_html,
                max_width=300
            )

        ).add_to(m)


    st_folium(
        m,
        use_container_width=True,
        height=500
    )


# =========================================================
# DEMO / ROTA PLANLAMA
# =========================================================

elif st.session_state.kullanici_rolu == "demo":

    # =====================================================
    # BAŞLIK
    # =====================================================

    col_baslik, col_cikis = st.columns([8, 1])

    with col_baslik:

        st.markdown(
            "### 🗺️ Demo Rota Planlama Paneli"
        )

    with col_cikis:

        if st.button("Çıkış Yap"):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.session_state.demo_yuklenenler = []
            st.session_state.demo_secilenler = []

            st.rerun()


    # =====================================================
    # 3 SÜTUN
    #
    # SOL  : TOPLU YÜKLEME
    # ORTA : HARİTA
    # SAĞ  : ROTA HAVUZU
    # =====================================================

    sol, orta, sag = st.columns(
        [2.3, 5.2, 2.5]
    )


    # =====================================================
    # SOL PANEL
    # =====================================================

    with sol:

        st.markdown(
            "### 📥 Toplu Tesisat Yükleme"
        )

        st.caption(
            "Tesisat numaralarını alt alta yazın."
        )


        toplu_input = st.text_area(

            "Tesisatlar",

            height=300,

            placeholder=
            "100001\n"
            "100002\n"
            "100003\n"
            "100004\n"
            "100005"

        )


        if st.button(
            "📍 Tesisatları Haritaya Yükle",
            use_container_width=True
        ):

            if df is None or df.empty:

                st.error(
                    "Tesisatlar.xlsx dosyası bulunamadı!"
                )

            else:

                girilen_liste = [

                    t.strip()

                    for t in toplu_input.splitlines()

                    if t.strip()

                ]


                yeni_sayisi = 0

                bulunamayanlar = []


                for t_no in girilen_liste:

                    # Daha önce haritada veya havuzda varsa tekrar ekleme
                    zaten_var = any(
                        x["tesisat"] == t_no
                        for x in (
                            st.session_state.demo_yuklenenler
                            +
                            st.session_state.demo_secilenler
                        )
                    )


                    if zaten_var:
                        continue


                    match = df[
                        df["Tesisat"] == t_no
                    ]


                    if match.empty:

                        bulunamayanlar.append(t_no)

                        continue


                    row = match.iloc[0]


                    lat = None
                    lon = None


                    # Önce Enlem.1 / Boylam.1
                    # sonra Enlem / Boylam
                    for l_col, b_col in [

                        ("Enlem.1", "Boylam.1"),

                        ("Enlem", "Boylam")

                    ]:

                        try:

                            v_lat = float(
                                str(row[l_col])
                                .replace(",", ".")
                            )

                            v_lon = float(
                                str(row[b_col])
                                .replace(",", ".")
                            )


                            if (
                                v_lat != 0
                                and
                                v_lon != 0
                            ):

                                lat = v_lat
                                lon = v_lon

                                break

                        except:

                            continue


                    if (
                        lat is not None
                        and
                        lon is not None
                    ):

                        st.session_state.demo_yuklenenler.append({

                            "tesisat": t_no,

                            "lat": lat,

                            "lon": lon

                        })

                        yeni_sayisi += 1

                    else:

                        bulunamayanlar.append(
                            f"{t_no} (koordinat yok)"
                        )


                if yeni_sayisi > 0:

                    st.success(
                        f"✅ {yeni_sayisi} tesisat haritaya eklendi."
                    )


                if bulunamayanlar:

                    st.warning(
                        "Bulunamayan / koordinatı olmayan tesisatlar: "
                        +
                        ", ".join(bulunamayanlar)
                    )


                st.rerun()


        st.markdown("---")


        st.metric(
            "Haritadaki Tesisat",
            len(
                st.session_state.demo_yuklenenler
            )
        )


        st.metric(
            "Rota Havuzundaki",
            len(
                st.session_state.demo_secilenler
            )
        )


        st.markdown("---")


        if st.button(
            "🗑️ Tümünü Temizle",
            use_container_width=True
        ):

            st.session_state.demo_yuklenenler = []

            st.session_state.demo_secilenler = []

            st.rerun()


    # =====================================================
    # ORTA - HARİTA
    # =====================================================

    with orta:

        st.markdown(
            "### 🗺️ Harita"
        )

        st.caption(
            "Tesisat noktasına tıklayıp "
            "\"ROTAYA EKLE\" butonuna basın."
        )


        # Harita merkezi
        if st.session_state.demo_yuklenenler:

            harita_merkez = [

                st.session_state.demo_yuklenenler[0]["lat"],

                st.session_state.demo_yuklenenler[0]["lon"]

            ]

        elif st.session_state.demo_secilenler:

            harita_merkez = [

                st.session_state.demo_secilenler[0]["lat"],

                st.session_state.demo_secilenler[0]["lon"]

            ]

        else:

            harita_merkez = [
                38.5,
                43.4
            ]


        m_demo = folium.Map(

            location=harita_merkez,

            zoom_start=13,

            control_scale=True

        )


        # =================================================
        # HARİTADAKİ MARKERLAR
        # =================================================

        for item in st.session_state.demo_yuklenenler:

            t_no = item["tesisat"]

            lat = item["lat"]

            lon = item["lon"]


            # Marker popup
            popup_html = f"""

            <div style="
                font-family:Arial;
                width:180px;
                text-align:center;
            ">

                <div style="
                    font-size:16px;
                    font-weight:bold;
                    margin-bottom:10px;
                ">

                    Tesisat: {t_no}

                </div>


                <div style="
                    color:#666;
                    font-size:12px;
                    margin-bottom:10px;
                ">

                    {lat:.6f},
                    {lon:.6f}

                </div>


                <div style="
                    background:#16a34a;
                    color:white;
                    padding:8px;
                    border-radius:5px;
                    font-weight:bold;
                ">

                    Tıklayınca tesisatı
                    rotaya ekleyin

                </div>

            </div>

            """


            folium.Marker(

                location=[
                    lat,
                    lon
                ],

                popup=folium.Popup(
                    popup_html,
                    max_width=250
                ),

                tooltip=f"Tesisat: {t_no}",

                icon=folium.Icon(
                    color="green",
                    icon="home",
                    prefix="fa"
                )

            ).add_to(m_demo)


        # =================================================
        # HARİTA
        # =================================================

        map_data = st_folium(

            m_demo,

            use_container_width=True,

            height=650,

            returned_objects=[
                "last_object_clicked"
            ]

        )


        # =================================================
        # MARKER TIKLAMA
        # =================================================

        if map_data:

            clicked = map_data.get(
                "last_object_clicked"
            )


            if clicked:

                click_lat = clicked.get("lat")

                click_lon = clicked.get("lng")


                if (
                    click_lat is not None
                    and
                    click_lon is not None
                ):

                    secilen_item = None


                    # En yakın markerı bul
                    en_yakin_mesafe = 999999


                    for item in st.session_state.demo_yuklenenler:

                        fark = (
                            abs(item["lat"] - click_lat)
                            +
                            abs(item["lon"] - click_lon)
                        )


                        if fark < en_yakin_mesafe:

                            en_yakin_mesafe = fark

                            secilen_item = item


                    # Marker bulunduysa
                    if (
                        secilen_item is not None
                        and
                        en_yakin_mesafe < 0.00001
                    ):

                        # Haritadan çıkar
                        st.session_state.demo_yuklenenler.remove(
                            secilen_item
                        )


                        # Rota havuzuna ekle
                        if not any(
                            x["tesisat"]
                            ==
                            secilen_item["tesisat"]
                            for x in
                            st.session_state.demo_secilenler
                        ):

                            st.session_state.demo_secilenler.append(
                                secilen_item
                            )


                        st.rerun()


    # =====================================================
    # SAĞ PANEL - ROTA HAVUZU
    # =====================================================

    with sag:

        st.markdown(
            "### 📌 Rota Havuzu"
        )


        # -------------------------------------------------
        # ROTA ADI
        # -------------------------------------------------

        rota_adi = st.text_input(

            "Rota Adı",

            value=st.session_state.demo_rota_adi,

            key="rota_adi_input"

        )


        st.session_state.demo_rota_adi = rota_adi


        st.markdown("---")


        if st.session_state.demo_secilenler:

            st.success(
                f"{len(st.session_state.demo_secilenler)} "
                "tesisat seçildi."
            )


            st.caption(
                "Tesisata tıklarsanız haritaya geri gönderilir."
            )


            # -------------------------------------------------
            # HAVUZDAKİ TESİSATLAR
            # -------------------------------------------------

            for idx, item in enumerate(
                st.session_state.demo_secilenler
            ):

                t_no = item["tesisat"]


                col_no, col_btn = st.columns(
                    [4, 1]
                )


                with col_no:

                    st.markdown(
                        f"**{idx + 1}. {t_no}**"
                    )


                with col_btn:

                    if st.button(
                        "↩️",
                        key=f"geri_{t_no}_{idx}",
                        help="Haritaya geri gönder"
                    ):

                        # Havuzdan çıkar
                        st.session_state.demo_secilenler.pop(
                            idx
                        )


                        # Haritaya geri ekle
                        if not any(
                            x["tesisat"] == t_no
                            for x in
                            st.session_state.demo_yuklenenler
                        ):

                            st.session_state.demo_yuklenenler.append(
                                item
                            )


                        st.rerun()


                st.markdown(
                    "<hr style='margin:4px 0'>",
                    unsafe_allow_html=True
                )


            # -------------------------------------------------
            # EXCEL OLUŞTUR
            # -------------------------------------------------

            excel_df = pd.DataFrame([

                {

                    "Rota Adı":
                    rota_adi,

                    "Sıra":
                    i + 1,

                    "Tesisat":
                    item["tesisat"],

                    "Enlem":
                    item["lat"],

                    "Boylam":
                    item["lon"]

                }

                for i, item in enumerate(
                    st.session_state.demo_secilenler
                )

            ])


            output = BytesIO()


            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ):

                excel_df.to_excel(

                    index=False,

                    sheet_name="Rota"

                )


            processed_data = output.getvalue()


            st.markdown("---")


            # -------------------------------------------------
            # EXCEL İNDİR
            # -------------------------------------------------

            st.download_button(

                label="📊 Rota Excelini İndir",

                data=processed_data,

                file_name=(
                    f"{rota_adi}.xlsx"
                ),

                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),

                use_container_width=True

            )


        else:

            st.info(
                "Henüz rota havuzunda tesisat yok."
            )

            st.caption(
                "Haritadaki tesisatlara tıklayarak "
                "rotaya ekleyebilirsiniz."
            )
