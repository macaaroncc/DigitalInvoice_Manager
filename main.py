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

class InvoiceCreateDialog(QtWidgets.QDialog):
    invoiceCreated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Invoice")
        self.setMinimumSize(400, 300)

        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()
        self.number_input = QtWidgets.QLineEdit()
        self.client_input = QtWidgets.QLineEdit()
        self.date_input = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Invoice Number:", self.number_input)
        form_layout.addRow("Client:", self.client_input)
        form_layout.addRow("Date:", self.date_input)
        layout.addLayout(form_layout)

        self.drop_area = DropArea()
        layout.addWidget(self.drop_area)

        self.save_button = QtWidgets.QPushButton("Save Invoice")
        layout.addWidget(self.save_button)

        self.files_to_copy = []
        self.drop_area.filesDropped.connect(self.files_dropped)
        self.save_button.clicked.connect(self.save_invoice)

    def files_dropped(self, files):
        self.files_to_copy.extend(files)
        self.drop_area.label.setText(f"{len(self.files_to_copy)} PDF(s) ready to add")

    def save_invoice(self):
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

        for file_path in self.files_to_copy:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(folder, filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(folder, f"{base}_{counter}{ext}")
                counter += 1
            try:
                shutil.copy(file_path, dest_path)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error Copying File", f"Could not copy {filename}:\n{str(e)}")

        QtWidgets.QMessageBox.information(self, "Invoice Saved", f"Invoice '{number}' saved with {len(self.files_to_copy)} PDFs.")
        self.invoiceCreated.emit()
        self.close()

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigitalInvoice_Manager")
        self.setGeometry(200, 200, 900, 600)

        main_layout = QtWidgets.QVBoxLayout(self)

        # Horizontal layout for table and pdf list
        top_layout = QtWidgets.QHBoxLayout()

        # Table for invoices (left side)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Number", "Client", "Date", "Folder"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumWidth(450)
        top_layout.addWidget(self.table)

        # List widget for PDFs (right side)
        self.pdf_list = QtWidgets.QListWidget()
        self.pdf_list.setMinimumWidth(400)
        self.pdf_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        top_layout.addWidget(self.pdf_list)

        main_layout.addLayout(top_layout)

        # Button below, centered
        self.create_btn = QtWidgets.QPushButton("Create Invoice")
        self.create_btn.setFixedWidth(200)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.create_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Connections
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.table.itemSelectionChanged.connect(self.show_invoice_pdfs)
        self.pdf_list.itemDoubleClicked.connect(self.open_pdf_file)

        self.load_invoices()

    def load_invoices(self):
        self.table.setRowCount(0)
        for row_data in get_invoices():
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data[1:]):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))

    def open_create_dialog(self):
        dialog = InvoiceCreateDialog()
        dialog.invoiceCreated.connect(self.load_invoices)
        dialog.exec()

    def show_invoice_pdfs(self):
        self.pdf_list.clear()
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        folder_item = self.table.item(row, 3)
        if not folder_item:
            return
        folder_path = folder_item.text()
        if not os.path.exists(folder_path):
            return

        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        self.pdf_list.addItems(pdf_files)

    def open_pdf_file(self, item):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        folder_item = self.table.item(row, 3)
        if not folder_item:
            return
        folder_path = folder_item.text()
        pdf_path = os.path.join(folder_path, item.text())

        if os.path.exists(pdf_path):
            if sys.platform == 'win32':
                os.startfile(pdf_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{pdf_path}"')
            else:
                os.system(f'xdg-open "{pdf_path}"')

if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
