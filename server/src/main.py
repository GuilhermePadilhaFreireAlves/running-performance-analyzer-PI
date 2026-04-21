from fastapi import FastAPI

from server.src.routers import analysis, auth, historico, users, videos

app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(analysis.router)
app.include_router(historico.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
