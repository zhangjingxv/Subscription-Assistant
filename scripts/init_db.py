#!/usr/bin/env python3
"""Initialize database - simple and direct"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from app.core.db import Base, engine

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")