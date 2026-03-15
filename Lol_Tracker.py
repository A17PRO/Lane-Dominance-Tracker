import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import random

st.set_page_config(page_title="League of Legends Lane Analyzer", layout="wide")

st.sidebar.header("⚙️ Settings")
API_KEY = st.sidebar.text_input("🔑 Enter Riot API Key", type="password")
RIOT_ID = st.sidebar.text_input("👤 Enter Riot ID (e.g. Faker#KR1)")
REGION = st.sidebar.selectbox("🌍 Select Region", ["sea", "americas", "europe", "asia"], index=0)

@st.cache_data(ttl=86400)
def get_item_map():
    try:
        versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        latest = versions[0]
        items_data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/item.json").json()
        return {int(item_id): item_info['name'] for item_id, item_info in items_data['data'].items()}
    except Exception as e:
        return {}

ITEM_MAP = get_item_map()

QUEUE_MAP = {
    400: "Normal Draft",
    420: "Ranked Solo/Duo",
    430: "Normal Blind",
    440: "Ranked Flex",
    450: "ARAM",
    480: "Swiftplay",
    490: "Quickplay",
    700: "Clash",
    830: "Co-op vs AI",
    840: "Co-op vs AI",
    850: "Co-op vs AI",
    900: "URF",
    1700: "Arena",
}

def get_luna_remark(win, kills, deaths, assists, kda, cs, enemy_cs, vision, obj_damage, team_kills, team_deaths, team_assists, duration_sec, items):
    general_roast = ""
    item_roast = ""
    cs_diff = cs - enemy_cs
    duration_min = duration_sec / 60
    
    rest_of_team_kills = team_kills - kills
    rest_of_team_deaths = team_deaths - deaths
    rest_of_team_assists = team_assists - assists
    rest_of_team_kda = (rest_of_team_kills + rest_of_team_assists) / max(1, rest_of_team_deaths)
    
    kp = ((kills + assists) / max(1, team_kills)) * 100

    if win:
        if kda >= 4.0 and kp >= 50:
            general_roast = random.choice([
                f"A {round(kda, 2)} KDA with {round(kp)}% KP? Fine, I'll stroke your ego. You actually hard-carried these peasants. Don't expect a medal, though. ",
                f"Look at you, putting on your backpack and carrying {team_deaths} collective deaths across the finish line. An actual 1v9 miracle. "
            ])
        elif kda >= 2.0 and kda < 4.0:
            general_roast = random.choice([
                "You won, but let's not pretend you were the main character. You did *just* enough to not ruin it for the people actually trying. ",
                "A perfectly painfully average game. You existed, the nexus exploded, and you got your LP. Move along. "
            ])
        elif kda < 2.0 and rest_of_team_kda >= 2.5:
            general_roast = random.choice([
                f"You got carried so hard your spine must be shattered. Your team bailed out your miserable {kills}/{deaths} performance. Hit 'Honor' and queue up again, you parasite. ",
                f"Absolutely shameless. You played like a blindfolded toddler and still got the Win screen because your team dragged you there. "
            ])
        else:
            general_roast = random.choice([
                "A disgusting, sloppy mudfight of a win. You played like ass, your team played like ass, but the enemy somehow choked harder. ",
                "Everyone in this lobby deserved to lose, including you. But hey, a win is a win, even if it's ugly as sin. "
            ])
    else:
        if kda >= 3.0 and rest_of_team_kda < 1.5:
            general_roast = random.choice([
                f"Welcome to Elo Hell. You actually had hands this game, but your teammates were an all-you-can-eat buffet for the enemy. Tragic. ",
                f"You tried your best, but {rest_of_team_deaths} teammate deaths is too heavy for anyone to carry. Keep your head up, king/queen. "
            ])
        elif kda >= 1.5 and kda < 3.0:
            general_roast = random.choice([
                "Mediocre performance resulting in a mediocre loss. You weren't the absolute worst, but you sure as hell didn't do anything to stop the bleeding. ",
                "You were just a background character in your own tragic defeat. Do something impactful next time instead of just existing. "
            ])
        elif kda < 1.5 and rest_of_team_kda >= 2.0:
            general_roast = random.choice([
                f"Look in the mirror. YOU are the reason you lost. Your team was actually sweating, and you were out here running it down with {deaths} deaths. Unbelievable. ",
                f"Reportable offense, honestly. {kills}/{deaths}/{assists}? You single-handedly sabotaged four other people who just wanted to win. "
            ])
        else:
            general_roast = random.choice([
                f"Complete and utter team diff. You sucked, your team sucked, everybody sucked. {team_deaths} total deaths? Just uninstall. ",
                "An absolute slaughter. The enemy team treated you all like training dummies. Go play some Co-op vs AI to recover your dignity. "
            ])

    if cs_diff <= -40:
        general_roast += f"\n\nOh, and your farming is pathetic. You were down {abs(cs_diff)} CS. Are you clicking the minions or just staring at them?"
    if obj_damage < 2000 and kills >= 5:
        general_roast += "\n\nStop playing team deathmatch and hit the damn towers! Kills don't break the Nexus."

    real_items = [i for i in items if i != "Stealth Ward" and i != "Farsight Alteration" and i != "Oracle Lens" and i != "Unknown Item"]
    has_boots = any("Boots" in i or "Shoes" in i or "Greaves" in i or "Treads" in i for i in real_items)
    
    item_roast += f"**Your Final Build:** {', '.join(real_items) if real_items else 'Literally nothing. Were you AFK?'} \n\n"
    
    if duration_min > 30 and len(real_items) < 4:
        item_roast += "The game went past 30 minutes and you couldn't even afford 4 items. Your gold generation is completely nonexistent. "
    
    if not has_boots and duration_min > 15:
        item_roast += "You didn't buy upgraded boots. Walking around barefoot in the mid-game is exactly why you get caught out. "
        
    if vision < 15:
        item_roast += "I see absolutely zero investment in vision control. Buy a Control Ward next time so you stop dying to obvious ganks. "
    else:
        item_roast += "At least your build and vision aren't a total disaster. Small victories, right?"

    return general_roast.strip(), item_roast.strip()


