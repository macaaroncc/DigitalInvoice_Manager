import sys
import os
import shutil
import subprocess
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6 import QtWebEngineWidgets
from PyQt6.QtCore import QUrl, QUrlQuery
from PyQt6.QtGui import QIcon
from db import init_db, add_invoice, get_invoices, update_invoice_status

# Función para obtener la ruta correcta de recursos (para PyInstaller)
def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona tanto para dev como para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ======== ESTILOS FUTURISTAS ========
futuristic_style_main = """
    QWidget {
        background-color: #ffffff;  /* fondo blanco puro */
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #333333;
        font-size: 14px;
    }
    QTableWidget {
        border: none;
        gridline-color: #e6e6e6;
        selection-background-color: #1f6feb;
        selection-color: white;
        background-color: #ffffff;
    }
    QTableWidget QHeaderView::section {
        background-color: #f5f5f5;  /* gris muy claro */
        color: #333333;
        padding: 8px;
        border: none;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton {
        background-color: #238636;  /* verde original */
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2ea043;
    }
    QPushButton:pressed {
        background-color: #196c2e;
    }
    QLineEdit, QComboBox {
        border: 1px solid #e6e6e6;
        border-radius: 6px;
        padding: 6px;
        background-color: #fafafa;  /* gris claro */
        color: #333333;
        selection-background-color: #1f6feb;
    }
    QListWidget {
        border: 1px solid #e6e6e6;
        background-color: #fafafa;
        font-size: 13px;
        color: #333333;
        border-radius: 6px;
    }
    QLabel {
        font-size: 13px;
        color: #555555;
    }
"""

futuristic_style_droparea = """
    DropArea {
        border: 2px dashed #58a6ff;
        border-radius: 8px;
        background-color: rgba(56,139,253,0.05);
    }
    QLabel {
        color: #58a6ff;
        font-size: 14px;
        font-weight: bold;
    }
"""

futuristic_style_dialog = """
    QDialog {
        background-color: #ffffff;  /* fondo blanco puro */
    }
    QLabel {
        color: #555555;
        font-size: 13px;
    }
    QLineEdit, QDateEdit {
        border: 1px solid #e6e6e6;
        border-radius: 6px;
        padding: 6px;
        background-color: #fafafa;
        color: #333333;
    }
    QPushButton {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        padding: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2ea043;
    }
"""


