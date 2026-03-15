import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import random
import time

# ----------------------------
# CONFIG & THEME
# ----------------------------
st.set_page_config(page_title="Strategic Analytics Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; min-height: 125px; }
    .remark-card { padding: 20px; border-radius: 10px; margin-bottom: 10px; font-family: 'Segoe UI', sans-serif; border-left: 8px solid; }
    .hero-text { text-align: center; padding: 20px; background: linear-gradient(90deg, #00d4ff, #0055ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
    .remark-title { font-weight: bold; text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; margin-bottom: 5px; opacity: 0.8; }
    </style>
""", unsafe_allow_html=True)

if 'last_fetched_id' not in st.session_state:
    st.session_state.last_fetched_id = ""
if 'match_data' not in st.session_state:
    st.session_state.match_data = None

try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except:
    API_KEY = st.sidebar.text_input("🔑 Enter Riot API Key", type="password")

st.sidebar.markdown("---")
RIOT_ID = st.sidebar.text_input("👤 Enter Riot ID (Player#Tag) & Press Enter")
REGION = st.sidebar.selectbox("🌍 Select Region", ["sea", "americas", "europe", "asia"], index=0)

@st.cache_data
def get_latest_version():
    try: return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    except: return "14.1.1"

VER = get_latest_version()

# Queue ID Mapping for Game Modes
QUEUE_MAP = {
    400: "Normal Draft", 420: "Ranked Solo", 430: "Normal Blind", 
    440: "Ranked Flex", 450: "ARAM", 490: "Quickplay", 700: "Clash",
    830: "Co-op vs AI", 840: "Co-op vs AI", 850: "Co-op vs AI", 
    900: "URF", 1700: "Arena"
}

# ----------------------------
# DYNAMIC REMARK ENGINE (V4 - EXPANDED VAULT)
# ----------------------------
def get_styled_remark(m, player_name):
    score = 0
    if m['win']: score += 2
    if m['kda'] >= 3.0: score += 2
    elif m['kda'] >= 1.5: score += 1
    if m['cs_per_min'] >= 6.0: score += 1
    
    optimal_roasts = [
        "Clean execution. You actually played like a human being for once. Keep this up and you might actually climb.",
        "Not bad. I was fully expecting you to throw, but you carried your own weight. Gold star for doing the bare minimum.",
        f"A genuinely impressive performance. Who are you and what did you do with the real {player_name}?",
        "You won, and you actually contributed. Your teammates should be thanking whatever deity they pray to.",
        "Damn, look at those stats. Did your monitor finally turn on? Keep playing like this and I might stop insulting you.",
        f"Holy shit, {player_name}, you actually popped the f*** off. Now do it again instead of immediately queuing up to feed.",
        "I ran the data three times. No bugs, no glitches—you actually carried. I'm terrified.",
        "You dragged four lifeless anchors across the finish line. I hope you have a good chiropractor.",
        "Flawless victory. I'm assuming the enemy team had a collective brain aneurysm, but a win is a win.",
        f"My heuristic engine literally cannot find a flaw here. This is a frustratingly good game, {player_name}.",
        "Look at you, the undisputed MVP. Take a screenshot before you inevitably ruin your match history next game.",
        "10/10 macro, clean mechanics. I'd roast you, but there's nothing here to roast. It's pissing me off.",
        "Are you account sharing? Because there is no way the person who played this match is the same one from yesterday.",
        "You actually stepped up and carried. Write down exactly what you had for breakfast and eat it every day.",
        f"The enemy team is definitely reporting you for scripting. Beautifully played, {player_name}."
    ]
    
    mediocre_roasts = [
        "You existed. You didn't carry, but you didn't run it down. Basically the participation trophy of League games.",
        "Mid. Just... painfully average. You were basically a glorified super minion out there.",
        "You didn't feed, but you didn't pop off either. Congratulations on achieving absolute neutrality.",
        "A completely forgettable performance. I'm already deleting this match from my memory banks.",
        "You were just kind of... there. Like background music, but slightly more annoying."
    ]
    
    critical_roasts = [
        "Absolute disaster. Your presence on the map was a gift to the enemy team. Uninstalling is free, you know.",
        "Holy shit, this is hard to look at. Were you playing with your monitor turned off, or are you just this bad?",
        "I've seen intermediate bots with better macro. You single-handedly dragged your team into the abyss.",
        "A masterclass in feeding. If there was a Nobel Prize for griefing, you'd be the undisputed laureate.",
        "This performance is a literal war crime. Do everyone a favor and stick to single-player games."
    ]
    
    if score >= 4:
        bg, border, title, txt = "rgba(40, 167, 69, 0.1)", "#28a745", "OPTIMAL PERFORMANCE", random.choice(optimal_roasts)
    elif score >= 2:
        bg, border, title, txt = "rgba(255, 193, 7, 0.1)", "#ffc107", "MEDIOCRE OUTPUT", random.choice(mediocre_roasts)
    else:
        bg, border, title, txt = "rgba(220, 53, 69, 0.1)", "#dc3545", "CRITICAL SYSTEM FAILURE", random.choice(critical_roasts)
    
    return f"""<div class="remark-card" style="background-color: {bg}; border-color: {border}; color: {border};">
                <div class="remark-title">DATA INSIGHT // {title}</div>
                <div>{txt}</div>
              </div>"""

# ----------------------------
# AUTO-TRIGGER DATA FETCHING (60-MATCH DEEP DIVE)
# ----------------------------
if API_KEY and RIOT_ID and "#" in RIOT_ID and RIOT_ID != st.session_state.last_fetched_id:
    with st.spinner("Bypassing Rate Limits... Synchronizing Deep Data Clusters..."):
        gn, tl = RIOT_ID.split("#", 1)
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gn}/{tl}?api_key={API_KEY}"
        acc_resp = requests.get(acc_url)
        
        if acc_resp.status_code == 200:
            USER_PUUID = acc_resp.json().get("puuid")
            
            ids_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{USER_PUUID}/ids?count=75&api_key={API_KEY}"
            match_ids = requests.get(ids_url).json()
            raw_data = []
            
            progress_bar = st.progress(0, text="Initiating Mass Data Ingestion...")
            
            valid_matches_processed = 0
            for i, mid in enumerate(match_ids):
                progress_bar.progress((i + 1) / len(match_ids), text=f"Extracting Match {valid_matches_processed}/60 (Scanning {i+1}/{len(match_ids)})")
                
                time.sleep(0.06) 
                
                m_resp = requests.get(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{mid}?api_key={API_KEY}")
                if m_resp.status_code == 200:
                    info = m_resp.json()['info']
                    
                    if info.get('gameDuration', 0) < 240:
                        continue 
                        
                    me = next(p for p in info['participants'] if p['puuid'] == USER_PUUID)
                    try: enemy = next(p for p in info['participants'] if p['teamPosition'] == me['teamPosition'] and p['teamId'] != me['teamId'])
                    except: enemy = next(p for p in info['participants'] if p['teamId'] != me['teamId'])
                    
                    # Fetch Match Type
                    q_id = info.get('queueId', 0)
                    match_type = QUEUE_MAP.get(q_id, "Special Mode")
                    
                    duration_min = info['gameDuration'] / 60
                    raw_data.append({
                        "win": me['win'], "champion": me['championName'], "enemy_champion": enemy['championName'],
                        "kills": me['kills'], "deaths": me['deaths'], "assists": me['assists'], 
                        "kda": (me['kills']+me['assists'])/max(1, me['deaths']),
                        "gold": me['goldEarned'], "enemy_gold": enemy['goldEarned'],
                        "cs": me['totalMinionsKilled'] + me.get('neutralMinionsKilled', 0),
                        "enemy_cs": enemy['totalMinionsKilled'] + enemy.get('neutralMinionsKilled', 0),
                        "cs_per_min": round((me['totalMinionsKilled'] + me.get('neutralMinionsKilled', 0))/duration_min, 1),
                        "vision": me['visionScore'], "enemy_vision": enemy['visionScore'],
                        "items": [me[f'item{j}'] for j in range(7)],
                        "obj_dmg": me['damageDealtToObjectives'], 
                        "kp": round((me['kills']+me['assists'])/max(1, sum(p['kills'] for p in info['participants'] if p['teamId']==me['teamId']))*100),
                        "time": pd.to_datetime(info['gameCreation'], unit='ms'),
                        "queue_name": match_type
                    })
                    
                    valid_matches_processed += 1
                    if valid_matches_processed >= 60:
                        break
            
            st.session_state.match_data = pd.DataFrame(raw_data)
            st.session_state.last_fetched_id = RIOT_ID  
            progress_bar.empty() 
        else: 
            st.error("Riot ID not found. Check your spelling and region.")
            st.session_state.last_fetched_id = ""

# ----------------------------
# DASHBOARD RENDERING
# ----------------------------
if st.session_state.match_data is not None and not st.session_state.match_data.empty:
    df = st.session_state.match_data
    current_player_name = RIOT_ID.split("#")[0] if "#" in RIOT_ID else "Player"
    
    t_col1, t_col2 = st.columns([1, 1])
    
    with t_col1:
        st.subheader("💎 Archetype Diamond")
        categories = ['Combat %', 'CS Speed', 'Map Vision', 'Objectives']
        r_values = [min(df['kp'].mean(), 100), min((df['cs_per_min'].mean()/10)*100, 100), min((df['vision'].mean()/40)*100, 100), min((df['obj_dmg'].mean()/15000)*100, 100)]
        
        fig_radar = go.Figure(data=go.Scatterpolar(r=r_values + [r_values[0]], theta=categories + [categories[0]], fill='toself', line_color="#00d4ff", fillcolor="rgba(0, 212, 255, 0.2)"))
        fig_radar.update_layout(polar=dict(gridshape='linear', bgcolor="#161b22", radialaxis=dict(visible=False, range=[0, 100]), angularaxis=dict(direction="clockwise", period=4)), paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=40, l=40, r=40))
        st.plotly_chart(fig_radar, use_container_width=True)

    with t_col2:
        st.subheader("📊 Champion Distribution")
        
        champ_counts = df['champion'].value_counts().reset_index()
        fig_pie = px.pie(
            champ_counts, 
            values='count', 
            names='champion', 
            hole=0.6, 
            # Brightened Hextech/Neon Color Palette
            color_discrete_sequence=['#00d4ff', '#007bf5', '#7b2cbf', '#c77dff', '#ff006e', '#ffb703'] 
        )
        
        fig_pie.update_traces(
            textinfo='none', 
            hovertemplate="<b>%{label}</b><br>Matches: %{value}<extra></extra>",
            marker=dict(line=dict(color='#0d1117', width=3))
        )
        # Dynamic text showing the actual number of matches parsed
        fig_pie.update_layout(
            showlegend=True, 
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0, font=dict(color="#c9d1d9")),
            paper_bgcolor="rgba(0,0,0,0)", 
            margin=dict(t=20, b=20, l=0, r=0), 
            annotations=[dict(text=f"{len(df)}<br>Games", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="white")]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # Ban Intel Logic
        toughest_champ = df.groupby('enemy_champion')['deaths'].sum().idxmax()
        deaths_to_champ = df.groupby('enemy_champion')['deaths'].sum().max()
        
        st.markdown(f"""
        <div style="background-color: rgba(220, 53, 69, 0.08); border-left: 5px solid #dc3545; padding: 15px; border-radius: 8px;">
            <div style="color: #dc3545; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; font-size: 0.9em;">
                🛑 Toughest Matchup: {toughest_champ}
            </div>
            <div style="color: #c9d1d9; font-size: 0.95em;">
                Farmed you for <b>{deaths_to_champ} total deaths</b> recently. Have you considered banning them?
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- RIVAL COMPARISON ---
    st.subheader("⚔️ Rival Comparison Trends")
    v1, v2 = st.columns(2)
    with v1:
        fig_v_gold = go.Figure()
        fig_v_gold.add_trace(go.Scatter(x=df.index, y=df['gold'], name='Self', line=dict(color='#00d4ff', width=3)))
        fig_v_gold.add_trace(go.Scatter(x=df.index, y=df['enemy_gold'], name='Rival', line=dict(color='#ef553b', dash='dot')))
        fig_v_gold.update_layout(title="Economy Gap", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_v_gold, use_container_width=True)
    with v2:
        fig_v_cs = go.Figure()
        fig_v_cs.add_trace(go.Bar(x=df.index, y=df['cs'], name='Self', marker_color='#00d4ff'))
        fig_v_cs.add_trace(go.Bar(x=df.index, y=df['enemy_cs'], name='Rival', marker_color='#ef553b'))
        fig_v_cs.update_layout(title="CS Differential", barmode='group', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_v_cs, use_container_width=True)

    st.divider()

    # --- MATCH BREAKDOWN (DROP-DOWN STYLE) ---
    st.subheader("🔬 Match Performance Breakdown")
    # Updated to show the Queue Type (Ranked, Normal, Quickplay, etc.)
    opts = [f"{'🏆 WIN' if r['win'] else '💀 LOSS'} | {r['champion']} ({r['queue_name']}) vs {r['enemy_champion']} ({r['time'].strftime('%b %d')})" for i, r in df.iterrows()]
    selected_idx = st.selectbox("Select match record:", range(len(opts)), format_func=lambda x: opts[x])
    cur = df.iloc[selected_idx]
    
    outcome_color = "#28a745" if cur['win'] else "#dc3545"
    outcome_text = "VICTORY" if cur['win'] else "DEFEAT"
    
    st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px;">
            <h1 style='color: {outcome_color}; letter-spacing: 2px; margin: 0;'>{outcome_text}</h1>
            <div style="display: flex; align-items: center; gap: 15px; margin-top: 10px;">
                <img src="https://ddragon.leagueoflegends.com/cdn/{VER}/img/champion/{cur['champion']}.png" width="60" style="border-radius: 50%; border: 2px solid {outcome_color};">
                <h4 style='margin: 0;'>Playing <b>{cur['champion']}</b> in <b>{cur['queue_name']}</b> against <b>{cur['enemy_champion']}</b></h4>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    col_stats, col_ai = st.columns([1.5, 1])
    
    with col_stats:
        st.markdown("### 📈 Core Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("KDA", f"{cur['kills']}/{cur['deaths']}/{cur['assists']}", f"{round(cur['kda'], 2)} Ratio", delta_color="off")
        c2.metric("Farming (CS)", f"{cur['cs']}", f"{cur['cs'] - cur['enemy_cs']:+} vs Enemy")
        c3.metric("Gold Advantage", f"{cur['gold']:,} G", f"{cur['gold'] - cur['enemy_gold']:+,} G")
        
        st.markdown("### 🤝 Team Impact")
        c4, c5, c6 = st.columns(3)
        c4.metric("Kill Participation", f"{cur['kp']}%", " ", delta_color="off")
        c5.metric("Vision Score", f"{cur['vision']}", f"{cur['vision'] - cur['enemy_vision']:+} vs Enemy")
        c6.metric("CS / Min", f"{cur['cs_per_min']}", " ", delta_color="off")

    with col_ai:
        st.markdown("### 🤖 Automated Judgment")
        st.markdown(get_styled_remark(cur, current_player_name), unsafe_allow_html=True)
        
        st.markdown("### 🎒 Inventory")
        def get_item_html(item_id, is_trinket=False):
            rad = "50%" if is_trinket else "8px"
            if item_id == 0:
                return f"<div style='width:45px; height:45px; background:#0d1117; border:1px solid #30363d; border-radius:{rad};'></div>"
            return f"<img src='https://ddragon.leagueoflegends.com/cdn/{VER}/img/item/{item_id}.png' width='45' style='border:1px solid #30363d; border-radius:{rad};'>"

        grid_html = f"""
        <div style="display: grid; grid-template-columns: repeat(4, 50px); gap: 8px; padding: 15px; background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; width: fit-content;">
            {get_item_html(cur['items'][0])}
            {get_item_html(cur['items'][1])}
            {get_item_html(cur['items'][2])}
            {get_item_html(cur['items'][6], is_trinket=True)}
            {get_item_html(cur['items'][3])}
            {get_item_html(cur['items'][4])}
            {get_item_html(cur['items'][5])}
        </div>
        """
        st.markdown(grid_html, unsafe_allow_html=True)

else:
    st.markdown("<h1 class='hero-text'>STRATEGIC ANALYTICS TERMINAL</h1>", unsafe_allow_html=True)
    
    col_l, col_mid, col_r = st.columns([1, 1, 1])
    with col_mid:
        st.image("hero_bg.png", width=420)
    
    st.markdown("<br><h3 style='text-align:center;'>Terminal Operations Guide</h3><hr>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("1. API Key")
        st.write("Secure a Match-V5 development key from the Riot Portal and input it in the sidebar.")
    with col2:
        st.subheader("2. Target ID")
        st.write("Enter the target player's Riot ID, including the hashtag (e.g., Target#NA1).")
    with col3:
        st.subheader("3. Execute")
        st.write("Hit ENTER on your keyboard. The terminal will automatically ingest and parse the data.")