def get_puuid(riot_id):
    if "#" not in riot_id: return None
    game_name, tag_line = riot_id.split("#", 1)
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200: return response.json().get("puuid")
    else:
        st.error(f"🚨 Could not find Riot ID. (Error: {response.status_code})")
        return None

def get_match_ids(puuid, count=10):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}&api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"🚨 Failed to get Match IDs. (Error: {response.status_code})")
        return []
    return response.json()

def get_match_data(match_id, target_puuid):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200: return None
    
    data = response.json()
    info = data['info']
    
    queue_id = info.get('queueId', 0)
    game_mode = QUEUE_MAP.get(queue_id, f"Other Mode ({queue_id})")
    duration = info.get('gameDuration', 0)
    
    try:
        me = next(p for p in info['participants'] if p['puuid'] == target_puuid)
        my_role = me['teamPosition']
        my_team_id = me['teamId']
        
        try:
            enemy = next(p for p in info['participants'] 
                         if p['teamPosition'] == my_role and p['teamId'] != my_team_id)
        except StopIteration:
            enemy = next(p for p in info['participants'] if p['teamId'] != my_team_id)

        my_team_kills = sum(p['kills'] for p in info['participants'] if p['teamId'] == my_team_id)
        my_team_deaths = sum(p['deaths'] for p in info['participants'] if p['teamId'] == my_team_id)
        my_team_assists = sum(p['assists'] for p in info['participants'] if p['teamId'] == my_team_id)
        
        enemy_team_kills = sum(p['kills'] for p in info['participants'] if p['teamId'] != my_team_id)
        enemy_team_deaths = sum(p['deaths'] for p in info['participants'] if p['teamId'] != my_team_id)
        enemy_team_assists = sum(p['assists'] for p in info['participants'] if p['teamId'] != my_team_id)

        kda = (me['kills'] + me['assists']) / max(1, me['deaths'])
        enemy_kda = (enemy['kills'] + enemy['assists']) / max(1, enemy['deaths'])
        
        cs = me['totalMinionsKilled'] + me['neutralMinionsKilled']
        enemy_cs = enemy['totalMinionsKilled'] + enemy['neutralMinionsKilled']
        vision_score = me.get('visionScore', 0)
        obj_damage = me.get('damageDealtToObjectives', 0)
        kp = round(((me['kills'] + me['assists']) / max(1, my_team_kills)) * 100) if my_team_kills > 0 else 0

        raw_items = [me.get(f'item{i}', 0) for i in range(7)]
        item_names = [ITEM_MAP.get(i, "Unknown Item") for i in raw_items if i != 0]

        gen_roast, item_roast = get_luna_remark(
            me['win'], me['kills'], me['deaths'], me['assists'], kda, cs, enemy_cs, 
            vision_score, obj_damage, my_team_kills, my_team_deaths, my_team_assists, duration, item_names
        )

        return {
            "game_creation": info['gameCreation'], "game_mode": game_mode, "duration": duration,
            "champion": me['championName'], "enemy_champion": enemy['championName'], "win": me['win'],
            "kills": me['kills'], "deaths": me['deaths'], "assists": me['assists'], "kda": kda, "kp": kp,
            "enemy_kills": enemy['kills'], "enemy_deaths": enemy['deaths'], "enemy_assists": enemy['assists'], "enemy_kda": enemy_kda,
            "cs": cs, "enemy_cs": enemy_cs, "gold": me['goldEarned'], "enemy_gold": enemy['goldEarned'],
            "vision_score": vision_score, "obj_damage": obj_damage,
            "my_team_kda": f"{my_team_kills} / {my_team_deaths} / {my_team_assists}",
            "enemy_team_kda": f"{enemy_team_kills} / {enemy_team_deaths} / {enemy_team_assists}",
            "gen_roast": gen_roast, "item_roast": item_roast
        }
    except Exception:
        return None


