# GrowMap API
Base URL: `http://127.0.0.1:5000`

## Auth and pages
- `GET /login` - login page
- `POST /login` - login
- `GET /register` - register page
- `POST /register` - register
- `GET /logout` - logout

## Maps
- `GET /maps` - list user maps
- `GET /maps/create` - create map page
- `POST /maps/create` - create map
- `GET /editor/<map_id>` - editor page

## Catalog and compatibility
- `GET /api/catalog`
  - Response: list of plant catalog items.
- `GET /api/compat`
  - Response: list of compatibility pairs.

## Map objects
- `GET /api/maps/<map_id>/objects`
  - Response: objects for a map (includes plant details if plant).

- `POST /api/maps/<map_id>/objects`
  - Body (circle):
    - `type`, `shape`, `x`, `y`, `size`, `color`, `name`, `plant_id`, `planted_at`, `bed_type`
  - Body (rect):
    - `type`, `shape`, `x`, `y`, `width`, `height`, `color`, `name`, `plant_id`, `planted_at`, `bed_type`
  - Body (polygon):
    - `type`, `shape`, `points`, `color`, `name`

- `DELETE /api/objects/<obj_id>`
  - Deletes object (ownership checked).

## Logs
- `GET /api/logs?map_id=<map_id>`
  - Response: last 50 logs for map.
- `POST /api/logs`
  - Body: `map_id`, `action_type`, `plant_object_id`, `amount`, `note`

## Harvest
- `POST /api/harvest`
  - Body: `map_id`, `plant_object_id`, `amount`, `unit`
  - Response: efficiency vs average yield (if available).

## Weather
- `GET /weather`
  - Weather recommendations and forecast UI.
- `POST /weather`
  - Body: `lat`, `lon` to update location.
