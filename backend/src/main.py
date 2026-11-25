from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from application.realtime.connection_manager import get_connection_manager
from application.realtime.ws_subscriber import subscribe_realtime
from infrastructure.events.composition import get_event_bus
from infrastructure.settings import settings
from interfaces.api.actuators import router as actuators_router
from interfaces.api.alerts import router as alerts_router
from interfaces.api.automation import router as automation_router
from interfaces.api.commands import device_commands_router
from interfaces.api.commands import router as commands_router
from interfaces.api.devices import router as devices_router
from interfaces.api.health import router as health_router
from interfaces.api.locations import router as locations_router
from interfaces.api.overview import router as overview_router
from interfaces.api.sensors import router as sensors_router
from interfaces.api.ws import router as ws_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start the WebSocket hub and attach it to the shared event bus."""
    manager = get_connection_manager()
    await manager.start()
    unsubscribe = subscribe_realtime(get_event_bus(), manager)
    try:
        yield
    finally:
        unsubscribe()
        await manager.stop()


app = FastAPI(
    title="Smart Greenhouse API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(actuators_router)
app.include_router(commands_router)
app.include_router(device_commands_router)
app.include_router(alerts_router)
app.include_router(locations_router)
app.include_router(automation_router)
app.include_router(overview_router)
app.include_router(ws_router)


@app.get("/")
def root():
    return {
        "message": "Smart Greenhouse API",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
        "websocket": "/api/ws",
    }


@app.get("/scalar", include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
