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
        self.setMinimumSize(400, 250)

        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()
        self.number_input = QtWidgets.QLineEdit()
        self.date_input = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Invoice Number:", self.number_input)
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
        self.setWindowTitle("DigitalInvoice_Manager")
        self.setGeometry(200, 200, 900, 600)

        main_layout = QtWidgets.QVBoxLayout(self)

        # Tabla de facturas
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Number", "Date", "Folder", "Status"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumWidth(450)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(2, True)  # Oculta columna Folder
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Barra de búsqueda y botón (solo para la izquierda)
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search by Invoice Number or Date (YYYY-MM-DD)")
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.clicked.connect(self.search_invoices)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)

        # Layout izquierdo: búsqueda + tabla + botón abajo
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addLayout(search_layout)
        left_layout.addWidget(self.table)
        
        self.create_btn = QtWidgets.QPushButton("Create Invoice")
        left_layout.addWidget(self.create_btn)

        # Layout derecho: estado, lista pdf y botones
        right_layout = QtWidgets.QVBoxLayout()

        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["incompleto", "completo"])
        self.status_combo.setEnabled(False)
        right_layout.addWidget(self.status_combo)

        self.pdf_list = QtWidgets.QListWidget()
        self.pdf_list.setMinimumWidth(400)
        self.pdf_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        right_layout.addWidget(self.pdf_list)

        self.delete_pdf_btn = QtWidgets.QPushButton("Eliminar PDF")
        self.delete_pdf_btn.setEnabled(False)
        right_layout.addWidget(self.delete_pdf_btn)

        # Layout horizontal principal: izquierda y derecha
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addLayout(left_layout, stretch=1)   # Izquierda ocupa mitad
        top_layout.addLayout(right_layout, stretch=1)  # Derecha ocupa mitad

        main_layout.addLayout(top_layout)

        # Conexiones
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.table.itemSelectionChanged.connect(self.show_invoice_pdfs)
        self.table.itemDoubleClicked.connect(self.toggle_invoice_status)
        self.pdf_list.itemDoubleClicked.connect(self.open_pdf_file)
        self.pdf_list.itemSelectionChanged.connect(self.update_delete_button_state)
        self.delete_pdf_btn.clicked.connect(self.delete_selected_pdf)
        self.status_combo.currentIndexChanged.connect(self.change_status)

        # Carga inicial
        self.load_invoices()

    def load_invoices(self, invoices=None):
        self.table.setRowCount(0)
        # Si no recibe lista, la obtiene
        if invoices is None:
            invoices = get_invoices()
        # Ordenar por número descendente (numérico)
        def get_num(i):
            try:
                return int(i[1])
            except:
                return 0
        invoices = sorted(invoices, key=get_num, reverse=True)

        for row_data in invoices:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # row_data = (id, number, date, folder, status)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row_data[1])))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(row_data[2])))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(row_data[3])))

            status_item = QtWidgets.QTableWidgetItem("✔" if row_data[4] == "verde" else "❌")
            status_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QtGui.QColor("green") if row_data[4] == "verde" else QtGui.QColor("red"))
            self.table.setItem(row, 3, status_item)

        # Reset combo y PDF lista
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
            # inv = (id, number, date, folder, status)
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
        self.delete_pdf_btn.setEnabled(False)  # Desactivar botón hasta selección

        # Set status combo according to current invoice status
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
        # Alterna entre rojo y verde
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
                QtWidgets.QMessageBox.information(self, "Eliminado", f"Archivo '{pdf_name}' eliminado correctamente.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"No se pudo eliminar '{pdf_name}':\n{str(e)}")
                return
        else:
            QtWidgets.QMessageBox.warning(self, "Error", f"Archivo '{pdf_name}' no encontrado.")

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
