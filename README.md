# 🧾 Digital Invoice Manager

<p align="center">
  <img src="icons/Captura de pantalla 2025-08-16 153257.png" alt="Futura Petroleum Manager Logo" width="400">
</p>

<p align="center">
  <strong>A modern, professional invoice management system built with PyQt6</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#screenshots">Screenshots</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#building">Building</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## 📋 Overview

**Digital Invoice Manager** (also known as **Futura Petroleum Manager**) is a comprehensive desktop application designed for efficient invoice management and PDF document organization. Built with Python and PyQt6, it provides a modern, intuitive interface for creating, viewing, organizing, and managing invoices with integrated PDF support.

### 🎯 Key Highlights

- **Modern UI Design**: Clean, futuristic interface with GitHub-inspired styling
- **Integrated PDF Viewer**: Built-in PDF.js integration for seamless document viewing
- **Year-based Organization**: Automatic invoice organization by year
- **Database Integration**: SQLite backend for reliable data management
- **Drag & Drop Support**: Intuitive file management
- **Status Tracking**: Visual status indicators for invoice completion
- **Multi-format Export**: Support for different document types

---

## ✨ Features

### 📊 Invoice Management
- ✅ **Create New Invoices**: Generate invoices with custom numbers and dates
- ✅ **Year-based Filtering**: Organize and filter invoices by year (2022-2025)
- ✅ **Status Tracking**: Mark invoices as complete/incomplete with visual indicators
- ✅ **Search Functionality**: Quick search by invoice number or date
- ✅ **Batch Operations**: Delete invoices and associated files

### 📄 PDF Management
- ✅ **Drag & Drop Interface**: Easy PDF attachment to invoices
- ✅ **Integrated PDF Viewer**: View PDFs directly within the application
- ✅ **PDF Navigation**: Previous/Next buttons for multi-PDF invoices
- ✅ **File Operations**: Add, delete, and manage PDF attachments
- ✅ **External Opening**: Open PDFs in default system viewer

### 🎨 User Interface
- ✅ **Modern Design**: Clean, professional GitHub-inspired UI
- ✅ **Responsive Layout**: Three-panel layout with tables, viewer, and file list
- ✅ **Visual Status Indicators**: Green checkmarks and red crosses for status
- ✅ **Intuitive Navigation**: Easy-to-use interface with clear visual hierarchy
- ✅ **Year Selector**: Dropdown for easy year filtering

### 🔧 Technical Features
- ✅ **SQLite Database**: Reliable local data storage
- ✅ **PyQt6 Framework**: Modern Qt-based GUI framework
- ✅ **PDF.js Integration**: Web-based PDF viewing without external dependencies
- ✅ **PyInstaller Support**: Create standalone executables
- ✅ **Cross-platform**: Windows, macOS, and Linux support

---

## 🚀 Installation

### Prerequisites

- **Python 3.8+** (recommended: Python 3.9 or higher)
- **pip** (Python package installer)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/DigitalInvoice_Manager.git
   cd DigitalInvoice_Manager
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

### Dependencies

The application requires the following Python packages:

```
PyQt6>=6.5.0          # Modern GUI framework
reportlab>=3.6.12      # PDF generation
PyMuPDF>=1.22.5       # PDF manipulation
```

---

## 💻 Usage

### Getting Started

1. **Launch the Application**
   ```bash
   python main.py
   ```

2. **Create Your First Invoice**
   - Click "Create New Invoice"
   - Enter invoice number (e.g., "INV-2025-001")
   - Set the date
   - Drag and drop PDF files
   - Click "Save Invoice"

3. **Navigate by Year**
   - Use the year dropdown to filter invoices
   - Switch between 2022, 2023, 2024, and 2025

### Main Interface

The application features a three-panel layout:

- **Left Panel**: Invoice table with year selector and search
- **Center Panel**: Integrated PDF viewer with navigation controls
- **Right Panel**: PDF file list for selected invoice

### Key Operations

#### Creating Invoices
1. Select the target year from the dropdown
2. Click "Create New Invoice"
3. Fill in invoice details
4. Drag PDF files to the drop area
5. Save to create invoice folder and database entry

#### Managing Invoices
- **View PDFs**: Select invoice → Select PDF from list
- **Change Status**: Double-click status column (green ✓ or red ✗)
- **Search**: Enter invoice number or date in search box
- **Delete**: Select invoice → Click "Delete Invoice"

#### PDF Operations
- **Navigate**: Use Previous/Next buttons for multi-PDF invoices
- **Open External**: Double-click PDF name to open in system viewer
- **Delete PDF**: Select PDF → Click "Delete Selected PDF"
- **Add PDFs**: Use "Open Folder" to access invoice directory

---

## 🏗️ Architecture

### Project Structure

