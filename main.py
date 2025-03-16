from fastapi import FastAPI
from api.user.user_router import user_router
from api.search.search_router import search_router
import uvicorn

app = FastAPI()
app.include_router(user_router, tags=["Users"])
app.include_router(search_router, tags=["Searches"])


@app.get("/health")
async def root():
    return {"hello": "i am healthy"}


if __name__ == "__main__":
    from data.database import init_db

    init_db(drop_existing=False)
    uvicorn.run(app, host="0.0.0.0", port=7999)
