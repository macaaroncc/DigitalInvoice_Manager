import sys
import os
import shutil
from PyQt6 import QtWidgets, QtCore, QtGui
from db import init_db, add_invoice, get_invoices

class DropArea(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            border: 2px dashed #aaa;
            border-radius: 10px;
            background-color: #fafafa;
        """)
        self.label = QtWidgets.QLabel("Drag and drop PDF files here", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.pdf'):
                files.append(path)
        if files:
            self.filesDropped.emit(files)

class InvoiceApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigitalInvoice_Manager")
        self.setGeometry(200, 200, 800, 600)
        self.layout = QtWidgets.QVBoxLayout(self)

        # Table of invoices
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Number", "Client", "Date", "Folder"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_invoice_folder)
        self.layout.addWidget(self.table)

        # Form inputs
        form_layout = QtWidgets.QFormLayout()
        self.number_input = QtWidgets.QLineEdit()
        self.client_input = QtWidgets.QLineEdit()
        self.date_input = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        form_layout.addRow("Invoice Number:", self.number_input)
        form_layout.addRow("Client:", self.client_input)
        form_layout.addRow("Date:", self.date_input)

        self.layout.addLayout(form_layout)

        # Drop area for PDFs
        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self.handle_files_dropped)
        self.layout.addWidget(self.drop_area)

        # Save button
        self.save_button = QtWidgets.QPushButton("Create Invoice Record")
        self.save_button.clicked.connect(self.create_invoice)
        self.layout.addWidget(self.save_button)

        self.current_invoice_folder = None

        self.load_invoices()

    def load_invoices(self):
        self.table.setRowCount(0)
        for row_data in get_invoices():
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data[1:]):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))

    def create_invoice(self):
        number = self.number_input.text().strip()
        client = self.client_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")

        if not number:
            QtWidgets.QMessageBox.warning(self, "Error", "Invoice number is required")
            return

        folder = os.path.join("data", number)
        if not os.path.exists(folder):
            os.makedirs(folder)

        add_invoice(number, client, date, "", folder)
        self.current_invoice_folder = folder
        self.load_invoices()

        QtWidgets.QMessageBox.information(self, "Invoice Created", f"Invoice record created.\nNow drag and drop PDFs into the area below to add them to the invoice folder:\n{folder}")

    def handle_files_dropped(self, files):
        if not self.current_invoice_folder:
            QtWidgets.QMessageBox.warning(self, "No Invoice Selected", "Please create or select an invoice first")
            return

        for file_path in files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.current_invoice_folder, filename)

            # Avoid overwrite: add suffix if exists
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(self.current_invoice_folder, f"{base}_{counter}{ext}")
                counter += 1

            try:
                shutil.copy(file_path, dest_path)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error Copying File", f"Could not copy {filename}:\n{str(e)}")
                continue

        QtWidgets.QMessageBox.information(self, "Files Added", f"{len(files)} PDF(s) added to invoice folder:\n{self.current_invoice_folder}")

    def open_invoice_folder(self, row, _col):
        folder_item = self.table.item(row, 3)
        if folder_item:
            folder_path = folder_item.text()
            if os.path.exists(folder_path):
                # Open folder in file explorer
                if sys.platform == 'win32':
                    os.startfile(folder_path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{folder_path}"')
                else:
                    os.system(f'xdg-open "{folder_path}"')
            else:
                QtWidgets.QMessageBox.warning(self, "Folder not found", "The invoice folder does not exist.")

if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec())
