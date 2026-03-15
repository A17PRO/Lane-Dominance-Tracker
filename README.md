# 🎮 League of Legends Lane Dominance Tracker

A dynamic, real-time data analysis dashboard built with Python and Streamlit that tracks League of Legends match history, calculates advanced macro metrics, and provides highly opinionated AI-generated roasts based on your performance.

## 🚀 Features
* **Live API Integration:** Fetches real-time match data, participant stats, and queues using the Riot Games API.
* **Advanced Analytics:** Calculates KDA, Kill Participation (KP%), CS differentials, and Gold advantages.
* **Interactive Data Visualizations:** Uses Plotly to graph performance trends over time.
* **AI Coaching/Roasting Engine:** Dynamically generates custom commentary analyzing your macro gameplay, vision score, objective damage, and itemization. 

## 🛠️ Tech Stack
* **Python** (Pandas for data manipulation, Requests for API calls)
* **Streamlit** (Frontend UI and caching)
* **Plotly** (Interactive charting)
* **Riot Games API & Data Dragon** (Live match data and static item asset mapping)

## ⚙️ How to Run Locally
1. Clone the repository:
   `git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`
2. Install the dependencies:
   `pip install -r requirements.txt`
3. Run the Streamlit app:
   `streamlit run your_script_name.py`
*(Note: You will need your own Riot Development API Key to fetch data).*
