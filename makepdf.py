from fpdf import FPDF

# Initialize PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

# 1. Add normal text
pdf.multi_cell(w=0, text="This is a dummy financial report for testing Qdrant ingestion. "
                        "The table below contains the revenue and profit margins for the last three fiscal years. "
                        "When queried, the RAG system should extract this text and the table image.")
pdf.ln(10) # Add a line break

# 2. Add Tabular Data
table_data = [
    ["Fiscal Year", "Revenue", "Profit Margin", "Status"],
    ["2023", "$10.5M", "12%", "Audited"],
    ["2024", "$14.2M", "15%", "Audited"],
    ["2025", "$18.9M", "18%", "Projected"]
]

# Draw the table with visible borders
with pdf.table(borders_layout="ALL") as table:
    for data_row in table_data:
        row = table.row()
        for datum in data_row:
            row.cell(datum)

# Save the file
pdf.output("dummy_test.pdf")
print("dummy_test.pdf created successfully!")