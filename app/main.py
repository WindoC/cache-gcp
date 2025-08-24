from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routes import files, auth

app = FastAPI(title="File Storage API", version="2.0.0")

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(files.router)

# Frontend Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    return templates.TemplateResponse("files.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/download/private/{file_id}", response_class=HTMLResponse)
async def download_private_page(request: Request, file_id: str):
    return templates.TemplateResponse("download_private.html", {"request": request, "file_id": file_id})

@app.get("/download/public/{file_id}", response_class=HTMLResponse)
async def download_public_page(request: Request, file_id: str):
    return templates.TemplateResponse("download_public.html", {"request": request, "file_id": file_id})