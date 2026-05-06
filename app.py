
import os
import base64
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


st.set_page_config(
    page_title="INEVOKE — Dashboard Énergie Renouvelable",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BLUE = "#2196F3"
ORANGE = "#F9A825"
NAVY = "#0D47A1"
LIGHT = "#E3F2FD"
GREEN = "#2E7D32"
RED = "#C62828"
DARK = "#1A1A2E"

PALETTE = [BLUE, ORANGE, "#26C6DA", "#66BB6A", "#AB47BC", "#EF5350", "#26A69A", "#FFA726"]
KOBO_FORM_LINK = "https://ee.kobotoolbox.org/x/uvI57z6J"

try:
    KOBO_API_URL = st.secrets.get("KOBO_API_URL", "https://kf.kobotoolbox.org")
    KOBO_ASSET_UID = st.secrets.get("KOBO_ASSET_UID", "uvI57z6J")
    KOBO_API_TOKEN = st.secrets.get("KOBO_API_TOKEN", "")
except Exception:
    KOBO_API_URL = "https://kf.kobotoolbox.org"
    KOBO_ASSET_UID = "uvI57z6J"
    KOBO_API_TOKEN = ""


st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] {{font-family:'Barlow',sans-serif;}}

.main-header {{
    background:linear-gradient(135deg,{NAVY} 0%,{BLUE} 100%);
    padding:22px 28px;border-radius:18px;margin-bottom:1.4rem;
    display:flex;align-items:center;gap:20px;
    box-shadow:0 8px 28px rgba(33,150,243,.25);
}}
.main-header h1 {{color:white;font-size:28px;font-weight:800;margin:0;}}
.main-header p {{color:rgba(255,255,255,.88);font-size:14px;margin:5px 0 0;}}

.kpi-card {{
    background:white;border-radius:15px;padding:18px 16px;
    border-top:5px solid {BLUE};box-shadow:0 3px 15px rgba(0,0,0,.08);
    text-align:center;min-height:112px;
}}
.kpi-card.orange {{border-top-color:{ORANGE};}}
.kpi-card.green {{border-top-color:{GREEN};}}
.kpi-card.red {{border-top-color:{RED};}}
.kpi-card.navy {{border-top-color:{NAVY};}}

.kpi-label {{
    font-size:11px;color:#666;text-transform:uppercase;
    letter-spacing:.08em;font-weight:700;
}}
.kpi-value {{font-size:27px;color:{NAVY};font-weight:800;margin-top:8px;}}

