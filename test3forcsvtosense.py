import pandas as pd

def summarize_chart_geometry(csv_path):
    df = pd.read_csv(csv_path)
    summary = []

    for page in df['page'].unique():
        page_df = df[df['page'] == page]
        summary.append(f"--- Analysis of Page {page} ---")
        
        # 1. Identify the Chart Canvas (The biggest rectangles)
        canvas = page_df[page_df['type'] == 'rectangle/bar'].sort_values(by='width', ascending=False).iloc[0]
        summary.append(f"Chart Area: Located between X({canvas['x0']}-{canvas['x0']+canvas['width']})")
        
        # 2. Identify Gridlines (Horizontal lines usually represent scale)
        h_lines = page_df[(page_df['type'] == 'line') & (page_df['y0'] == page_df['y1'])].sort_values(by='y0')
        if not h_lines.empty:
            summary.append(f"Detected {len(h_lines)} horizontal gridlines (Y-axis scale markers).")
            intervals = h_lines['y0'].diff().dropna().unique()
            summary.append(f"Gridline spacing (pixel units): {list(intervals)}")

        # 3. Identify Data Bars (Rectangles that are not the canvas)
        # We filter for smaller rectangles that usually represent data
        bars = page_df[(page_df['type'] == 'rectangle/bar') & (page_df['width'] < canvas['width']*0.5)]
        
        summary.append(f"Detected {len(bars)} potential data points (bars/markers):")
        for i, (idx, bar) in enumerate(bars.iterrows()):
            # We describe the bar's position relative to the left of the chart
            rel_pos = "Left" if bar['x0'] < canvas['x0'] + (canvas['width']/2) else "Right"
            summary.append(f" - Object {i+1}: Color {bar['color']}, Height {bar['height']} units, Positioned on the {rel_pos} side.")

    return "\n".join(summary)

# Run and Save
spatial_text = summarize_chart_geometry("chart_vectors.csv")
with open("llm_chart_prompt.txt", "w") as f:
    f.write(spatial_text)

print("Spatial text ready for LLM!")
