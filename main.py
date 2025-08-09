import sys
import os
import shutil
from PyQt6 import QtWidgets, QtCore, QtGui
from db import init_db, add_invoice, get_invoices, update_invoice_status

class DropArea(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #4fc3f7;
                border-radius: 8px;
                background-color: #f8fdff;
            }
            QLabel {
                color: black;
                font-size: 14px;
            }
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
        self.setMinimumSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: black;
                font-size: 13px;
            }
            QLineEdit, QDateEdit {
                border: 1px solid #b3e5fc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                color: black;
            }
            QPushButton {
                background-color: #4fc3f7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #29b6f6;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        self.number_input = QtWidgets.QLineEdit()
        self.number_input.setPlaceholderText("e.g. INV-2023-001")
        self.date_input = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        
        form_layout.addRow("Invoice Number:", self.number_input)
        form_layout.addRow("Date:", self.date_input)
        layout.addLayout(form_layout)

        self.drop_area = DropArea()
        layout.addWidget(self.drop_area)

        self.save_button = QtWidgets.QPushButton("Save Invoice")
        self.save_button.setFixedHeight(40)
        layout.addWidget(self.save_button)

        self.files_to_copy = []
        self.drop_area.filesDropped.connect(self.files_dropped)
        self.save_button.clicked.connect(self.save_invoice)

    def files_dropped(self, files):
        self.files_to_copy.extend(files)
        self.drop_area.label.setText(f"{len(self.files_to_copy)} PDF(s) ready to add")

    def save_invoice(self):
        number = self.number_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")

        if not number:
            QtWidgets.QMessageBox.warning(self, "Error", "Invoice number is required")
            return

        folder = os.path.join("data", number)
        if not os.path.exists(folder):
            os.makedirs(folder)

        add_invoice(number, date, folder, "rojo")

        for file_path in self.files_to_copy:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(folder, filename)
            if not os.path.exists(dest_path):
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
        self.setWindowTitle("DigitalInvoice Manager")
        self.setGeometry(200, 200, 1000, 700)
        
        # Estilo principal
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: black;
            }
            QTableWidget {
                border: 1px solid #e1f5fe;
                gridline-color: #e1f5fe;
                selection-background-color: #b3e5fc;
                selection-color: black;
                font-size: 13px;
            }
            QTableWidget QHeaderView::section {
                background-color: #4fc3f7;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4fc3f7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #29b6f6;
            }
            QPushButton:pressed {
                background-color: #0288d1;
            }
            QLineEdit, QComboBox {
                border: 1px solid #b3e5fc;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
                color: black;
            }
            QListWidget {
                border: 1px solid #e1f5fe;
                background-color: #f8fdff;
                font-size: 13px;
                color: black;
            }
            QLabel {
                font-size: 13px;
                color: black;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header con logo
        header = QtWidgets.QHBoxLayout()
        header.addStretch()
        
        logo = QtWidgets.QLabel("FUTURA PETROLIUM INVOICE MANAGER")
        logo.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        header.addWidget(logo)
        header.addStretch()
        main_layout.addLayout(header)

        # Contenido principal
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(20)

        # Panel izquierdo
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setSpacing(10)

        # Barra de búsqueda
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search by Invoice Number or Date (YYYY-MM-DD)")
        self.search_input.setStyleSheet("padding: 8px;")
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setFixedWidth(100)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)

        # Tabla de facturas
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Number", "Date", "Folder", "Status"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(2, True)  # Oculta columna Folder
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget::item {
                padding: 5px;
                color: black;
            }
        """)

        # Botón crear
        self.create_btn = QtWidgets.QPushButton("Create New Invoice")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #00acc1;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0097a7;
            }
        """)

        left_panel.addLayout(search_layout)
        left_panel.addWidget(self.table)
        left_panel.addWidget(self.create_btn)

        # Panel derecho
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.setSpacing(10)

        # Estado
        status_layout = QtWidgets.QHBoxLayout()
        status_label = QtWidgets.QLabel("Invoice Status:")
        status_label.setStyleSheet("font-weight: bold;")
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["incompleto", "completo"])
        self.status_combo.setEnabled(False)
        self.status_combo.setFixedHeight(30)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        right_panel.addLayout(status_layout)

        # Lista PDF
        pdf_label = QtWidgets.QLabel("Attached PDFs:")
        pdf_label.setStyleSheet("font-weight: bold;")
        right_panel.addWidget(pdf_label)
        
        self.pdf_list = QtWidgets.QListWidget()
        self.pdf_list.setMinimumWidth(400)
        self.pdf_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        right_panel.addWidget(self.pdf_list)

        # Botón eliminar
        self.delete_pdf_btn = QtWidgets.QPushButton("Delete Selected PDF")
        self.delete_pdf_btn.setEnabled(False)
        self.delete_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef5350;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:disabled {
                background-color: #ef9a9a;
            }
        """)
        right_panel.addWidget(self.delete_pdf_btn)

        content_layout.addLayout(left_panel, stretch=2)
        content_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

        # Conexiones
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.table.itemSelectionChanged.connect(self.show_invoice_pdfs)
        self.table.itemDoubleClicked.connect(self.toggle_invoice_status)
        self.pdf_list.itemDoubleClicked.connect(self.open_pdf_file)
        self.pdf_list.itemSelectionChanged.connect(self.update_delete_button_state)
        self.delete_pdf_btn.clicked.connect(self.delete_selected_pdf)
        self.status_combo.currentIndexChanged.connect(self.change_status)
        self.search_btn.clicked.connect(self.search_invoices)
        self.search_input.returnPressed.connect(self.search_invoices)

        # Carga inicial
        self.load_invoices()

    def load_invoices(self, invoices=None):
        self.table.setRowCount(0)
        if invoices is None:
            invoices = get_invoices()
        
        def get_num(i):
            try:
                return int(i[1])
            except:
                return 0
        invoices = sorted(invoices, key=get_num, reverse=True)

        for row_data in invoices:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row_data[1])))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(row_data[2])))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(row_data[3])))

            status_item = QtWidgets.QTableWidgetItem("✔" if row_data[4] == "verde" else "❌")
            status_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QtGui.QColor("#00c853") if row_data[4] == "verde" else QtGui.QColor("#d50000"))
            self.table.setItem(row, 3, status_item)

        self.status_combo.setEnabled(False)
        self.pdf_list.clear()
        self.delete_pdf_btn.setEnabled(False)

    def search_invoices(self):
        text = self.search_input.text().strip().lower()
        if not text:
            self.load_invoices()
            return

        invoices = get_invoices()
        filtered = []
        for inv in invoices:
            if text in str(inv[1]).lower() or text in str(inv[2]).lower():
                filtered.append(inv)
        self.load_invoices(filtered)

    def open_create_dialog(self):
        dialog = InvoiceCreateDialog()
        dialog.invoiceCreated.connect(self.load_invoices)
        dialog.exec()

    def show_invoice_pdfs(self):
        self.pdf_list.clear()
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.delete_pdf_btn.setEnabled(False)
            self.status_combo.setEnabled(False)
            return

        row = selected_rows[0].row()
        folder_item = self.table.item(row, 2)
        if not folder_item:
            self.delete_pdf_btn.setEnabled(False)
            self.status_combo.setEnabled(False)
            return
        folder_path = folder_item.text()
        if not os.path.exists(folder_path):
            self.delete_pdf_btn.setEnabled(False)
            self.status_combo.setEnabled(False)
            return

        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        self.pdf_list.addItems(pdf_files)
        self.delete_pdf_btn.setEnabled(False)

        status_item = self.table.item(row, 3)
        if status_item and status_item.text() == "✔":
            self.status_combo.setCurrentText("completo")
        else:
            self.status_combo.setCurrentText("incompleto")
        self.status_combo.setEnabled(True)

    def open_pdf_file(self, item):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        folder_item = self.table.item(row, 2)
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

    def toggle_invoice_status(self, item):
        row = item.row()
        number = self.table.item(row, 0).text()
        current_status_symbol = self.table.item(row, 3).text()

        new_status = "verde" if current_status_symbol == "❌" else "rojo"
        update_invoice_status(number, new_status)
        self.load_invoices()

    def update_delete_button_state(self):
        has_selection = bool(self.pdf_list.selectedItems())
        self.delete_pdf_btn.setEnabled(has_selection)

    def delete_selected_pdf(self):
        selected_items = self.pdf_list.selectedItems()
        if not selected_items:
            return
        pdf_name = selected_items[0].text()

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        folder_item = self.table.item(row, 2)
        if not folder_item:
            return
        folder_path = folder_item.text()

        pdf_path = os.path.join(folder_path, pdf_name)
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                QtWidgets.QMessageBox.information(self, "Deleted", f"File '{pdf_name}' was deleted successfully.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete '{pdf_name}':\n{str(e)}")
                return
        else:
            QtWidgets.QMessageBox.warning(self, "Error", f"File '{pdf_name}' not found.")

        self.show_invoice_pdfs()

    def change_status(self):
        if not self.status_combo.isEnabled():
            return
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        number = self.table.item(row, 0).text()
        new_status = "verde" if self.status_combo.currentText() == "completo" else "rojo"
        update_invoice_status(number, new_status)
        self.load_invoices()

if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    
    # Establecer estilo de la aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    sys.exit(app.exec())