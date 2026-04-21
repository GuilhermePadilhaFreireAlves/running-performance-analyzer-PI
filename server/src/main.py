from fastapi import FastAPI

from server.src.routers import auth, users

app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
