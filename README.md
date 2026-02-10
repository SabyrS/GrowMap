# GrowMap
Personal assistant for planning and analyzing garden or balcony plantings.

## Features
- User accounts: registration, login, private maps and plants per user.
- Interactive 2D map (SVG) with objects and plant info on click.
- Plant catalog with basic requirements (water, sun, bed type).
- Weather-driven recommendations (not just raw temperature).
- One analytics page with 1-2 charts and short summary.
- Plant compatibility warnings when objects are close.
- Harvest logging with efficiency vs average yield.
- Action history (watering, planting, harvest) for analytics.

## Tech stack
- Python + Flask
- SQLite
- Vanilla JS + SVG
- Chart.js (analytics page)
- Open-Meteo API (no key required)

## Setup
1. Create and activate virtual environment.
   - Windows (PowerShell):
     - `python -m venv venv`
     - `venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the app:
   - `python app.py`
4. Open in browser:
   - `http://127.0.0.1:5000`

## Usage
1. Register a user and log in.
2. Create a map with plot dimensions.
3. Open the editor and add plants, buildings, or zones.
4. Select plants to log watering or harvest.
5. Check Weather for recommendations and Analytics for trends.

## Documentation
- API description: [docs/API.md](docs/API.md)
- ML usage: [docs/ML.md](docs/ML.md)
- Presentation: [docs/Presentation.pdf](docs/Presentation.pdf)

## Notes
- The database file is local and ignored by Git.
- Weather data comes from Open-Meteo.
