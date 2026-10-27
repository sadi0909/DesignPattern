# Facade — location overview

`LocationOverviewFacade.get_overview(location_id)` gives the HTTP handler one entry point for a dashboard read model. It coordinates the location, device and reading repositories and delegates the recommendation to `AutomationService`; it does not implement sensor translation, strategy policy or persistence. The handler knows only the facade, and the UI uses one overview request rather than assembling multiple responses.

The facade reads the existing `locations`, `zones`, `devices`, `sensor_readings`, and `automation_rules` tables. No new business table, view, or migration is needed. `last_recommendation` is computed on each GET, not a stored history item; the active strategy is the saved key or the existing default. Refreshing the overview fetches current database values.

Device counts are grouped in one query. Latest readings use a window function to select one row per sensor in one query, rather than making a query for every device (the N+1 problem). The automation service performs its own bounded set of queries. Results from concurrent writes can change between these queries; the response is not a transactionally consistent snapshot.

**Important scope limitation:** devices currently have no location or zone association. Counts and readings are therefore global, not location-specific, and the automation service also evaluates the newest global moisture reading. The API schema and dashboard state this explicitly; do not use the result as location-isolated automation. The route does scope the location, zones and strategy by `location_id`. Fixing device ownership requires a separate schema and workflow change, outside the no-new-business-schema scope of this phase. No freshness limit is currently applied to moisture readings.
