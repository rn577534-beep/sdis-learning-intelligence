"""Vercel entrypoint for the SDIS FastAPI application."""

# Keep this entrypoint separate from the package to avoid Python import collisions.
from sdis_app.main import app

__all__ = ["app"]
