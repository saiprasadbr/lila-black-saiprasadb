import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os

# --- 1. SETTINGS & INITIALIZATION ---
MAP_CONFIGS = {
    'AmbroseValley': {'scale': 900, 'ox': -370, 'oz': -473, 'img': 'AmbroseValley_Minimap.png'},
    'GrandRift': {'scale': 581, 'ox': -290, 'oz': -290, 'img': 'GrandRift_Minimap.png'},
    'Lockdown': {'scale': 1000, 'ox': -500, 'oz': -500, 'img': 'Lockdown_Minimap.jpg'}
}

if 'last_match_loaded' not in st.session_state:
    st.session_state.last_match_loaded = None

def map_to_pixel(df, map_id, img_width, img_height):
    c = MAP_CONFIGS[map_id]
    df['u'] = (df['x'] - c['ox']) / c['scale']
    df['v'] = (df['z'] - c['oz']) / c['scale']
    df['pixel_x'] = df['u'] * img_width
    df['pixel_y'] = (1 - df['v']) * img_height 
    return df

# --- THE UPGRADED DATA DUPLICATOR ---
@st.cache_data
def build_animation_dataframe(df, num_frames=60):
    if df.empty: return pd.DataFrame(), {}, {}
    
    df = df.sort_values('ts').reset_index(drop=True)
    df['uid'] = df.index.astype(str) 
    
    min_ts, max_ts = df['ts'].min(), df['ts'].max()
    time_step = (max_ts - min_ts) / num_frames if max_ts > min_ts else 1
    
    def get_cat(row):
        if row['event'] == 'Position': return f"👤 Player: {str(row['user_id'])[:6]}"
        if row['event'] == 'BotPosition': return "🤖 Bot (PvE)"
        if row['event'] in ['Kill', 'BotKill']: return "⭐ Combat: Kill"
        if row['event'] in ['Killed', 'BotKilled', 'KilledByStorm']: return "💀 Combat: Death"
        if row['event'] == 'Loot': return "💎 Loot"
        return "Other"
        
    df['Legend'] = df.apply(get_cat, axis=1)
    
    size_map = {"🤖 Bot (PvE)": 5, "⭐ Combat: Kill": 12, "💀 Combat: Death": 12, "💎 Loot": 8, "Other": 5}
    df['marker_size'] = df['Legend'].map(lambda x: size_map.get(x, 5))
    
    frames = []
    frame_labels = {} 
    frame_stats = {} 
    
    for i in range(1, num_frames + 1):
        current_time = min_ts + (time_step * i)
        prev_time = min_ts + (time_step * (i-1))
        
        frame_df = df[df['ts'] <= current_time].copy()
        if not frame_df.empty:
            frame_df['video_frame'] = i
            frames.append(frame_df)
            
            frame_stats[i] = {
                "kills": len(frame_df[frame_df['Legend'] == '⭐ Combat: Kill']),
                "deaths": len(frame_df[frame_df['Legend'] == '💀 Combat: Death']),
                "loot": len(frame_df[frame_df['Legend'] == '💎 Loot'])
            }
            
        exact_events = df[(df['ts'] > prev_time) & (df['ts'] <= current_time)] if i > 1 else df[df['ts'] <= current_time]
        
        icon_list = []
        if exact_events['Legend'].str.contains("⭐ Combat: Kill").any(): icon_list.append("<b><span style='color:#FFD700; font-size:16px;'>★</span></b>")
        if exact_events['Legend'].str.contains("💀 Combat: Death").any(): icon_list.append("<b><span style='color:#FF0000; font-size:14px;'>✖</span></b>")
        if exact_events['Legend'].str.contains("💎 Loot").any(): icon_list.append("<b><span style='color:#32CD32; font-size:16px;'>♦</span></b>")
        
        icons_str = "<br>".join(icon_list)
        frame_labels[i] = f"{i}<br>{icons_str}" if icons_str else str(i)
            
    anim_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    if not anim_df.empty:
        unique_legends = anim_df['Legend'].unique()
        dummy_rows = []
        for cat in unique_legends:
            dummy_rows.append({
                'video_frame': 1, 'Legend': cat, 'pixel_x': -9999, 'pixel_y': -9999, 
                'marker_size': 0.1, 'uid': f"dummy_{cat}", 'user_id': 'sys', 'event': 'sys'
            })
        anim_df = pd.concat([pd.DataFrame(dummy_rows), anim_df], ignore_index=True)

    return anim_df, frame_labels, frame_stats