```
DigitalInvoice_Manager/
├── main.py                 # Main application entry point
├── db.py                   # Database operations
├── pdfgen.py              # PDF generation utilities
├── requirements.txt        # Python dependencies
├── build_executable.spec   # PyInstaller configuration
├── hook-main.py           # PyInstaller hooks
├── invoices.db            # SQLite database (auto-created)
├── icons/                 # Application icons and images
│   ├── app_icon.png       # Application icon
│   ├── logo.png           # Company logo
│   ├── green_check.png    # Status indicator (complete)
│   ├── red_cross.png      # Status indicator (incomplete)
│   ├── next.png           # Navigation icon
│   └── prev.png           # Navigation icon
├── viewer/                # PDF.js integration
│   ├── build/             # PDF.js build files
│   └── web/               # PDF.js web viewer
└── data/                  # Invoice storage (auto-created)
    ├── 2022/              # Year-based organization
    ├── 2023/
    ├── 2024/
    └── 2025/
```

### Database Schema

```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    date TEXT NOT NULL,
    folder TEXT NOT NULL,
    status TEXT DEFAULT 'incompleto'
);
```

### Key Components

#### `MainWindow` Class
- Primary application interface
- Handles invoice table, PDF viewer, and file management
- Manages year-based filtering and search functionality

#### `InvoiceCreateDialog` Class
- Modal dialog for creating new invoices
- Drag-and-drop interface for PDF files
- Validates input and creates directory structure

#### `DropArea` Class
- Custom PyQt6 widget for drag-and-drop functionality
- Accepts PDF files only
- Provides visual feedback during drag operations

#### Database Operations (`db.py`)
- `init_db()`: Initialize SQLite database
- `add_invoice()`: Create new invoice record
- `get_invoices()`: Retrieve all invoices
- `update_invoice_status()`: Change completion status
- `delete_invoice()`: Remove invoice record

---

## 🔨 Building

### Creating Executable

The project includes PyInstaller configuration for creating standalone executables:

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build executable**
   ```bash
   pyinstaller build_executable.spec
   ```

3. **Find executable**
   - Windows: `dist/DigitalInvoiceManager.exe`
   - macOS: `dist/DigitalInvoiceManager.app`
   - Linux: `dist/DigitalInvoiceManager`

### Build Configuration

The `build_executable.spec` file includes:
- All icons and resources
- PDF.js viewer files
- Database inclusion
- Hidden imports for PyQt6 and dependencies
- Application icon setting

---

## 🎨 Screenshots

### Main Interface
*The main application window showing the three-panel layout with invoice table, PDF viewer, and file list.*

### Creating Invoices
*Invoice creation dialog with drag-and-drop PDF support and date selection.*

### PDF Viewing
*Integrated PDF viewer with navigation controls and file selection.*

---

## 🔧 Development

### Code Style
- **Python Style**: PEP 8 compliant
- **UI Style**: GitHub-inspired modern design
- **Comments**: Comprehensive Spanish comments in source code

### Key Features Implementation

#### Modern UI Styling
```python
futuristic_style_main = """
    QWidget {
        background-color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #333333;
    }
    QPushButton {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        padding: 8px 14px;
    }
"""
```

#### PDF.js Integration
```python
def show_pdf_in_viewer(self, current, previous):
    pdfjs_viewer_path = resource_path("viewer/web/viewer.html")
    viewer_url = QUrl.fromLocalFile(pdfjs_viewer_path)
    pdf_url = QUrl.fromLocalFile(abs_path)
    query = QUrlQuery()
    query.addQueryItem("file", pdf_url.toString())
    viewer_url.setQuery(query)
    self.pdf_viewer.setUrl(viewer_url)
```

#### Year-based Organization
```python
def load_invoices_by_year(self):
    selected_year = self.year_combo.currentText()
    year_folder = os.path.join("data", selected_year)
    # Load invoices from year-specific folder
```

---

## 🤝 Contributing

### Getting Started
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 Python style guidelines
- Add comments in Spanish (as per project convention)
- Test changes across different years and invoice scenarios
- Ensure PyInstaller compatibility for new features

### Areas for Contribution
- 🌐 **Internationalization**: Multi-language support
- 📊 **Reporting**: Advanced invoice reporting and analytics
- 🔄 **Import/Export**: Excel/CSV import/export functionality
- 🎨 **Themes**: Additional UI themes and customization
- 📱 **Responsive Design**: Better scaling for different screen sizes
- 🔍 **Advanced Search**: More sophisticated filtering options

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **PyQt6**: For providing the excellent GUI framework
- **PDF.js**: For the robust PDF viewing capabilities
- **ReportLab**: For PDF generation functionality
- **SQLite**: For reliable local database storage

---

## 📞 Support

For support, bug reports, or feature requests:

1. **Issues**: Use GitHub Issues for bug reports and feature requests
2. **Discussions**: Use GitHub Discussions for general questions
3. **Email**: Contact the maintainers directly

---

<p align="center">
  <strong>Built with ❤️ for modern invoice management</strong>
</p>

<p align="center">
  <img src="icons/logoApp.png" alt="Application Logo" width="100">
</p>
