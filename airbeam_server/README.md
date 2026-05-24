# 🌬️ AirBeam Research Dashboard

Sasha's air quality research project — Summer 2026.
Measures PM1, PM2.5, PM10, temperature, and humidity across environments in Parksville/Nanaimo, BC using an AirBeam sensor.

---

## Quick Start (Server Setup)

### Requirements
- Ubuntu/Debian Linux
- Python 3.8+
- Nginx (for domain routing)

### 1. Clone the repo
```bash
git clone https://github.com/SashaCharnock/airbeam-research.git
cd airbeam-research
```

### 2. Run the deploy script
```bash
chmod +x deploy.sh
./deploy.sh
```

This installs dependencies and sets up a systemd service that starts automatically on reboot.

### 3. Set up Nginx
Follow the instructions printed by `deploy.sh` to point your domain at the app.

### 4. Seed the database with existing data
Once the server is running, open the dashboard in a browser, log in, and upload `merged_sessions.xlsx` using the upload button. All 59 existing sessions will sync automatically.

---

## Usage

**Password:** `airbeam2026`

**Uploading new data:**
1. Run `python merge.py` on your local machine to generate `merged_sessions.xlsx`
2. Open the dashboard → drag and drop `merged_sessions.xlsx` onto the upload area
3. New sessions sync to the server instantly — your teacher sees them immediately

**Editing sessions:**
- Click any session to expand it
- Click **Edit** to add location, independent variables, notes, and photos
- Changes save to the server automatically

---

## File Structure

```
airbeam-research/
├── app.py              ← Flask backend (API + serves the dashboard)
├── requirements.txt    ← Python dependencies
├── deploy.sh           ← One-command server setup
├── templates/
│   └── index.html      ← The full dashboard (React, no build step)
└── airbeam.db          ← SQLite database (auto-created, NOT in git)
```

---

## Local Python Scripts (run on Sasha's computer)

| Script | Purpose |
|---|---|
| `merge.py` | Pairs session + notes CSVs → `merged_sessions.xlsx` |
| `update_template.py` | Inserts sessions into `template_filled.xlsx` |

**Workflow:**
```
Export CSVs from AirCasting app
        ↓
  python merge.py          → merged_sessions.xlsx
        ↓
  Upload to dashboard      → server database updated
        ↓
  python update_template.py → template_filled.xlsx updated
```

---

## Research Categories

| Category | Color | Independent Variables |
|---|---|---|
| Bus Stops | 🟡 Gold | Distance, Shelter, Traffic, Highway |
| Riding Bus | 🟢 Green | # People, Position, Windows |
| City Comparison | 🔵 Blue | Crowding, Traffic, Wind, Weather |
| Dental | 🩷 Pink | Dog Size, Tartar, # Extractions, Mask |
| Cooking | 💛 Yellow | Appliance, Windows |
| Events | 🟣 Purple | Crowding, Proximity |
| For Fun | 🌸 Rose | Crowding |

---

*Project by Sasha Charnock · Built with Flask + React · 2026*
