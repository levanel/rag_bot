import pdfplumber
import pandas as pd

def extract_vectors_to_csv(pdf_path, output_csv):
    vector_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Extract Rectangles (often used for Bar Charts)
            for rect in page.rects:
                vector_data.append({
                    "page": i + 1,
                    "type": "rectangle/bar",
                    "x0": rect['x0'], 
                    "y0": rect['y0'],
                    "width": rect['width'],
                    "height": rect['height'],
                    "color": rect.get('non_stroking_color') # Helps identify different series
                })
            
            # Extract Lines (often used for Line Charts or Axes)
            for line in page.lines:
                vector_data.append({
                    "page": i + 1,
                    "type": "line",
                    "x0": line['x0'],
                    "y0": line['y0'],
                    "x1": line['x1'],
                    "y1": line['y1'],
                    "width": None,
                    "height": None,
                    "color": line.get('stroking_color')
                })

    # Save to CSV
    df = pd.DataFrame(vector_data)
    df.to_csv(output_csv, index=False)
    print(f"Vector data saved to {output_csv}")

extract_vectors_to_csv("sdf.pdf", "chart_vectors.csv")

