import os
from io import BytesIO

import pandas as pd
import streamlit as st

import folium
from folium.plugins import FastMarkerCluster

from streamlit_folium import st_folium, folium_static


# =========================================================
# SAYFA AYARLARI
# =========================================================

st.set_page_config(
    page_title="Van-Navigasyon",
    page_icon="📍",
    layout="wide"
)


# =========================================================
# DOSYA YOLLARI
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TESISATLAR_DOSYA = os.path.join(
    BASE_DIR,
    "Tesisatlar.xlsx"
)

OKUMA_ROTALARI_DOSYA = os.path.join(
    BASE_DIR,
    "OkumaRotalari.xlsx"
)


# =========================================================
# GENEL CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# ANA TESİSAT EXCELİ
# =========================================================

@st.cache_data
def veri_yukle():

    if not os.path.exists(
        TESISATLAR_DOSYA
    ):
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
# OKUMA ROTALARI EXCELİ
#
# A = Tesisat
# B = Enlem
# C = Boylam
# F = Okuma Rotası
#
# SADECE DEMO1 GİRİŞİNDE ÇAĞRILACAK.
# =========================================================

@st.cache_data(show_spinner=False)
def okuma_rotasi_verisi_yukle():

    if not os.path.exists(
        OKUMA_ROTALARI_DOSYA
    ):
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


        # -----------------------------------------
        # TESİSAT
        # -----------------------------------------

        rota_df["Tesisat"] = (
            rota_df["Tesisat"]
            .fillna("")
            .astype(str)
            .str.strip()
        )


        # Excel bazen 12345.0 şeklinde okuyabilir
        rota_df["Tesisat"] = (
            rota_df["Tesisat"]
            .str.replace(
                r"\.0$",
                "",
                regex=True
            )
        )


        # -----------------------------------------
        # OKUMA ROTASI
        # -----------------------------------------

        rota_df["Okuma Rotası"] = (
            rota_df["Okuma Rotası"]
            .fillna("")
            .astype(str)
            .str.strip()
        )


        rota_df["Okuma Rotası"] = (
            rota_df["Okuma Rotası"]
            .str.replace(
                r"\.0$",
                "",
                regex=True
            )
        )


        # -----------------------------------------
        # KOORDİNATLAR
        # -----------------------------------------

        rota_df["Enlem"] = (
            rota_df["Enlem"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.replace(
                ",",
                ".",
                regex=False
            )
        )


        rota_df["Boylam"] = (
            rota_df["Boylam"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.replace(
                ",",
                ".",
                regex=False
            )
        )


        rota_df["Enlem"] = pd.to_numeric(
            rota_df["Enlem"],
            errors="coerce"
        )


        rota_df["Boylam"] = pd.to_numeric(
            rota_df["Boylam"],
            errors="coerce"
        )


        # -----------------------------------------
        # BOŞ / HATALI SATIRLAR
        # -----------------------------------------

        rota_df = rota_df[
            (rota_df["Tesisat"] != "")
            &
            (rota_df["Okuma Rotası"] != "")
            &
            (rota_df["Enlem"].notna())
            &
            (rota_df["Boylam"].notna())
        ].copy()


        # Türkiye için aşırı hatalı koordinatları ele
        rota_df = rota_df[
            (rota_df["Enlem"] > 30)
            &
            (rota_df["Enlem"] < 45)
            &
            (rota_df["Boylam"] > 20)
            &
            (rota_df["Boylam"] < 50)
        ].copy()


        # -----------------------------------------
        # OKUMA ROTASINI INDEX YAP
        #
        # Böylece her rota seçiminde yüz binlerce
        # satır tekrar taranmaz.
        # -----------------------------------------

        rota_df = rota_df.set_index(
            "Okuma Rotası",
            drop=False
        )


        rota_df = rota_df.sort_index()


        return rota_df


    except Exception as e:

        st.error(
            f"OkumaRotalari.xlsx okuma hatası: {e}"
        )

        return None


# =========================================================
# KOORDİNAT BULMA
# ADMIN + DEMO
# =========================================================

def koordinat_bul(row):

    for l_col, b_col in [

        ("Enlem.1", "Boylam.1"),

        ("Enlem", "Boylam")

    ]:

        try:

            lat = float(
                str(
                    row[l_col]
                ).replace(
                    ",",
                    "."
                )
            )


            lon = float(
                str(
                    row[b_col]
                ).replace(
                    ",",
                    "."
                )
            )


            if (
                lat != 0
                and
                lon != 0
            ):

                return lat, lon

        except Exception:

            pass


    return None, None


# =========================================================
# CONVEX HULL
#
# Okuma rotasındaki tesisatların dış sınırını bulur.
# Kaynak sitedeki kırmızı bölgeye benzer görüntü sağlar.
# =========================================================

@st.cache_data(show_spinner=False)
def convex_hull_hesapla(points_tuple):

    if not points_tuple:
        return []


    # longitude, latitude
    points = sorted(
        set(
            (
                float(lon),
                float(lat)
            )
            for lat, lon
            in points_tuple
        )
    )


    if len(points) == 1:

        return [
            [
                points[0][1],
                points[0][0]
            ]
        ]


    def cross(o, a, b):

        return (
            (a[0] - o[0])
            *
            (b[1] - o[1])
            -
            (a[1] - o[1])
            *
            (b[0] - o[0])
        )


    lower = []


    for p in points:

        while (
            len(lower) >= 2
            and
            cross(
                lower[-2],
                lower[-1],
                p
            ) <= 0
        ):

            lower.pop()


        lower.append(p)


    upper = []


    for p in reversed(points):

        while (
            len(upper) >= 2
            and
            cross(
                upper[-2],
                upper[-1],
                p
            ) <= 0
        ):

            upper.pop()


        upper.append(p)


    hull = (
        lower[:-1]
        +
        upper[:-1]
    )


    return [
        [
            y,
            x
        ]
        for x, y
        in hull
    ]


# =========================================================
# SESSION STATE
# =========================================================

if "giris_yapildi" not in st.session_state:

    st.session_state.giris_yapildi = False


if "kullanici_rolu" not in st.session_state:

    st.session_state.kullanici_rolu = None


# =========================================================
# ADMIN HAFIZASI
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
# DEMO HAFIZASI
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
# GİRİŞ
# =========================================================

if not st.session_state.giris_yapildi:

    st.title(
        "📍 Van-Navigasyon Giriş"
    )


    with st.form(
        "login_form"
    ):

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

            if (
                kadi == "admin"
                and
                sifre == "admin"
            ):

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "admin"

                st.rerun()


            # =================================================
            # DEMO
            # =================================================

            elif (
                kadi == "demo"
                and
                sifre == "demo"
            ):

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

            elif (
                kadi == "demo1"
                and
                sifre == "demo1"
            ):

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "demo1"

                st.rerun()


            else:

                st.error(
                    "Hatalı Kullanıcı Adı veya Şifre!"
                )


# =========================================================
# ADMIN PANEL
# =========================================================

elif (
    st.session_state.kullanici_rolu
    ==
    "admin"
):

    col_baslik, col_cikis = st.columns(
        [8, 1]
    )


    with col_baslik:

        st.markdown(
            "### Van Navigasyon - Admin Paneli"
        )


    with col_cikis:

        if st.button(
            "Çıkış Yap",
            key="admin_logout"
        ):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.rerun()


    # =====================================================
    # ARAMA
    # =====================================================

    with st.form(
        "arama_formu"
    ):

        tesisat_no = st.text_input(

            "Tesisat No",

            placeholder=
            "Tesisat No girin...",

            value=(
                st.session_state.aktif_tesisat

                if
                st.session_state.aktif_tesisat

                else
                ""
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


        elif (
            df is None
            or
            df.empty
        ):

            st.session_state.hata_mesaji = (
                "⚠️ Tesisatlar.xlsx dosyası bulunamadı!"
            )

            st.session_state.aktif_tesisat = None


        else:

            bulunan = df[
                df["Tesisat"]
                ==
                tesisat_no.strip()
            ]


            if bulunan.empty:

                st.session_state.hata_mesaji = (
                    "Bu tesisat numarası bulunamadı!"
                )

                st.session_state.aktif_tesisat = None


            else:

                row = bulunan.iloc[0]


                lat, lon = koordinat_bul(
                    row
                )


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


    # =====================================================
    # MESAJ
    # =====================================================

    if st.session_state.hata_mesaji:

        st.error(
            st.session_state.hata_mesaji
        )


    elif st.session_state.aktif_tesisat:

        st.success(
            f"Tesisat Bulundu: "
            f"{st.session_state.aktif_tesisat}"
        )


    # =====================================================
    # ADMIN HARİTA
    # =====================================================

    m = folium.Map(

        location=[
            st.session_state.son_lat,
            st.session_state.son_lon
        ],

        zoom_start=
        st.session_state.son_zoom

    )


    if st.session_state.aktif_tesisat:


        gmaps_url = (

            "https://www.google.com/maps/dir/"
            "?api=1"

            f"&destination="
            f"{st.session_state.son_lat},"
            f"{st.session_state.son_lon}"

        )


        popup_html = f"""

        <div style="
            font-family:Arial,sans-serif;
            min-width:170px;
            text-align:center;
        ">

            <b>
                Tesisat:
                {st.session_state.aktif_tesisat}
            </b>

            <br><br>

            <a
                href="{gmaps_url}"
                target="_blank"

                style="
                    display:inline-block;
                    padding:8px 14px;
                    background:#2563eb;
                    color:white;
                    text-decoration:none;
                    border-radius:6px;
                    font-weight:bold;
                "
            >

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

        ).add_to(
            m
        )


    st_folium(
        m,
        use_container_width=True,
        height=500
    )


# =========================================================
# DEMO / ROTA PLANLAMA
# =========================================================

elif (
    st.session_state.kullanici_rolu
    ==
    "demo"
):

    col_baslik, col_cikis = st.columns(
        [8, 1]
    )


    with col_baslik:

        st.markdown(
            "### 🗺️ Rota Planlama"
        )


    with col_cikis:

        if st.button(
            "Çıkış Yap",
            key="demo_logout"
        ):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.rerun()


    sol, orta, sag = st.columns(
        [2.3, 5.4, 2.3]
    )


    # =====================================================
    # SOL PANEL
    # =====================================================

    with sol:

        st.markdown(
            "### 📥 Toplu Tesisat"
        )


        st.caption(
            "Tesisat numaralarını alt alta yazın."
        )


        toplu_input = st.text_area(

            "Tesisat Listesi",

            height=320,

            placeholder=
            "100001\n"
            "100002\n"
            "100003\n"
            "100004",

            label_visibility=
            "collapsed"

        )


        if st.button(
            "📍 Haritaya Yükle",
            use_container_width=True
        ):


            if (
                df is None
                or
                df.empty
            ):

                st.error(
                    "Tesisatlar.xlsx dosyası bulunamadı!"
                )


            else:

                girilen_liste = [

                    x.strip()

                    for x
                    in toplu_input.splitlines()

                    if x.strip()

                ]


                yeni_sayisi = 0

                bulunamayanlar = []


                for t_no in girilen_liste:


                    mevcut = any(

                        x["tesisat"] == t_no

                        for x
                        in (
                            st.session_state.demo_yuklenenler
                            +
                            st.session_state.demo_secilenler
                        )

                    )


                    if mevcut:

                        continue


                    # Daha önce kayıtlı rotaya eklenmiş mi?
                    kayitli_mi = False


                    for rota in (
                        st.session_state.demo_kayitli_rotalar
                    ):


                        if any(

                            x["Tesisat"] == t_no

                            for x
                            in rota["tesisatlar"]

                        ):

                            kayitli_mi = True
                            break


                    if kayitli_mi:

                        continue


                    match = df[
                        df["Tesisat"]
                        ==
                        t_no
                    ]


                    if match.empty:

                        bulunamayanlar.append(
                            t_no
                        )

                        continue


                    row = match.iloc[0]


                    lat, lon = koordinat_bul(
                        row
                    )


                    if (
                        lat is not None
                        and
                        lon is not None
                    ):

                        st.session_state.demo_yuklenenler.append({

                            "tesisat":
                            t_no,

                            "lat":
                            lat,

                            "lon":
                            lon

                        })


                        yeni_sayisi += 1


                    else:

                        bulunamayanlar.append(
                            f"{t_no} - koordinat yok"
                        )


                if yeni_sayisi:

                    st.success(
                        f"✅ {yeni_sayisi} tesisat "
                        "haritaya eklendi."
                    )


                if bulunamayanlar:

                    st.warning(
                        "Bulunamayan tesisatlar: "
                        +
                        ", ".join(
                            bulunamayanlar
                        )
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
            "📌 Aktif Rota",
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
    # ORTA PANEL
    # =====================================================

    with orta:

        st.markdown(
            "### 🗺️ Harita"
        )


        st.caption(
            "Yeşil noktaya tıklayarak "
            "rota havuzuna ekleyin."
        )


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

                tooltip=str(
                    item["tesisat"]
                ),

                icon=folium.Icon(
                    color="green",
                    icon="info-sign"
                )

            ).add_to(
                m_demo
            )


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


                    secilen = None

                    en_yakin = float(
                        "inf"
                    )


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

                            if
                            x["tesisat"]
                            !=
                            secilen["tesisat"]

                        ]


                        if not any(

                            x["tesisat"]
                            ==
                            secilen["tesisat"]

                            for x
                            in st.session_state.demo_secilenler

                        ):

                            st.session_state.demo_secilenler.append(
                                secilen
                            )


                        st.rerun()


    # =====================================================
    # SAĞ PANEL
    # =====================================================

    with sag:

        st.markdown(
            "### 📌 Rota Havuzu"
        )


        rota_adi = st.text_input(

            "Rota Adı",

            value=
            st.session_state.demo_rota_adi,

            key=
            "demo_rota_adi_input"

        )


        st.session_state.demo_rota_adi = (
            rota_adi
        )


        st.caption(
            f"Seçilen tesisat: "
            f"**{len(st.session_state.demo_secilenler)}**"
        )


        # -----------------------------------------
        # KAYDIRILABİLİR HAVUZ
        # -----------------------------------------

        with st.container(
            height=430,
            border=True
        ):


            if st.session_state.demo_secilenler:


                for idx, item in enumerate(
                    st.session_state.demo_secilenler
                ):


                    if st.button(

                        f"{idx + 1}. "
                        f"{item['tesisat']}",

                        key=(
                            f"havuz_"
                            f"{idx}_"
                            f"{item['tesisat']}"
                        ),

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


        st.caption(
            "💡 Tesisat numarasına tıklarsanız "
            "haritaya geri gönderilir."
        )


        # -----------------------------------------
        # ROTA KAYDET
        # -----------------------------------------

        if st.session_state.demo_secilenler:


            if st.button(
                "💾 Rotayı Kaydet",
                use_container_width=True
            ):


                if not rota_adi.strip():

                    st.error(
                        "Lütfen rota adı girin."
                    )


                else:


                    ayni_isim = any(

                        r["rota_adi"].lower()
                        ==
                        rota_adi.strip().lower()

                        for r
                        in st.session_state.demo_kayitli_rotalar

                    )


                    if ayni_isim:

                        st.warning(
                            "Bu isimde bir rota zaten kayıtlı."
                        )


                    else:


                        kayit = []


                        for sira, item in enumerate(

                            st.session_state.demo_secilenler,

                            start=1

                        ):


                            kayit.append({

                                "Rota Adı":
                                rota_adi.strip(),

                                "Sıra":
                                sira,

                                "Tesisat":
                                item["tesisat"]

                            })


                        st.session_state.demo_kayitli_rotalar.append({

                            "rota_adi":
                            rota_adi.strip(),

                            "tesisatlar":
                            kayit

                        })


                        st.session_state.demo_secilenler = []


                        sonraki_no = (

                            len(
                                st.session_state.demo_kayitli_rotalar
                            )

                            +

                            1

                        )


                        st.session_state.demo_rota_adi = (
                            f"Rota {sonraki_no}"
                        )


                        st.rerun()


        # -----------------------------------------
        # KAYITLI ROTALAR
        # -----------------------------------------

        if st.session_state.demo_kayitli_rotalar:


            st.markdown("---")


            st.markdown(
                "##### 💾 Kaydedilen Rotalar"
            )


            with st.container(
                height=220,
                border=True
            ):


                for i, rota in enumerate(
                    st.session_state.demo_kayitli_rotalar
                ):


                    st.write(
                        f"📁 **{rota['rota_adi']}**"
                    )


                    st.caption(
                        f"{len(rota['tesisatlar'])} tesisat"
                    )


                    if (
                        i
                        <
                        len(
                            st.session_state.demo_kayitli_rotalar
                        ) - 1
                    ):

                        st.divider()


            # -------------------------------------
            # EXCEL
            # -------------------------------------

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


                try:


                    with pd.ExcelWriter(
                        output,
                        engine="openpyxl"
                    ) as writer:


                        excel_df.to_excel(

                            writer,

                            index=False,

                            sheet_name="Rotalar"

                        )


                    excel_data = (
                        output.getvalue()
                    )


                    st.download_button(

                        "📊 TÜM ROTALARI EXCELE AKTAR",

                        data=
                        excel_data,

                        file_name=
                        "Tum_Rotalar.xlsx",

                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),

                        use_container_width=True

                    )


                except Exception as e:

                    st.error(
                        f"Excel oluşturulurken hata oluştu: {e}"
                    )


# =========================================================
# DEMO1
#
# HIZLI OKUMA ROTASI HARİTASI
# =========================================================

elif (
    st.session_state.kullanici_rolu
    ==
    "demo1"
):


    # =====================================================
    # ÜST BAŞLIK
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
            "Çıkış Yap",
            key="demo1_logout"
        ):

            st.session_state.giris_yapildi = False

            st.session_state.kullanici_rolu = None

            st.rerun()


    # =====================================================
    # EXCELİ LAZY LOAD ET
    #
    # admin/demo kullanırken bu Excel hiç okunmaz.
    # =====================================================

    if not os.path.exists(
        OKUMA_ROTALARI_DOSYA
    ):

        st.error(
            "⚠️ OkumaRotalari.xlsx bulunamadı."
        )

        st.stop()


    with st.spinner(
        "Okuma rotası listesi yükleniyor..."
    ):

        okuma_df = (
            okuma_rotasi_verisi_yukle()
        )


    if (
        okuma_df is None
        or
        okuma_df.empty
    ):

        st.error(
            "OkumaRotalari.xlsx içerisinde "
            "geçerli veri bulunamadı."
        )

        st.stop()


    # =====================================================
    # ROTA LİSTESİ
    # =====================================================

    rotalar = (
        okuma_df[
            "Okuma Rotası"
        ]
        .drop_duplicates()
        .astype(str)
        .tolist()
    )


    # doğal sıralama
    try:

        rotalar = sorted(
            rotalar,
            key=lambda x: (
                0,
                int(x)
            )
            if str(x).isdigit()
            else (
                1,
                str(x)
            )
        )

    except Exception:

        rotalar = sorted(
            rotalar
        )


    # =====================================================
    # STREAMLIT FRAGMENT
    #
    # ROTA DEĞİŞTİRİLDİĞİNDE SADECE BU BÖLÜM
    # YENİDEN ÇALIŞIR.
    # =====================================================

    fragment_decorator = getattr(
        st,
        "fragment",
        lambda func: func
    )


    @fragment_decorator
    def okuma_rotasi_haritasi():


        # =================================================
        # ROTA SEÇ
        # =================================================

        col_secim, col_adet = st.columns(
            [5, 1]
        )


        with col_secim:


            secilen_rota = st.selectbox(

                "📋 Okuma Rotası",

                options=
                rotalar,

                key=
                "demo1_rota_secimi",

                help=(
                    "Kutuyu açıp rota numarasını "
                    "yazarak arayabilirsiniz."
                )

            )


        # =================================================
        # SADECE SEÇİLEN ROTANIN SATIRLARI
        # =================================================

        try:

            rota_df = okuma_df.loc[
                [
                    secilen_rota
                ]
            ].copy()


        except KeyError:

            rota_df = pd.DataFrame()


        with col_adet:

            st.metric(
                "Tesisat",
                len(
                    rota_df
                )
            )


        if rota_df.empty:

            st.warning(
                "Bu okuma rotasında tesisat bulunamadı."
            )

            return


        # =================================================
        # NOKTALAR
        # =================================================

        points_tuple = tuple(

            zip(
                rota_df["Enlem"].tolist(),
                rota_df["Boylam"].tolist()
            )

        )


        # =================================================
        # KIRMIZI DIŞ SINIR
        # =================================================

        hull = convex_hull_hesapla(
            points_tuple
        )


        # =================================================
        # HARİTA MERKEZ
        # =================================================

        merkez_lat = float(
            rota_df["Enlem"].mean()
        )


        merkez_lon = float(
            rota_df["Boylam"].mean()
        )


        # =================================================
        # HARİTA
        # =================================================

        m_rota = folium.Map(

            location=[
                merkez_lat,
                merkez_lon
            ],

            zoom_start=14,

            tiles=None,

            control_scale=True,

            prefer_canvas=True

        )


        # =================================================
        # HARİTA KATMANLARI
        # =================================================

        folium.TileLayer(

            tiles=(
                "https://{s}.tile.openstreetmap.org/"
                "{z}/{x}/{y}.png"
            ),

            attr="© OpenStreetMap",

            name="🗺️ Yol Haritası",

            max_zoom=21

        ).add_to(
            m_rota
        )


        folium.TileLayer(

            tiles=(
                "https://server.arcgisonline.com/"
                "ArcGIS/rest/services/"
                "World_Imagery/MapServer/"
                "tile/{z}/{y}/{x}"
            ),

            attr="Esri",

            name="🛰️ Uydu",

            max_zoom=20

        ).add_to(
            m_rota
        )


        # =================================================
        # KIRMIZI ROTA ALANI
        # =================================================

        if len(hull) >= 3:


            folium.Polygon(

                locations=
                hull,

                color=
                "#dc2626",

                weight=
                4,

                opacity=
                0.95,

                fill=
                True,

                fill_color=
                "#dc2626",

                fill_opacity=
                0.08,

                tooltip=(
                    f"Okuma Rotası: "
                    f"{secilen_rota}"
                )

            ).add_to(
                m_rota
            )


            m_rota.fit_bounds(

                hull,

                padding=(
                    40,
                    40
                )

            )


        elif len(hull) == 2:


            folium.PolyLine(

                locations=
                hull,

                color=
                "#dc2626",

                weight=
                4

            ).add_to(
                m_rota
            )


            m_rota.fit_bounds(
                hull
            )


        elif len(hull) == 1:


            m_rota.location = (
                hull[0]
            )


        # =================================================
        # FAST MARKER CLUSTER
        #
        # Normal Folium Marker'dan çok daha hafif.
        # =================================================

        cluster_data = [

            [
                float(
                    row["Enlem"]
                ),

                float(
                    row["Boylam"]
                ),

                str(
                    row["Tesisat"]
                )

            ]

            for _,
            row
            in rota_df.iterrows()

        ]


        marker_callback = """

        function (row) {

            var lat = row[0];

            var lon = row[1];

            var tesisat = row[2];


            var dotIcon = L.divIcon({

                className: '',

                html:
                    '<div style="' +
                    'width:14px;' +
                    'height:14px;' +
                    'background:#0f766e;' +
                    'border:2px solid white;' +
                    'border-radius:50%;' +
                    'box-shadow:0 1px 4px rgba(0,0,0,.55);' +
                    '"></div>',

                iconSize:
                    [14,14],

                iconAnchor:
                    [7,7]

            });


            var marker = L.marker(

                new L.LatLng(
                    lat,
                    lon
                ),

                {
                    icon:
                    dotIcon
                }

            );


            marker.bindTooltip(

                'Tesisat: '
                +
                tesisat

            );


            var googleUrl =

                'https://www.google.com/maps/dir/?api=1'

                +

                '&destination='
                +
                lat
                +
                ','
                +
                lon

                +

                '&travelmode=driving';


            var popup =

                '<div style="' +

                    'font-family:Arial,sans-serif;' +

                    'min-width:180px;' +

                    'text-align:center;' +

                '">' +


                '<div style="' +

                    'font-size:12px;' +

                    'color:#64748b;' +

                    'margin-bottom:4px;' +

                '">' +

                    'TESİSAT' +

                '</div>' +


                '<div style="' +

                    'font-size:20px;' +

                    'font-weight:bold;' +

                    'margin-bottom:12px;' +

                '">' +

                    tesisat +

                '</div>' +


                '<a ' +

                    'href="' +
                    googleUrl +
                    '" ' +

                    'target="_blank" ' +

                    'style="' +

                        'display:inline-block;' +

                        'background:#0f766e;' +

                        'color:white;' +

                        'text-decoration:none;' +

                        'padding:9px 14px;' +

                        'border-radius:7px;' +

                        'font-weight:bold;' +

                    '"' +

                '>' +

                    '🚗 Yol Tarifi Al' +

                '</a>' +


                '</div>';


            marker.bindPopup(
                popup
            );


            return marker;

        }

        """


        FastMarkerCluster(

            data=
            cluster_data,

            callback=
            marker_callback,

            maxClusterRadius=
            45,

            disableClusteringAtZoom=
            18,

            showCoverageOnHover=
            False

        ).add_to(
            m_rota
        )


        # =================================================
        # KATMAN SEÇİCİ
        # =================================================

        folium.LayerControl(
            position="bottomleft"
        ).add_to(
            m_rota
        )


        # =================================================
        # KONUM BUTONU
        # =================================================

        try:

            from folium.plugins import LocateControl


            LocateControl(

                auto_start=False,

                position="bottomright",

                strings={
                    "title":
                    "Konumumu Göster"
                }

            ).add_to(
                m_rota
            )


        except Exception:

            pass


        # =================================================
        # TAM EKRAN
        # =================================================

        try:

            from folium.plugins import Fullscreen


            Fullscreen(

                position="topright",

                title="Tam Ekran",

                title_cancel="Tam Ekrandan Çık",

                force_separate_button=True

            ).add_to(
                m_rota
            )


        except Exception:

            pass


        # =================================================
        # BİLGİ
        # =================================================

        st.caption(
            f"🔴 **{secilen_rota}** okuma rotası — "
            f"**{len(rota_df)} tesisat**"
        )


        # =================================================
        # HARİTA GÖSTER
        #
        # folium_static kullanıyoruz.
        #
        # Haritaya tıklamak Streamlit'e veri göndermez.
        # Bu yüzden marker / popup / zoom işlemlerinde
        # sayfa tekrar çalışmaz.
        # =================================================

        folium_static(

            m_rota,

            height=700

        )


    # Fragmenti çalıştır
    okuma_rotasi_haritasi()
