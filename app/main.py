from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import files, auth

app = FastAPI(title="File Storage API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(files.router)

@app.get("/")
async def root():
    return {"message": "File Storage API"}