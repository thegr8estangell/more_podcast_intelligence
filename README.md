# More Podcast Intelligence

Weekly email report tracking top podcast charts across **Spotify**, **Amazon Music**, and **YouTube** — with iHeartMedia show detection built in.

## What it tracks

| Platform | Sections | Source |
|---|---|---|
| 🟢 Spotify | Editors Pick + Top 5 Shows | podcastcharts.byspotify.com |
| 🟠 Amazon Music | Featured + Top 5 Shows | music.amazon.com/podcasts/pages/topcharts |
| 🔴 YouTube | Top 10 Shows (by watchtime) | charts.youtube.com/podcasts |

Each platform section includes:
- **Count box** showing how many shows were pulled
- **iHeart badge** on any detected iHeartMedia shows
- **Side-by-side layout** — featured/editorial left, ranked list right (YouTube is full-width)

A summary bar at the top of the email shows the total iHeart show count across all platforms for that week.

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/more-podcast-intelligence.git
cd more-podcast-intelligence
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### 3. Set environment variables (local testing)
```bash
export GMAIL_EMAIL="your.email@gmail.com"
export GMAIL_PASSWORD="your-app-password"   # Gmail App Password, not your real password
export REPORT_EMAIL="recipient@email.com"
```

> **Gmail App Password**: Go to Google Account → Security → 2-Step Verification → App Passwords. Generate one for "Mail".

### 4. Run locally
```bash
python scraper.py       # Scrapes all platforms → podcast_data.json
python send_report.py   # Builds email → sends it + saves email_preview.html
```

Open `email_preview.html` in your browser to preview before sending.

---

## GitHub Actions (automated weekly)

### Add GitHub Secrets
Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|---|---|
| `GMAIL_EMAIL` | Your Gmail address |
| `GMAIL_PASSWORD` | Your Gmail App Password |
| `REPORT_EMAIL` | Who receives the report |

### Schedule
Runs automatically every **Monday at 8:00 AM EST**.

To trigger manually: Actions tab → "Weekly Podcast Intelligence" → "Run workflow".

---

## iHeart Detection

The scraper checks every show title, author, and description against a list of iHeartMedia identifiers including parent company names, owned studio names (HowStuffWorks, Cool Zone Media, Tenderfoot TV, Pushkin, Shondaland, etc.), and known show titles.

To add new shows, open `scraper.py` and add to the `IHEART_IDENTIFIERS` list at the top.

---

## File Structure

```
more-podcast-intelligence/
├── scraper.py              # Scrapes Spotify, Amazon, YouTube → podcast_data.json
├── send_report.py          # Builds HTML email and sends it
├── requirements.txt
├── .github/
│   └── workflows/
│       └── weekly_scraper.yml
└── README.md
```
