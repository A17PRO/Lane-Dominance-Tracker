import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import random
import time
import json

# ----------------------------
# CONFIG & THEME
# ----------------------------
st.set_page_config(page_title="Strategic Analytics Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; min-height: 125px; }
    .remark-card { padding: 20px; border-radius: 10px; margin-bottom: 20px; font-family: 'Segoe UI', sans-serif; border-left: 8px solid; }
    .hero-text { text-align: center; padding: 20px; background: linear-gradient(90deg, #00d4ff, #0055ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
    .remark-title { font-weight: bold; text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; margin-bottom: 5px; opacity: 0.8; }
    
    /* LEAGUE OF LEGENDS CUSTOM TOOLTIP CSS */
    .item-wrapper { position: relative; display: inline-block; cursor: help; }
    .item-tooltip { visibility: hidden; width: 260px; background-color: #010a13; color: #a09b8c; text-align: left; border: 1px solid #785a28; padding: 12px; position: absolute; z-index: 9999; bottom: 125%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; font-family: 'Segoe UI', sans-serif; font-size: 0.85em; box-shadow: 0 4px 12px rgba(0,0,0,0.8); pointer-events: none; }
    .item-wrapper:hover .item-tooltip { visibility: visible; opacity: 1; }
    .item-name { color: #00d4ff; font-weight: bold; font-size: 1.1em; border-bottom: 1px solid #392a14; padding-bottom: 4px; margin-bottom: 6px; }
    .item-cost { color: #f1b24a; font-weight: bold; margin-bottom: 8px; font-size: 0.9em; }
    
    /* RIOT'S INTERNAL JSON TAG STYLING */
    .item-desc stats { color: #86d2a0; display: block; margin-bottom: 6px; line-height: 1.4; }
    .item-desc attention { font-weight: bold; color: #fff; }
    .item-desc active, .item-desc passive { color: #f1b24a; font-weight: bold; }
    .item-desc mana { color: #44bbf2; }
    .item-desc rules { font-style: italic; color: #8b949e; display: block; margin-top: 6px; }
    </style>
""", unsafe_allow_html=True)

if 'last_fetched_id' not in st.session_state:
    st.session_state.last_fetched_id = ""
if 'match_data' not in st.session_state:
    st.session_state.match_data = None

try:
    API_KEY = st.secrets["RIOT_API_KEY"]
    st.sidebar.success("✅ API Key Secured")
except:
    API_KEY = st.sidebar.text_input("🔑 Enter Riot API Key", type="password")

st.sidebar.markdown("---")
RIOT_ID = st.sidebar.text_input("👤 Enter Riot ID (Player#Tag)")
REGION = st.sidebar.selectbox("🌍 Select Region", ["sea", "americas", "europe", "asia"], index=0)

fetch_button = st.sidebar.button("Analyze")

# ----------------------------
# CACHING & DATA LOADERS
# ----------------------------
@st.cache_data
def get_latest_version():
    try: return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    except: return "14.1.1"

VER = get_latest_version()

@st.cache_data
def get_item_data():
    try: 
        with open('item.json', 'r', encoding='utf-8') as f:
            return json.load(f)['data']
    except FileNotFoundError: 
        st.error("🚨 Missing item.json! Did you actually put it in the same folder as this script?")
        return {}

ITEM_DATA = get_item_data()

@st.cache_data
def get_rune_data():
    try:
        with open('runesReforged.json', 'r', encoding='utf-8') as f:
            raw_runes = json.load(f)
            rune_dict = {}
            for tree in raw_runes:
                rune_dict[str(tree['id'])] = {'name': tree['name'], 'desc': tree.get('name', '') + ' Tree', 'icon': tree['icon']}
                for slot in tree['slots']:
                    for rune in slot['runes']:
                        rune_dict[str(rune['id'])] = {'name': rune['name'], 'desc': rune.get('shortDesc', ''), 'icon': rune['icon']}
            return rune_dict
    except FileNotFoundError:
        st.error("🚨 Missing runesReforged.json! Put it in the folder next to your script.")
        return {}

RUNE_DATA = get_rune_data()

QUEUE_MAP = {
    400: "Normal Draft", 420: "Ranked Solo", 430: "Normal Blind", 
    440: "Ranked Flex", 450: "ARAM", 490: "Quickplay", 700: "Clash",
    830: "Co-op vs AI", 840: "Co-op vs AI", 850: "Co-op vs AI", 
    900: "URF", 1700: "Arena"
}

# ----------------------------
# DYNAMIC REMARK ENGINE (V5 - THE MEGA VAULT)
# ----------------------------
def get_styled_remark(m, player_name):
    score = 0
    if m['win']: score += 2
    if m['kda'] >= 3.0: score += 2
    elif m['kda'] >= 1.5: score += 1
    if m['cs_per_min'] >= 6.0: score += 1
    
    optimal_roasts = [
        "Clean execution. You actually played like a human being for once. Keep this up and you might actually climb.",
        "Not bad. I was fully expecting you to throw, but you carried your own weight.",
        f"A genuinely impressive performance. Who are you and what did you do with the real {player_name}?",
        "You won, and you actually contributed. Your teammates should be thanking whatever deity they pray to.",
        "Damn, look at those stats. Did your monitor finally turn on?",
        "Are you getting boosted? Because this level of competence from you is highly suspicious.",
        "You put the team on your back and didn't immediately break your spine. Impressive.",
        "Someone call an ambulance, but not for you. You actually dismantled them.",
        "I didn't know they updated the intermediate bots to play this well. Good job.",
        "An actual carry performance. Print this out and put it on your fridge so your parents have something to be proud of."
    ]
    
    mediocre_roasts = [
        "You existed. You didn't carry, but you didn't run it down. Basically the participation trophy of League games.",
        "Mid. Just... painfully average. You were basically a glorified super minion out there.",
        "You didn't feed, but you didn't pop off either. Congratulations on achieving absolute neutrality.",
        "You were the human equivalent of a control ward. Useful, but entirely passive.",
        "You dealt damage, you took damage, the game ended. A truly whelming experience.",
        "You rode your team's coattails so hard you probably gave them rug burn.",
        "You were present. That is the highest compliment I can legally give this performance.",
        "Congratulations on not being the explicit reason you lost. Aim higher next time.",
        "You played like someone who is afraid of their own shadow. Step up and make a play.",
        "A 5/10 performance. You didn't ruin the game, but you certainly didn't win it either."
    ]
    
    critical_roasts = [
        "Absolute disaster. Your presence on the map was a gift to the enemy team. Uninstalling is free, you know.",
        "Holy shit, this is hard to look at. Were you playing with your monitor turned off, or are you just this bad?",
        "I've seen intermediate bots with better macro. You single-handedly dragged your team into the abyss.",
        "A masterclass in feeding. If there was a Nobel Prize for griefing, you'd be the undisputed laureate.",
        "If feeding was an Olympic sport, you would be taking home the gold.",
        "You were essentially a walking bag of gold for the enemy team. Do better.",
        "I'm genuinely impressed by how much of a liability you were in this match.",
        "Please apologize to the trees that produce the oxygen you wasted during this game.",
        f"You didn't just lose the lane, {player_name}, you lost the entire zip code.",
        "Are you playing with a USB steering wheel? Because that would explain a lot.",
        "This match is a statistical anomaly of pure incompetence.",
        "You have officially lowered the win rate of that champion globally. Riot should send you a warning."
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
# DATA FETCHING 
# ----------------------------
if fetch_button:
    if not API_KEY or "#" not in RIOT_ID:
        st.sidebar.error("Provide a valid API Key and Riot ID (Player#Tag).")
    else:
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
                        
                        if info.get('gameDuration', 0) < 240: continue 
                            
                        me = next(p for p in info['participants'] if p['puuid'] == USER_PUUID)
                        try: enemy = next(p for p in info['participants'] if p['teamPosition'] == me['teamPosition'] and p['teamId'] != me['teamId'])
                        except: enemy = next(p for p in info['participants'] if p['teamId'] != me['teamId'])
                        
                        q_id = info.get('queueId', 0)
                        match_type = QUEUE_MAP.get(q_id, "Special Mode")
                        duration_min = info['gameDuration'] / 60
                        
                        raw_data.append({
                            "match_id": mid,
                            "me_id": me['participantId'], 
                            "enemy_id": enemy['participantId'], 
                            "win": me['win'], "champion": me['championName'], "enemy_champion": enemy['championName'],
                            "kills": me['kills'], "deaths": me['deaths'], "assists": me['assists'], 
                            "kda": (me['kills']+me['assists'])/max(1, me['deaths']),
                            "gold": me['goldEarned'], "enemy_gold": enemy['goldEarned'],
                            "cs": me['totalMinionsKilled'] + me.get('neutralMinionsKilled', 0),
                            "enemy_cs": enemy['totalMinionsKilled'] + enemy.get('neutralMinionsKilled', 0),
                            "cs_per_min": round((me['totalMinionsKilled'] + me.get('neutralMinionsKilled', 0))/duration_min, 1),
                            "vision": me['visionScore'], "enemy_vision": enemy['visionScore'],
                            "obj_dmg": me['damageDealtToObjectives'], 
                            "kp": round((me['kills']+me['assists'])/max(1, sum(p['kills'] for p in info['participants'] if p['teamId']==me['teamId']))*100),
                            "time": pd.to_datetime(info['gameCreation'], unit='ms'),
                            "queue_name": match_type
                        })
                        
                        valid_matches_processed += 1
                        if valid_matches_processed >= 60: break
                
                st.session_state.match_data = pd.DataFrame(raw_data)
                progress_bar.empty() 
            else: 
                st.sidebar.error("Riot ID not found. Check your spelling and region.")


# ----------------------------
# DASHBOARD RENDERING
# ----------------------------
if st.session_state.match_data is not None and not st.session_state.match_data.empty:
    df = st.session_state.match_data
    current_player_name = RIOT_ID.split("#")[0] if "#" in RIOT_ID else "Player"
    
    # --- TOP ROW ---
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
        fig_pie = px.pie(champ_counts, values='count', names='champion', hole=0.6, color_discrete_sequence=['#00d4ff', '#007bf5', '#7b2cbf', '#c77dff', '#ff006e', '#ffb703'])
        fig_pie.update_traces(textinfo='none', hovertemplate="<b>%{label}</b><br>Matches: %{value}<extra></extra>", marker=dict(line=dict(color='#0d1117', width=3)))
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0, font=dict(color="#c9d1d9")), paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0), annotations=[dict(text=f"{len(df)}<br>Games", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="white")])
        st.plotly_chart(fig_pie, use_container_width=True)
        
        toughest_champ = df.groupby('enemy_champion')['deaths'].sum().idxmax()
        st.markdown(f"<div style='background-color: rgba(220, 53, 69, 0.08); border-left: 5px solid #dc3545; padding: 15px; border-radius: 8px;'><div style='color: #dc3545; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; font-size: 0.9em;'>🛑 Toughest Matchup: {toughest_champ}</div><div style='color: #c9d1d9; font-size: 0.95em;'>Farmed you for <b>{df.groupby('enemy_champion')['deaths'].sum().max()} total deaths</b> recently. Have you considered banning them?</div></div>", unsafe_allow_html=True)

    st.divider()

    # --- MIDDLE ROW ---
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

    # --- BOTTOM ROW: OP.GG SCOREBOARD INTEGRATION ---
    st.subheader("🔬 Match Performance Breakdown")
    opts = [f"{'🏆 WIN' if r['win'] else '💀 LOSS'} | {r['champion']} ({r.get('queue_name', 'Unknown')}) vs {r['enemy_champion']} ({r['time'].strftime('%b %d')})" for i, r in df.iterrows()]
    selected_idx = st.selectbox("Select match record to expand:", range(len(opts)), format_func=lambda x: opts[x])
    cur = df.iloc[selected_idx]
    
    outcome_color = "#28a745" if cur['win'] else "#dc3545"
    st.markdown(f"""
        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px;'>
            <h1 style='color: {outcome_color}; letter-spacing: 2px; margin: 0;'>{'VICTORY' if cur['win'] else 'DEFEAT'}</h1>
            <div style='display: flex; align-items: center; gap: 15px; margin-top: 10px;'>
                <img src='https://ddragon.leagueoflegends.com/cdn/{VER}/img/champion/{cur['champion']}.png' width='60' style='border-radius: 50%; border: 2px solid {outcome_color};'>
                <h4 style='margin: 0;'>Playing <b>{cur['champion']}</b> in <b>{cur.get('queue_name', 'Unknown')}</b> against <b>{cur['enemy_champion']}</b></h4>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(get_styled_remark(cur, current_player_name), unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # FETCH 10-PLAYER SCOREBOARD
    # ---------------------------------------------------------
    with st.spinner("Extracting Full Team Scoreboard..."):
        match_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{cur['match_id']}?api_key={API_KEY}"
        m_resp = requests.get(match_url)
        
        if m_resp.status_code == 200:
            match_info = m_resp.json()['info']
            participants = match_info['participants']
            
            st.subheader("📋 Full Team Scoreboard")
            team_100 = [p for p in participants if p['teamId'] == 100]
            team_200 = [p for p in participants if p['teamId'] == 200]
            max_dmg = max([p['totalDamageDealtToChampions'] for p in participants])
            max_gold = max([p['goldEarned'] for p in participants])

            def render_scoreboard(team_data, team_color, team_name):
                bg_color = "#161b22" 
                team_total_kills = max(sum([p['kills'] for p in team_data]), 1)
                
                html = f"""
                <div style="background-color: {bg_color}; border-left: 5px solid {team_color}; border-radius: 10px; padding: 15px; margin-bottom: 25px; box-shadow: 0 8px 16px rgba(0,0,0,0.4);">
                    <h3 style="color: {team_color}; margin-top: 0; margin-bottom: 15px; font-family: 'Segoe UI', sans-serif; letter-spacing: 1px;">{team_name}</h3>
                    <table style="width: 100%; text-align: left; border-collapse: collapse; font-family: 'Segoe UI', sans-serif; font-size: 0.9em; color: #c9d1d9;">
                        <tr style="border-bottom: 2px solid #30363d; color: #8b949e; text-transform: uppercase; font-size: 0.8em; letter-spacing: 0.5px;">
                            <th style="padding: 10px 5px; width: 40px;"></th>
                            <th style="padding: 10px 5px; width: 15%;">Summoner</th>
                            <th style="padding: 10px 5px; width: 5%;">Runes</th>
                            <th style="padding: 10px 5px; text-align: center; width: 18%;">Items</th>
                            <th style="padding: 10px 5px; text-align: center; width: 15%;">KDA / KP%</th>
                            <th style="padding: 10px 5px; width: 18%;">Damage</th>
                            <th style="padding: 10px 5px; text-align: center; width: 5%;">CS</th>
                            <th style="padding: 10px 5px; width: 15%;">Economy</th>
                        </tr>
                """
                
                def get_advanced_tooltip(iid, is_rune=False):
                    if is_rune and str(iid) in RUNE_DATA:
                        r = RUNE_DATA[str(iid)]
                        name, desc = r['name'], r['desc'].replace("'", "&#39;").replace('"', '&quot;')
                        return f"<div class='item-tooltip'><div class='item-name' style='color:#ffc107;'>{name}</div><div class='item-desc'>{desc}</div></div>"
                    elif not is_rune and str(iid) in ITEM_DATA:
                        item = ITEM_DATA[str(iid)]
                        name = item.get('name', 'Unknown')
                        cost = item.get('gold', {}).get('total', 0)
                        desc = item.get('description', 'No description available.') 
                        return f"<div class='item-tooltip'><div class='item-name'>{name}</div><div class='item-cost'>🪙 {cost} Gold</div><div class='item-desc'>{desc}</div></div>"
                    return "<div class='item-tooltip'>Unknown Data</div>"
                
                for p in team_data:
                    game_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                    tag_line = p.get('riotIdTagline', '')
                    full_name = f"{game_name}#{tag_line}" if tag_line else game_name
                    if len(full_name) > 16: full_name = full_name[:14] + "..."
                    
                    kda_str = f"<span style='color:#fff;'>{p['kills']}</span> / <span style='color:#ff4b4b;'>{p['deaths']}</span> / <span style='color:#fff;'>{p['assists']}</span>"
                    kp = round(((p['kills'] + p['assists']) / team_total_kills) * 100)
                    
                    dmg_pct = (p['totalDamageDealtToChampions'] / max_dmg) * 100 if max_dmg else 0
                    gold_pct = (p['goldEarned'] / max_gold) * 100 if max_gold else 0
                    
                    # RUNES
                    try: keystone_id = p['perks']['styles'][0]['selections'][0]['perk']
                    except: keystone_id = 0
                    try: secondary_id = p['perks']['styles'][1]['style']
                    except: secondary_id = 0

                    runes_html = "<div style='display: flex; flex-direction: column; gap: 4px; justify-content: center;'>"
                    for rid, size in [(keystone_id, 28), (secondary_id, 22)]:
                        if rid != 0 and str(rid) in RUNE_DATA:
                            r_img = RUNE_DATA[str(rid)]['icon']
                            tt = get_advanced_tooltip(rid, is_rune=True)
                            runes_html += f"<div class='item-wrapper'><img src='https://ddragon.leagueoflegends.com/cdn/img/{r_img}' width='{size}' height='{size}' style='border-radius:50%; background:#000;'>{tt}</div>"
                        else:
                            runes_html += f"<div style='width:{size}px; height:{size}px; border-radius:50%; background:#0d1117; border:1px solid #30363d;'></div>"
                    runes_html += "</div>"

                    # ITEMS (3x2 + 1 Centered Grid)
                    items_html = "<div style='display: flex; gap: 6px; align-items: center; justify-content: center;'>"
                    items_html += "<div style='display: grid; grid-template-columns: repeat(3, 26px); gap: 3px;'>"
                    for i in range(6):
                        iid = p[f'item{i}']
                        if iid == 0:
                            items_html += f"<div style='width:26px; height:26px; background:#0d1117; border:1px solid #30363d; border-radius:4px;'></div>"
                        else:
                            tt_html = get_advanced_tooltip(iid)
                            items_html += f"<div class='item-wrapper'><img src='https://ddragon.leagueoflegends.com/cdn/{VER}/img/item/{iid}.png' width='26' height='26' style='border:1px solid #30363d; border-radius:4px;'>{tt_html}</div>"
                    items_html += "</div>"
                    
                    t_id = p['item6']
                    if t_id == 0:
                        items_html += f"<div style='width:26px; height:26px; background:#0d1117; border:1px solid #30363d; border-radius:4px;'></div>"
                    else:
                        tt_html = get_advanced_tooltip(t_id)
                        items_html += f"<div class='item-wrapper'><img src='https://ddragon.leagueoflegends.com/cdn/{VER}/img/item/{t_id}.png' width='26' height='26' style='border:1px solid #30363d; border-radius:4px;'>{tt_html}</div>"
                    items_html += "</div>"
                    
                    is_me = f"background: linear-gradient(90deg, {team_color}22, transparent);" if p['participantId'] == cur['me_id'] else ""
                    
                    dmg_display = f"""
                    <div style="display: flex; flex-direction: column; justify-content: center; gap: 4px;">
                        <span style="font-family: monospace; font-weight: bold; font-size: 1.1em; color: #fff;">{p['totalDamageDealtToChampions']:,}</span>
                        <div style="width: 100%; background: #0d1117; height: 6px; border-radius: 3px; border: 1px solid #30363d;">
                            <div style="width: {dmg_pct}%; background: {team_color}; height: 100%; border-radius: 3px; box-shadow: 0 0 5px {team_color};"></div>
                        </div>
                    </div>"""
                    
                    gold_display = f"""
                    <div style="display: flex; flex-direction: column; justify-content: center; gap: 4px;">
                        <span style="font-family: monospace; font-weight: bold; font-size: 1.1em; color: #fff;">{p['goldEarned']:,} <span style="font-size: 0.8em; color: #ffc107;">G</span></span>
                        <div style="width: 100%; background: #0d1117; height: 6px; border-radius: 3px; border: 1px solid #30363d;">
                            <div style="width: {gold_pct}%; background: #ffc107; height: 100%; border-radius: 3px; box-shadow: 0 0 5px #ffc107;"></div>
                        </div>
                    </div>"""
                    
                    html += f"""
                        <tr style="border-bottom: 1px solid #21262d; {is_me}">
                            <td style="padding: 10px 5px;">
                                <img src='https://ddragon.leagueoflegends.com/cdn/{VER}/img/champion/{p['championName']}.png' width='40' style='border-radius:50%; border:2px solid {team_color}; box-shadow: 0 0 8px {team_color}44;'>
                            </td>
                            <td style="padding: 10px 5px; font-weight: bold; color: #fff; font-size: 0.9em;">
                                {full_name}
                            </td>
                            <td style="padding: 10px 5px;">{runes_html}</td>
                            <td style="padding: 10px 5px; text-align: center;">{items_html}</td>
                            <td style="padding: 10px 5px; text-align: center;">
                                <div style="font-family: monospace; font-size: 1.1em;">{kda_str}</div>
                                <div style="font-size: 0.8em; color: #8b949e; margin-top: 2px;">{kp}% KP</div>
                            </td>
                            <td style="padding: 10px 5px; padding-right: 15px;">{dmg_display}</td>
                            <td style="padding: 10px 5px; text-align: center; font-family: monospace; font-size: 1.1em; color: #fff;">
                                {p['totalMinionsKilled'] + p.get('neutralMinionsKilled', 0)}
                            </td>
                            <td style="padding: 10px 5px;">{gold_display}</td>
                        </tr>
                    """
                html += "</table></div>"
                return "".join(line.strip() for line in html.split("\n"))

            st.markdown(render_scoreboard(team_100, "#00d4ff", "BLUE SIDE"), unsafe_allow_html=True)
            st.markdown(render_scoreboard(team_200, "#ef553b", "RED SIDE"), unsafe_allow_html=True)
                
        else:
            st.error("Failed to extract deep telemetry. Riot API may be throttling requests.")

else:
    st.markdown("<h1 class='hero-text'>STRATEGIC ANALYTICS TERMINAL</h1>", unsafe_allow_html=True)
    col_l, col_mid, col_r = st.columns([1, 1, 1])
    with col_mid: st.image("hero_bg.png", width=420)
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
        st.write("Click 'Analyze' in the sidebar. The terminal will automatically ingest and parse the data.")