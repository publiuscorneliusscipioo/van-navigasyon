import os
from io import BytesIO

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium


# =========================================================
# SAYFA AYARLARI
# =========================================================

st.set_page_config(
    page_title="Van-Navigasyon",
    page_icon="📍",
    layout="wide"
)


# =========================================================
# DOSYA KLASÖRÜ
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TESISATLAR_DOSYA = os.path.join(
    BASE_DIR,
    "Tesisatlar.xlsx"
)

OKUMA_ROTALARI_DOSYA = os.path.join(
    BASE_DIR,
    "OkumaRotalari.xlsx"
)


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

.rota-baslik {
    font-size: 22px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# TESİSATLAR EXCEL
# =========================================================

@st.cache_data
def veri_yukle():

    if not os.path.exists(TESISATLAR_DOSYA):
        return None

    try:

        df = pd.read_excel(
            TESISATLAR_DOSYA,
            dtype={"Tesisat": str}
        )

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        if "Tesisat" not in df.columns:
            return None

        df["Tesisat"] = (
            df["Tesisat"]
            .astype(str)
            .str.strip()
        )

        return df

    except Exception as e:

        st.error(
            f"Tesisatlar.xlsx okuma hatası: {e}"
        )

        return None


df = veri_yukle()


# =========================================================
# OKUMA ROTALARI EXCEL
#
# A = Tesisat
# B = Enlem
# C = Boylam
# F = Okuma Rotası
# =========================================================

@st.cache_data
def okuma_rotasi_verisi_yukle():

    if not os.path.exists(OKUMA_ROTALARI_DOSYA):
        return None

    try:

        raw = pd.read_excel(
            OKUMA_ROTALARI_DOSYA,
            usecols="A:F",
            dtype=str
        )

        if len(raw.columns) < 6:
            return None

        raw.columns = [
            "Tesisat",
            "Enlem",
            "Boylam",
            "D",
            "E",
            "Okuma Rotası"
        ]

        rota_df = raw[
            [
                "Tesisat",
                "Enlem",
                "Boylam",
                "Okuma Rotası"
            ]
        ].copy()

        # Tesisat
        rota_df["Tesisat"] = (
            rota_df["Tesisat"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # Okuma rotası
        rota_df["Okuma Rotası"] = (
            rota_df["Okuma Rotası"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # Enlem
        rota_df["Enlem"] = (
            rota_df["Enlem"]
            .fillna("")
            .astype(str)
            .str.replace(",", ".", regex=False)
        )

        # Boylam
        rota_df["Boylam"] = (
            rota_df["Boylam"]
            .fillna("")
            .astype(str)
            .str.replace(",", ".", regex=False)
        )

        rota_df["Enlem"] = pd.to_numeric(
            rota_df["Enlem"],
            errors="coerce"
        )

        rota_df["Boylam"] = pd.to_numeric(
            rota_df["Boylam"],
            errors="coerce"
        )

        # Geçersiz satırları çıkar
        rota_df = rota_df[
            (rota_df["Tesisat"] != "")
            &
            (rota_df["Okuma Rotası"] != "")
            &
            (rota_df["Enlem"].notna())
            &
            (rota_df["Boylam"].notna())
        ].copy()

        return rota_df

    except Exception as e:

        st.error(
            f"OkumaRotalari.xlsx okuma hatası: {e}"
        )

        return None


okuma_df = okuma_rotasi_verisi_yukle()


# =========================================================
# SESSION STATE
# =========================================================

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if "kullanici_rolu" not in st.session_state:
    st.session_state.kullanici_rolu = None


# =========================================================
# ADMIN SESSION
# =========================================================

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


# =========================================================
# DEMO SESSION
# =========================================================

if "demo_yuklenenler" not in st.session_state:
    st.session_state.demo_yuklenenler = []

if "demo_secilenler" not in st.session_state:
    st.session_state.demo_secilenler = []

if "demo_kayitli_rotalar" not in st.session_state:
    st.session_state.demo_kayitli_rotalar = []

if "demo_rota_adi" not in st.session_state:
    st.session_state.demo_rota_adi = "Rota 1"


# =========================================================
# DEMO1 SESSION
# =========================================================

if "demo1_rota" not in st.session_state:
    st.session_state.demo1_rota = None

if "demo1_secili_tesisat" not in st.session_state:
    st.session_state.demo1_secili_tesisat = None


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

            # =================================================
            # ADMIN
            # =================================================

            if kadi == "admin" and sifre == "admin":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "admin"

                st.rerun()


            # =================================================
            # DEMO
            # =================================================

            elif kadi == "demo" and sifre == "demo":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "demo"

                st.session_state.demo_yuklenenler = []
                st.session_state.demo_secilenler = []
                st.session_state.demo_kayitli_rotalar = []
                st.session_state.demo_rota_adi = "Rota 1"

                st.rerun()


            # =================================================
            # DEMO1
            # =================================================

            elif kadi == "demo1" and sifre == "demo1":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "demo1"

                st.session_state.demo1_rota = None
                st.session_state.demo1_secili_tesisat = None

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


        elif df is None or df.empty:

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

                lat = None
                lon = None


                for l_col, b_col in [
                    ("Enlem.1", "Boylam.1"),
                    ("Enlem", "Boylam")
                ]:

                    try:

                        val_lat = float(
                            str(row[l_col])
                            .replace(",", ".")
                        )

                        val_lon = float(
                            str(row[b_col])
                            .replace(",", ".")
                        )

                        if (
                            val_lat != 0
                            and
                            val_lon != 0
                        ):

                            lat = val_lat
                            lon = val_lon

                            break

                    except:

                        pass


                if (
                    lat is not None
                    and
                    lon is not None
                ):

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


    if st.session_state.hata_mesaji:

        st.error(
            st.session_state.hata_mesaji
        )

    elif st.session_state.aktif_tesisat:

        st.success(
            f"Tesisat Bulundu: "
            f"{st.session_state.aktif_tesisat}"
        )


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
        <div style="
            font-family:sans-serif;
            min-width:160px;
        ">

            <b>Tesisat:</b>
            {st.session_state.aktif_tesisat}

            <br><br>

            <a href="{gmaps_url}"
               target="_blank"
               style="
               background:#2563eb;
               color:white;
               padding:7px 12px;
               text-decoration:none;
               border-radius:5px;
               display:inline-block;
               font-weight:bold;
               ">

                🚗 Yol Tarifi Al

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

    col_baslik, col_cikis = st.columns([8, 1])

    with col_baslik:

        st.markdown(
            "### 🗺️ Rota Planlama"
        )

    with col_cikis:

        if st.button("Çıkış Yap"):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.rerun()


    sol, orta, sag = st.columns(
        [2.3, 5.4, 2.3]
    )


    # =====================================================
    # SOL
    # =====================================================

    with sol:

        st.markdown(
            "### 📥 Toplu Tesisat"
        )

        toplu_input = st.text_area(

            "Tesisat Listesi",

            height=320,

            placeholder=
            "100001\n"
            "100002\n"
            "100003",

            label_visibility="collapsed"

        )


        if st.button(
            "📍 Haritaya Yükle",
            use_container_width=True
        ):

            if df is None or df.empty:

                st.error(
                    "Tesisatlar.xlsx dosyası bulunamadı!"
                )

            else:

                girilen_liste = [
                    x.strip()
                    for x in toplu_input.splitlines()
                    if x.strip()
                ]

                yeni_sayisi = 0


                for t_no in girilen_liste:

                    mevcut = any(

                        x["tesisat"] == t_no

                        for x in (
                            st.session_state.demo_yuklenenler
                            +
                            st.session_state.demo_secilenler
                        )

                    )

                    if mevcut:
                        continue


                    match = df[
                        df["Tesisat"] == t_no
                    ]


                    if match.empty:
                        continue


                    row = match.iloc[0]

                    lat = None
                    lon = None


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

                            pass


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


                st.success(
                    f"{yeni_sayisi} tesisat haritaya eklendi."
                )

                st.rerun()


        st.markdown("---")


        st.metric(
            "🗺️ Haritada",
            len(
                st.session_state.demo_yuklenenler
            )
        )


        st.metric(
            "📌 Rota Havuzu",
            len(
                st.session_state.demo_secilenler
            )
        )


    # =====================================================
    # ORTA HARİTA
    # =====================================================

    with orta:

        if st.session_state.demo_yuklenenler:

            merkez = [
                st.session_state.demo_yuklenenler[0]["lat"],
                st.session_state.demo_yuklenenler[0]["lon"]
            ]

        elif st.session_state.demo_secilenler:

            merkez = [
                st.session_state.demo_secilenler[0]["lat"],
                st.session_state.demo_secilenler[0]["lon"]
            ]

        else:

            merkez = [
                38.5,
                43.4
            ]


        m_demo = folium.Map(
            location=merkez,
            zoom_start=13
        )


        for item in (
            st.session_state.demo_yuklenenler
        ):

            folium.Marker(

                location=[
                    item["lat"],
                    item["lon"]
                ],

                popup=folium.Popup(
                    f"<b>Tesisat:</b> "
                    f"{item['tesisat']}",
                    max_width=200
                ),

                tooltip=str(
                    item["tesisat"]
                ),

                icon=folium.Icon(
                    color="green",
                    icon="info-sign"
                )

            ).add_to(m_demo)


        map_data = st_folium(

            m_demo,

            use_container_width=True,

            height=650,

            returned_objects=[
                "last_object_clicked"
            ]

        )


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

                    secilen = None
                    en_yakin = float("inf")


                    for item in (
                        st.session_state.demo_yuklenenler
                    ):

                        mesafe = (
                            abs(
                                item["lat"]
                                -
                                click_lat
                            )
                            +
                            abs(
                                item["lon"]
                                -
                                click_lon
                            )
                        )


                        if mesafe < en_yakin:

                            en_yakin = mesafe
                            secilen = item


                    if (
                        secilen is not None
                        and
                        en_yakin < 0.00001
                    ):

                        st.session_state.demo_yuklenenler = [

                            x

                            for x
                            in st.session_state.demo_yuklenenler

                            if x["tesisat"]
                            != secilen["tesisat"]

                        ]


                        st.session_state.demo_secilenler.append(
                            secilen
                        )

                        st.rerun()


    # =====================================================
    # SAĞ
    # =====================================================

    with sag:

        st.markdown(
            "### 📌 Rota Havuzu"
        )


        rota_adi = st.text_input(
            "Rota Adı",
            value=st.session_state.demo_rota_adi
        )


        st.session_state.demo_rota_adi = rota_adi


        with st.container(
            height=430,
            border=True
        ):

            if st.session_state.demo_secilenler:

                for idx, item in enumerate(
                    st.session_state.demo_secilenler
                ):

                    if st.button(

                        f"{idx + 1}. {item['tesisat']}",

                        key=f"havuz_{idx}_{item['tesisat']}",

                        use_container_width=True

                    ):

                        st.session_state.demo_secilenler.pop(
                            idx
                        )

                        st.session_state.demo_yuklenenler.append(
                            item
                        )

                        st.rerun()

            else:

                st.info(
                    "Haritadan tesisat seçin."
                )


        if st.session_state.demo_secilenler:

            if st.button(
                "💾 Rotayı Kaydet",
                use_container_width=True
            ):

                kayit = []

                for sira, item in enumerate(
                    st.session_state.demo_secilenler,
                    start=1
                ):

                    kayit.append({

                        "Rota Adı": rota_adi,
                        "Sıra": sira,
                        "Tesisat": item["tesisat"]

                    })


                st.session_state.demo_kayitli_rotalar.append({

                    "rota_adi": rota_adi,
                    "tesisatlar": kayit

                })


                st.session_state.demo_secilenler = []

                st.session_state.demo_rota_adi = (
                    f"Rota "
                    f"{len(st.session_state.demo_kayitli_rotalar) + 1}"
                )

                st.rerun()


        # =================================================
        # KAYITLI ROTALAR
        # =================================================

        if st.session_state.demo_kayitli_rotalar:

            st.markdown("---")

            st.markdown(
                "##### 💾 Kaydedilen Rotalar"
            )


            with st.container(
                height=220,
                border=True
            ):

                for rota in (
                    st.session_state.demo_kayitli_rotalar
                ):

                    st.write(
                        f"📁 **{rota['rota_adi']}**"
                    )

                    st.caption(
                        f"{len(rota['tesisatlar'])} tesisat"
                    )


            tum_kayitlar = []

            for rota in (
                st.session_state.demo_kayitli_rotalar
            ):

                tum_kayitlar.extend(
                    rota["tesisatlar"]
                )


            if tum_kayitlar:

                excel_df = pd.DataFrame(
                    tum_kayitlar,
                    columns=[
                        "Rota Adı",
                        "Sıra",
                        "Tesisat"
                    ]
                )


                output = BytesIO()


                with pd.ExcelWriter(
                    output,
                    engine="openpyxl"
                ) as writer:

                    excel_df.to_excel(
                        writer,
                        index=False,
                        sheet_name="Rotalar"
                    )


                st.download_button(

                    "📊 TÜM ROTALARI EXCELE AKTAR",

                    data=output.getvalue(),

                    file_name="Tum_Rotalar.xlsx",

                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),

                    use_container_width=True

                )


# =========================================================
# DEMO1
# OKUMA ROTALARI
# =========================================================

elif st.session_state.kullanici_rolu == "demo1":

    # =====================================================
    # BAŞLIK
    # =====================================================

    col_baslik, col_cikis = st.columns(
        [8, 1]
    )


    with col_baslik:

        st.markdown(
            "### 🗺️ Okuma Rotaları"
        )


    with col_cikis:

        if st.button(
            "Çıkış Yap"
        ):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.session_state.demo1_rota = None
            st.session_state.demo1_secili_tesisat = None

            st.rerun()


    # =====================================================
    # EXCEL KONTROL
    # =====================================================

    if okuma_df is None:

        st.error(
            "⚠️ OkumaRotalari.xlsx bulunamadı."
        )

        st.info(
            "Dosya adı GitHub'da tam olarak "
            "'OkumaRotalari.xlsx' olmalı ve "
            "streamlit_app.py ile aynı klasörde "
            "bulunmalıdır."
        )

        st.stop()


    if okuma_df.empty:

        st.warning(
            "OkumaRotalari.xlsx içerisinde "
            "geçerli veri bulunamadı."
        )

        st.stop()


    # =====================================================
    # ROTALAR
    # =====================================================

    rotalar = sorted(

        okuma_df[
            "Okuma Rotası"
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()

    )


    if not rotalar:

        st.warning(
            "Excelde Okuma Rotası bulunamadı."
        )

        st.stop()


    # =====================================================
    # SOL PANEL / HARİTA
    # =====================================================

    sol, harita_alani = st.columns(
        [2.2, 7.8]
    )


    # =====================================================
    # SOL PANEL
    # =====================================================

    with sol:

        st.markdown(
            "### 📋 Okuma Rotası"
        )


        if (
            st.session_state.demo1_rota
            not in rotalar
        ):

            st.session_state.demo1_rota = (
                rotalar[0]
            )


        secilen_rota = st.selectbox(

            "Okuma Rotası",

            options=rotalar,

            index=rotalar.index(
                st.session_state.demo1_rota
            ),

            label_visibility="collapsed"

        )


        if (
            secilen_rota
            !=
            st.session_state.demo1_rota
        ):

            st.session_state.demo1_rota = (
                secilen_rota
            )

            st.session_state.demo1_secili_tesisat = None

            st.rerun()


        # =================================================
        # SEÇİLEN ROTA
        # =================================================

        rota_df = okuma_df[
            okuma_df["Okuma Rotası"]
            ==
            secilen_rota
        ].copy()


        st.markdown("---")


        st.metric(
            "📍 Tesisat Sayısı",
            len(rota_df)
        )


        st.markdown("---")


        st.markdown(
            "### 📌 Tesisatlar"
        )


        # =================================================
        # TESİSAT LİSTESİ
        # =================================================

        with st.container(
            height=470,
            border=True
        ):

            for sıra, (_, row) in enumerate(
                rota_df.iterrows(),
                start=1
            ):

                t_no = str(
                    row["Tesisat"]
                )


                if st.button(

                    f"📍 {sıra}. {t_no}",

                    key=(
                        f"demo1_tesisat_"
                        f"{sıra}_{t_no}"
                    ),

                    use_container_width=True

                ):

                    st.session_state.demo1_secili_tesisat = (
                        t_no
                    )

                    st.rerun()


    # =====================================================
    # HARİTA
    # =====================================================

    with harita_alani:

        if rota_df.empty:

            st.warning(
                "Bu rotada tesisat bulunamadı."
            )

        else:

            # =================================================
            # MERKEZ
            # =================================================

            merkez_lat = rota_df[
                "Enlem"
            ].mean()

            merkez_lon = rota_df[
                "Boylam"
            ].mean()


            m_rota = folium.Map(

                location=[
                    merkez_lat,
                    merkez_lon
                ],

                zoom_start=13,

                control_scale=True

            )


            # =================================================
            # MARKERLAR
            # =================================================

            for _, row in rota_df.iterrows():

                t_no = str(
                    row["Tesisat"]
                )

                lat = float(
                    row["Enlem"]
                )

                lon = float(
                    row["Boylam"]
                )


                gmaps_url = (
                    "https://www.google.com/maps/dir/?api=1"
                    f"&destination={lat},{lon}"
                )


                popup_html = f"""
                <div style="
                    font-family:Arial,sans-serif;
                    min-width:190px;
                    text-align:center;
                ">

                    <div style="
                        font-size:12px;
                        color:#64748b;
                        margin-bottom:5px;
                    ">

                        TESİSAT

                    </div>

                    <div style="
                        font-size:20px;
                        font-weight:bold;
                        margin-bottom:8px;
                    ">

                        {t_no}

                    </div>

                    <div style="
                        font-size:12px;
                        color:#64748b;
                        margin-bottom:10px;
                    ">

                        Okuma Rotası:<br>

                        <b>{secilen_rota}</b>

                    </div>

                    <a href="{gmaps_url}"
                       target="_blank"
                       style="
                       background:#2563eb;
                       color:white;
                       padding:8px 14px;
                       text-decoration:none;
                       border-radius:6px;
                       display:inline-block;
                       font-weight:bold;
                       font-size:13px;
                       ">

                        🚗 Yol Tarifi Al

                    </a>

                </div>
                """


                # =================================================
                # SEÇİLİ MARKER
                # =================================================

                if (
                    st.session_state.demo1_secili_tesisat
                    ==
                    t_no
                ):

                    marker_color = "red"

                else:

                    marker_color = "blue"


                folium.Marker(

                    location=[
                        lat,
                        lon
                    ],

                    popup=folium.Popup(
                        popup_html,
                        max_width=280
                    ),

                    tooltip=(
                        f"Tesisat: {t_no}"
                    ),

                    icon=folium.Icon(
                        color=marker_color,
                        icon="home",
                        prefix="fa"
                    )

                ).add_to(m_rota)


            # =================================================
            # HARİTA
            # =================================================

            map_data = st_folium(

                m_rota,

                use_container_width=True,

                height=700,

                returned_objects=[
                    "last_object_clicked"
                ]

            )


            # =================================================
            # HARİTA TIKLAMA
            # =================================================

            if map_data:

                clicked = map_data.get(
                    "last_object_clicked"
                )


                if clicked:

                    click_lat = clicked.get(
                        "lat"
                    )

                    click_lon = clicked.get(
                        "lng"
                    )


                    if (
                        click_lat is not None
                        and
                        click_lon is not None
                    ):

                        en_yakin = float("inf")
                        secilen = None


                        for _, row in (
                            rota_df.iterrows()
                        ):

                            lat = float(
                                row["Enlem"]
                            )

                            lon = float(
                                row["Boylam"]
                            )


                            mesafe = (

                                abs(
                                    lat
                                    -
                                    click_lat
                                )

                                +

                                abs(
                                    lon
                                    -
                                    click_lon
                                )

                            )


                            if mesafe < en_yakin:

                                en_yakin = mesafe

                                secilen = str(
                                    row["Tesisat"]
                                )


                        if (
                            secilen is not None
                            and
                            en_yakin < 0.00001
                        ):

                            st.session_state.demo1_secili_tesisat = (
                                secilen
                            )

                            st.rerun()