class DropArea(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet(futuristic_style_droparea)
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
        self.setStyleSheet(futuristic_style_dialog)

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
        self.setWindowIcon(QtGui.QIcon(resource_path("icons/app_icon.png")))
        self.setWindowTitle("Futura Petrolium Manager")
        self.setGeometry(400, 200, 1800, 1400)
        self.setStyleSheet(futuristic_style_main)

        # Cargar íconos
        self.green_check_icon = QtGui.QIcon(resource_path("icons/green_check.png"))
        self.red_cross_icon = QtGui.QIcon(resource_path("icons/red_cross.png"))
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Panel horizontal principal
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(20)

        # -------- LEFT PANEL --------
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setSpacing(10)

        # Logo
        logo = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(resource_path("icons/logo.png"))
        logo_width, logo_height = 1297, 593
        aspect_ratio = logo_width / logo_height
        max_width, max_height = 300, 150
        if logo_width > max_width or logo_height > max_height:
            width = max_width
            height = int(width / aspect_ratio)
            if height > max_height:
                height = max_height
                width = int(height * aspect_ratio)
        else:
            width, height = logo_width, logo_height
        logo.setPixmap(pixmap.scaled(width, height, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        logo.setFixedSize(width, height)
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        left_panel.addWidget(logo)

        # Buscador
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search by Invoice Number or Date (YYYY-MM-DD)")
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setFixedWidth(100)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        left_panel.addLayout(search_layout)

        # Tabla
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Number", "Date", "Folder", "Status"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(2, True)
        header_table = self.table.horizontalHeader()
        header_table.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header_table.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header_table.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        left_panel.addWidget(self.table)
        

        # Botones debajo de la tabla
        buttons_layout = QtWidgets.QHBoxLayout()
        self.delete_invoice_btn = QtWidgets.QPushButton("Delete Invoice")
        self.delete_invoice_btn.setEnabled(False)
        self.delete_invoice_btn.setMinimumWidth(120)
        self.btn_open_folder = QtWidgets.QPushButton("Open Folder")
        self.btn_open_folder.setMinimumWidth(120)
        buttons_layout.addWidget(self.delete_invoice_btn)
        buttons_layout.addWidget(self.btn_open_folder)
        left_panel.addLayout(buttons_layout)

        self.create_btn = QtWidgets.QPushButton("Create New Invoice")
        self.create_btn.setMinimumHeight(40)
        left_panel.addWidget(self.create_btn)

        content_layout.addLayout(left_panel, stretch=1)

        # -------- CENTER PANEL (visor PDF) --------
        center_panel = QtWidgets.QVBoxLayout()
        center_panel.setSpacing(10)

        self.pdf_viewer = QtWebEngineWidgets.QWebEngineView()
        self.pdf_viewer.setMinimumHeight(300)
        center_panel.addWidget(self.pdf_viewer)

        # Crear un contenedor para los botones de navegación PDF
        btn_container = QtWidgets.QWidget()
        btn_container.setFixedHeight(50)
        btn_layout = QtWidgets.QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)  # solo margen superior
        btn_layout.setSpacing(5)  # 5px de espacio entre botones

        self.prev_pdf_btn = QtWidgets.QPushButton()
        self.prev_pdf_btn.setIcon(QIcon(resource_path("icons/prev.png")))
        self.prev_pdf_btn.setIconSize(QtCore.QSize(32, 32))
        self.prev_pdf_btn.setFlat(True)
        self.prev_pdf_btn.setFixedSize(32, 32)
        self.prev_pdf_btn.setStyleSheet("background: none; border: none; padding: 0; margin: 0;")

        self.next_pdf_btn = QtWidgets.QPushButton()
        self.next_pdf_btn.setIcon(QIcon(resource_path("icons/next.png")))
        self.next_pdf_btn.setIconSize(QtCore.QSize(32, 32))
        self.next_pdf_btn.setFlat(True)
        self.next_pdf_btn.setFixedSize(32, 32)
        self.next_pdf_btn.setStyleSheet("background: none; border: none; padding: 0; margin: 0;")

        # Centrar los botones con un poco de separación entre ellos
        btn_layout.addStretch()  # empuja hacia el centro desde la izquierda
        btn_layout.addWidget(self.prev_pdf_btn)
        btn_layout.addWidget(self.next_pdf_btn)
        btn_layout.addStretch()  # empuja hacia el centro desde la derecha

        # Agregamos el contenedor al final del center_panel
        center_panel.addWidget(btn_container)

        # Conectar señales
        self.prev_pdf_btn.clicked.connect(self.show_previous_pdf)
        self.next_pdf_btn.clicked.connect(self.show_next_pdf)

        content_layout.addLayout(center_panel, stretch=3)

        # -------- RIGHT PANEL --------
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.setSpacing(10)

        pdf_label = QtWidgets.QLabel("Attached PDFs:")
        right_panel.addWidget(pdf_label)

        self.pdf_list = QtWidgets.QListWidget()
        self.pdf_list.setMinimumWidth(400)
        self.pdf_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.pdf_list.currentItemChanged.connect(self.show_pdf_in_viewer)
        right_panel.addWidget(self.pdf_list, stretch=1)

        self.delete_pdf_btn = QtWidgets.QPushButton("Delete Selected PDF")
        self.delete_pdf_btn.setEnabled(False)
        right_panel.addWidget(self.delete_pdf_btn)

        content_layout.addLayout(right_panel, stretch=1)

        # Agregar a layout principal
        main_layout.addLayout(content_layout)

        # Conexiones
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.table.itemSelectionChanged.connect(self.show_invoice_pdfs)
        self.delete_invoice_btn.clicked.connect(self.delete_selected_invoice)
        self.delete_invoice_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;  /* rojo */
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e53935;  /* rojo más claro al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #7b0000;  /* rojo más oscuro al presionar */
            }
        """)

        self.table.itemSelectionChanged.connect(self.update_delete_invoice_button_state)
        self.table.itemDoubleClicked.connect(self.toggle_invoice_status)
        self.pdf_list.itemDoubleClicked.connect(self.open_pdf_file)
        self.pdf_list.itemSelectionChanged.connect(self.update_delete_button_state)
        self.pdf_list.itemSelectionChanged.connect(self.update_pdf_nav_buttons) 
        self.delete_pdf_btn.clicked.connect(self.delete_selected_pdf)
        self.delete_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;  /* rojo */
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e53935;  /* rojo más claro al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #7b0000;  /* rojo más oscuro al presionar */
            }
        """)
        self.search_btn.clicked.connect(self.search_invoices)
        self.search_input.returnPressed.connect(self.search_invoices)
        self.btn_open_folder.clicked.connect(self.open_add_pdfs_dialog)

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
                status_item.setToolTip("Complete - Double click to change to incomplete")
            else:
                status_item.setIcon(self.red_cross_icon)
                status_item.setToolTip("Incomplete - Double click to change to complete")
            self.table.setItem(row, 3, status_item)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def load_pdfs_for_invoice(self, invoice_folder):
        self.pdf_list.clear()
        if os.path.exists(invoice_folder):
            for file in os.listdir(invoice_folder):
                if file.lower().endswith(".pdf"):
                    self.pdf_list.addItem(file)

    def on_invoice_selected(self):
        selected_invoice = self.table.selectedItems()
        if not selected_invoice:
            return
        folder = self.table.item(selected_invoice[0].row(), 2).text()
        self.load_pdfs_for_invoice(folder)

    def open_create_dialog(self):
        dialog = InvoiceCreateDialog()
        dialog.invoiceCreated.connect(self.load_invoices)
        dialog.exec()

    def show_invoice_pdfs(self):
        selected = self.table.selectedItems()
        self.pdf_list.clear()
        self.pdf_viewer.setHtml("")  # limpiar visor al cambiar factura
        self.delete_pdf_btn.setEnabled(False)

        if not selected:
            return
        
        folder = self.table.item(selected[0].row(), 2).text()

        if not os.path.exists(folder):
            return

        files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        self.pdf_list.addItems(files)

    def toggle_invoice_status(self, item):
        # Solo permitir cambio si se hace clic en la columna de estado (columna 3)
        if item.column() != 3:
            return
            
        row = item.row()
        current_status = self.table.item(row, 3).icon()
        current_status_text = "completo" if current_status.cacheKey() == self.green_check_icon.cacheKey() else "incompleto"
        new_status = "incompleto" if current_status_text == "completo" else "completo"
        number = self.table.item(row, 0).text()
        
        # Mostrar confirmación visual rápida
        reply = QtWidgets.QMessageBox.question(
            self, "Change Status", 
            f"Change invoice '{number}' status to '{new_status}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
    
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
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

    def search_invoices(self):
        text = self.search_input.text().strip().lower()
        if not text:
            self.load_invoices()
            return
        
        invoices = get_invoices()
        filtered = [inv for inv in invoices if text in inv[1].lower() or text in inv[2].lower()]
        self.load_invoices(filtered)

    def update_delete_invoice_button_state(self):
        # Activa o desactiva el botón eliminar factura según selección
        selected = self.table.selectedItems()
        self.delete_invoice_btn.setEnabled(bool(selected))

    def delete_selected_invoice(self):
        selected = self.table.selectedItems()
        if not selected:
            return
    
        row = selected[0].row()
        number = self.table.item(row, 0).text()
        folder = self.table.item(row, 2).text()
        
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Invoice",
            f"Are you sure you want to delete the invoice '{number}' and all its PDFs?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                # Borra carpeta completa
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                
                # Aquí debes borrar la factura de la base de datos
                from db import delete_invoice
                delete_invoice(number)
                
                QtWidgets.QMessageBox.information(self, "Deleted", f"Invoice '{number}' deleted successfully.")
                self.load_invoices()
                self.pdf_list.clear()
                self.pdf_viewer.setHtml("")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete invoice:\n{str(e)}")

    def open_add_pdfs_dialog(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.warning(self, "No Invoice Selected", "Please select an invoice in the table first.")
            return
        row = selected_rows[0].row()
        invoice_folder_name = self.table.model().index(row, 2).data()
        if not invoice_folder_name:
            QtWidgets.QMessageBox.warning(self, "Error", "Selected row has no folder information.")
            return
        invoice_folder_name = invoice_folder_name.strip()
        invoice_folder = invoice_folder_name
        if not os.path.exists(invoice_folder):
            QtWidgets.QMessageBox.warning(self, "Error", f"Invoice folder not found:\n{invoice_folder}")
            return

        # Abrir la carpeta en el explorador según el sistema operativo
        if sys.platform == 'win32':
            os.startfile(invoice_folder)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', invoice_folder])
        else:  # Linux y otros
            subprocess.Popen(['xdg-open', invoice_folder])

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
            pdfjs_viewer_path = resource_path(os.path.join("viewer", "web", "viewer.html"))
            if os.path.exists(pdfjs_viewer_path):
                viewer_url = QUrl.fromLocalFile(pdfjs_viewer_path)
                pdf_url = QUrl.fromLocalFile(abs_path)
                query = QUrlQuery()
                query.addQueryItem("file", pdf_url.toString())
                viewer_url.setQuery(query)
                self.pdf_viewer.setUrl(viewer_url)
            else:
                self.pdf_viewer.setHtml("<h3 style='color:white;text-align:center'>⚠️ No se encontró PDF.js</h3>")
        else:
            self.pdf_viewer.setHtml("<h3 style='color:white;text-align:center'>📄 Archivo PDF no encontrado</h3>")

    def update_pdf_nav_buttons(self):
        total = self.pdf_list.count()
        current_row = self.pdf_list.currentRow()
        self.prev_pdf_btn.setEnabled(total > 1 and current_row > 0)
        self.next_pdf_btn.setEnabled(total > 1 and current_row < total - 1)

    def show_previous_pdf(self):
        current_row = self.pdf_list.currentRow()
        if current_row > 0:
            self.pdf_list.setCurrentRow(current_row - 1)

    def show_next_pdf(self):
        current_row = self.pdf_list.currentRow()
        if current_row < self.pdf_list.count() - 1:
            self.pdf_list.setCurrentRow(current_row + 1)


if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
