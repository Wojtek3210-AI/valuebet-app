ModuleNotFoundError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/valuebet-app/app.py", line 5, in <module>
    from sklearn.ensemble import RandomForestClassifier
import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

st.set_page_config(page_title="⚽ Fußball Value Bet KI", layout="wide")
st.title("⚽ Fußball-Wettprognose & Value Bets mit KI")

# Beispiel-Liga-Auswahl mit API-Football Ligen IDs
auth_headers = {
    "X-RapidAPI-Key": "0e87632ed2b24209d19c5472559e2436",
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

leagues = {
    "Premier League (ENG)": 39,
    "Bundesliga (GER)": 78,
    "La Liga (ESP)": 140,
    "Serie A (ITA)": 135,
    "Ekstraklasa (POL)": 106,
    "Champions League (CL)": 2
}

liga = st.selectbox("🔎 Wähle eine Liga", list(leagues.keys()))
liga_id = leagues[liga]

st.markdown("---")
st.subheader(f"📆 Anstehende Spiele: {liga}")

# Abruf der Spiele über API-Football
params = {"league": liga_id, "season": 2024, "next": 10}
try:
    response = requests.get("https://api-football-v1.p.rapidapi.com/v3/fixtures", headers=auth_headers, params=params)
    data = response.json()
    spiele = [s for s in data.get("response", []) if s.get("league", {}).get("id") == liga_id]

    if not spiele:
        st.warning("⚠️ Für diese Liga wurden keine gültigen Spiele gefunden (evtl. liegt es an der API-Saisonangabe).")
    else:
        for s in spiele:
            try:
                home = s['teams']['home']['name']
                away = s['teams']['away']['name']
                datum = s['fixture']['date'][:10]
                st.write(f"{home} vs {away} ({datum})")
            except Exception as e:
                st.error(f"⚠️ Fehler beim Parsen eines Spiels: {e}")
except Exception as e:
    st.error(f"Fehler beim Laden der Spieldaten: {e}")

st.markdown("---")
st.subheader("📊 Historische CSV-Daten laden (zur Modell-Trainierung)")

liga_urls = {
    "Premier League (ENG)": "https://www.football-data.co.uk/mmz4281/2223/E0.csv",
    "Bundesliga (GER)": "https://www.football-data.co.uk/mmz4281/2223/D1.csv",
    "La Liga (ESP)": "https://www.football-data.co.uk/mmz4281/2223/SP1.csv",
    "Serie A (ITA)": "https://www.football-data.co.uk/mmz4281/2223/I1.csv",
    "Ekstraklasa (POL)": "https://www.football-data.co.uk/mmz4281/2223/PL.csv",
    "Champions League (CL)": "https://www.football-data.co.uk/mmz4281/2223/E1.csv"
}

csv_url = liga_urls[liga]

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df = df[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']].dropna()
    df['GoalDiff'] = df['FTHG'] - df['FTAG']
    return df

df = load_data(csv_url)
st.dataframe(df.head())

# Daten vorbereiten
X = df[['FTHG', 'FTAG', 'GoalDiff']]
y = df['FTR']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Modell trainieren
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Neue Prognosen eingeben
st.markdown("---")
st.subheader("🔮 Neue Spiel-Prognose eingeben")
col1, col2, col3 = st.columns(3)

with col1:
    fthg = st.number_input("⛳ Erwartete Tore Heimteam", value=1)
with col2:
    ftag = st.number_input("🎯 Erwartete Tore Auswärtsteam", value=1)
with col3:
    quote_home = st.number_input("💰 Quote Heim", value=2.0)
    quote_draw = st.number_input("💰 Quote Unentschieden", value=3.2)
    quote_away = st.number_input("💰 Quote Auswärts", value=3.5)

if st.button("🔎 Prognose & Value-Berechnung"):
    goaldiff = fthg - ftag
    input_data = pd.DataFrame([[fthg, ftag, goaldiff]], columns=['FTHG', 'FTAG', 'GoalDiff'])
    probs = model.predict_proba(input_data)[0]
    class_map = model.classes_

    # Wahrscheinlichkeiten + Value
    results = []
    for i, result in enumerate(class_map):
        quote = quote_home if result == 'H' else quote_draw if result == 'D' else quote_away
        value = (probs[i] * quote) - 1
        results.append({"Ergebnis": result, "Wahrscheinlichkeit": round(probs[i]*100, 2), "Quote": quote, "Value": round(value, 2)})

    result_df = pd.DataFrame(results)
    st.dataframe(result_df.sort_values(by="Value", ascending=False))

    st.success("✅ Berechnung abgeschlossen. Value Bets oben gelistet.")
