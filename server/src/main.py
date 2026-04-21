from fastapi import FastAPI

from server.src.routers import users

app = FastAPI()
app.include_router(users.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
