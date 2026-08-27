"""
RoboPulse Fleet Command Center
Day 4 - FastAPI application entrypoint.

Run from backend/ with the venv active:
    fastapi dev app/main.py

Day 7 update- Added CORS configuration to connect with the frontend    
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import robots, missions, auth

#set up the FastAPI application with a title, description, and version. 
# This metadata is used in the automatically generated OpenAPI documentation.
app = FastAPI(
    title="RoboPulse Fleet Command Center",
    description=(
        "Fleet management API for Apex Robotics' autonomous "
        "inspection rovers and aerial drones."
    ),
    version="0.1.0",
)

#CORS Configuration
app.add_middleware(
    CORSMiddleware,
    #The endpoint for our frontent, currently provided by the vite dev server
    allow_origins=["http://localhost:5173"],
    #This allows us to pass an Authorization header (JWT)
    allow_credentials=True,
    #This allows all methods and headers through
    allow_methods=["*"],
    allow_headers=["*"]
)


#include the /robots router in the FastAPI application. This means that all routes defined
# in the robots router will be available under the /robots path.
app.include_router(robots.router)
app.include_router(missions.router)
app.include_router(auth.router)

#A simple health check endpoint to verify that the API is running.
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

