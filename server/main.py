"""ASGI entrypoint for Uvicorn.

IMPORTANT:
- Always import using the package path to avoid Windows/uvicorn --reload subprocess
	import issues.
- Run from repo root:
		python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8001
"""

from server.app import app

__all__ = ["app"]
"""ASGI entrypoint for Uvicorn.

This project defines the FastAPI app in app.py. Uvicorn commonly looks for `main:app`,
so this module re-exports it for convenience.
"""

from importlib import import_module


def _load_app():
	# Prefer absolute import from the package/module path when running from repo root.
	try:
		return import_module("server.app").app
	except Exception:
		# Fallback when running from within the `server/` directory.
		return import_module("app").app


app = _load_app()

__all__ = ["app"]