st.title("🎮 League of Legends Lane Dominance Tracker")

if not API_KEY or not RIOT_ID:
    st.warning("👈 Stick your Riot API Key and Riot ID in the sidebar so we can actually do something.")
elif "#" not in RIOT_ID:
    st.error("Your Riot ID needs the hashtag! (Example: Hide on bush#KR1)")
else:
    with st.spinner(f"Hunting down {RIOT_ID}..."):
        USER_PUUID = get_puuid(RIOT_ID)
        
        if USER_PUUID:
            st.success("Target acquired. Ripping match history, macro stats, and judging your gameplay...")
            match_ids = get_match_ids(USER_PUUID, count=10)
            
            if match_ids:
                raw_data = []
                progress_bar = st.progress(0)
                
                for i, mid in enumerate(match_ids):
                    data = get_match_data(mid, USER_PUUID)
                    if data:
                        raw_data.append(data)
                    progress_bar.progress((i + 1) / len(match_ids))
                    time.sleep(0.1) 
                
                if not raw_data:
                    st.error("Pulled the matches, but failed to parse stats. Probably a weird game mode.")
                else:
                    df = pd.DataFrame(raw_data)
                    df['game_creation'] = pd.to_datetime(df['game_creation'], unit='ms')
                    df = df.sort_values('game_creation', ascending=True)

                    df['gold_diff'] = df['gold'] - df['enemy_gold']

                    winrate = round(df["win"].mean() * 100, 1)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Winrate", f"{winrate}%")
                    col2.metric("Avg KDA", round(df["kda"].mean(), 2))
                    col3.metric("CS/Match", int(df["cs"].mean()))

                    st.divider()

                    st.subheader("📊 Performance Analytics")
                    
                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        fig_kda = px.line(df, x="game_creation", y=["kda", "enemy_kda"], title="KDA Evolution", markers=True, color_discrete_map={"kda": "#00d4ff", "enemy_kda": "#ff4b4b"})
                        st.plotly_chart(fig_kda, use_container_width=True)
                    with g_col2:
                        fig_cs = px.line(df, x="game_creation", y=["cs", "enemy_cs"], title="CS Farming Trends", markers=True, color_discrete_map={"cs": "#00d4ff", "enemy_cs": "#ff4b4b"})
                        st.plotly_chart(fig_cs, use_container_width=True)

                    g_col3, g_col4 = st.columns(2)
                    with g_col3:
                        fig_kills = px.bar(df, x="game_creation", y=["kills", "enemy_kills"], barmode="group", title="Raw Kills", color_discrete_map={"kills": "#00d4ff", "enemy_kills": "#ff4b4b"})
                        st.plotly_chart(fig_kills, use_container_width=True)
                    with g_col4:
                        df['gold_color'] = df['gold_diff'].apply(lambda x: 'Ahead' if x > 0 else 'Behind')
                        fig_gold = px.bar(df, x="game_creation", y="gold_diff", title="Gold Advantage", color="gold_color", color_discrete_map={"Ahead": "#00cc96", "Behind": "#ef553b"})
                        st.plotly_chart(fig_gold, use_container_width=True)

                    st.divider()

                    st.subheader("📜 The Judgment (Match History)")
                    
                    df_history = df.sort_values('game_creation', ascending=False)
                    
                    for index, row in df_history.iterrows():
                        status = "🏆 VICTORY" if row['win'] else "💀 DEFEAT"
                        
                        with st.expander(f"{status} | {row['game_mode']} | {row['champion']} vs {row['enemy_champion']} | KDA: {row['kills']}/{row['deaths']}/{row['assists']}"):
                            
                            tab1, tab2, tab3 = st.tabs(["📊 Game Stats", "⚔️ Team Diff", "🤖 Final Coaching & Items"])
                            
                            with tab1:
                                st.write(f"**Champion:** {row['champion']}")
                                st.write(f"**KDA:** {row['kills']} / {row['deaths']} / {row['assists']} ({round(row['kda'], 2)})")
                                st.write(f"**Kill Participation:** {row['kp']}%")
                                st.write(f"**CS:** {row['cs']} (Opponent: {row['enemy_cs']})")
                                st.write(f"**Vision Score:** {row['vision_score']}")
                                st.write(f"**Objective Damage:** {row['obj_damage']}")
                                
                            with tab2:
                                st.write(f"**Your Team (K/D/A):** {row['my_team_kda']}")
                                st.write(f"**Enemy Team (K/D/A):** {row['enemy_team_kda']}")
                                if row['win']:
                                    st.success("Your team actually managed to destroy the nexus. A miracle.")
                                else:
                                    st.error("Absolute canyon of a team diff.")
                                
                            with tab3:
                                st.markdown("### Gameplay Verdict")
                                st.warning(row['gen_roast'])
                                st.markdown("### Itemization & Vision")
                                st.info(row['item_roast'])