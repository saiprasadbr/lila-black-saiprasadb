# LILA BLACK: System Architecture & Engineering Defense

## 1. Tech Stack Selection
* **Streamlit:** Chosen for its unmatched speed in building internal tooling. It allows data scientists and PMs to stand up interactive UIs without needing to write React/Node.js boilerplate.
* **Plotly:** Chosen over Matplotlib/Seaborn because of its native JavaScript engine. To analyze Level Design, developers need to zoom, pan, and watch animations at 60fps. Plotly handles this entirely client-side without lagging the Python server.
* **Pandas/PyArrow:** Chosen for memory-efficient handling of large Parquet telemetry files.

## 2. Data Flow
1. **Ingestion:** `@st.cache_data` is used to load and concatenate the daily Parquet files into memory only once, drastically reducing load times on filter changes.
2. **Filtering:** Data is sequentially filtered by Map -> Match ID -> Player ID to minimize the size of the dataframe before passing it to the rendering engine.
3. **Animation Prep:** For video replay, the dataframe is sliced into 60 cumulative time-steps. Invisible "dummy" data is injected into Frame 1 to bypass a known Plotly bug where SVG groups (like Kill/Loot icons) fail to render if they don't exist in the first millisecond of the animation.

## 3. Coordinate Mapping Math
Mapping 3D world coordinates `(x, y, z)` to a 2D image `(pixel_x, pixel_y)` requires normalizing the data against the map's specific scale and origin offsets. 
* *Note: The `y` axis (vertical height) is discarded for top-down 2D mapping.*
1. **Normalize:** We calculate the percentage position `(u, v)` relative to the map's origin (`ox`, `oz`) and total `scale`.
   `u = (x - ox) / scale`
   `v = (z - oz) / scale`
2. **Translate to Pixels:** We multiply the normalized float by the actual pixel dimensions of the loaded `PIL` image. The `v` axis is inverted `(1 - v)` because computer graphics render from top-left, while game engines render from bottom-left.
   `pixel_x = u * img_width`
   `pixel_y = (1 - v) * img_height`

## 4. Trade-offs & Assumptions
| Feature/Decision | The Trade-off |
| :--- | :--- |
| **Animation Engine** | Streamlit `st.rerun()` loops allow for dynamic Python text updates but cause aggressive screen flickering. I opted for **Plotly's Native JS Engine**. *Trade-off:* Buttery smooth map rendering, but required building a custom HUD annotation loop because JS locks legend text on load. |
| **Bot Identification** | *Assumption:* I assumed `event == 'Position'` strictly denoted a human client, while `BotPosition` denoted AI. Therefore, human-only tracking filters inherently drop bot data. |
| **Time-slicing vs Real-time** | *Trade-off:* Slicing the animation into exactly 60 distinct frames standardizes playback speed across different match lengths, but slightly generalizes the exact millisecond timestamps of events. |