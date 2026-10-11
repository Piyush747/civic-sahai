# API contracts

All application routes are under `/api/v1`.

- `GET /health` -> `{"status":"ok"}`
- `GET /ready` -> readiness status
- `POST /api/v1/complaints` -> `201` and a complaint
- `GET /api/v1/complaints?skip=0&limit=20&category=...&status=...` -> paginated complaints
- `GET /api/v1/complaints/{complaint_id}` -> complaint or `404`

Create body:

```json
{"title":"Large pothole","description":"A deep pothole near the bus stop.","category":"ROAD_DAMAGE","location":{"latitude":13.0827,"longitude":80.2707,"address":"Example Road, Chennai"},"zone_id":"zone_01"}
```

Errors use `{"error":{"code":"...","message":"..."}}` at the application boundary.

