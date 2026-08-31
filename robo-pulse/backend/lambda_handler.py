"""
Robopulse Command Center
Day 9 - the entrypoint that AWS Lambda actually calls. Mangum translates
between lambda's event/context invocation model and the ASGI interface
that FastAPI already speaks - app.main:app itself needs zero changes
to run inside lambda
"""

from mangum import Mangum

from app.main import app

handler = Mangum(app)