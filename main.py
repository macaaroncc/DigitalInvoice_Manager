import sys
import os
import shutil
from PyQt6 import QtWidgets, QtCore, QtGui

# Import necesario para visor PDF
from PyQt6 import QtWebEngineWidgets

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
        
        # Cargar íconos
        self.green_check_icon = QtGui.QIcon("icons/green_check.png")
        self.red_cross_icon = QtGui.QIcon("icons/red_cross.png")
        
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
        
        logo = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("icons/logo.png")
        logo.setPixmap(pixmap)
        logo.setScaledContents(True)  # Para que el logo se escale al tamaño del label
        logo.setFixedHeight(60)       # Ajusta la altura que quieras para el logo

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

        # Visor PDF agregado aquí:
        self.pdf_viewer = QtWebEngineWidgets.QWebEngineView()
        self.pdf_viewer.setMinimumHeight(300)
        right_panel.addWidget(self.pdf_viewer)

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
            number, date, folder, status = row_data[1], row_data[2], row_data[3], row_data[4]

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(number))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(date))
            folder_item = QtWidgets.QTableWidgetItem(folder)
            self.table.setItem(row, 2, folder_item)

            status_item = QtWidgets.QTableWidgetItem()
            if status == "completo":
                status_item.setIcon(self.green_check_icon)
            else:
                status_item.setIcon(self.red_cross_icon)
            self.table.setItem(row, 3, status_item)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def open_create_dialog(self):
        dialog = InvoiceCreateDialog()
        dialog.invoiceCreated.connect(self.load_invoices)
        dialog.exec()

    def show_invoice_pdfs(self):
        selected = self.table.selectedItems()
        self.pdf_list.clear()
        self.pdf_viewer.setHtml("")  # limpiar visor al cambiar factura
        self.status_combo.setEnabled(False)
        self.delete_pdf_btn.setEnabled(False)

        if not selected:
            return
        
        folder = self.table.item(selected[0].row(), 2).text()
        status = self.table.item(selected[0].row(), 3).icon()

        # Mostrar estado y habilitar combo
        current_status_text = "completo" if self.table.item(selected[0].row(), 3).icon().cacheKey() == self.green_check_icon.cacheKey() else "incompleto"
        self.status_combo.setCurrentText(current_status_text)
        self.status_combo.setEnabled(True)

        if not os.path.exists(folder):
            return

        files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        self.pdf_list.addItems(files)

    def toggle_invoice_status(self, item):
        row = item.row()
        current_status = self.table.item(row, 3).icon()
        current_status_text = "completo" if current_status.cacheKey() == self.green_check_icon.cacheKey() else "incompleto"
        new_status = "incompleto" if current_status_text == "completo" else "completo"
        number = self.table.item(row, 0).text()
        update_invoice_status(number, new_status)
        self.load_invoices()

    def open_pdf_file(self, item):
        selected_invoice = self.table.selectedItems()
        if not selected_invoice:
            return
        folder = self.table.item(selected_invoice[0].row(), 2).text()
        path = os.path.join(folder, item.text())
        if os.path.exists(path):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    def update_delete_button_state(self):
        self.delete_pdf_btn.setEnabled(self.pdf_list.currentItem() is not None)

    def delete_selected_pdf(self):
        selected_invoice = self.table.selectedItems()
        selected_pdf = self.pdf_list.currentItem()
        if not selected_invoice or not selected_pdf:
            return
        
        folder = self.table.item(selected_invoice[0].row(), 2).text()
        path = os.path.join(folder, selected_pdf.text())

        reply = QtWidgets.QMessageBox.question(self, "Delete PDF", f"Are you sure you want to delete '{selected_pdf.text()}'?",
                                               QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                self.pdf_list.takeItem(self.pdf_list.currentRow())
                self.pdf_viewer.setHtml("")  # limpiar visor si borró el pdf mostrado
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete file:\n{str(e)}")

    def change_status(self, index):
        if not self.status_combo.isEnabled():
            return
        selected = self.table.selectedItems()
        if not selected:
            return
        number = self.table.item(selected[0].row(), 0).text()
        new_status = self.status_combo.currentText()
        update_invoice_status(number, new_status)
        self.load_invoices()

    def search_invoices(self):
        text = self.search_input.text().strip().lower()
        if not text:
            self.load_invoices()
            return
        
        invoices = get_invoices()
        filtered = [inv for inv in invoices if text in inv[1].lower() or text in inv[2].lower()]
        self.load_invoices(filtered)

def show_pdf_in_viewer(self, current, previous):
    if not current:
        self.pdf_viewer.setHtml("")
        return
    selected_invoice = self.table.selectedItems()
    if not selected_invoice:
        self.pdf_viewer.setHtml("")
        return
    folder = self.table.item(selected_invoice[0].row(), 2).text()
    pdf_file = current.text()
    path = os.path.join(folder, pdf_file)
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        url = QtCore.QUrl.fromLocalFile(abs_path)
        self.pdf_viewer.setUrl(url)
    else:
        self.pdf_viewer.setHtml("")


if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
