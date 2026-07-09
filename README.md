# 🛡️ StegoScan - LSB Image Steganography & Detection System

StegoScan is a cybersecurity-based web application that allows users to hide, extract, and detect hidden information inside digital images using Least Significant Bit (LSB) steganography techniques.

The project combines image processing, data hiding, payload recovery, and statistical steganalysis to demonstrate both the creation and detection of steganographic content.

---

## 🚀 Live Demo

🔗 https://stegoscan-h56i.onrender.com

---

## 📌 Features

### 🔐 Data Embedding

- Hide secret text messages inside images
- Hide files inside images
- Hide images inside images
- Password protected embedding support
- Supports PNG, JPG, WEBP input formats
- Automatic conversion to PNG stego output
- Adaptive image optimization
- Standard and Robust embedding profiles

---

### 🔎 Data Extraction

- Extract hidden messages from stego images
- Recover embedded files
- Recover hidden images
- Password verification support
- Secure payload reconstruction

---

### 📊 Steganography Detection

StegoScan includes statistical analysis techniques to identify possible hidden data:

- Chi-Square Analysis
- LSB Balance Analysis
- Entropy Analysis
- Region-based LSB Difference Detection
- Visual LSB Plane Inspection

Detection results include:

- Risk score
- Detection confidence
- Suspicious pattern indicators
- Statistical metrics visualization

---

## 🧠 How It Works

### LSB Embedding

Digital images store pixels using RGB values.

Example:

```
Original pixel:
10110110

Modified pixel:
10110111
```

Only the least significant bit is changed, creating a visually invisible modification while storing hidden information.

---

### Detection Logic

The detector analyzes statistical changes introduced by LSB modifications.

It checks:

- Randomness of LSB distribution
- Difference between image regions
- Bit balance patterns
- Statistical deviation using Chi-Square testing

---

## 🛠️ Tech Stack

### Frontend

- HTML5
- CSS3
- JavaScript
- Canvas animations
- Responsive UI

### Backend

- Python
- Flask
- NumPy
- Pillow
- SciPy

---

## 📁 Project Structure

```
StegoScan/

├── app.py
├── requirements.txt
├── README.md

├── templates/
│   └── index.html

├── static/

│   ├── css/
│   │   ├── base.css
│   │   ├── layout.css
│   │   ├── header-hero.css
│   │   ├── forms.css
│   │   ├── results.css
│   │   └── tabs.css

│   ├── js/
│   │   ├── background.js
│   │   ├── ui.js
│   │   ├── embed.js
│   │   ├── extract.js
│   │   └── detect.js

│   └── images/
│       └── logo.png
```

---

## ⚙️ Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_LINK
```

Move into project folder:

```bash
cd StegoScan
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run application:

```bash
python app.py
```

Open:

```
http://localhost:5000
```

---

## 🔐 Security Note

This project is created for educational and research purposes.

Steganography detection is based on statistical probability. Results indicate possible hidden data patterns but cannot guarantee absolute detection for every steganography technique.

---

## 🎯 Future Improvements

- AI-based steganography detection
- Support for additional embedding algorithms
- Advanced encryption methods
- Batch image analysis
- Detailed forensic reports

---

## 👨‍💻 Developer

Developed by Prabhat

Cybersecurity & Image Processing Project