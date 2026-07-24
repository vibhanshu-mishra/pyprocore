"""Optional FastAPI read API starter for PyProcore.

This copied template is not part of the PyProcore runtime and does not run
unless you install its optional dependencies and start it yourself.
"""

from app.routes import analytics, health, projects, rfis, submittals
from fastapi import FastAPI

app = FastAPI(title="PyProcore Read API Starter")

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(rfis.router)
app.include_router(submittals.router)
app.include_router(analytics.router)
