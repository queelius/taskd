# Run: uvicorn main:app --reload
# Docs: http://
# API: http://
# Dashboard: http://localhost:8000/rq/dashboard

# let's go over workflow

# 1. create a workspace
# 2. upload a file
# 3. execute a script
# 4. delete a workspace

# let's go over how to get the server up and running

# 1. install dependencies
# 2. run `redis-server`
# 3. run `rq worker`
# 4. run `rq-dashboard`
# 5. run `uvicorn main:app --reload`
# 6. open `http://localhost:8000/docs` for the docs

from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
from flask import Flask
import rq_dashboard

from routes import router

# Create a Flask app for RQ Dashboard
flask_app = Flask(__name__)
# Configure the Flask app for RQ Dashboard
flask_app.config["RQ_DASHBOARD_REDIS_URL"] = "redis://localhost:6379/0"
rq_dashboard.web.setup_rq_connection(flask_app)
flask_app.register_blueprint(rq_dashboard.blueprint, url_prefix="/dashboard")

# Create a FastAPI app
app = FastAPI()
# Mount the Flask app (RQ Dashboard) in the FastAPI app
app.mount("/rq", WSGIMiddleware(flask_app))

app.include_router(router)