# --- 2. DATA LOADING ---
@st.cache_data
def load_data(date_folder):
    folder_path = os.path.join("player_data", date_folder)
    frames = []
    if not os.path.exists(folder_path): return pd.DataFrame()

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for f in files: 
        try:
            table = pq.read_table(os.path.join(folder_path, f))
            frames.append(table.to_pandas())
        except Exception: continue
            
    if not frames: return pd.DataFrame()
    final_df = pd.concat(frames, ignore_index=True)
    final_df['event'] = final_df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
    return final_df

# --- 3. USER INTERFACE ---
st.set_page_config(layout="wide", page_title="LILA BLACK Level Design Tool")
st.title("🕹️ Player Journey Visualization Tool")

st.sidebar.header("🗺️ Global Filters")
selected_map = st.sidebar.selectbox("Select Map", list(MAP_CONFIGS.keys()), key="select_map")
selected_date = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"], key="select_date")

view_mode = st.sidebar.radio("Map Data Layer", ["Player Paths", "Traffic Heatmap", "Combat Heatmap"], key="view_mode")

# --- 4. THE LOGIC & SIDEBAR ---
df = load_data(selected_date)
match_view = "Static Interactive Map"

if not df.empty:
    
    map_df = df[df['map_id'] == selected_map].copy()
    
    if not map_df.empty:
        
        humans_only = map_df[map_df['event'] == 'Position']
        match_human_counts = humans_only.groupby('match_id')['user_id'].nunique()
        multiplayer_matches = match_human_counts[match_human_counts > 1]
        
        if not multiplayer_matches.empty:
            with st.sidebar.expander("🔥 View Multiplayer Match IDs"):
                display_df = multiplayer_matches.reset_index()
                display_df.columns = ["Match ID", "Humans"]
                st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.sidebar.header("🎯 Match Filters")
        unique_matches = map_df['match_id'].unique().tolist()
        selected_match = st.sidebar.selectbox("Select Specific Match", ["All Matches"] + unique_matches, key="select_match")
        
        if selected_match != "All Matches":
            map_df = map_df[map_df['match_id'] == selected_match]
            
            human_users_in_match = map_df[map_df['event'] == 'Position']['user_id'].dropna().unique().tolist()
            
            if st.session_state.last_match_loaded != selected_match:
                human_count = len(human_users_in_match)
                if human_count > 1:
                    st.toast(f"Multiplayer Match Loaded: {human_count} Humans Detected!", icon="🔥")
                else:
                    st.toast("Solo Match Loaded.", icon="👤")
                st.session_state.last_match_loaded = selected_match
            
            st.sidebar.markdown("### 🎬 Replay Engine")
            match_view = st.sidebar.radio("Playback Mode", ["Static Interactive Map", "Smooth Video Replay"], key="match_view")
            
            selected_user_to_track = st.sidebar.selectbox("Track Specific Player", ["All Players"] + human_users_in_match, key="select_user_map")
            
            if selected_user_to_track != "All Players":
                map_df = map_df[map_df['user_id'] == selected_user_to_track]
        
        st.sidebar.divider()
        st.sidebar.header("👤 Player Stats")
        all_humans = df[df['event'] == 'Position']['user_id'].dropna().unique().tolist()
        lookup_player = st.sidebar.selectbox("Look up Player Profile", ["Select a Player..."] + all_humans, key="lookup_player")
        
        if lookup_player != "Select a Player...":
            player_history_df = df[df['user_id'] == lookup_player]
            stat_rows = []
            for m_id in player_history_df['map_id'].unique():
                m_data = player_history_df[player_history_df['map_id'] == m_id]
                stat_rows.append({
                    "Map": m_id, "Matches": m_data['match_id'].nunique(),
                    "PvP Kills": len(m_data[m_data['event'] == 'Kill']), "PvE Kills": len(m_data[m_data['event'] == 'BotKill']),
                    "PvP Deaths": len(m_data[m_data['event'] == 'Killed']), "PvE Deaths": len(m_data[m_data['event'] == 'BotKilled']),
                    "Storm Deaths": len(m_data[m_data['event'] == 'KilledByStorm']), "Loot": len(m_data[m_data['event'] == 'Loot'])
                })
            if stat_rows: st.sidebar.dataframe(pd.DataFrame(stat_rows).set_index("Map"), use_container_width=True)

        st.sidebar.divider()
        map_df = map_df.sort_values('ts')
        
        st.markdown("### Match Analytics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Events", len(map_df))
        col2.metric("Tracked Human Players", map_df[map_df['event'] == 'Position']['user_id'].nunique())
        col3.metric(label="Total Eliminations Scored", value=len(map_df[map_df['event'].isin(['Kill', 'BotKill'])]), help="Enemies eliminated.")
        col4.metric(label="Human Player Deaths", value=len(map_df[map_df['event'].isin(['Killed', 'BotKilled', 'KilledByStorm'])]), help="Times human players died.")
        st.divider() 
            
        img_path = os.path.join("player_data", "minimaps", MAP_CONFIGS[selected_map]['img'])
        try:
            bg_image = Image.open(img_path)
            img_width, img_height = bg_image.size 
            map_df = map_to_pixel(map_df, selected_map, img_width, img_height)
            
            # --- RENDER MODES ---
            if selected_match != "All Matches" and match_view == "Smooth Video Replay":
                
                anim_df, frame_labels, frame_stats = build_animation_dataframe(map_df, num_frames=60)
                
                if not anim_df.empty:
                    color_map = {"🤖 Bot (PvE)": "#FF007F", "⭐ Combat: Kill": "#FFD700", "💀 Combat: Death": "#FF0000", "💎 Loot": "#32CD32", "Other": "#FFFFFF"}
                    symbol_map = {"🤖 Bot (PvE)": "circle", "⭐ Combat: Kill": "star", "💀 Combat: Death": "x", "💎 Loot": "diamond", "Other": "circle"}
                    
                    palette = px.colors.qualitative.Alphabet 
                    unique_humans = [c for c in anim_df['Legend'].unique() if "👤 Player:" in c]
                    
                    player_hud_colors = {}
                    for i, cat_name in enumerate(unique_humans):
                        assigned_color = palette[i % len(palette)]
                        color_map[cat_name] = assigned_color
                        symbol_map[cat_name] = "circle"
                        player_hud_colors[cat_name] = assigned_color
                        
                    fig = px.scatter(
                        anim_df, x='pixel_x', y='pixel_y', 
                        animation_frame='video_frame', animation_group='uid', 
                        color='Legend', symbol='Legend', size='marker_size',
                        color_discrete_map=color_map, symbol_map=symbol_map,
                        size_max=12, opacity=0.8, hover_data=['user_id', 'event']
                    )
                    
                    fig.update_layout(
                        title=f"Native Video Replay (Match: {selected_match})", width=900, height=800, margin=dict(l=0, r=0, t=40, b=0),
                        images=[dict(
                            source=bg_image, xref="x", yref="y", 
                            x=0, y=0, # 🛠️ THE FIX: 0 is the physical top of our reversed axis!
                            sizex=img_width, sizey=img_height, 
                            sizing="stretch", opacity=1.0, layer="below",
                            xanchor="left", yanchor="top" 
                        )],
                        xaxis=dict(range=[0, img_width], visible=False, autorange=False, fixedrange=True),
                        yaxis=dict(range=[img_height, 0], visible=False, autorange=False, fixedrange=True)
                    )
                    
                    def build_hud(stats_dict):
                        hud_str = "<b>Live Match Stats</b><br><br>"
                        hud_str += f"<span style='color:#FFD700;'>⭐ Kills: {stats_dict['kills']}</span><br>"
                        hud_str += f"<span style='color:#FF0000;'>💀 Deaths: {stats_dict['deaths']}</span><br>"
                        hud_str += f"<span style='color:#32CD32;'>💎 Loot: {stats_dict['loot']}</span><br><br>"
                        hud_str += "<b>Active Players:</b><br>"
                        for p_name, p_hex in player_hud_colors.items():
                            hud_str += f"<span style='color:{p_hex};'>{p_name}</span><br>"
                        return hud_str
                    
                    hud_layout = dict(
                        x=img_width * 0.98, y=img_height * 0.02, xref="x", yref="y",
                        text=build_hud(frame_stats.get(1, {"kills":0, "deaths":0, "loot":0})),
                        showarrow=False, align="left", bgcolor="rgba(0,0,0,0.7)", 
                        font=dict(color="white", size=14), bordercolor="white", borderwidth=1
                    )
                    fig.update_layout(annotations=[hud_layout])
                    
                    for frame in fig.frames:
                        f_val = int(frame.name)
                        f_hud = hud_layout.copy()
                        f_hud["text"] = build_hud(frame_stats.get(f_val, {"kills":0, "deaths":0, "loot":0}))
                        frame.layout.annotations = [f_hud]
                    
                    play_action = fig.layout.updatemenus[0].buttons[0].args
                    pause_action = fig.layout.updatemenus[0].buttons[1].args
                    play_action[1]["frame"]["duration"] = 150 
                    fig.layout.updatemenus[0].buttons = [dict(label="▶ / ⏸ Play/Pause", method="animate", args=play_action, args2=pause_action)]
                    
                    if fig.layout.sliders:
                        fig.layout.sliders[0].pad = {"t": 80} 
                        for step in fig.layout.sliders[0].steps:
                            try:
                                frame_val = int(step.args[0][0])
                                step.label = frame_labels.get(frame_val, str(frame_val))
                            except (ValueError, IndexError): pass
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Not enough data to animate this selection.")

            else:
                # --- NORMAL STATIC/SLIDER MODE ---
                if selected_match != "All Matches":
                    max_events = len(map_df)
                    if max_events > 1:
                        start_step, end_step = st.slider("⏱️ Isolate Match Time Window", min_value=1, max_value=max_events, value=(1, max_events), key="timeline_slider")
                        map_df = map_df.iloc[start_step-1:end_step]
                
                paths_df = map_df[map_df['event'].isin(['Position', 'BotPosition'])]
                fig = px.imshow(bg_image)
                
                if view_mode == "Player Paths": 
                    human_df = paths_df[paths_df['event'] == 'Position']
                    if not human_df.empty:
                        color_palette = px.colors.qualitative.Alphabet 
                        unique_humans = human_df['user_id'].unique()
                        
                        for i, user_id in enumerate(unique_humans):
                            user_df = human_df[human_df['user_id'] == user_id]
                            assigned_color = color_palette[i % len(color_palette)]
                            
                            kill_count = len(map_df[(map_df['user_id'] == user_id) & (map_df['event'].isin(['Kill', 'BotKill']))])
                            pvp_deaths = len(map_df[(map_df['user_id'] == user_id) & (map_df['event'] == 'Killed')])
                            pve_deaths = len(map_df[(map_df['user_id'] == user_id) & (map_df['event'] == 'BotKilled')])
                            storm_deaths = len(map_df[(map_df['user_id'] == user_id) & (map_df['event'] == 'KilledByStorm')])
                            loot_count = len(map_df[(map_df['user_id'] == user_id) & (map_df['event'] == 'Loot')])
                            
                            legend_label = f"<b><span style='color:{assigned_color};'>👤 {str(user_id)[:6]}</span></b> | ⭐:{kill_count} | 💀:{pvp_deaths+pve_deaths+storm_deaths} | 💎:{loot_count}"
                            fig.add_scatter(x=user_df['pixel_x'], y=user_df['pixel_y'], mode='markers', name=legend_label, marker=dict(color=assigned_color, size=5), hovertext=user_df['user_id'])
                        
                    bot_df = paths_df[paths_df['event'] == 'BotPosition']
                    if not bot_df.empty:
                        fig.add_scatter(x=bot_df['pixel_x'], y=bot_df['pixel_y'], mode='markers', name='🤖 Bots (PvE)', marker=dict(color='#FF007F', size=5), hovertext=bot_df['user_id'])
                    
                    event_styles = {
                        'Kill': {'color': '#FFD700', 'symbol': 'star', 'name': '⭐ Combat: Kill (PvP)'}, 'BotKill': {'color': '#FFD700', 'symbol': 'star', 'name': '⭐ Combat: Kill (PvE)'},
                        'Killed': {'color': '#FF0000', 'symbol': 'x', 'name': '💀 Combat: Death (PvP)'}, 'BotKilled': {'color': '#FF0000', 'symbol': 'x', 'name': '💀 Combat: Death (PvE)'},
                        'KilledByStorm': {'color': '#8A2BE2', 'symbol': 'triangle-up', 'name': '💀 Storm Death'}, 'Loot': {'color': '#32CD32', 'symbol': 'diamond', 'name': '💎 Loot'}
                    }

                    for ev_name, style in event_styles.items():
                        ev_df = map_df[map_df['event'] == ev_name]
                        if not ev_df.empty:
                            fig.add_scatter(x=ev_df['pixel_x'], y=ev_df['pixel_y'], mode='markers', name=style['name'], marker=dict(color=style['color'], size=10, symbol=style['symbol'], opacity=0.6, line=dict(width=1, color='white')))
                            
                elif view_mode == "Traffic Heatmap":
                    fig.add_trace(go.Histogram2dContour(x=paths_df['pixel_x'], y=paths_df['pixel_y'], colorscale='Hot', reversescale=True, opacity=0.6, showscale=False))
                elif view_mode == "Combat Heatmap":
                    combat_df = map_df[map_df['event'].isin(['Kill', 'Killed', 'BotKill', 'BotKilled'])]
                    if not combat_df.empty:
                        fig.add_trace(go.Histogram2dContour(x=combat_df['pixel_x'], y=combat_df['pixel_y'], colorscale='Reds', opacity=0.7, showscale=False))

                title_text = f"Live Visualization (Match: {selected_match})" if selected_match != "All Matches" else "Aggregated Visualization"
                fig.update_layout(title=title_text, width=800, height=800, margin=dict(l=0, r=0, t=40, b=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
                st.plotly_chart(fig, use_container_width=True)
            
        except FileNotFoundError:
            st.error(f"Could not find the minimap image at: {img_path}. Check your minimaps folder!")
    else:
        st.warning("No data found for this specific map. Try changing the global filters!")
