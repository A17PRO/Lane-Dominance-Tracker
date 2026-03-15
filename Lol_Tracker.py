import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import time

# ----------------------------
# CONFIG & SECRETS
# ----------------------------
st.set_page_config(page_title="League Analytics Terminal", layout="wide")
st.sidebar.header("⚙️ Configuration")

try:
    API_KEY = st.secrets["RIOT_API_KEY"]
    st.sidebar.success("🔑 API Key securely loaded.")
except Exception:
    API_KEY = st.sidebar.text_input("🔑 Enter Riot API Key", type="password")
    st.sidebar.info("Local environment: Please provide API Key.")

RIOT_ID = st.sidebar.text_input("👤 Enter Riot ID (e.g. Player#Tag)")
REGION = st.sidebar.selectbox("🌍 Select Region", ["sea", "americas", "europe", "asia"], index=0)

# ----------------------------
# STATIC MAPPING & ENGINES
# ----------------------------
@st.cache_data(ttl=86400)
def get_item_map():
    try:
        versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        items_data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{versions[0]}/data/en_US/item.json").json()
        return {int(k): v['name'] for k, v in items_data['data'].items()}
    except: return {}

ITEM_MAP = get_item_map()

QUEUE_MAP = {400: "Normal Draft", 420: "Ranked Solo/Duo", 430: "Normal Blind", 440: "Ranked Flex", 450: "ARAM", 480: "Swiftplay", 490: "Quickplay", 700: "Clash", 1700: "Arena"}

def get_luna_macro_roast(win, kills, deaths, assists, kda, cs_diff, obj_damage, kp):
    roast = ""
    if win:
        if kda >= 4.0 and kp >= 50: roast += "Hard-carried. An incredibly rare and terrifying sight. "
        elif kda >= 2.0: roast += "You did just enough to not ruin the game. "
        else: roast += "You got completely carried. Say 'thank you' to your team and move on. "
    else:
        if kda >= 3.0: roast += "You tried, but your team was an all-you-can-eat buffet. Tragic. "
        elif kda >= 1.5: roast += "Mediocre performance resulting in a mediocre loss. "
        else: roast += f"Look in the mirror. YOU are the reason you lost. {deaths} deaths is criminal. "

    if cs_diff <= -30: roast += f" Your farming is pathetic (down {abs(cs_diff)} CS). "
    if obj_damage < 2000 and kills >= 5: roast += " Stop playing team deathmatch and hit the damn towers. "
    return roast.strip()

def get_item_roast(items, duration_sec):
    real = [i for i in items if i not in ["Stealth Ward", "Farsight Alteration", "Oracle Lens", "Unknown Item"]]
    has_boots = any("Boots" in i or "Shoes" in i or "Greaves" in i or "Treads" in i for i in real)
    dur_m = duration_sec / 60
    roast = f"**Final Build:** {', '.join(real) if real else 'Literally nothing. Were you AFK?'} \n\n"
    if dur_m > 30 and len(real) < 4: roast += "Game went 30+ minutes and you couldn't afford 4 items. Absolute poverty. "
    if not has_boots and dur_m > 15: roast += "No upgraded boots. Do you enjoy walking back to lane like a crippled snail? "
    return roast

# ----------------------------
# DATA FETCHING
# ----------------------------
st.title("📊 League of Legends Performance Terminal")

if 'match_data' not in st.session_state: st.session_state.match_data = None

