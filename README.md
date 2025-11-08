# 💳 Card Checker Pro - Web UI

Fast and accurate credit card validation tool with beautiful web interface.

## 🚀 Features

- ✅ **Real-time checking** - See results instantly as cards are validated
- 📊 **Live statistics** - Track LIVE, DEAD, INVALID, and UNKNOWN cards
- 💾 **Export LIVE cards** - Download all valid cards to a text file
- 📁 **File upload** - Upload card lists from .txt files
- 🎨 **Beautiful UI** - Modern gradient design with smooth animations
- ⚡ **Fast processing** - Automated browser-based validation

## 📋 Requirements

- Python 3.7+
- Chrome/Chromium browser
- Virtual environment (recommended)

## 🔧 Installation

1. **Clone or download the project**

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install seleniumbase flask flask-cors requests
```

## 🎯 Usage

### Starting the Web UI

1. **Activate virtual environment**
```bash
source venv/bin/activate
```

2. **Run the Flask app**
```bash
python app.py
```

3. **Open browser**
Navigate to: `http://localhost:5001`

### Using the Interface

1. **Input Cards**
   - Type or paste cards into the textarea (one per line)
   - Or click "Choose File" to upload a .txt file

2. **Card Format**
   ```
   number|month|year|cvv
   ```
   Example: `5312600051185964|3|2027|682`

3. **Start Checking**
   - Click "🚀 Start Checking" button
   - Watch results appear in real-time

4. **Export LIVE Cards**
   - After checking completes, click "💾 Export LIVE Cards"
   - File will download automatically with timestamp

### Command Line Usage

You can also use the command-line version:

```bash
python card_checker_pro.py -i cards.txt -o results.txt
```

Options:
- `-i, --input`: Input file with card list
- `-o, --output`: Output file for results
- `-t, --threads`: Number of threads (default: 5)
- `--headless`: Run browser in headless mode
- `--no-headless`: Show browser window

## 📁 File Structure

```
Check_ci/
├── app.py                  # Flask web application
├── card_checker_pro.py     # Core checker logic
├── templates/
│   └── index.html         # Web UI template
├── static/
│   ├── css/
│   │   └── style.css      # Styles
│   └── js/
│       └── app.js         # Frontend logic
├── cards_sample.txt       # Sample cards
└── README.md             # This file
```

## 🎨 Features Explained

### Real-time Results
Results appear instantly as each card is checked, with color coding:
- 🟢 **LIVE** - Card is valid and accepted
- 🔴 **DEAD** - Card was declined
- 🟡 **INVALID** - Wrong format
- 🔵 **UNKNOWN** - Status unclear

### Export Function
- Automatically saves all LIVE cards
- Filename includes timestamp: `live_cards_2025-11-05T01-30-00.txt`
- One card per line, ready to use

### Statistics Dashboard
Real-time counters show:
- Total LIVE cards found
- Total DEAD cards
- Invalid format cards
- Unknown status cards

## ⚙️ Configuration

### Change Port
Edit `app.py` line 179:
```python
app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
```

### Adjust Threads
For command-line mode, use `-t` flag:
```bash
python card_checker_pro.py -i cards.txt -t 10
```

## 🔒 Security Notes

- This tool is for educational purposes only
- Never use on real credit cards without authorization
- Always respect privacy and legal regulations
- Use responsibly and ethically

## 🐛 Troubleshooting

### Port Already in Use
If port 5001 is busy, change it in `app.py` or disable AirPlay Receiver on macOS.

### Browser Not Opening
Make sure Chrome/Chromium is installed and accessible.

### Slow Performance
- Reduce thread count
- Use headless mode
- Check internet connection

## 📝 License

This project is for educational purposes only.

## 👨‍💻 Author

Created with ❤️ for learning and testing purposes.
