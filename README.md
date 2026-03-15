# 🏆 League of Legends Performance Analytics Terminal

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live-FF4B4B.svg)](#) [![Data Engine](https://img.shields.io/badge/Data-Pandas%20%7C%20Plotly-150458.svg)](#)

**Live Dashboard:** [(https://lane-dominance-tracker-lol.streamlit.app)](https://lane-dominance-tracker-lol.streamlit.app)
**Developer:** Aditya Mathew

## 📌 Project Overview
This project is a full-stack, automated data analytics dashboard designed to ingest, process, and visualize complex JSON data from the official **Riot Games REST API**. It serves as a comprehensive player profiling tool, transforming raw match histories into actionable macro-level insights and chronological performance trends.

The application was built to demonstrate end-to-end data engineering skills, including API authentication, rate-limit handling, dynamic ETL (Extract, Transform, Load) processes, and interactive front-end data visualization.

## ⚙️ Key Features
* **Dynamic Data Ingestion:** Securely queries the Riot `Match-V5` and `Account-V1` APIs to fetch real-time player data.
* **Psychological Profiling (Radar Chart):** Uses normalized data scaling to map a player's tendencies across four axes: Combat Aggression (KP%), Resource Generation (CS), Map Control (Vision), and Objective Focus (Damage).
* **Macro Trends Dashboard:** Plots chronological performance metrics (KDA, Net Gold Differential, Kill Volume) using `Plotly Graph Objects` for high-fidelity, interactive visualizations.
* **Heuristic Analytics Engine:** A custom algorithmic text-generator that evaluates in-game metrics (e.g., gold deficits at specific timestamps, suboptimal itemization) to output automated performance judgments.
* **Session State Optimization:** Minimizes API payload and latency by caching complex dataframes locally during the user session.

## 🛠️ Technology Stack
* **Language:** Python 3
* **Front-End / Deployment:** Streamlit, Streamlit Community Cloud
* **Data Manipulation:** Pandas
* **Data Visualization:** Plotly (Express & Graph Objects)
* **Networking:** Requests (REST API Integration)

## 🚀 Local Installation & Setup
To run this dashboard locally, you will need a Riot Games Developer API Key.

1. Clone the repository:
   ```bash
   git clone [https://github.com/A17PRO/Lane-Dominance-Tracker.git](https://github.com/A17PRO/Lane-Dominance-Tracker.git)
   cd Lane-Dominance-Tracker
