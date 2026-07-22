"""Resource modules for Xboard Admin API.

Each module wraps one API domain (plan, user, server, etc.).
All inherit from BaseResource which provides common CRUD patterns.
"""

from .base import BaseResource

__all__ = ["BaseResource"]
