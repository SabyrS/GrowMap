# GrowMap
Personal assistant for planning and analyzing garden or balcony plantings.

## Features
- **User accounts**: Registration with secure password validation (12+ chars, letters, digits, special characters), login, private maps per user.
- **Interactive 2D map (SVG)**: Create and edit objects (plants, buildings, zones) with visual feedback.
- **Plant catalog**: Basic requirements (water, sun, bed type) with plant compatibility checking.
- **Smart geolocation**: Browser-based location detection with IP fallback (4 providers: ipwho.is, ipapi.co, MaxMind, ip-api.com).
- **Weather recommendations**: Current weather + 7-day forecast with gardening advice based on Open-Meteo API.
- **Area & age calculations**: Automatic area display (m²) and object age tracking.
- **Plant compatibility**: Warnings when incompatible objects are placed nearby.
- **Building restrictions**: Prevents watering and harvest logging on building objects.
- **Harvest logging**: Track harvests with efficiency vs average yield comparison.
- **Action history**: Watering, planting, and harvest logs for analytics.
- **Analytics dashboard**: Temperature trends, watering activity, and harvest comparison charts.
- **Input validation**: SQL injection protection, password security requirements.
- **Logging system**: Authentication and system activity tracking in `growmap_auth.log`.

## Tech stack
- **Backend**: Python 3.11 + Flask 3.0.2
- **Database**: SQLite3 with 8 tables (users, maps, map_objects, plant_catalog, plant_compat, logs, harvests, schema)
- **Frontend**: Vanilla JavaScript + SVG + CSS
- **Charts**: Chart.js 3.x with value label plugins
- **APIs**: 
  - Open-Meteo (weather data)
  - OSM Nominatim (reverse geocoding)
  - Multiple IP geolocation providers
- **Security**: Werkzeug password hashing, parameterized SQL queries, input validation

## Setup
1. Create and activate virtual environment.
   - Windows (PowerShell):
     - `python -m venv venv`
     - `venv\Scripts\Activate.ps1`
   - Linux/macOS:
     - `python3 -m venv venv`
     - `source venv/bin/activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the app:
   - `python app.py`
4. Open in browser:
   - `http://127.0.0.1:5000`

## Password Requirements
When registering, passwords must meet these security criteria:
- Minimum **12 characters**
- At least one **letter** (A-Z, a-z, а-я, А-Я)
- At least one **digit** (0-9)
- At least one **special character** (!@#$%^&* etc.)
- No SQL injection patterns (SELECT, DROP, UNION, etc.)

## Usage
1. Register a user with a secure password and log in.
2. Create a map with plot dimensions.
3. Open the editor and add plants, buildings, or zones.
4. Select objects to view area, age, and log actions.
5. Log harvests with weight (only for plant objects).
6. Check **Weather** for location-based recommendations and 7-day forecast.
7. Visit **Analytics** for temperature trends, watering activity, and harvest efficiency.

## Project Structure
```
growmap/
├── app.py              # Flask app initialization
├── auth.py             # Authentication routes with validation and logging
├── db.py               # Database connection
├── models.py           # Database schema
├── routes.py           # Main API endpoints
├── runtime.txt         # Python version for deployment
├── requirements.txt    # Python dependencies
├── tempa.py            # Database operations guide
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   ├── home.html       # Landing page
│   ├── login.html      # Login page
│   ├── register.html   # Registration with validation
│   ├── maps.html       # User's maps list
│   ├── create_map.html # Map creation form
│   ├── editor.html     # SVG map editor with harvest logging
│   ├── weather.html    # Weather page with geolocation
│   └── analytics.html  # Charts and statistics
├── static/
│   ├── style.css       # Main styles
│   ├── map.js          # Map list functionality
│   └── editor.js       # Editor logic (objects, selection, harvest UI)
└── docs/
    ├── API.md          # API documentation
    ├── ML.md           # ML usage documentation
    ├── index.html      # GitHub Pages landing
    └── style.css       # Docs styling
```

## Documentation
- API description: [docs/API.md](docs/API.md)
- ML usage: [docs/ML.md](docs/ML.md)
- Database operations guide: [tempa.py](tempa.py)

## Deployment (Free)
### Frontend (GitHub Pages)
1. Ensure GitHub Pages is set to use the `/docs` folder.
2. The landing page lives at `docs/index.html`.

### Backend (Render)
1. Create a new Web Service from this repo on [render.com](https://render.com).
2. **Build command**: `pip install -r requirements.txt`
3. **Start command**: `gunicorn app:app`
4. Set environment variables:
   - `SECRET_KEY` for Flask session security (recommended: generate random string)
   - `PYTHON_VERSION=3.11` (optional, specified in runtime.txt)
5. After deployment, update Render URL in frontend code if needed.

**Important**: Make sure `requirements.txt` includes all dependencies:
```
Flask==3.0.2
Werkzeug==3.0.1
gunicorn==20.1.0
requests==2.31.0
```

## Security Features
- **Password hashing**: Werkzeug's `generate_password_hash()` with salt
- **SQL injection prevention**: Parameterized queries, input validation with regex
- **Session management**: Flask sessions with `SECRET_KEY`
- **Input sanitization**: Username and password validation before database operations
- **Dangerous pattern detection**: Blocks SQL keywords and malicious sequences
- **Activity logging**: All authentication attempts logged to `growmap_auth.log`

## API Endpoints
### Authentication
- `POST /register` - User registration with validation
- `POST /login` - User authentication
- `GET /logout` - Clear session

### Maps
- `GET /` - User's maps list
- `POST /api/maps` - Create new map
- `DELETE /api/maps/<id>` - Delete map

### Objects
- `POST /api/maps/<id>/objects` - Add object to map
- `GET /api/maps/<id>/objects` - Get all objects
- `DELETE /api/objects/<id>` - Delete object

### Logs & Harvests
- `POST /api/logs` - Log watering/planting action
- `POST /api/harvest` - Log harvest (with building restriction)
- `GET /api/harvests?plant_object_id=<id>` - Get harvest history
- `DELETE /api/harvests/<id>` - Delete harvest record

### Location & Weather
- `GET /api/location/ip` - Get location by IP (4-provider fallback)
- `GET /api/location/reverse?lat=<lat>&lon=<lon>` - Reverse geocoding (city/country from coordinates)
- `GET /weather` - Weather page with geolocation
- `GET /analytics` - Analytics dashboard

## Notes
- The database file (`instance/growmap.db`) is created automatically and ignored by Git.
- Weather data comes from Open-Meteo API (no API key required).
- Geolocation uses browser API first, then falls back to IP-based detection.
- IP geolocation providers rotate on failure: ipwho.is → ipapi.co → MaxMind → ip-api.com
- City/country names retrieved via OSM Nominatim reverse geocoding.
- All logs written to `growmap_auth.log` (not tracked in Git).

## Contributing
For adding new plants to the catalog or compatibility rules, see the SQL examples in [tempa.py](tempa.py).
