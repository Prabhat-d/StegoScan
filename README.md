# 🛡️ StegoScan - Advanced Steganography & Forensic Inspector

**StegoScan** is an end-to-end cybersecurity and steganalysis web platform built to embed, extract, and inspect hidden payloads in digital cover images using Least Significant Bit (LSB) steganography and statistical steganalysis math.

Combines high-speed in-memory image processing, authenticated AES-256-GCM encryption, RS Steganalysis (Fridrich et al.), and Westfeld Chi-Square PoV (Pairs of Values) parity equalization for real-time forensic detection.

---

## 🔗 Live Application Link

- 🌐 **Vercel Live Application**: [https://stegoscan-tau.vercel.app](https://stegoscan-tau.vercel.app)

---

## ⚡ Core Modules & Features

### 🔐 1. Payload Embedder (`/embed`)
- **Multi-Format Payloads**: Hide secret text messages, documents (`.pdf`, `.docx`, `.zip`), or hidden cover images inside PNG/JPG/WEBP/BMP cover images.
- **Authenticated AES-256-GCM Encryption**: Optional password protection using PBKDF2 key derivation and Galois/Counter Mode authentication.
- **Protocol Magic Headers**: Injects zero-latency magic prefixes (`STGO` for unencrypted, `PWS1` for AES-256 encrypted packages).
- **Adaptive Memory Safety**: Enforces 25MB safety caps and explicit memory garbage collection (`gc.collect()`).

### 📥 2. Payload Extractor (`/extract`)
- **Smart Payload Reconstruction**: Recovers plaintext messages, downloads original embedded files with intact filenames/MIME types, or displays hidden images.
- **Cryptographic Verification**: Verifies AES-256 GCM authentication tags and prompts for passwords when accessing encrypted packages.
- **Strict Format Checking**: Rejects lossy formats (`.jpg`/`.webp`) during extraction to prevent bit corruption.

### 🔬 3. Forensic Steganalysis Engine (`/detect`)
- **RS Steganalysis (Fridrich et al.)**: Dual quadratic curve solver evaluating regular ($R_m$) vs singular ($S_m$) pixel mask correlations to estimate hidden payload volume in KB and cover capacity percentage.
- **Spatial Block Westfeld Chi-Square PoV**: Evaluates 4 spatial image blocks (0–25%, 25–50%, 50–75%, 75–100%) to catch sequential, localized, and single-channel LSB attacks ($p \to 1.0$).
- **Regional LSB Variance**: Measures LSB ratio variance across 20 spatial image slices to flag non-uniform embedding patterns.
- **LSB Bit Balance & Entropy**: Evaluates Shannon LSB entropy ($1.0000$ max) and 50:50 parity distribution shifts.
- **📦 Payload Metadata Inspector**: Conditional sub-tab unlocked only when hidden data is detected. Displays decoded encryption layer, content type, exact byte size, and header signature validation.
- **29x Speedup Acceleration**: Optimized PNG base64 stream encoding, executing full statistical analysis in **<0.3 seconds**.

---

## 🧠 Forensic Math & Detection Logic

### 1. RS Steganalysis (Fridrich et al.)
Calculates regular ($R_m$, $R_{-m}$) and singular ($S_m$, $S_{-m}$) pixel groups under dual spatial masks ($M = [0, 1, 1, 0]$):
$$\Delta R = R_m - R_{-m}, \quad \Delta S = S_m - S_{-m}$$
Solving the quadratic intersection estimates the payload ratio $p$ independently of header signatures or encryption.

### 2. Westfeld Chi-Square PoV Parity Test
Evaluates frequency equalization between adjacent intensity pairs $(2k, 2k+1)$:
$$\chi^2 = \sum_{k=0}^{127} \frac{(n_{2k} - n_{2k+1})^2}{2 y_k}$$
Under steganographic embedding, $n_{2k} \approx n_{2k+1}$, causing $\chi^2 \to 0$ and $p \to 1.0000$ (indicating stego parity equalization).

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism UI, Responsive Mobile Design), Client-Side JS, HTML5 Canvas.
- **Backend**: Python 3.13, Flask 3.1, NumPy 2.2, SciPy 1.15, Pillow (PIL) 11.1, Cryptography 44.0.
- **Deployment**: Render WSGI (Gunicorn), Vercel Serverless (`@vercel/python`).

---

## 📁 Project Structure

```
StegoScan/
├── app.py                     # Main Flask Application & Blueprint Registry
├── vercel.json                # Vercel Serverless Deployment Configuration
├── requirements.txt           # Python Dependencies
├── README.md                  # Project Documentation
├── core/
│   ├── security.py            # AES-256-GCM Cryptographic Engine (PBKDF2)
│   ├── steganalysis.py        # RS Steganalysis, Chi-Square PoV & Metadata Probe
│   └── stego_engine.py        # LSB Payload Serialization & Bit Manipulation
├── routes/
│   ├── embed_routes.py        # /embed Endpoint with Format & 25MB Caps
│   ├── extract_routes.py      # /extract Endpoint with Format & Password Verification
│   └── detect_routes.py       # /detect Endpoint with Spatial Block Analysis & Metadata
├── templates/
│   └── index.html             # Main Forensic Dashboard Template
└── static/
    ├── css/                   # Modular Glassmorphism Stylesheets
    └── js/                    # Modular Client JS (detect.js, ui.js, embed.js, etc.)
```

---

## ⚙️ Local Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Prabhat-d/StegoScan.git
   cd StegoScan
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the local development server**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   Open `http://localhost:5000` in your web browser.

---

## 🚀 Deploying to Vercel

1. Fork or push this repository to GitHub.
2. Log in to [Vercel](https://vercel.com) and click **Add New Project**.
3. Import `Prabhat-d/StegoScan`. Vercel automatically detects `vercel.json`.
4. Click **Deploy**.

---

## 👨‍💻 Developer Profile

Developed with ❤️ by **Prabhat Jhanji**  
- **Portfolio**: [https://prabhatjhanji.netlify.app](https://prabhatjhanji.netlify.app)  
- **GitHub**: [@Prabhat-d](https://github.com/Prabhat-d)  

---

## 🔐 License & Security Notice

Created for educational, security research, and digital forensics purposes. Steganography detection provides probabilistic indicators based on statistical signals.