if st.sidebar.button("🚀 Fetch Match History"):
    if not API_KEY or not RIOT_ID or "#" not in RIOT_ID: st.error("Please provide a valid API Key and Riot ID.")
    else:
        with st.spinner(f"Querying Riot API for {RIOT_ID}..."):
            gn, tl = RIOT_ID.split("#", 1)
            acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gn}/{tl}?api_key={API_KEY}"
            acc_resp = requests.get(acc_url)
            if acc_resp.status_code == 200:
                USER_PUUID = acc_resp.json().get("puuid")
                ids_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{USER_PUUID}/ids?count=10&api_key={API_KEY}"
                match_ids = requests.get(ids_url).json()
                raw_data = []
                bar = st.progress(0, text="Processing match datasets...")
                for i, mid in enumerate(match_ids):
                    m_resp = requests.get(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{mid}?api_key={API_KEY}")
                    if m_resp.status_code == 200:
                        info = m_resp.json()['info']
                        try:
                            me = next(p for p in info['participants'] if p['puuid'] == USER_PUUID)
                            try: enemy = next(p for p in info['participants'] if p['teamPosition'] == me['teamPosition'] and p['teamId'] != me['teamId'])
                            except: enemy = next(p for p in info['participants'] if p['teamId'] != me['teamId'])
                            
                            t_kills = sum(p['kills'] for p in info['participants'] if p['teamId'] == me['teamId'])
                            t_deaths = sum(p['deaths'] for p in info['participants'] if p['teamId'] == me['teamId'])
                            
                            kda = (me['kills'] + me['assists']) / max(1, me['deaths'])
                            enemy_kda = (enemy['kills'] + enemy['assists']) / max(1, enemy['deaths'])
                            
                            cs = me['totalMinionsKilled'] + me.get('neutralMinionsKilled', 0)
                            ecs = enemy['totalMinionsKilled'] + enemy.get('neutralMinionsKilled', 0)
                            kp = round(((me['kills'] + me['assists']) / max(1, t_kills)) * 100) if t_kills > 0 else 0
                            items = [ITEM_MAP.get(me.get(f'item{j}', 0), "Unknown") for j in range(7) if me.get(f'item{j}', 0) != 0]
                            
                            raw_data.append({
                                "match_id": mid, "game_creation": info['gameCreation'], "duration": info['gameDuration'],
                                "game_mode": QUEUE_MAP.get(info.get('queueId', 0), "Unknown Mode"),
                                "champion": me['championName'], "enemy_champion": enemy['championName'],
                                "win": me['win'], "kills": me['kills'], "deaths": me['deaths'], "assists": me['assists'], 
                                "enemy_kills": enemy['kills'], "enemy_deaths": enemy['deaths'], 
                                "kda": kda, "enemy_kda": enemy_kda, "kp": kp, "cs": cs, "enemy_cs": ecs, 
                                "vision": me.get('visionScore', 0), "obj_dmg": me.get('damageDealtToObjectives', 0),
                                "gold": me.get('goldEarned', 0), "enemy_gold": enemy.get('goldEarned', 0), 
                                "gold_diff": me.get('goldEarned', 0) - enemy.get('goldEarned', 0), 
                                "team_kda": f"{t_kills} / {t_deaths}",
                                "roast": get_luna_macro_roast(me['win'], me['kills'], me['deaths'], me['assists'], kda, cs - ecs, me.get('damageDealtToObjectives', 0), kp), 
                                "item_roast": get_item_roast(items, info['gameDuration'])
                            })
                        except Exception: pass 
                    bar.progress((i + 1) / len(match_ids))
                if raw_data:
                    df = pd.DataFrame(raw_data)
                    df['game_creation'] = pd.to_datetime(df['game_creation'], unit='ms')
                    st.session_state.match_data = df.sort_values('game_creation', ascending=False)
                    st.success("Data successfully processed and loaded.")
            else: st.error("Failed to authenticate Riot ID.")

# ----------------------------
# DASHBOARD RENDERING
# ----------------------------
if st.session_state.match_data is not None:
    df = st.session_state.match_data
    df_chrono = df.sort_values('game_creation', ascending=True)

    # --- PSYCHOLOGICAL PROFILER ---
    st.subheader("🧠 Playstyle & Behavioral Profiling")
    p_col1, p_col2 = st.columns([1, 1])
    
    with p_col1:
        bloodthirst = min(df['kp'].mean(), 100)
        greed = min((df['cs'].mean() / 250) * 100, 100)
        paranoia = min((df['vision'].mean() / 40) * 100, 100) 
        demolition = min((df['obj_dmg'].mean() / 15000) * 100, 100)
        
        radar_df = pd.DataFrame(dict(
            r=[bloodthirst, greed, paranoia, demolition], 
            theta=['Combat Aggression (KP%)','Resource Generation (CS)','Map Control (Vision)','Objective Focus (Dmg)']
        ))
        
        fig_radar = px.line_polar(radar_df, r='r', theta='theta', line_close=True, title="Player Tendency Radar")
        fig_radar.update_traces(fill='toself', line_color="#00d4ff", fillcolor="rgba(0, 212, 255, 0.3)")
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 100]),
                angularaxis=dict(gridcolor='rgba(255, 255, 255, 0.2)', linecolor='rgba(255, 255, 255, 0.2)'),
                bgcolor='rgba(0,0,0,0)', gridshape='linear'
            ),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with p_col2:
        champ_df = df.groupby('champion').agg(games=('win', 'count')).reset_index()
        fig_pie = px.pie(champ_df, values='games', names='champion', title="Champion Pool Distribution", hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma)
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- HIGHLIGHT REELS ---
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        losses_in_a_row = 0
        for win in df_chrono['win'].iloc[-3:]:
            if not win: losses_in_a_row += 1
            else: losses_in_a_row = 0
            
        if losses_in_a_row >= 3: st.error(f"📉 **Streak Alert:** Currently on a {losses_in_a_row}-game losing streak. Close the client, touch grass, and go to sleep.")
        elif losses_in_a_row > 0: st.warning("⚠️ **Recent Form:** You lost your last game. Don't rage queue.")
        else: st.success("📈 **Recent Form:** Stable. You are currently winning. Don't let it go to your head.")

    with h_col2:
        nemesis_df = df.groupby('enemy_champion')['deaths'].sum().reset_index()
        nemesis = nemesis_df.loc[nemesis_df['deaths'].idxmax()]
        st.error(f"🦹 **Toughest Matchup:** {nemesis['enemy_champion']} (Farmed you for {nemesis['deaths']} total deaths recently. Have you considered banning them?)")

    st.divider()

    # --- GLOBAL ANALYTICS ---
    st.subheader("📈 Macro Trends Dashboard")
    g_col1, g_col2 = st.columns(2)
    
    with g_col1: 
        fig_kda = go.Figure()
        fig_kda.add_trace(go.Scatter(x=df_chrono["game_creation"], y=df_chrono["kda"], mode="lines+markers", name="Player KDA", line=dict(color="#00d4ff")))
        fig_kda.add_trace(go.Scatter(x=df_chrono["game_creation"], y=df_chrono["enemy_kda"], mode="lines+markers", name="Opponent KDA", line=dict(color="#ff4b4b")))
        fig_kda.update_layout(title="KDA Ratio Evolution", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_kda, use_container_width=True)
        
    with g_col2: 
        fig_cs = go.Figure()
        fig_cs.add_trace(go.Scatter(x=df_chrono["game_creation"], y=df_chrono["cs"], mode="lines+markers", name="Player CS", line=dict(color="#00d4ff")))
        fig_cs.add_trace(go.Scatter(x=df_chrono["game_creation"], y=df_chrono["enemy_cs"], mode="lines+markers", name="Opponent CS", line=dict(color="#ff4b4b")))
        fig_cs.update_layout(title="Resource Generation (CS)", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_cs, use_container_width=True)

    g_col3, g_col4 = st.columns(2)
    with g_col3: 
        fig_kills = go.Figure()
        fig_kills.add_trace(go.Bar(x=df_chrono["game_creation"], y=df_chrono["kills"], name="Player Kills", marker_color="#00d4ff"))
        fig_kills.add_trace(go.Bar(x=df_chrono["game_creation"], y=df_chrono["enemy_kills"], name="Opponent Kills", marker_color="#ff4b4b"))
        fig_kills.update_layout(title="Combat Participation (Kills)", barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_kills, use_container_width=True)
        
    with g_col4:
        df_chrono['gold_color'] = df_chrono['gold_diff'].apply(lambda x: '#00cc96' if x > 0 else '#ef553b')
        fig_gold = go.Figure()
        fig_gold.add_trace(go.Bar(x=df_chrono["game_creation"], y=df_chrono["gold_diff"], marker_color=df_chrono['gold_color']))
        fig_gold.update_layout(title="Net Gold Differential", showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gold, use_container_width=True)
        
    st.divider()

    # --- MATCH DEEP DIVE ---
    st.subheader("🔬 Match Performance Breakdown")
    opts = [f"{'🏆 WIN' if r['win'] else '💀 LOSS'} | {r['champion']} vs {r['enemy_champion']} ({r['game_mode']})" for i, r in df.iterrows()]
    selected_idx = st.selectbox("Select match record:", range(len(opts)), format_func=lambda x: opts[x])
    cur = df.iloc[selected_idx]
    
    outcome_color = "#00cc96" if cur['win'] else "#ef553b"
    outcome_text = "VICTORY" if cur['win'] else "DEFEAT"
    
    st.markdown(f"<h1 style='text-align: center; color: {outcome_color}; letter-spacing: 2px;'>{outcome_text}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>Playing <b>{cur['champion']}</b> against <b>{cur['enemy_champion']}</b></h4>", unsafe_allow_html=True)
    st.divider()
    
    col_stats, col_ai = st.columns([1.5, 1])
    
    with col_stats:
        st.markdown("### 📈 Core Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("KDA", f"{cur['kills']}/{cur['deaths']}/{cur['assists']}", f"{round(cur['kda'], 2)} Ratio", delta_color="off")
        c2.metric("Farming (CS)", f"{cur['cs']}", f"{cur['cs'] - cur['enemy_cs']:+} vs Enemy")
        c3.metric("Gold Advantage", f"{cur['gold']:,} G", f"{cur['gold_diff']:+,} G")
        
        st.markdown("### 🤝 Team Impact")
        c4, c5, c6 = st.columns(3)
        c4.metric("Kill Participation", f"{cur['kp']}%")
        c5.metric("Vision Score", f"{cur['vision']}")
        c6.metric("Team K/D", f"{cur['team_kda']}")

    with col_ai:
        st.markdown("### 🤖 Automated Performance Judgment")
        st.info(f"**Macro Analysis:**\n\n{cur['roast']}")
        st.warning(f"**Itemization & Economy:**\n\n{cur['item_roast']}")