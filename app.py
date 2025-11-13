from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import netcine
import get_channels

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Minimal manifest for Stremio
MANIFEST = {
    "id": "org.skyflix.addon",
    "version": "1.0.0",
    "name": "Skyflix",
    "description": "Skyflix aggregated addon",
    "resources": ["catalog", "meta", "stream"],
    "types": ["movie", "series", "tv"],
    "catalogs": [
        {
            "type": "movie",
            "id": "skyflix-movies",
            "name": "Skyflix Movies"
        },
        {
            "type": "series",
            "id": "skyflix-series",
            "name": "Skyflix Series"
        }
    ],
    "idPrefixes": ["skyflix", "tt"]
}


@app.get("/manifest.json")
async def manifest():
    return JSONResponse(content=MANIFEST)


@app.get("/catalog/{type}/{id}.json")
async def catalog(type: str, id: str, request: Request):
    # Get search query from URL params
    query = request.query_params.get('search', '')
    if query:
        items = netcine.ntc_search_catalog(query)
        return JSONResponse(content={"metas": items})
    return JSONResponse(content={"metas": []})


@app.get("/meta/{type}/{id}.json")
async def meta(type: str, id: str):
    m = netcine.meta_ntc(type, id)
    return JSONResponse(content=m)


@app.get("/stream/{type}/{id}.json")
async def stream(type: str, id: str):
    streams = netcine.get_stream_ntc(type, id)
    return JSONResponse(content={"streams": streams})


@app.get("/healthz")
async def health():
    return JSONResponse(content={"status": "ok"})


@app.get("/")
async def root():
    return JSONResponse(content={"message": "Skyflix Addon - Access /manifest.json"})
