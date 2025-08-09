from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

def generate_pdf(invoice_number, client, date, items, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    filenames = []
    for doc_type in ["Internal", "Client", "DeliveryNote"]:
        filename = os.path.join(output_folder, f"{invoice_number}_{doc_type}.pdf")
        c = canvas.Canvas(filename, pagesize=A4)
        c.setFont("Helvetica", 14)
        c.drawString(100, 800, f"{doc_type} - Invoice #{invoice_number}")
        c.drawString(100, 780, f"Client: {client}")
        c.drawString(100, 760, f"Date: {date}")
        c.drawString(100, 740, "Items:")
        y = 720
        for item in items.split("\n"):
            c.drawString(120, y, item)
            y -= 20
        c.save()
        filenames.append(filename)
    return filenames
