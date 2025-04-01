from http.client import HTTPResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Response
from api.user.user_router import user_router
from api.search.search_router import search_router
from api.jobs.job_router import job_router
import uvicorn

from services.environment_manager import get_environment

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to a specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_router, tags=["Users"])
app.include_router(search_router, tags=["Searches"])
app.include_router(job_router, tags=["Jobs"])
app.add_route("/health", lambda r: Response(status_code=200) , methods=["GET"])



@app.get("/health")
async def root():
    return {"hello": "i am healthy"}


if __name__ == "__main__":
    from data.database import init_db

    init_db(drop_existing=False)
    env = get_environment()
    uvicorn.run(app, host="localhost", port=env.app_port)