.section-title {{
    font-size:17px;font-weight:800;color:{NAVY};
    border-left:5px solid {ORANGE};padding-left:12px;margin:1.1rem 0 .8rem;
}}
.alert-box {{
    background:{LIGHT};border-left:5px solid {BLUE};border-radius:12px;
    padding:14px 18px;color:{NAVY};font-size:14px;margin-bottom:1rem;
}}
.empty-box {{
    background:white;border:2px dashed {BLUE};border-radius:16px;
    padding:30px;color:{NAVY};text-align:center;margin-top:1rem;
}}
section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,{NAVY} 0%,#1565C0 100%);
}}
section[data-testid="stSidebar"] * {{color:white !important;}}
.stDownloadButton>button {{
    background:{ORANGE};color:{DARK};border:none;border-radius:8px;font-weight:800;
}}
.stButton>button {{
    background:{BLUE};color:white;border:none;border-radius:8px;font-weight:800;
}}
</style>
""",
    unsafe_allow_html=True,
)


def image_to_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def empty_dataframe():
    cols = [
        "id_contrat", "client", "type_site", "type_intervention",
        "date_visite", "date_debut", "responsable_technique",
        "disponibilite_materiel", "materiel_a_louer",
        "temps_moyen_jours", "statut_intervention",
        "revenu_genere", "modalite_paiement",
        "satisfaction_client", "commercial",
        "observations", "ville", "latitude", "longitude",
        "date_soumission",
    ]
    return pd.DataFrame(columns=cols)


def normalize_yes_no(value):
    value = str(value).strip().lower()
    if value in ["oui", "yes", "true", "1", "disponible", "ok"]:
        return "Oui"
    if value in ["non", "no", "false", "0", "indisponible"]:
        return "Non"
    if value in ["nan", "none", ""]:
        return "Non renseigné"
    return str(value).strip()


def normalize_columns(df):
    if df is None or len(df) == 0:
        return empty_dataframe()

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    mapping = {
        "ID du contrat / Intervention": "id_contrat",
        "id_contrat": "id_contrat",
        "Client": "client",
        "client": "client",
        "Type de site": "type_site",
        "type_site": "type_site",
        "Type d’intervention": "type_intervention",
        "Type d'intervention": "type_intervention",
        "type_intervention": "type_intervention",
        "Date de visite de chantier": "date_visite",
        "date_visite": "date_visite",
        "Date de début de chantier": "date_debut",
        "Date de debut de chantier": "date_debut",
        "date_debut": "date_debut",
        "Responsable technique en charge du chantier": "responsable_technique",
        "responsable_technique": "responsable_technique",
        "Disponibilité du matériel": "disponibilite_materiel",
        "Disponibilite du materiel": "disponibilite_materiel",
        "disponibilite_materiel": "disponibilite_materiel",
        "Matériel à louer": "materiel_a_louer",
        "Materiel a louer": "materiel_a_louer",
        "materiel_a_louer": "materiel_a_louer",
        "Temps moyen (jours)": "temps_moyen_jours",
        "temps_moyen_jours": "temps_moyen_jours",
        "Statut intervention": "statut_intervention",
        "statut_intervention": "statut_intervention",
        "Revenu généré (FCFA)": "revenu_genere",
        "Revenu genere (FCFA)": "revenu_genere",
        "revenu_genere": "revenu_genere",
        "Modalité de paiement": "modalite_paiement",
        "Modalite de paiement": "modalite_paiement",
        "modalite_paiement": "modalite_paiement",
        "Satisfaction client": "satisfaction_client",
        "satisfaction_client": "satisfaction_client",
        "Commercial en charge": "commercial",
        "commercial": "commercial",
        "Observations": "observations",
        "observations": "observations",
        "Ville": "ville",
        "ville": "ville",
        "_submission_time": "date_soumission",
        "_geolocation": "geolocation",
    }

    df = df.rename(columns={c: mapping.get(c, c) for c in df.columns})

    for col in empty_dataframe().columns:
        if col not in df.columns:
            df[col] = np.nan

    if "geolocation" in df.columns:
        def get_lat(x):
            if isinstance(x, list) and len(x) >= 2:
                return x[0]
            return np.nan

        def get_lon(x):
            if isinstance(x, list) and len(x) >= 2:
                return x[1]
            return np.nan

        df["latitude"] = df["geolocation"].apply(get_lat)
        df["longitude"] = df["geolocation"].apply(get_lon)

    for col in ["date_visite", "date_debut", "date_soumission"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["revenu_genere"] = pd.to_numeric(df["revenu_genere"], errors="coerce").fillna(0)
    df["temps_moyen_jours"] = pd.to_numeric(df["temps_moyen_jours"], errors="coerce").fillna(0)

    text_cols = [
        "id_contrat", "client", "type_site", "type_intervention",
        "responsable_technique", "materiel_a_louer", "statut_intervention",
        "modalite_paiement", "satisfaction_client", "commercial",
        "observations", "ville",
    ]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["disponibilite_materiel"] = df["disponibilite_materiel"].apply(normalize_yes_no)
    df["annee"] = df["date_debut"].dt.year
    df["mois"] = df["date_debut"].dt.month
    df["mois_label"] = df["date_debut"].dt.strftime("%Y-%m")
    df["delai_visite_debut"] = (df["date_debut"] - df["date_visite"]).dt.days

    return df


@st.cache_data(ttl=60, show_spinner=False)
def fetch_kobo_data(api_url, asset_uid, token):
    if not asset_uid or not token:
        return empty_dataframe()

    url = f"{api_url.rstrip('/')}/api/v2/assets/{asset_uid}/data.json"
    headers = {"Authorization": f"Token {token}"}

    rows = []
    next_url = url

    try:
        while next_url:
            response = requests.get(next_url, headers=headers, timeout=35)
            response.raise_for_status()
            payload = response.json()
            rows.extend(payload.get("results", []))
            next_url = payload.get("next")
            if next_url and next_url.startswith("/"):
                next_url = api_url.rstrip("/") + next_url

        return normalize_columns(pd.DataFrame(rows))

    except Exception as e:
        st.error(f"Erreur de connexion à Kobo : {e}")
        return empty_dataframe()


def format_fcfa(value):
    try:
        value = float(value)
    except Exception:
        value = 0
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.1f} M"
    return f"{value:,.0f}"


def kpi_card(label, value, color_class="blue"):
    st.markdown(
        f"""
        <div class="kpi-card {color_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def value_counts_df(df, col, count_name="Nombre"):
    if len(df) == 0 or col not in df.columns:
        return pd.DataFrame({col: [], count_name: []})
    temp = df[col].replace("", "Non renseigné").value_counts().reset_index()
    temp.columns = [col, count_name]
    return temp


