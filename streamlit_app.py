import os
import json
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import folium
from streamlit_folium import st_folium


# =========================================================
# SAYFA
# =========================================================

st.set_page_config(
    page_title="Van-Navigasyon",
    page_icon="📍",
    layout="wide"
)


# =========================================================
# DOSYA YOLLARI
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
# ANA TESİSAT EXCEL
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


        rota_df["Tesisat"] = (
            rota_df["Tesisat"]
            .fillna("")
            .astype(str)
            .str.strip()
        )


        rota_df["Okuma Rotası"] = (
            rota_df["Okuma Rotası"]
            .fillna("")
            .astype(str)
            .str.strip()
        )


        rota_df["Enlem"] = (
            rota_df["Enlem"]
            .fillna("")
            .astype(str)
            .str.replace(",", ".", regex=False)
        )


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


        rota_df = rota_df[
            (rota_df["Tesisat"] != "")
            &
            (rota_df["Okuma Rotası"] != "")
            &
            (rota_df["Enlem"].notna())
            &
            (rota_df["Boylam"].notna())
        ].copy()


        # Türkiye dışında bariz hatalı koordinatlar gelirse çıkar
        rota_df = rota_df[
            (rota_df["Enlem"] > 30)
            &
            (rota_df["Enlem"] < 45)
            &
            (rota_df["Boylam"] > 20)
            &
            (rota_df["Boylam"] < 50)
        ].copy()


        return rota_df

    except Exception as e:

        st.error(
            f"OkumaRotalari.xlsx okuma hatası: {e}"
        )

        return None


okuma_df = okuma_rotasi_verisi_yukle()


# =========================================================
# CONVEX HULL
#
# Excelde hazır bölge sınırı olmadığı için tesisatların
# dış çevresini hesaplar.
# =========================================================

def convex_hull(points):

    if len(points) <= 1:
        return points

    # x = longitude
    # y = latitude

    pts = sorted(
        set(
            (float(lon), float(lat))
            for lat, lon in points
        )
    )

    if len(pts) <= 1:
        return [
            [pts[0][1], pts[0][0]]
        ]


    def cross(o, a, b):

        return (
            (a[0] - o[0]) *
            (b[1] - o[1])
            -
            (a[1] - o[1]) *
            (b[0] - o[0])
        )


    lower = []

    for p in pts:

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

    for p in reversed(pts):

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
        [y, x]
        for x, y in hull
    ]


# =========================================================
# DEMO1 İÇİN TARAYICI VERİSİ
# =========================================================

@st.cache_data
def demo1_verisini_hazirla(dataframe):

    sonuc = {}


    for rota_adi, grup in dataframe.groupby(
        "Okuma Rotası",
        sort=True
    ):

        binalar = []

        noktalar = []


        for _, row in grup.iterrows():

            tesisat = str(
                row["Tesisat"]
            ).strip()

            lat = float(
                row["Enlem"]
            )

            lon = float(
                row["Boylam"]
            )


            binalar.append({
                "tesisat": tesisat,
                "lat": lat,
                "lon": lon
            })


            noktalar.append(
                (lat, lon)
            )


        merkez_lat = sum(
            p[0]
            for p in noktalar
        ) / len(noktalar)


        merkez_lon = sum(
            p[1]
            for p in noktalar
        ) / len(noktalar)


        # Rotanın çevresini hesapla
        hull = convex_hull(
            noktalar
        )


        sonuc[str(rota_adi)] = {

            "kod":
            str(rota_adi),

            "n":
            len(binalar),

            "clat":
            merkez_lat,

            "clon":
            merkez_lon,

            "polygon":
            hull,

            "buildings":
            binalar

        }


    return sonuc


# =========================================================
# SESSION STATE
# =========================================================

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if "kullanici_rolu" not in st.session_state:
    st.session_state.kullanici_rolu = None


