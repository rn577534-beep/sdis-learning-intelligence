"""Vercel entrypoint for the SDIS FastAPI application."""

from sdis_app.main import app

__all__ = ["app"]
