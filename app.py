
import streamlit as st
import requests

st.set_page_config(page_title="ValueBet Analyse", layout="centered")

st.title("⚽ ValueBet Analyse mit API-Football")
st.markdown("Automatisierte Quotenbewertung mit Expected Goals (xG) und Value-Wetten.")

API_KEY = "0e87632ed2b24209d19c5472559e2436"
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}

@st.cache_data
def get_leagues():
    url = f"{BASE_URL}/leagues"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()["response"]
        leagues = [
            {
                "name": f"{l['league']['name']} ({l['country']['name']})",
                "id": l['league']['id'],
                "season": l['seasons'][-1]['year']
            }
            for l in data if l['seasons'][-1]['year'] >= 2023 and l['league']['type'] == 'League'
        ]
        return leagues
    else:
        st.error("Fehler beim Abrufen der Ligen.")
        return []

leagues = get_leagues()

selected = st.selectbox("🔎 Wähle eine Liga", leagues, format_func=lambda x: x["name"])

@st.cache_data
def get_fixtures(league_id, season):
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()["response"]
    return []

fixtures = get_fixtures(selected['id'], selected['season'])

match = st.selectbox("📆 Spiel auswählen", fixtures, format_func=lambda m: f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}")

if match:
    home = match['teams']['home']['name']
    away = match['teams']['away']['name']
    st.subheader(f"🔍 {home} vs {away}")

    st.markdown("### 🔢 Buchmacher-Quoten eingeben")
    q_home = st.number_input("Quote Heimsieg", min_value=1.01, step=0.01)
    q_draw = st.number_input("Quote Unentschieden", min_value=1.01, step=0.01)
    q_away = st.number_input("Quote Auswärtssieg", min_value=1.01, step=0.01)

    if st.button("🎯 Value-Bet analysieren"):
        prob_home = 1 / q_home
        prob_draw = 1 / q_draw
        prob_away = 1 / q_away
        total = prob_home + prob_draw + prob_away

        prob_home /= total
        prob_draw /= total
        prob_away /= total

        fair_q_home = 1 / prob_home
        fair_q_draw = 1 / prob_draw
        fair_q_away = 1 / prob_away

        st.markdown("### 📊 Ergebnis:")
        st.write(f"Faire Quote Heimsieg: **{fair_q_home:.2f}**")
        st.write(f"Faire Quote Unentschieden: **{fair_q_draw:.2f}**")
        st.write(f"Faire Quote Auswärtssieg: **{fair_q_away:.2f}**")

        def check_value_bet(real_q, fair_q):
            if real_q > fair_q:
                return f"✅ Value Bet ({real_q:.2f} > {fair_q:.2f})"
            else:
                return f"❌ Kein Value ({real_q:.2f} ≤ {fair_q:.2f})"

        st.markdown("### ✅ Value-Bet Bewertung:")
        st.write(f"Heimsieg: {check_value_bet(q_home, fair_q_home)}")
        st.write(f"Unentschieden: {check_value_bet(q_draw, fair_q_draw)}")
        st.write(f"Auswärtssieg: {check_value_bet(q_away, fair_q_away)}")
