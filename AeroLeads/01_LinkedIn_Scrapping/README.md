# LinkedIn Profile Scraper (MacBook Local Version)

A Streamlit-based LinkedIn profile scraper with **visible browser** support, optimized for MacBook.

## ⚠️ Important Legal Disclaimer

**This tool is for demo purposes only.** Automated scraping of LinkedIn violates their Terms of Service and may result in:
- Account suspension or ban
- IP address blocking
- Legal consequences

**Use at your own risk.**

---

## ✨ Features

- 🖥️ **Visible Chrome Browser** - Watch the scraping happen in real-time
- 🔐 Manual CAPTCHA solving - Browser stays open for you to solve challenges
- 📊 Customizable filters (location, industry, profile count)
- 💾 CSV export with profile data
- 🎨 Clean Streamlit interface
- 🍎 Optimized for MacBook (Intel & Apple Silicon)

## 📋 Data Collected

Each profile includes:
- Name
- Headline/Title
- Current Company & Position
- Location
- About/Summary
- Profile URL

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### 2. Set Up Credentials

Create a `.env` file in the project root:

```env
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
```

### 3. Run the Application

```bash
streamlit run app.py
```

### 4. Start Scraping

1. Open http://localhost:8501 in your browser
2. Configure filters in the sidebar
3. Click "Start Scraping"
4. A Chrome window will open - watch it work!
5. If CAPTCHA appears, solve it manually
6. Download results as CSV

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
MIN_DELAY = 3              # Minimum delay between actions
MAX_DELAY = 7              # Maximum delay between actions
MAX_PROFILES_LIMIT = 20    # Max profiles per session
```

---

## 💡 Tips for Success

### ✅ Best Practices

1. **Use visible browser** - More reliable, less likely to be blocked
2. **Scrape during off-peak hours** - Less traffic, fewer CAPTCHAs
3. **Start small** - Test with 5 profiles first
4. **Use a test account** - Don't risk your primary LinkedIn account
5. **Add delays** - Don't rush, let pages load fully

### Browser Mode Options

The app offers two modes:

- **Visible Browser (Recommended)** 
  - ✅ Watch the scraping process
  - ✅ Solve CAPTCHAs manually
  - ✅ Less likely to be detected
  - ✅ Better for debugging

- **Headless Mode**
  - ⚠️ Runs in background
  - ⚠️ More likely to trigger security
  - ⚠️ Can't solve CAPTCHAs manually

---

## 🐛 Troubleshooting



## 📁 Project Structure

```
LinkedIn_Scrapping/
├── app.py           # Streamlit interface
├── scraper.py       # Selenium scraping logic
├── config.py        # Configuration settings
├── requirements.txt # Python dependencies
├── data/           # Output directory
│   └── linkedin_profiles.csv
└── README.md       # This file
```
