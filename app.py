import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from scipy.stats import poisson
import io

# Streamlit app title
st.title("Football Match Betting Predictions")

# User inputs via Streamlit form
with st.form("match_form"):
    team_a = st.text_input("Enter Team A", value="Arsenal")
    team_b = st.text_input("Enter Team B", value="Chelsea")
    match_date = st.date_input("Enter match date")
    submit_button = st.form_submit_button("Generate Predictions")

# Placeholder match data
match_data = {
    "match": f"{team_a} vs. {team_b}",
    "date": match_date.strftime("%Y-%m-%d") if match_date else "N/A",
    "team_a_avg_goals_home": 2.0,
    "team_a_avg_conceded_home": 1.0,
    "team_b_avg_goals_away": 1.5,
    "team_b_avg_conceded_away": 1.2,
    "team_a_avg_goals_ht_home": 0.9,
    "team_a_avg_conceded_ht_home": 0.4,
    "team_b_avg_goals_ht_away": 0.6,
    "team_b_avg_conceded_ht_away": 0.5,
    "team_a_avg_goals_2h_home": 1.1,
    "team_a_avg_conceded_2h_home": 0.6,
    "team_b_avg_goals_2h_away": 0.9,
    "team_b_avg_conceded_2h_away": 0.7,
    "odds_over_2_5": 2.30,
    "odds_under_2_5": 1.70,
    "odds_over_1_5_ht": 2.10,
    "odds_under_1_5_ht": 1.80,
    "odds_over_1_5_2h": 1.95,
    "odds_under_1_5_2h": 1.85,
    "injury_adjustment_team_a": 0.9,
    "injury_adjustment_team_b": 0.95
}

# Calculate expected goals (xG) - Fixed syntax error
def calculate_xg(team_avg_goals, opp_avg_conceded, adjustment=1.0):
    return (team_avg_goals + opp_avg_conceded) / 2 * adjustment

# Predict probabilities using Poisson distribution
def predict_probabilities(team1_xg, team2_xg, threshold):
    total_xg = team1_xg + team2_xg
    over_prob = 1 - poisson.cdf(threshold - 0.5, total_xg)
    under_prob = poisson.cdf(threshold + 0.5, total_xg)
    return over_prob, under_prob

# Calculate value bet
def calculate_value(pred_prob, odds):
    return (pred_prob * odds) - 1

# Function to generate PDF
def generate_pdf(team_a, team_b, table_data):
    buffer = io.BytesIO()
    pdf_file = f"{team_a}_vs_{team_b}_Betting_Predictions.pdf"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    doc.build([table])
    buffer.seek(0)
    return buffer, pdf_file

# Process predictions when form is submitted
if submit_button:
    # Input validation
    if not team_a or not team_b:
        st.error("Please enter valid team names.")
    else:
        # Calculate xG for full match, first half, and second half
        team_a_xg = calculate_xg(
            match_data["team_a_avg_goals_home"],
            match_data["team_b_avg_conceded_away"],
            match_data["injury_adjustment_team_a"]
        )
        team_b_xg = calculate_xg(
            match_data["team_b_avg_goals_away"],
            match_data["team_a_avg_conceded_home"],
            match_data["injury_adjustment_team_b"]
        )
        team_a_xg_ht = calculate_xg(
            match_data["team_a_avg_goals_ht_home"],
            match_data["team_b_avg_conceded_ht_away"],
            match_data["injury_adjustment_team_a"]
        )
        team_b_xg_ht = calculate_xg(
            match_data["team_b_avg_goals_ht_away"],
            match_data["team_a_avg_conceded_ht_home"],
            match_data["injury_adjustment_team_b"]
        )
        team_a_xg_2h = calculate_xg(
            match_data["team_a_avg_goals_2h_home"],
            match_data["team_b_avg_conceded_2h_away"],
            match_data["injury_adjustment_team_a"]
        )
        team_b_xg_2h = calculate_xg(
            match_data["team_b_avg_goals_2h_away"],
            match_data["team_a_avg_conceded_2h_home"],
            match_data["injury_adjustment_team_b"]
        )

        # Calculate probabilities and values
        over_2_5_prob, under_2_5_prob = predict_probabilities(team_a_xg, team_b_xg, 2.5)
        over_2_5_value = calculate_value(over_2_5_prob, match_data["odds_over_2_5"])
        under_2_5_value = calculate_value(under_2_5_prob, match_data["odds_under_2_5"])
        full_recommended = "Over 2.5" if over_2_5_value > under_2_5_value and over_2_5_value > 0 else "Under 2.5"

        over_1_5_ht_prob, under_1_5_ht_prob = predict_probabilities(team_a_xg_ht, team_b_xg_ht, 1.5)
        over_1_5_ht_value = calculate_value(over_1_5_ht_prob, match_data["odds_over_1_5_ht"])
        under_1_5_ht_value = calculate_value(under_1_5_ht_prob, match_data["odds_under_1_5_ht"])
        ht_recommended = "Over 1.5 HT" if over_1_5_ht_value > under_1_5_ht_value and over_1_5_ht_value > 0 else "Under 1.5 HT"

        over_1_5_2h_prob, under_1_5_2h_prob = predict_probabilities(team_a_xg_2h, team_b_xg_2h, 1.5)
        over_1_5_2h_value = calculate_value(over_1_5_2h_prob, match_data["odds_over_1_5_2h"])
        under_1_5_2h_value = calculate_value(under_1_5_2h_prob, match_data["odds_under_1_5_2h"])
        sh_recommended = "Over 1.5 2H" if over_1_5_2h_value > under_1_5_2h_value and over_1_5_2h_value > 0 else "Under 1.5 2H"

        # Prepare table data
        table_data = [
            [
                "Match",
                "Over/Under 2.5 Prob",
                "Over/Under 1.5 HT Prob",
                "Over/Under 1.5 2H Prob",
                "Recommended Bet",
                "Value"
            ],
            [
                match_data["match"],
                f"