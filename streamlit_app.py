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
# EXCEL VERİSİNİ YÜKLE
# =========================================================

@st.cache_data
def veri_yukle():

    yol = "Tesisatlar.xlsx"

    if not os.path.exists(yol):
        return None

    try:

        df = pd.read_excel(
            yol,
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

# Haritada bulunan tesisatlar
if "demo_yuklenenler" not in st.session_state:
    st.session_state.demo_yuklenenler = []


# Aktif rota havuzu
if "demo_secilenler" not in st.session_state:
    st.session_state.demo_secilenler = []


# Kaydedilen rotalar
if "demo_kayitli_rotalar" not in st.session_state:
    st.session_state.demo_kayitli_rotalar = []


# Varsayılan rota adı
if "demo_rota_adi" not in st.session_state:
    st.session_state.demo_rota_adi = "Rota 1"


# =========================================================
# GİRİŞ EKRANI
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

            # -------------------------------------------------
            # ADMIN
            # -------------------------------------------------

            if kadi == "admin" and sifre == "admin":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "admin"

                st.rerun()


            # -------------------------------------------------
            # DEMO
            # -------------------------------------------------

            elif kadi == "demo" and sifre == "demo":

                st.session_state.giris_yapildi = True
                st.session_state.kullanici_rolu = "demo"

                st.session_state.demo_yuklenenler = []
                st.session_state.demo_secilenler = []
                st.session_state.demo_kayitli_rotalar = []
                st.session_state.demo_rota_adi = "Rota 1"

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


    # -------------------------------------------------------
    # ARAMA
    # -------------------------------------------------------

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


    # -------------------------------------------------------
    # MESAJ
    # -------------------------------------------------------

    if st.session_state.hata_mesaji:

        st.error(
            st.session_state.hata_mesaji
        )

    elif st.session_state.aktif_tesisat:

        st.success(
            f"Tesisat Bulundu: "
            f"{st.session_state.aktif_tesisat}"
        )


    # -------------------------------------------------------
    # ADMIN HARİTA
    # -------------------------------------------------------

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
            min-width:140px;
        ">

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
            "### 🗺️ Rota Planlama"
        )

    with col_cikis:

        if st.button("Çıkış Yap"):

            st.session_state.giris_yapildi = False
            st.session_state.kullanici_rolu = None

            st.session_state.demo_yuklenenler = []
            st.session_state.demo_secilenler = []
            st.session_state.demo_kayitli_rotalar = []

            st.rerun()


    # =====================================================
    # ANA 3 KOLON
    # =====================================================

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
            "100004\n"
            "100005",

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

                girilen_liste = []

                for satir in toplu_input.splitlines():

                    satir = satir.strip()

                    if satir:

                        girilen_liste.append(
                            satir
                        )


                yeni_sayisi = 0
                bulunamayanlar = []


                for t_no in girilen_liste:

                    # Zaten aktif alanda var mı?

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


                    # Daha önce kaydedilen rotalarda var mı?

                    kayitli_mi = False


                    for rota in (
                        st.session_state.demo_kayitli_rotalar
                    ):

                        if any(

                            x["Tesisat"] == t_no

                            for x in rota["tesisatlar"]

                        ):

                            kayitli_mi = True

                            break


                    if kayitli_mi:
                        continue


                    match = df[
                        df["Tesisat"] == t_no
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
    # ORTA PANEL - HARİTA
    # =====================================================

    with orta:

        st.markdown(
            "### 🗺️ Harita"
        )

        st.caption(
            "Yeşil noktaya tıklayarak rota havuzuna ekleyin."
        )


        # -------------------------------------------------
        # HARİTA MERKEZİ
        # -------------------------------------------------

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


        # -------------------------------------------------
        # HARİTA
        # -------------------------------------------------

        m_demo = folium.Map(

            location=harita_merkez,

            zoom_start=13,

            control_scale=True

        )


        # -------------------------------------------------
        # MARKERLAR
        # -------------------------------------------------

        for item in st.session_state.demo_yuklenenler:

            t_no = item["tesisat"]

            lat = item["lat"]

            lon = item["lon"]


            popup_html = f"""
            <div style="
                font-family:Arial;
                width:190px;
                text-align:center;
            ">

                <div style="
                    font-size:17px;
                    font-weight:bold;
                    margin-bottom:10px;
                ">

                    Tesisat

                </div>

                <div style="
                    font-size:18px;
                    font-weight:bold;
                    color:#166534;
                    margin-bottom:12px;
                ">

                    {t_no}

                </div>

                <div style="
                    font-size:11px;
                    color:#666;
                ">

                    Rota havuzuna eklemek için tıklayın.

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

                tooltip=str(t_no),

                icon=folium.Icon(
                    color="green",
                    icon="map-marker",
                    prefix="fa"
                )

            ).add_to(m_demo)


        # -------------------------------------------------
        # HARİTAYI GÖSTER
        # -------------------------------------------------

        map_data = st_folium(

            m_demo,

            use_container_width=True,

            height=650,

            returned_objects=[
                "last_object_clicked"
            ]

        )


        # -------------------------------------------------
        # HARİTA TIKLAMA
        # -------------------------------------------------

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

                            secilen_item = item


                    if (
                        secilen_item is not None
                        and
                        en_yakin < 0.00001
                    ):

                        tesisat = (
                            secilen_item["tesisat"]
                        )


                        # Haritadan çıkar

                        st.session_state.demo_yuklenenler = [

                            x

                            for x
                            in st.session_state.demo_yuklenenler

                            if x["tesisat"] != tesisat

                        ]


                        # Havuzda yoksa ekle

                        if not any(

                            x["tesisat"] == tesisat

                            for x
                            in st.session_state.demo_secilenler

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


        st.caption(

            f"Seçilen tesisat: "
            f"**{len(st.session_state.demo_secilenler)}**"

        )


        # -------------------------------------------------
        # HAVUZ
        # -------------------------------------------------

        with st.container(
            height=430,
            border=True
        ):

            if st.session_state.demo_secilenler:

                for idx, item in enumerate(
                    st.session_state.demo_secilenler
                ):

                    t_no = item["tesisat"]


                    if st.button(

                        f"{idx + 1}.  {t_no}",

                        key=f"havuz_{t_no}_{idx}",

                        use_container_width=True

                    ):

                        # Havuzdan çıkar

                        st.session_state.demo_secilenler.pop(
                            idx
                        )


                        # Haritaya geri gönder

                        if not any(

                            x["tesisat"] == t_no

                            for x
                            in st.session_state.demo_yuklenenler

                        ):

                            st.session_state.demo_yuklenenler.append(
                                item
                            )


                        st.rerun()


            else:

                st.info(
                    "Haritadan tesisat seçtiğinizde "
                    "burada görünecek."
                )


        st.caption(
            "💡 Tesisat numarasına tıklarsanız "
            "haritaya geri gönderilir."
        )


        # -------------------------------------------------
        # ROTAYI KAYDET
        # -------------------------------------------------

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


                        # Aktif havuzu temizle

                        st.session_state.demo_secilenler = []


                        # Sonraki rota adı

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


                        st.success(
                            f"✅ {rota_adi.strip()} kaydedildi."
                        )


                        st.rerun()


        # =================================================
        # KAYDEDİLEN ROTALAR
        # =================================================

        if st.session_state.demo_kayitli_rotalar:

            st.markdown("---")

            st.markdown(
                "##### 💾 Kaydedilen Rotalar"
            )


            # -------------------------------------------------
            # KAYDIRILABİLİR ROTA LİSTESİ
            # -------------------------------------------------

            with st.container(
                height=220,
                border=True
            ):

                for i, rota in enumerate(
                    st.session_state.demo_kayitli_rotalar
                ):

                    rota_adi_kayitli = (
                        rota["rota_adi"]
                    )

                    tesisat_sayisi = len(
                        rota["tesisatlar"]
                    )


                    st.write(
                        f"📁 **{rota_adi_kayitli}**"
                    )


                    st.caption(
                        f"{tesisat_sayisi} tesisat"
                    )


                    if i < len(
                        st.session_state.demo_kayitli_rotalar
                    ) - 1:

                        st.divider()


        # =================================================
        # TÜM ROTALARI EXCEL'E AKTAR
        # =================================================

        if st.session_state.demo_kayitli_rotalar:

            tum_kayitlar = []


            for rota in (
                st.session_state.demo_kayitli_rotalar
            ):

                for tesisat in rota["tesisatlar"]:

                    tum_kayitlar.append({

                        "Rota Adı":
                        rota["rota_adi"],

                        "Sıra":
                        tesisat["Sıra"],

                        "Tesisat":
                        tesisat["Tesisat"]

                    })


            # -------------------------------------------------
            # EXCEL OLUŞTUR
            # -------------------------------------------------

            if tum_kayitlar:

                final_df = pd.DataFrame(

                    tum_kayitlar,

                    columns=[
                        "Rota Adı",
                        "Sıra",
                        "Tesisat"
                    ]

                )


                output = BytesIO()


                try:

                    # SADECE OPENPYXL
                    with pd.ExcelWriter(

                        output,

                        engine="openpyxl"

                    ) as writer:

                        final_df.to_excel(

                            writer,

                            index=False,

                            sheet_name="Rotalar"

                        )


                    excel_data = output.getvalue()


                    st.markdown("---")


                    st.download_button(

                        label="📊 TÜM ROTALARI EXCELE AKTAR",

                        data=excel_data,

                        file_name="Tum_Rotalar.xlsx",

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