# =========================================================
# ADMIN
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
# DEMO
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
# LOGIN
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
            "Çıkış Yap"
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

                lat = None
                lon = None


                for l_col, b_col in [

                    (
                        "Enlem.1",
                        "Boylam.1"
                    ),

                    (
                        "Enlem",
                        "Boylam"
                    )

                ]:

                    try:

                        val_lat = float(
                            str(
                                row[l_col]
                            ).replace(
                                ",",
                                "."
                            )
                        )


                        val_lon = float(
                            str(
                                row[b_col]
                            ).replace(
                                ",",
                                "."
                            )
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
            font-family:sans-serif;
            min-width:160px;
        ">

            <b>Tesisat:</b>
            {st.session_state.aktif_tesisat}

            <br><br>

            <a
                href="{gmaps_url}"
                target="_blank"

                style="
                    background:#2563eb;
                    color:white;
                    padding:7px 12px;
                    text-decoration:none;
                    border-radius:5px;
                    display:inline-block;
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

        ).add_to(m)


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
            "Çıkış Yap"
        ):

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

                    # -----------------------------------------
                    # aktif alanda var mı
                    # -----------------------------------------

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


                    # -----------------------------------------
                    # kayıtlı rotalarda var mı
                    # -----------------------------------------

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

                    lat = None
                    lon = None


                    for l_col, b_col in [

                        (
                            "Enlem.1",
                            "Boylam.1"
                        ),

                        (
                            "Enlem",
                            "Boylam"
                        )

                    ]:

                        try:

                            v_lat = float(
                                str(
                                    row[l_col]
                                ).replace(
                                    ",",
                                    "."
                                )
                            )


                            v_lon = float(
                                str(
                                    row[b_col]
                                ).replace(
                                    ",",
                                    "."
                                )
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
                        f"haritaya eklendi."
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
    # ORTA
    # =====================================================

    with orta:

        st.markdown(
            "### 🗺️ Harita"
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
        # SCROLL HAVUZ
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
            "💡 Tesisata tıklarsanız haritaya geri gönderilir."
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


            # -----------------------------------------
            # EXCEL
            # -----------------------------------------

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
# HIZLI LEAFLET OKUMA ROTALARI
# =========================================================

elif (
    st.session_state.kullanici_rolu
    ==
    "demo1"
):

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
    # EXCEL KONTROL
    # =====================================================

    if okuma_df is None:

        st.error(
            "⚠️ OkumaRotalari.xlsx bulunamadı."
        )

        st.info(
            "Dosya GitHub'da streamlit_app.py "
            "ile aynı klasörde ve adı birebir "
            "OkumaRotalari.xlsx olmalıdır."
        )

        st.stop()


    if okuma_df.empty:

        st.warning(
            "OkumaRotalari.xlsx içerisinde "
            "geçerli tesisat / rota / koordinat bulunamadı."
        )

        st.stop()


    # =====================================================
    # TÜM VERİYİ BİR KEZ HAZIRLA
    # =====================================================

    demo1_data = demo1_verisini_hazirla(
        okuma_df
    )


    # JSON
    demo1_json = json.dumps(

        demo1_data,

        ensure_ascii=False,

        separators=(
            ",",
            ":"
        )

    )


    # script kapanmasını bozmasın
    demo1_json = demo1_json.replace(
        "</",
        "<\\/"
    )


    # =====================================================
    # LEAFLET HTML
    # =====================================================

    demo1_html = """
<!DOCTYPE html>

<html lang="tr">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="
        width=device-width,
        initial-scale=1.0,
        maximum-scale=1.0,
        user-scalable=no
    "
>

<link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
/>

<link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.css"
/>

<link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.css"
/>


<style>

:root {
    --primary:#0f766e;
    --primary-dark:#0b5a54;
    --accent:#dc2626;
    --bg:#f4f6f5;
    --panel:#ffffff;
    --border:#e2e8f0;
    --text:#1e293b;
    --muted:#64748b;
}


* {
    box-sizing:border-box;
}


html,
body {
    margin:0;
    padding:0;
    height:100%;
    width:100%;
    overflow:hidden;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;

    background:var(--bg);
    color:var(--text);
}


#app {
    position:relative;
    width:100%;
    height:800px;
    overflow:hidden;
    border-radius:12px;
    border:1px solid #dfe5e4;
}


#map {
    position:absolute;
    inset:0;
    z-index:1;
}


/* =======================================================
   ÜST PANEL
   ======================================================= */

#topbar {

    position:absolute;

    top:0;
    left:0;
    right:0;

    z-index:1000;

    padding:10px 12px;

    background:var(--primary);

    color:white;

    box-shadow:
        0 2px 10px rgba(0,0,0,.2);
}


#topTitle {

    font-size:15px;

    font-weight:700;

    margin-bottom:8px;
}


#routeWrap {
    position:relative;
}


#routeInput {

    width:100%;

    padding:11px 12px;

    border:none;

    border-radius:8px;

    outline:none;

    font-size:15px;

    color:#1e293b;
}


#routeSuggest {

    display:none;

    position:absolute;

    left:0;
    right:0;

    top:100%;

    margin-top:4px;

    background:white;

    border-radius:8px;

    box-shadow:
        0 4px 14px rgba(0,0,0,.25);

    max-height:300px;

    overflow-y:auto;

    z-index:1005;
}


.route-item {

    padding:10px 12px;

    border-bottom:
        1px solid #edf0ef;

    cursor:pointer;

    color:#1e293b;

    font-size:14px;
}


.route-item:hover {
    background:#f1f5f4;
}


.route-code {

    font-weight:700;

    color:var(--primary-dark);
}


.route-count {

    font-size:12px;

    color:#64748b;

    margin-left:6px;
}


/* =======================================================
   BİLGİ PANELİ
   ======================================================= */

#infoBar {

    position:absolute;

    left:12px;
    right:12px;

    z-index:999;

    display:none;

    padding:10px 12px;

    background:white;

    border-radius:10px;

    box-shadow:
        0 2px 10px rgba(0,0,0,.17);

    font-size:13px;
}


#infoBar b {
    color:var(--primary-dark);
}


/* =======================================================
   KONUM BUTONU
   ======================================================= */

#locateBtn {

    position:absolute;

    z-index:999;

    right:12px;
    bottom:20px;

    width:48px;
    height:48px;

    border:none;

    border-radius:50%;

    background:white;

    box-shadow:
        0 2px 10px rgba(0,0,0,.28);

    font-size:21px;

    cursor:pointer;
}


/* =======================================================
   BOTTOM SHEET
   ======================================================= */

#bottomSheet {

    display:none;

    position:absolute;

    left:0;
    right:0;
    bottom:0;

    z-index:1100;

    background:white;

    border-radius:
        16px 16px 0 0;

    box-shadow:
        0 -4px 16px rgba(0,0,0,.22);

    padding:
        14px 16px 18px;
}


.handle {

    width:42px;
    height:4px;

    border-radius:4px;

    background:#d6dcda;

    margin:
        0 auto 12px;
}


#sheetTitle {

    margin:0 0 5px;

    font-size:18px;
}


#sheetMeta {

    font-size:13px;

    color:#64748b;

    margin-bottom:13px;
}


.sheetButtons {

    display:flex;

    gap:8px;
}


.navBtn {

    flex:1;

    display:flex;

    align-items:center;

    justify-content:center;

    padding:12px 10px;

    border-radius:10px;

    font-size:14px;

    font-weight:700;

    text-decoration:none;

    border:none;

    cursor:pointer;
}


.primaryBtn {

    background:var(--primary);

    color:white;
}


.secondaryBtn {

    background:#eef2f1;

    color:#1e293b;
}


/* =======================================================
   MARKER
   ======================================================= */

.building-dot {

    width:14px;

    height:14px;

    border-radius:50%;

    background:#0f766e;

    border:
        2px solid white;

    box-shadow:
        0 1px 4px rgba(0,0,0,.55);
}


/* =======================================================
   LOADING
   ======================================================= */

#loading {

    position:absolute;

    inset:0;

    z-index:2000;

    display:flex;

    align-items:center;

    justify-content:center;

    flex-direction:column;

    gap:10px;

    background:#f4f6f5;
}


.spinner {

    width:38px;

    height:38px;

    border:
        4px solid #d4dfdc;

    border-top-color:
        var(--primary);

    border-radius:50%;

    animation:
        spin .75s linear infinite;
}


@keyframes spin {

    to {
        transform:
            rotate(360deg);
    }

}


#loadingText {

    color:#64748b;

    font-size:14px;
}


/* =======================================================
   MOBİL
   ======================================================= */

@media(max-width:600px) {

    #app {
        height:780px;
        border-radius:0;
    }

}

</style>

</head>


<body>


<div id="app">


    <div id="loading">

        <div class="spinner"></div>

        <div id="loadingText">
            Okuma rotaları hazırlanıyor...
        </div>

    </div>


    <div id="map"></div>


    <div id="topbar">

        <div id="topTitle">
            📍 Okuma Rotası Seç
        </div>


        <div id="routeWrap">

            <input

                id="routeInput"

                type="text"

                autocomplete="off"

                placeholder="Okuma rotası yazın veya seçin..."

            >


            <div id="routeSuggest"></div>

        </div>

    </div>


    <div id="infoBar"></div>


    <button

        id="locateBtn"

        title="Konumum"

        onclick="locateMe()"

    >
        🧭
    </button>


    <div id="bottomSheet">

        <div class="handle"></div>


        <h3 id="sheetTitle">
            -
        </h3>


        <div id="sheetMeta">
            -
        </div>


        <div class="sheetButtons">


            <a

                id="navBtn"

                class="
                    navBtn
                    primaryBtn
                "

                target="_blank"

                href="#"

            >

                🚗 Yol Tarifi Al

            </a>


            <button

                class="
                    navBtn
                    secondaryBtn
                "

                onclick="closeSheet()"

            >

                Kapat

            </button>


        </div>

    </div>


</div>


<script
    src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js">
</script>


<script
    src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js">
</script>


<script>


/* =======================================================
   VERİ
   ======================================================= */

const APP_DATA = __DEMO1_JSON__;


const routeCodes =
    Object.keys(
        APP_DATA
    ).sort(
        (a,b) =>
        a.localeCompare(
            b,
            'tr',
            {
                numeric:true
            }
        )
    );


let map = null;

let selectedAreaLayer = null;

let buildingClusterLayer = null;

let userMarker = null;


/* =======================================================
   HARİTA BAŞLAT
   ======================================================= */

function initMap() {


    let firstLat = 38.5;

    let firstLon = 43.4;


    if (
        routeCodes.length > 0
    ) {

        const first =
            APP_DATA[
                routeCodes[0]
            ];


        firstLat =
            first.clat;


        firstLon =
            first.clon;

    }


    map = L.map(
        'map',
        {
            zoomControl:true,
            attributionControl:true
        }
    ).setView(
        [
            firstLat,
            firstLon
        ],
        12
    );


    /* -------------------------------------------------------
       HARİTA KATMANLARI
       ------------------------------------------------------- */


    const osm =
        L.tileLayer(

            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',

            {
                maxZoom:21,

                attribution:
                '&copy; OpenStreetMap'
            }

        );


    const esri =
        L.tileLayer(

            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',

            {
                maxZoom:20,

                attribution:
                'Tiles &copy; Esri'
            }

        );


    osm.addTo(
        map
    );


    L.control.layers(

        {

            '🗺️ Yol Haritası':
            osm,

            '🛰️ Uydu':
            esri

        },

        null,

        {

            position:
            'bottomleft',

            collapsed:
            true

        }

    ).addTo(
        map
    );


    buildRouteSearch();


    document.getElementById(
        'loading'
    ).style.display =
        'none';


    if (
        routeCodes.length
        >
        0
    ) {

        selectRoute(
            routeCodes[0]
        );

    }

}


/* =======================================================
   ROTA ARAMA
   ======================================================= */

function buildRouteSearch() {


    const input =
        document.getElementById(
            'routeInput'
        );


    const box =
        document.getElementById(
            'routeSuggest'
        );


    function render(
        list
    ) {


        if (
            !list.length
        ) {

            box.innerHTML =
                '<div class="route-item">Eşleşme bulunamadı</div>';

            box.style.display =
                'block';

            return;

        }


        box.innerHTML =
            list
            .slice(
                0,
                80
            )
            .map(
                kod => {

                    const rec =
                        APP_DATA[
                            kod
                        ];


                    const safeKod =
                        kod
                        .replace(
                            /\\/g,
                            '\\\\'
                        )
                        .replace(
                            /'/g,
                            "\\'"
                        );


                    return `

                    <div

                        class="route-item"

                        onclick="
                            selectRoute(
                                '${safeKod}'
                            )
                        "

                    >

                        <span
                            class="route-code"
                        >
                            ${kod}
                        </span>

                        <span
                            class="route-count"
                        >
                            (${rec.n} tesisat)
                        </span>

                    </div>

                    `;

                }
            )
            .join(
                ''
            );


        box.style.display =
            'block';

    }


    input.addEventListener(
        'focus',
        () => {

            const q =
                input.value
                .trim()
                .toLocaleUpperCase(
                    'tr-TR'
                );


            if (
                !q
            ) {

                render(
                    routeCodes
                );

            }
            else {

                render(

                    routeCodes.filter(
                        x =>
                        x
                        .toLocaleUpperCase(
                            'tr-TR'
                        )
                        .includes(
                            q
                        )
                    )

                );

            }

        }
    );


    input.addEventListener(
        'input',
        () => {

            const q =
                input.value
                .trim()
                .toLocaleUpperCase(
                    'tr-TR'
                );


            const filtered =
                routeCodes.filter(

                    x =>
                    x
                    .toLocaleUpperCase(
                        'tr-TR'
                    )
                    .includes(
                        q
                    )

                );


            render(
                filtered
            );

        }
    );


    document.addEventListener(
        'click',
        event => {

            const wrap =
                document.getElementById(
                    'routeWrap'
                );


            if (
                !wrap.contains(
                    event.target
                )
            ) {

                box.style.display =
                    'none';

            }

        }
    );

}


/* =======================================================
   ROTA SEÇ
   ======================================================= */

function selectRoute(
    kod
) {


    const rec =
        APP_DATA[
            kod
        ];


    if (
        !rec
    ) {
        return;
    }


    document.getElementById(
        'routeInput'
    ).value =
        kod;


    document.getElementById(
        'routeSuggest'
    ).style.display =
        'none';


    closeSheet();


    /* -------------------------------------------------------
       ESKİ ALANI SİL
       ------------------------------------------------------- */

    if (
        selectedAreaLayer
    ) {

        map.removeLayer(
            selectedAreaLayer
        );

        selectedAreaLayer =
            null;

    }


    /* -------------------------------------------------------
       ESKİ MARKERLARI SİL
       ------------------------------------------------------- */

    if (
        buildingClusterLayer
    ) {

        map.removeLayer(
            buildingClusterLayer
        );

        buildingClusterLayer =
            null;

    }


    /* -------------------------------------------------------
       KIRMIZI ALAN / ÇİZGİ
       ------------------------------------------------------- */

    if (
        rec.polygon
        &&
        rec.polygon.length >= 3
    ) {

        selectedAreaLayer =
            L.polygon(

                rec.polygon,

                {

                    color:
                    '#dc2626',

                    weight:
                    4,

                    opacity:
                    0.95,

                    fillColor:
                    '#dc2626',

                    fillOpacity:
                    0.08

                }

            ).addTo(
                map
            );

    }


    else if (
        rec.polygon
        &&
        rec.polygon.length == 2
    ) {

        selectedAreaLayer =
            L.polyline(

                rec.polygon,

                {

                    color:
                    '#dc2626',

                    weight:
                    4,

                    opacity:
                    0.95

                }

            ).addTo(
                map
            );

    }


    /* -------------------------------------------------------
       MARKER CLUSTER
       ------------------------------------------------------- */

    buildingClusterLayer =
        L.markerClusterGroup({

            maxClusterRadius:
            45,

            disableClusteringAtZoom:
            18,

            spiderfyOnMaxZoom:
            true,

            showCoverageOnHover:
            false

        });


    rec.buildings.forEach(
        bina => {


            const marker =
                L.marker(

                    [
                        bina.lat,
                        bina.lon
                    ],

                    {

                        icon:
                        buildingIcon()

                    }

                );


            marker.bindTooltip(
                'Tesisat: '
                +
                bina.tesisat
            );


            marker.on(
                'click',
                () => {

                    openSheet(
                        bina,
                        kod
                    );

                }
            );


            buildingClusterLayer.addLayer(
                marker
            );

        }
    );


    map.addLayer(
        buildingClusterLayer
    );


    /* -------------------------------------------------------
       HARİTAYI ALANA UYDUR
       ------------------------------------------------------- */

    if (
        selectedAreaLayer
    ) {

        const bounds =
            selectedAreaLayer.getBounds();


        map.fitBounds(

            bounds,

            {

                padding:
                [45,45],

                maxZoom:
                17

            }

        );

    }


    else if (
        buildingClusterLayer.getLayers().length
        >
        0
    ) {

        const bounds =
            buildingClusterLayer.getBounds();


        map.fitBounds(

            bounds,

            {

                padding:
                [45,45],

                maxZoom:
                17

            }

        );

    }


    else {

        map.setView(
            [
                rec.clat,
                rec.clon
            ],
            15
        );

    }


    /* -------------------------------------------------------
       BİLGİ
       ------------------------------------------------------- */

    showInfo(

        '<b>Okuma Rotası:</b> '
        +
        kod
        +
        ' &nbsp; | &nbsp; '
        +
        '<b>'
        +
        rec.n
        +
        '</b> tesisat'

    );

}


/* =======================================================
   MARKER İKONU
   ======================================================= */

function buildingIcon() {


    return L.divIcon({

        className:
        '',

        html:
        '<div class="building-dot"></div>',

        iconSize:
        [14,14],

        iconAnchor:
        [7,7]

    });

}


/* =======================================================
   BİLGİ
   ======================================================= */

function showInfo(
    html
) {


    const bar =
        document.getElementById(
            'infoBar'
        );


    bar.innerHTML =
        html;


    bar.style.display =
        'block';


    positionInfo();

}


function positionInfo() {


    const top =
        document.getElementById(
            'topbar'
        ).offsetHeight;


    document.getElementById(
        'infoBar'
    ).style.top =
        (top + 8)
        +
        'px';

}


window.addEventListener(
    'resize',
    positionInfo
);


/* =======================================================
   TESİSAT PANELİ
   ======================================================= */

function openSheet(
    bina,
    rota
) {


    document.getElementById(
        'sheetTitle'
    ).textContent =
        'Tesisat: '
        +
        bina.tesisat;


    document.getElementById(
        'sheetMeta'
    ).textContent =
        'Okuma Rotası: '
        +
        rota;


    const url =
        'https://www.google.com/maps/dir/?api=1'
        +
        '&destination='
        +
        bina.lat
        +
        ','
        +
        bina.lon
        +
        '&travelmode=driving';


    document.getElementById(
        'navBtn'
    ).href =
        url;


    document.getElementById(
        'bottomSheet'
    ).style.display =
        'block';

}


function closeSheet() {


    document.getElementById(
        'bottomSheet'
    ).style.display =
        'none';

}


/* =======================================================
   KONUMUM
   ======================================================= */

function locateMe() {


    if (
        !navigator.geolocation
    ) {

        alert(
            'Tarayıcı konum servisini desteklemiyor.'
        );

        return;

    }


    navigator.geolocation.getCurrentPosition(

        pos => {


            const lat =
                pos.coords.latitude;


            const lon =
                pos.coords.longitude;


            if (
                userMarker
            ) {

                map.removeLayer(
                    userMarker
                );

            }


            userMarker =
                L.circleMarker(

                    [
                        lat,
                        lon
                    ],

                    {

                        radius:
                        8,

                        color:
                        '#2563eb',

                        fillColor:
                        '#3b82f6',

                        fillOpacity:
                        0.95,

                        weight:
                        3

                    }

                ).addTo(
                    map
                );


            map.setView(
                [
                    lat,
                    lon
                ],
                17
            );

        },


        err => {

            alert(
                'Konum alınamadı: '
                +
                err.message
            );

        },


        {

            enableHighAccuracy:
            true,

            timeout:
            10000

        }

    );

}


/* =======================================================
   START
   ======================================================= */

initMap();


</script>


</body>

</html>
"""


    # JSON'u HTML içine koy
    demo1_html = demo1_html.replace(
        "__DEMO1_JSON__",
        demo1_json
    )


    # =====================================================
    # COMPONENT
    # =====================================================

    components.html(

        demo1_html,

        height=820,

        scrolling=False

    )
