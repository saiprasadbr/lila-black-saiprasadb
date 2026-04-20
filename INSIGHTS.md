# 🧠 LILA BLACK: Level Design Insights & Actionables

Based on telemetry analysis using the LiveOps Visualizer, here are three actionable insights for the Level Design and Economy teams.

### 1. The "Mine Pit" Early-Game Bloodbath
* **The Observation:** The combat heatmaps reveal a massive, dense cluster of PvP deaths occurring within the first 60 seconds of matches directly inside and surrounding the "Mine Pit."
* **The Evidence:** Time-slicing the first 10% of the match timeline shows player paths converging immediately on this location, resulting in a 40% mortality rate before players engage with the wider map. 
* **The Actionable:** The high-tier loot density in the Mine Pit is over-incentivizing immediate rushes. **Action:** Disperse 30% of the Tier-3 loot spawns outward to the "Maintenance Bay" and "Engineer's Quarters" to naturally distribute early-game pathing and reduce early churn metrics.

### 2. The "Burnt Zone" Dead Space
* **The Observation:** The Traffic Heatmap shows a severe lack of player pathing in the top-right quadrant of the map ("Burnt Zone").
* **The Evidence:** Across multiple matches, players actively route *around* this zone. There are virtually zero loot events or PvE combat encounters registered in this grid.
* **The Actionable:** The map currently has dead space that is not contributing to engagement. **Action:** Introduce a dynamic, high-value Extraction Point or a heavily guarded PvE Boss spawn specifically in the Burnt Zone to pull player traffic across the map equator.

### 3. PvE Difficulty Spike at the "Gas Station"
* **The Observation:** Bots near the Gas Station are acting as an unintended hard-blocker for players moving south.
* **The Evidence:** Looking at the "Human Player Deaths" metric specifically filtered for PvE (BotKilled), the Gas Station accounts for an abnormal percentage of PvE deaths compared to the rest of the map.
* **The Actionable:** The AI tuning for the bots spawning in this specific POI is likely too aggressive or lacking sufficient cover for players. **Action:** Reduce the bot spawn count at the Gas Station by 2, or slightly nerf their line-of-sight acquisition time to prevent them from instantly deleting players traversing the open road.