# Facade — location overview

`LocationOverviewFacade.get_overview(location_id)` gives the HTTP handler one entry point for a dashboard read model. It coordinates the location, device and reading repositories and delegates the recommendation to `AutomationService`; it does not implement sensor translation, strategy policy or persistence. The handler knows only the facade, and the UI uses one overview request rather than assembling multiple responses.

The facade reads the existing `locations`, `zones`, `devices`, `sensor_readings`, and `automation_rules` tables. No new business table or view is needed. `last_recommendation` is computed on each GET, not a stored history item; the active strategy is the saved key or the existing default. Refreshing the overview fetches current database values.

Device counts are grouped in one query. Latest readings use a window function to select one row per sensor in one query, rather than making a query for every device (the N+1 problem). The automation service performs its own bounded set of queries. Results from concurrent writes can change between these queries; the response is not a transactionally consistent snapshot.

## Location ownership

`devices.location_id` is a nullable foreign key to `locations`. It is not a new Phase 7 business table: Phases 3 and 4 explicitly allowed this optional nullable link for future use, and this implementation activates that earlier-phase extension. Unassigned devices are excluded from location overviews until an operator assigns them.

The assignment path is `PATCH /api/devices/{device_id}/location` with `{ "location_id": "<uuid>" }`; sending `null` clears the assignment. The service validates both the device and location before saving, and the dashboard displays each device's current assignment.

Counts, latest readings, and the moisture input to the recommendation are now all filtered by the same `location_id`. This matters because the strategy is already selected per location; using a global moisture reading there would make the recommendation belong to a different site. No freshness limit is currently applied to moisture readings.
