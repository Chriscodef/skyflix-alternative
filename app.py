from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
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
    "idPrefixes": ["skyflix"]
}


@app.get("/manifest.json")
async def manifest():
    return JSONResponse(content=MANIFEST)


@app.post("/catalog")
async def catalog(request: Request):
    body = await request.json()
    # Expected fields: query or type/id
    query = body.get('query') or body.get('search')
    if query:
        items = netcine.ntc_search_catalog(query)
        return JSONResponse(content={"metas": items})
    # fallback: empty
    return JSONResponse(content={"metas": []})


@app.post("/meta")
async def meta(request: Request):
    body = await request.json()
    type_ = body.get('type')
    id_ = body.get('id')
    if not type_ or not id_:
        return JSONResponse(content={})
    m = netcine.meta_ntc(type_, id_)
    return JSONResponse(content=m)


@app.post("/stream")
async def stream(request: Request):
    body = await request.json()
    type_ = body.get('type')
    id_ = body.get('id')
    if not type_ or not id_:
        return JSONResponse(content={"streams": []})
    streams = netcine.get_stream_ntc(type_, id_)
    return JSONResponse(content={"streams": streams})


@app.get("/healthz")
async def health():
    return JSONResponse(content={"status": "ok"})
