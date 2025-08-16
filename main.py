import sys
import os
import shutil
import subprocess
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6 import QtWebEngineWidgets
from PyQt6.QtCore import QUrl, QUrlQuery
from PyQt6.QtGui import QIcon
from db import init_db, add_invoice, get_invoices, update_invoice_status, update_invoice_name

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
        border: 3px dashed #74b9ff;
        border-radius: 12px;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                  stop: 0 rgba(116, 185, 255, 0.08), 
                                  stop: 1 rgba(116, 185, 255, 0.15));
        margin: 10px;
    }
    DropArea:hover {
        border: 3px dashed #0984e3;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                  stop: 0 rgba(9, 132, 227, 0.12), 
                                  stop: 1 rgba(9, 132, 227, 0.20));
    }
    QLabel {
        color: #74b9ff;
        font-size: 16px;
        font-weight: 600;
        padding: 20px;
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

    def __init__(self, current_year="2025"):
        super().__init__()
        self.current_year = current_year
        self.setWindowTitle("Create New Invoice")
        self.setMinimumSize(400, 500)
        self.setStyleSheet(futuristic_style_dialog)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Invoice Number
        layout.addWidget(QtWidgets.QLabel("Invoice Number:"))
        self.number_input = QtWidgets.QLineEdit()
        layout.addWidget(self.number_input)
        
        # Name
        layout.addWidget(QtWidgets.QLabel("Name:"))
        self.name_input = QtWidgets.QLineEdit()
        layout.addWidget(self.name_input)
        
        # Date
        layout.addWidget(QtWidgets.QLabel("Date:"))
        self.date_input = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        layout.addWidget(self.date_input)
        
        # Drop area
        self.drop_area = DropArea()
        layout.addWidget(self.drop_area)
        
        # Botón para seleccionar archivos PDF
        self.select_files_btn = QtWidgets.QPushButton("Select PDF Files")
        layout.addWidget(self.select_files_btn)
        
        # Buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Save Invoice")
        buttons_layout.addWidget(self.save_button)
        layout.addLayout(buttons_layout)
        
        # Connections
        self.files_to_copy = []
        self.drop_area.filesDropped.connect(self.files_dropped)
        self.select_files_btn.clicked.connect(self.select_files)
        self.save_button.clicked.connect(self.save_invoice)

    def files_dropped(self, files):
        self.files_to_copy.extend(files)
        self.update_files_display()

    def select_files(self):
        """Abre un diálogo para seleccionar archivos PDF"""
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            "",
            "PDF Files (*.pdf)"
        )
        if files:
            self.files_to_copy.extend(files)
            self.update_files_display()
    
    def update_files_display(self):
        """Actualiza el texto del área de drop con el número de archivos seleccionados"""
        count = len(self.files_to_copy)
        if count == 0:
            self.drop_area.label.setText("Drag and drop PDF files here")
        else:
            self.drop_area.label.setText(f"{count} PDF(s) ready to add")

    def save_invoice(self):
        number = self.number_input.text().strip()
        name = self.name_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")

        if not number:
            QtWidgets.QMessageBox.warning(self, "Error", "Invoice number is required")
            return

        # Usar el año seleccionado en el desplegable para crear la carpeta
        year = self.current_year
        year_folder = os.path.join("data", year)
        
        # Crear carpeta del año si no existe
        if not os.path.exists(year_folder):
            os.makedirs(year_folder)
        
        # Crear carpeta de la factura dentro del año
        invoice_folder = os.path.join(year_folder, number)
        if not os.path.exists(invoice_folder):
            os.makedirs(invoice_folder)

        add_invoice(number, name, date, invoice_folder, "incompleto")

        for file_path in self.files_to_copy:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(invoice_folder, filename)
            if not os.path.exists(dest_path):
                try:
                    shutil.copy(file_path, dest_path)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, "Error Copying File", f"Could not copy {filename}:\n{str(e)}")

        QtWidgets.QMessageBox.information(self, "Invoice Saved", f"Invoice '{number}' saved in {year} with {len(self.files_to_copy)} PDFs.")
        self.invoiceCreated.emit()
        self.close()


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon(resource_path("icons/app_icon.png")))
        self.setWindowTitle("Futura Manager")
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
        left_panel_widget = QtWidgets.QWidget()
        left_panel_widget.setFixedWidth(370)  # Ancho fijo de 370px
        left_panel = QtWidgets.QVBoxLayout(left_panel_widget)
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

        # Selector de año y buscador
        controls_layout = QtWidgets.QHBoxLayout()
        
        # Selector de año
        year_layout = QtWidgets.QHBoxLayout()
        self.year_combo = QtWidgets.QComboBox()
        self.year_combo.addItems(["2022", "2023", "2024", "2025"])
        self.year_combo.setCurrentText("2025")  # Por defecto 2025
        self.year_combo.setMinimumWidth(80)
        self.year_combo.setMaximumWidth(100)
        year_layout.addWidget(self.year_combo)
        year_layout.addStretch()
        
        # Buscador
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search by Number or Name:")
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setFixedWidth(100)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        
        # Combinar año y buscador en una línea
        controls_layout.addLayout(year_layout)
        controls_layout.addLayout(search_layout)
        left_panel.addLayout(controls_layout)

        # Tabla
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Number", "Name", "Date", "Folder", "Status"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)  # Ocultar encabezados de columnas
        self.table.setColumnHidden(3, True)  # Ocultar Folder (ahora es columna 3)
        header_table = self.table.horizontalHeader()
        header_table.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)  # Number
        header_table.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)  # Name
        header_table.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Interactive)  # Date
        header_table.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)      # Status - fijo
        
        # Configurar anchos específicos
        self.table.setColumnWidth(0, 60)  # Number - ancho moderado
        self.table.setColumnWidth(1, 150)  # Name - más ancho para "MY SERENANA"
        self.table.setColumnWidth(2, 90)  # Date - ancho moderado
        self.table.setColumnWidth(4, 30)   # Status - muy estrecho solo para icono
        left_panel.addWidget(self.table)
        

        # Botones debajo de la tabla
        buttons_layout = QtWidgets.QHBoxLayout()
        self.delete_invoice_btn = QtWidgets.QPushButton("Delete Folder")
        self.delete_invoice_btn.setEnabled(False)
        self.delete_invoice_btn.setMinimumWidth(120)
        self.btn_open_folder = QtWidgets.QPushButton("Open Folder")
        self.btn_open_folder.setMinimumWidth(120)
        buttons_layout.addWidget(self.delete_invoice_btn)
        buttons_layout.addWidget(self.btn_open_folder)
        left_panel.addLayout(buttons_layout)

        self.create_btn = QtWidgets.QPushButton("Create Folder")
        self.create_btn.setMinimumHeight(40)
        left_panel.addWidget(self.create_btn)

        content_layout.addWidget(left_panel_widget)

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

        content_layout.addLayout(center_panel, stretch=2)

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

        # Botón para añadir PDFs a la factura seleccionada
        self.add_pdf_btn = QtWidgets.QPushButton("Add PDF")
        self.add_pdf_btn.setEnabled(False)
        right_panel.addWidget(self.add_pdf_btn)
        
        self.delete_pdf_btn = QtWidgets.QPushButton("Delete PDF")
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
        self.table.itemSelectionChanged.connect(self.update_add_pdf_button_state)
        self.table.itemDoubleClicked.connect(self.toggle_invoice_status)
        self.pdf_list.itemDoubleClicked.connect(self.open_pdf_file)
        self.pdf_list.itemSelectionChanged.connect(self.update_delete_button_state)
        self.pdf_list.itemSelectionChanged.connect(self.update_pdf_nav_buttons) 
        self.add_pdf_btn.clicked.connect(self.add_pdf_to_invoice)
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
        
        # Conectar selector de año
        self.year_combo.currentTextChanged.connect(self.on_year_changed)

        # Carga inicial - cargar facturas por año (por defecto 2025)
        self.load_invoices_by_year()

    def format_date_european(self, date_str):
        """Convierte fecha de formato YYYY-MM-DD a DD/MM/YYYY"""
        if not date_str or len(date_str) < 10:
            return date_str
        try:
            # Si la fecha está en formato YYYY-MM-DD
            if '-' in date_str and len(date_str) == 10:
                parts = date_str.split('-')
                if len(parts) == 3:
                    year, month, day = parts
                    return f"{day}/{month}/{year}"
            # Si ya está en formato DD/MM/YYYY, devolver tal como está
            elif '/' in date_str:
                return date_str
            # Si es solo el año
            elif len(date_str) == 4 and date_str.isdigit():
                return date_str
        except:
            pass
        return date_str


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
            # La estructura real es: id, number, date, folder, status, name
            if len(row_data) >= 6:  # Nuevo formato con name
                number, date, folder, status, name = row_data[1], row_data[2], row_data[3], row_data[4], row_data[5]
            else:  # Formato antiguo sin name
                number, date, folder, status, name = row_data[1], row_data[2], row_data[3], row_data[4], ""

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(number))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(name if name else ""))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(self.format_date_european(date)))
            folder_item = QtWidgets.QTableWidgetItem(folder)
            self.table.setItem(row, 3, folder_item)

            status_item = QtWidgets.QTableWidgetItem()
            if status == "completo":
                status_item.setIcon(self.green_check_icon)
                status_item.setToolTip("Complete - Double click to change to incomplete")
            else:
                status_item.setIcon(self.red_cross_icon)
                status_item.setToolTip("Incomplete - Double click to change to complete")
            self.table.setItem(row, 4, status_item)

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
        # Pasar el año actualmente seleccionado al diálogo
        current_year = self.year_combo.currentText()
        dialog = InvoiceCreateDialog(current_year)
        dialog.invoiceCreated.connect(self.load_invoices_by_year)  # Recargar vista por año
        dialog.exec()

    def show_invoice_pdfs(self):
        selected = self.table.selectedItems()
        self.pdf_list.clear()
        self.pdf_viewer.setHtml("")  # limpiar visor al cambiar factura
        self.delete_pdf_btn.setEnabled(False)

        if not selected:
            return
        
        folder = self.table.item(selected[0].row(), 3).text()  # Folder ahora está en columna 3

        if not os.path.exists(folder):
            return

        files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        self.pdf_list.addItems(files)
        
        # Seleccionar automáticamente el primer PDF si hay archivos
        if files:
            self.pdf_list.setCurrentRow(0)

    def toggle_invoice_status(self, item):
        # Solo permitir cambio si se hace clic en la columna de estado (columna 4)
        if item.column() != 4:
            return
            
        row = item.row()
        current_status = self.table.item(row, 4).icon()
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
            self.load_invoices_by_year()

    def open_pdf_file(self, item):
        selected_invoice = self.table.selectedItems()
        if not selected_invoice:
            return
        folder = self.table.item(selected_invoice[0].row(), 3).text()  # Folder está en columna 3
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
        
        folder = self.table.item(selected_invoice[0].row(), 3).text()
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
            self.load_invoices_by_year()  # Cargar vista por año cuando no hay búsqueda
            return
        
        # Buscar en todas las facturas de la base de datos
        invoices = get_invoices()
        filtered_invoices = []
        
        for invoice in invoices:
            # La estructura real es: id, number, date, folder, status, name
            number, date, folder, status = invoice[1], invoice[2], invoice[3], invoice[4]
            name = invoice[5] if len(invoice) >= 6 else ""  # Manejar facturas sin campo name
            
            # Buscar en número de factura, fecha o nombre
            if (text in number.lower() or 
                text in date.lower() or 
                (name and text in name.lower())):
                filtered_invoices.append(invoice)
        
        # Mostrar resultados filtrados
        self.load_invoices(filtered_invoices)

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
        folder = self.table.item(row, 3).text()
        
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
                self.load_invoices_by_year()  # Recargar vista por año
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
        invoice_folder_name = self.table.model().index(row, 3).data()
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

        folder = self.table.item(selected_invoice[0].row(), 3).text()
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

    # ===== NUEVAS FUNCIONES PARA MANEJO POR AÑO =====
    
    def on_year_changed(self, year):
        """Se ejecuta cuando cambia el año seleccionado"""
        self.pdf_list.clear()
        self.pdf_viewer.setHtml("")
        self.load_invoices_by_year()
    
    def load_invoices_by_year(self):
        """Carga las facturas únicamente desde la carpeta del año seleccionado"""
        selected_year = self.year_combo.currentText()
        year_folder = os.path.join("data", selected_year)
        
        self.table.setRowCount(0)
        
        if not os.path.exists(year_folder):
            self.pdf_viewer.setHtml(f"<h3 style='color:#666;text-align:center'>No hay carpeta para el año {selected_year}</h3>")
            return
        
        invoices_data = []
        
        try:
            # Obtener todas las carpetas de facturas del año
            for invoice_folder_name in os.listdir(year_folder):
                invoice_path = os.path.join(year_folder, invoice_folder_name)
                if os.path.isdir(invoice_path):
                    # Buscar información en la base de datos para obtener fecha, nombre y estado reales
                    all_invoices = get_invoices()
                    invoice_name = ""  # Por defecto vacío
                    invoice_date = selected_year  # Por defecto usar el año
                    invoice_status = "completo"  # Por defecto completo para facturas externas
                    
                    # Buscar en la BD si existe información adicional
                    for db_invoice in all_invoices:
                        if db_invoice[1] == invoice_folder_name:  # Coincidir por número de factura
                            # La estructura real es: id, number, date, folder, status, name
                            if len(db_invoice) >= 6:  # Nuevo formato con name
                                invoice_date = db_invoice[2]  # date está en índice 2
                                invoice_status = db_invoice[4]  # status está en índice 4
                                invoice_name = db_invoice[5] if db_invoice[5] else ""  # name está en índice 5
                            else:  # Formato antiguo sin name
                                invoice_date = db_invoice[2]
                                invoice_status = db_invoice[4]
                            break
                    
                    invoice_data = {
                        'number': invoice_folder_name,
                        'name': invoice_name,
                        'date': invoice_date,
                        'folder': invoice_path,
                        'status': invoice_status
                    }
                    invoices_data.append(invoice_data)
        except Exception as e:
            print(f"Error loading invoices from {year_folder}: {e}")
            return
        
        # Si no hay datos, mostrar mensaje
        if not invoices_data:
            self.pdf_viewer.setHtml(f"<h3 style='color:#666;text-align:center'>No hay facturas en la carpeta {selected_year}</h3>")
            return
        
        # Ordenar las facturas por número
        try:
            invoices_data.sort(key=lambda x: int(x['number']) if x['number'].isdigit() else 0, reverse=True)
        except:
            invoices_data.sort(key=lambda x: x['number'], reverse=True)
        
        # Llenar la tabla con los datos
        for invoice_data in invoices_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(invoice_data['number']))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(invoice_data['name']))  # Usar el nombre de la BD
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(self.format_date_european(invoice_data['date'])))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(invoice_data['folder']))
            
            # Icono de estado
            status_item = QtWidgets.QTableWidgetItem()
            if invoice_data['status'] == "completo":
                status_item.setIcon(self.green_check_icon)
                status_item.setToolTip("Complete - Double click to change to incomplete")
            else:
                status_item.setIcon(self.red_cross_icon)
                status_item.setToolTip("Incomplete - Double click to change to complete")
            self.table.setItem(row, 4, status_item)
        
        # Seleccionar la primera fila si hay datos
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
    
    def get_selected_year_folder(self):
        """Retorna la carpeta del año actualmente seleccionado"""
        return os.path.join("data", self.year_combo.currentText())

    def update_add_pdf_button_state(self):
        """Activa o desactiva el botón Add PDF to Invoice según si hay una factura seleccionada"""
        selected = self.table.selectedItems()
        self.add_pdf_btn.setEnabled(bool(selected))
    
    def add_pdf_to_invoice(self):
        """Permite al usuario seleccionar PDFs para añadir a la factura seleccionada"""
        selected_invoice = self.table.selectedItems()
        if not selected_invoice:
            QtWidgets.QMessageBox.warning(self, "No Invoice Selected", "Please select an invoice first.")
            return
        
        # Obtener la carpeta de la factura seleccionada
        folder = self.table.item(selected_invoice[0].row(), 3).text()
        invoice_number = self.table.item(selected_invoice[0].row(), 0).text()
        
        if not os.path.exists(folder):
            QtWidgets.QMessageBox.warning(self, "Error", f"Invoice folder not found:\n{folder}")
            return
        
        # Abrir diálogo de selección de archivos PDF
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            f"Select PDF Files for Invoice {invoice_number}",
            "",
            "PDF Files (*.pdf)"
        )
        
        if not files:
            return
        
        # Copiar archivos seleccionados a la carpeta de la factura
        copied_count = 0
        skipped_files = []
        
        for file_path in files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(folder, filename)
            
            # Verificar si el archivo ya existe
            if os.path.exists(dest_path):
                reply = QtWidgets.QMessageBox.question(
                    self, "File Exists", 
                    f"The file '{filename}' already exists in the invoice folder.\n\nDo you want to overwrite it?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel
                )
                
                if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                    break
                elif reply == QtWidgets.QMessageBox.StandardButton.No:
                    skipped_files.append(filename)
                    continue
            
            # Copiar el archivo
            try:
                shutil.copy(file_path, dest_path)
                copied_count += 1
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error Copying File", f"Could not copy '{filename}':\n{str(e)}")
        
        # Actualizar la lista de PDFs y mostrar mensaje de resultado
        self.show_invoice_pdfs()
        
        message = f"Successfully added {copied_count} PDF(s) to invoice '{invoice_number}'."
        if skipped_files:
            message += f"\n\nSkipped files: {', '.join(skipped_files)}"
        
        QtWidgets.QMessageBox.information(self, "PDFs Added", message)


if __name__ == "__main__":
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