with st.sidebar:
    st.markdown("### 🔄 Actualisation automatique")
    refresh_seconds = st.selectbox(
        "Fréquence",
        [30, 60, 120, 300],
        index=1,
        format_func=lambda x: f"Toutes les {x} secondes",
    )

if st_autorefresh is not None:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh_energie")


logo_b64 = image_to_base64("assets/logo_inevoke.jpeg")
logo_html = (
    f'<img src="data:image/jpeg;base64,{logo_b64}" style="height:72px;background:white;border-radius:12px;padding:6px;">'
    if logo_b64 else "☀️"
)

st.markdown(
    f"""
<div class="main-header">
    <div>{logo_html}</div>
    <div>
        <h1>Dashboard Marché — Énergie Renouvelable</h1>
        <p>INEVOKE SARL · Suivi des interventions, revenus, statuts chantier, matériel et satisfaction client</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔗 Formulaire Kobo")
    st.markdown(f"[Ouvrir le formulaire]({KOBO_FORM_LINK})")
    st.caption("Le dashboard lit les données via API Kobo.")
    if st.button("Forcer l’actualisation maintenant"):
        st.cache_data.clear()
        st.rerun()

df_all = fetch_kobo_data(KOBO_API_URL, KOBO_ASSET_UID, KOBO_API_TOKEN)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔍 Filtres")

    df = df_all.copy()

    if len(df_all) > 0 and df_all["date_debut"].notna().any():
        date_min = df_all["date_debut"].min().date()
        date_max = df_all["date_debut"].max().date()
        date_range = st.date_input("Période chantier", value=(date_min, date_max), min_value=date_min, max_value=date_max)

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df["date_debut"].dt.date >= start_date) & (df["date_debut"].dt.date <= end_date)]
    else:
        st.caption("Aucune date chantier disponible.")

    statuts = ["Tous"] + sorted([x for x in df_all["statut_intervention"].dropna().unique().tolist() if x])
    statut_sel = st.selectbox("Statut intervention", statuts)
    if statut_sel != "Tous":
        df = df[df["statut_intervention"] == statut_sel]

    sites = ["Tous"] + sorted([x for x in df_all["type_site"].dropna().unique().tolist() if x])
    site_sel = st.selectbox("Type de site", sites)
    if site_sel != "Tous":
        df = df[df["type_site"] == site_sel]

    interventions = ["Toutes"] + sorted([x for x in df_all["type_intervention"].dropna().unique().tolist() if x])
    intervention_sel = st.selectbox("Type d’intervention", interventions)
    if intervention_sel != "Toutes":
        df = df[df["type_intervention"] == intervention_sel]

    commerciaux = ["Tous"] + sorted([x for x in df_all["commercial"].dropna().unique().tolist() if x])
    commercial_sel = st.selectbox("Commercial", commerciaux)
    if commercial_sel != "Tous":
        df = df[df["commercial"] == commercial_sel]

    techs = ["Tous"] + sorted([x for x in df_all["responsable_technique"].dropna().unique().tolist() if x])
    tech_sel = st.selectbox("Responsable technique", techs)
    if tech_sel != "Tous":
        df = df[df["responsable_technique"] == tech_sel]


if len(df) == 0:
    nb_interventions = nb_clients = chantiers_termines = chantiers_en_cours = 0
    revenu_total = revenu_moyen = temps_moyen = materiel_dispo_pct = 0
else:
    statut_lower = df["statut_intervention"].str.lower()
    nb_interventions = len(df)
    nb_clients = df["client"].replace("", np.nan).nunique()
    revenu_total = df["revenu_genere"].sum()
    revenu_moyen = df["revenu_genere"].mean()
    temps_moyen = df["temps_moyen_jours"].mean()
    materiel_dispo_pct = (df["disponibilite_materiel"].str.lower() == "oui").mean() * 100
    chantiers_termines = statut_lower.str.contains("termin|fini|sign|clôt|clot|achev", regex=True, na=False).sum()
    chantiers_en_cours = statut_lower.str.contains("cours|execution|exécution|chantier", regex=True, na=False).sum()

st.markdown(
    f"""
<div class="alert-box">
    <b>Mode automatique Kobo :</b> actualisation toutes les {refresh_seconds} secondes.
    <br><b>Dernière actualisation :</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    <br><b>Soumissions reçues :</b> {len(df_all)}
</div>
""",
    unsafe_allow_html=True,
)

if not KOBO_API_TOKEN:
    st.warning("Connexion Kobo non configurée. Ajoute KOBO_ASSET_UID et KOBO_API_TOKEN dans .streamlit/secrets.toml ou dans les Secrets Streamlit Cloud.")

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi_card("Interventions", nb_interventions, "blue")
with c2: kpi_card("Clients uniques", nb_clients, "navy")
with c3: kpi_card("Revenu total", f"{format_fcfa(revenu_total)} FCFA", "green")
with c4: kpi_card("Revenu moyen", f"{format_fcfa(revenu_moyen)} FCFA", "orange")
with c5: kpi_card("Temps moyen", f"{temps_moyen:.1f} j", "blue")
with c6: kpi_card("Matériel dispo", f"{materiel_dispo_pct:.1f}%", "green")

st.markdown("<br>", unsafe_allow_html=True)

c7, c8, c9, c10 = st.columns(4)
with c7: kpi_card("Chantiers terminés", chantiers_termines, "green")
with c8: kpi_card("Chantiers en cours", chantiers_en_cours, "orange")
with c9: kpi_card("Sites suivis", df["type_site"].replace("", np.nan).nunique() if len(df) else 0, "navy")
with c10: kpi_card("Villes", df["ville"].replace("", np.nan).nunique() if len(df) else 0, "blue")

if len(df) == 0:
    st.markdown(
        """
<div class="empty-box">
    <h3>Aucune donnée énergie renouvelable pour le moment</h3>
    <p>Le dashboard est initialisé à zéro. Dès que le formulaire Kobo est soumis et que l’API est configurée,
    les indicateurs, graphiques et tableaux se mettront à jour automatiquement.</p>
</div>
""",
        unsafe_allow_html=True,
    )


tabs = st.tabs([
    "Vue d’ensemble",
    "Interventions",
    "Revenus & paiements",
    "Équipe & performance",
    "Carte Côte d’Ivoire",
    "Données",
])


with tabs[0]:
    st.markdown("<div class='section-title'>Vue d’ensemble du marché énergie renouvelable</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.35, 1])

    with col1:
        if len(df) > 0 and df["mois_label"].notna().any():
            evo = df.dropna(subset=["date_debut"]).groupby("mois_label").agg(
                interventions=("id_contrat", "count"),
                revenu=("revenu_genere", "sum"),
            ).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(x=evo["mois_label"], y=evo["interventions"], name="Interventions", marker_color=BLUE))
            fig.add_trace(go.Scatter(
                x=evo["mois_label"], y=evo["revenu"] / 1_000_000,
                name="Revenu (M FCFA)", mode="lines+markers",
                line=dict(color=ORANGE, width=3), yaxis="y2",
            ))
            fig.update_layout(
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h"),
                yaxis=dict(title="Nombre d’interventions"),
                yaxis2=dict(title="M FCFA", overlaying="y", side="right", showgrid=False),
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune évolution à afficher pour le moment.")

    with col2:
        if len(df) > 0:
            stat = value_counts_df(df, "statut_intervention", "Nombre")
            fig = px.pie(stat, values="Nombre", names="statut_intervention", hole=.45, color_discrete_sequence=PALETTE)
            fig.update_layout(height=380, paper_bgcolor="white", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun statut à afficher.")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='section-title'>Répartition par type de site</div>", unsafe_allow_html=True)
        if len(df) > 0:
            site_df = value_counts_df(df, "type_site", "Interventions")
            fig = px.bar(site_df, x="Interventions", y="type_site", orientation="h", color_discrete_sequence=[BLUE], text="Interventions")
            fig.update_layout(height=330, plot_bgcolor="white", paper_bgcolor="white", yaxis_title="", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun site à afficher.")

    with col4:
        st.markdown("<div class='section-title'>Types d’intervention</div>", unsafe_allow_html=True)
        if len(df) > 0:
            inter_df = value_counts_df(df, "type_intervention", "Interventions")
            fig = px.bar(inter_df, x="Interventions", y="type_intervention", orientation="h", color_discrete_sequence=[ORANGE], text="Interventions")
            fig.update_layout(height=330, plot_bgcolor="white", paper_bgcolor="white", yaxis_title="", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune intervention à afficher.")


with tabs[1]:
    st.markdown("<div class='section-title'>Analyse opérationnelle des interventions</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Disponibilité du matériel</div>", unsafe_allow_html=True)
        if len(df) > 0:
            dispo = value_counts_df(df, "disponibilite_materiel", "Nombre")
            fig = px.pie(dispo, values="Nombre", names="disponibilite_materiel", hole=.5, color_discrete_sequence=[GREEN, RED, ORANGE])
            fig.update_layout(height=330, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée matériel.")

    with col2:
        st.markdown("<div class='section-title'>Temps moyen par type d’intervention</div>", unsafe_allow_html=True)
        if len(df) > 0:
            temps = df.groupby("type_intervention").agg(temps_moyen=("temps_moyen_jours", "mean"), nb=("id_contrat", "count")).reset_index()
            fig = px.bar(temps, x="type_intervention", y="temps_moyen", color_discrete_sequence=[BLUE], text=temps["temps_moyen"].round(1))
            fig.update_layout(height=330, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Jours")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun temps moyen.")

    st.markdown("<div class='section-title'>Matériel à louer — priorités opérationnelles</div>", unsafe_allow_html=True)
    if len(df) > 0:
        mat = df["materiel_a_louer"].replace("", "Non renseigné").value_counts().reset_index()
        mat.columns = ["Matériel à louer", "Nombre"]
        st.dataframe(mat, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun matériel à louer enregistré.")


with tabs[2]:
    st.markdown("<div class='section-title'>Revenus & modalités de paiement</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if len(df) > 0:
            rev_site = df.groupby("type_site").agg(revenu=("revenu_genere", "sum"), interventions=("id_contrat", "count")).reset_index().sort_values("revenu")
            fig = px.bar(
                rev_site, x="revenu", y="type_site", orientation="h",
                color_discrete_sequence=[GREEN],
                text=rev_site["revenu"].apply(lambda x: f"{x/1e6:.1f}M"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="FCFA", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun revenu par site.")

    with col2:
        if len(df) > 0:
            paiement = value_counts_df(df, "modalite_paiement", "Nombre")
            fig = px.pie(paiement, values="Nombre", names="modalite_paiement", hole=.45, color_discrete_sequence=PALETTE)
            fig.update_layout(height=370, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune modalité de paiement.")

    st.markdown("<div class='section-title'>Revenu par type d’intervention</div>", unsafe_allow_html=True)
    if len(df) > 0:
        rev_inter = df.groupby("type_intervention").agg(
            revenu=("revenu_genere", "sum"),
            revenu_moyen=("revenu_genere", "mean"),
            interventions=("id_contrat", "count"),
        ).reset_index().sort_values("revenu", ascending=False)
        st.dataframe(rev_inter, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun revenu à afficher.")


with tabs[3]:
    st.markdown("<div class='section-title'>Performance équipes techniques & commerciales</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Responsables techniques</div>", unsafe_allow_html=True)
        if len(df) > 0:
            tech = df.groupby("responsable_technique").agg(
                interventions=("id_contrat", "count"),
                revenu=("revenu_genere", "sum"),
                temps_moyen=("temps_moyen_jours", "mean"),
            ).reset_index().sort_values("interventions", ascending=False)
            st.dataframe(tech, use_container_width=True, hide_index=True)
            fig = px.bar(tech, x="responsable_technique", y="interventions", color_discrete_sequence=[BLUE], text="interventions")
            fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Interventions")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune performance technique.")

    with col2:
        st.markdown("<div class='section-title'>Commerciaux</div>", unsafe_allow_html=True)
        if len(df) > 0:
            com = df.groupby("commercial").agg(
                interventions=("id_contrat", "count"),
                revenu=("revenu_genere", "sum"),
                revenu_moyen=("revenu_genere", "mean"),
            ).reset_index().sort_values("revenu", ascending=False)
            st.dataframe(com, use_container_width=True, hide_index=True)
            fig = px.bar(com, x="commercial", y="revenu", color_discrete_sequence=[ORANGE], text=com["revenu"].apply(lambda x: f"{x/1e6:.1f}M"))
            fig.update_traces(textposition="outside")
            fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="FCFA")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune performance commerciale.")

    st.markdown("<div class='section-title'>Satisfaction client</div>", unsafe_allow_html=True)
    if len(df) > 0:
        sat = value_counts_df(df, "satisfaction_client", "Nombre")
        fig = px.bar(sat, x="satisfaction_client", y="Nombre", color_discrete_sequence=[GREEN], text="Nombre")
        fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Nombre")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune satisfaction client enregistrée.")


with tabs[4]:
    st.markdown("<div class='section-title'>Carte Côte d’Ivoire — marché énergie renouvelable</div>", unsafe_allow_html=True)
    st.caption("La carte utilise d’abord les coordonnées Kobo si disponibles, sinon les villes reconnues.")

    coords = pd.DataFrame([
        {"ville": "Abidjan", "lat": 5.3599517, "lon": -4.0082563},
        {"ville": "Bouaké", "lat": 7.6906, "lon": -5.0391},
        {"ville": "Yamoussoukro", "lat": 6.8276, "lon": -5.2893},
        {"ville": "San-Pédro", "lat": 4.7485, "lon": -6.6363},
        {"ville": "Daloa", "lat": 6.8774, "lon": -6.4502},
        {"ville": "Korhogo", "lat": 9.4578, "lon": -5.6296},
        {"ville": "Divo", "lat": 5.8390, "lon": -5.3570},
        {"ville": "Gagnoa", "lat": 6.1319, "lon": -5.9506},
        {"ville": "Man", "lat": 7.4125, "lon": -7.5538},
        {"ville": "Abengourou", "lat": 6.7297, "lon": -3.4964},
        {"ville": "Bondoukou", "lat": 8.0402, "lon": -2.8000},
        {"ville": "Odienné", "lat": 9.5104, "lon": -7.5692},
        {"ville": "Séguéla", "lat": 7.9611, "lon": -6.6731},
    ])

    if len(df) > 0:
        geo_df = df.copy()
        geo_df["latitude"] = pd.to_numeric(geo_df["latitude"], errors="coerce")
        geo_df["longitude"] = pd.to_numeric(geo_df["longitude"], errors="coerce")
        geo_df = geo_df.dropna(subset=["latitude", "longitude"])

        fig = None

        if len(geo_df) > 0:
            map_df = geo_df.rename(columns={"latitude": "lat", "longitude": "lon"})
            fig = px.scatter_mapbox(
                map_df, lat="lat", lon="lon", size="revenu_genere",
                color="statut_intervention", hover_name="client",
                hover_data=["type_site", "type_intervention", "revenu_genere", "commercial"],
                zoom=5.8, height=620, color_discrete_sequence=PALETTE, size_max=42,
            )
        else:
            ville_df = df.groupby("ville").agg(interventions=("id_contrat", "count"), revenu=("revenu_genere", "sum")).reset_index()
            ville_df["ville_clean"] = ville_df["ville"].str.strip().str.lower()
            coords["ville_clean"] = coords["ville"].str.strip().str.lower()
            map_df = ville_df.merge(coords[["ville_clean", "lat", "lon"]], on="ville_clean", how="left").dropna(subset=["lat", "lon"])

            if len(map_df) > 0:
                fig = px.scatter_mapbox(
                    map_df, lat="lat", lon="lon", size="interventions", color="revenu",
                    hover_name="ville",
                    hover_data={"interventions": True, "revenu": ":,.0f", "lat": False, "lon": False},
                    zoom=5.7, height=620,
                    color_continuous_scale=[[0, LIGHT], [.5, ORANGE], [1, BLUE]],
                    size_max=46,
                )

        if fig is not None:
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox_center={"lat": 7.54, "lon": -5.55},
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune ville ou coordonnée reconnue pour afficher la carte.")
    else:
        st.info("La carte sera affichée dès qu’il y aura des données.")

    st.markdown("<div class='section-title'>Résumé géographique</div>", unsafe_allow_html=True)
    if len(df) > 0:
        geo_table = df.groupby("ville").agg(
            interventions=("id_contrat", "count"),
            revenu=("revenu_genere", "sum"),
            temps_moyen=("temps_moyen_jours", "mean"),
        ).reset_index().sort_values("revenu", ascending=False)
        st.dataframe(geo_table, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun résumé géographique.")


with tabs[5]:
    st.markdown("<div class='section-title'>Base des interventions énergie renouvelable</div>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Télécharger les données filtrées en CSV",
        data=csv,
        file_name="donnees_marche_energie_renouvelable_inevoke.csv",
        mime="text/csv",
    )


st.markdown("---")
st.caption("INEVOKE SARL — Dashboard Marché Énergie Renouvelable ")
