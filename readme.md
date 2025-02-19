# 📌 Create Question & Answer Table

A Flask-based web application that processes PDFs, extracts questions and answers(based on color mark as follows question(255, 0, 0) & answer (0, 176, 80)), and formats them into a structured table.

---

## 🚀 Getting Started

### **Prerequisites**
Before running the project, ensure you have the following installed:
- Python 3.10 or later
- pip (Python package manager)
- Virtual environment support (venv)

### **Setup Instructions**

#### **🔹 Windows (Using `run.bat` - Recommended)**
1. **Download or Clone** the project:
   ```batch
   git clone https://github.com/MdZillurRahman/create_question_answer_table.git
   cd create_question_answer_table
   ```
2. **Run the setup script** (creates venv, installs dependencies, and runs the app):
   ```batch
   run.bat
   ```
   Or double-click `run.bat`.

#### **🔹 Linux/macOS (Using `run.sh` - Recommended)**
1. **Download or Clone** the project:
   ```bash
   git clone https://github.com/MdZillurRahman/create_question_answer_table.git
   cd create_question_answer_table
   ```
2. **Give execution permission to the script** (only required once):
   ```bash
   chmod +x run.sh
   ```
3. **Run the setup script**:
   ```bash
   ./run.sh
   ```

---

## 🔍 **Manual Setup (If Not Using Scripts)**
If you prefer manual installation, follow these steps:

### **1️⃣ Create and Activate Virtual Environment**
```bash
python -m venv venv  # Create venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows
```

### **2️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3️⃣ Run the Flask App**
```bash
python app.py
```

---

## 🌍 Access the Web App
Once the app starts, open your browser and go to:
```
http://127.0.0.1:5000
```

---

## ❗ Troubleshooting
### **1️⃣ "ModuleNotFoundError: No module named 'fitz'"**
- Run:
  ```bash
  pip install pymupdf==1.21.0
  ```
- If using Python 3.12, downgrade to Python 3.10 or 3.11.

### **2️⃣ "Command Not Found: wkhtmltoimage" (for `imgkit`)**
- Install it manually:
  ```bash
  sudo apt install wkhtmltopdf -y  # Ubuntu/Linux
  brew install wkhtmltopdf  # macOS
  ```

### **3️⃣ Virtual Environment Not Activating on Windows**
- Run:
  ```batch
  Set-ExecutionPolicy Unrestricted -Scope Process
  .\venv\Scripts\activate
  ```

---

## 🎯 Features
✔️ Upload PDF Files  
✔️ Extract Questions & Answers (Based on color mark as follows question(255, 0, 0) & answer (0, 176, 80))
✔️ Generate Table with Formatting  
✔️ Customize Question & Answer Colors  

---

## 🛠 Built With
- **Backend:** Flask (Python)
- **PDF Processing:** PyMuPDF (`pymupdf`)
- **HTML Generation:** PrettyTable, imgkit
- **Styling:** TailwindCSS (optional)

---

## 📜 License
This project is open-source under the **MIT License**.

---

## 💡 Author
**Md Zillur Rahman**  
[MdZillurRahman](https://github.com/MdZillurRahman)  


Feel free to contribute and make this project even better! 🚀