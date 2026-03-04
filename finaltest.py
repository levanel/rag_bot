import pdfplumber

def final_attempt_parser(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i+1} Map ---")
            words = page.extract_words()
            bars = [r for r in page.rects if r['width'] < 100]

            for bar in bars:
                # Find the 'closest' word by calculating distance to the bar's center
                bar_center_x = (bar['x0'] + bar['x1']) / 2
                bar_center_y = (bar['y0'] + bar['y1']) / 2
                
                # Sort all words on the page by how close they are to this specific bar
                closest_words = sorted(words, key=lambda w: 
                    abs((w['x0'] + w['x1'])/2 - bar_center_x) + 
                    abs((w['top'] + w['bottom'])/2 - bar_center_y)
                )

                # Get the top 2 closest words (one might be the value, one the label)
                neighbors = [w['text'] for w in closest_words[:2]]
                
                print(f"Bar at X={round(bar['x0'])} | Height: {round(bar['height'], 2)} | Likely Labels: {neighbors}")

# Replace with your actual filename
final_attempt_parser("123.pdf")
