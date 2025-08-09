import sys
import os
from PyQt6 import QtWidgets, QtCore
from db import init_db, add_invoice, get_invoices
from pdfgen import generate_pdf

class InvoiceApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigitalInvoice_Manager")
        self.setGeometry(200, 200, 800, 600)
        self.layout = QtWidgets.QVBoxLayout(self)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Number", "Client", "Date", "Folder"])
        self.layout.addWidget(self.table)

        # Form
        form_layout = QtWidgets.QFormLayout()
        self.number_input = QtWidgets.QLineEdit()
        self.client_input = QtWidgets.QLineEdit()
        self.date_input = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.items_input = QtWidgets.QTextEdit()
        form_layout.addRow("Number:", self.number_input)
        form_layout.addRow("Client:", self.client_input)
        form_layout.addRow("Date:", self.date_input)
        form_layout.addRow("Items:", self.items_input)
        self.layout.addLayout(form_layout)

        # Buttons
        self.save_button = QtWidgets.QPushButton("Save Invoice")
        self.save_button.clicked.connect(self.save_invoice)
        self.layout.addWidget(self.save_button)

        self.load_invoices()

    def load_invoices(self):
        self.table.setRowCount(0)
        for row_data in get_invoices():
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data[1:]):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))

    def save_invoice(self):
        number = self.number_input.text()
        client = self.client_input.text()
        date = self.date_input.date().toString("yyyy-MM-dd")
        items = self.items_input.toPlainText()
        folder = os.path.join("data", number)
        generate_pdf(number, client, date, items, folder)
        add_invoice(number, client, date, items, folder)
        self.load_invoices()
        QtWidgets.QMessageBox.information(self, "Saved", "Invoice saved successfully!")

if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec())
