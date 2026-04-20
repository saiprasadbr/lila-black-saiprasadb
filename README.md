# 🕹️ LILA BLACK: LiveOps & Level Design Dashboard

A robust, web-based telemetry visualization tool built for the Level Design team at LILA Games. This dashboard translates raw Parquet telemetry data into an interactive, visual replay engine, allowing designers to track player paths, identify combat hotspots, and understand map flow.

## 🚀 Features
* **Interactive Mini-maps:** Accurately maps world coordinates `(x, z)` to pixel dimensions across three unique maps (Ambrose Valley, Grand Rift, Lockdown).
* **Smooth Video Replay Engine:** A buttery-smooth, 60fps JavaScript animation engine with a custom HUD that tracks live kills, deaths, and loot.
* **Contextual Emojis:** The timeline scrubber is dynamically stamped with emojis (⭐, 💀, 💎) to instantly highlight when major events happen during a match.
* **Player Profiling:** A global search tool to audit individual player performance (K/D ratios, looting habits) across all maps and matches.
* **Dual-Layer Analytics:** Toggle between individual player paths and aggregated heatmaps (Traffic & Combat).

## 🛠️ Tech Stack
* **Python 3.x:** Core backend logic.
* **Streamlit:** UI framework, state management, and rapid dashboard deployment.
* **Pandas & PyArrow:** High-performance data ingestion and transformation of Parquet files.
* **Plotly Express / Graph Objects:** Heavy-lifting for canvas rendering and native JavaScript video animations.

## ⚙️ Local Setup Instructions
1. Clone this repository.
2. Ensure you have Python installed, then install the requirements:
   `pip install streamlit pandas pyarrow plotly pillow`
3. Unzip the `player_data` folder into the root directory of the project.
4. Run the application:
   `streamlit run app.py`