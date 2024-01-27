from fastapi.routing import APIRoute
from fastapi.responses import FileResponse
from fastapi import APIRouter, File, UploadFile
import os
from pydantic import BaseModel
import importlib.util
import inspect
import utils
from db import q

BASE_DIR = "workspaces"

class FileContent(BaseModel):
    data: str

router = APIRouter()

@router.get("/api/{endpoint}")
async def get_api(endpoint: str, include_source: bool = False):
    """
    List API for routes matching the given endpoint name.

    Args:
        endpoint (str): The name of an endpoint to retrieve. Partial matching.
        include_source (bool, optional): Whether to include the source code of each endpoint. Defaults to False.
    Returns:
        dict: A list of API routes with their respective HTTP methods and descriptions.
    """
    paths = []
    for route in router.routes:
        if isinstance(route, APIRoute):
            if endpoint not in route.path:
                continue
            path_item = {
                "path": route.path,
                "methods": route.methods,
                "params": [param.name for param in inspect.signature(route.endpoint).parameters.values()],
                "doc": utils.format_docstring(route.description) ,
            }
            if include_source:
                path_item["source"] = inspect.getsource(route.endpoint)
            paths.append(path_item)
    return {"paths": paths}

@router.get("/api")
async def get_api(search: str = None, include_source: bool = False):
    """List API for routes matching the search query. We match the query against the path and the docstring.
    If the query is empty, we return all routes.

    Args:
        endpoint (str, optional): The search query. Defaults to None.
        include_source (bool, optional): Whether to include the source code of each endpoint. Defaults to False.
    Returns:
        dict: A list of API routes with their respective HTTP methods and descriptions."""
    paths = []
    for route in router.routes:
        if isinstance(route, APIRoute):
            if search and search not in route.path and search not in route.endpoint.__doc__:
                continue
            path_item = {
                "path": route.path,
                "params": [param.name for param in inspect.signature(route.endpoint).parameters.values()],
                "methods": route.methods,
                "doc": utils.format_docstring(route.description),
            }
            if include_source:
                path_item["source"] = inspect.getsource(route.endpoint)
            paths.append(path_item)
    return {"paths": paths}

@router.get("/workspaces")
async def list_workspaces():
    """
    Retrieve a list of all workspaces.

    This endpoint scans the base directory and returns a list of all workspaces (directories) present.

    Returns:
        dict: A dictionary containing a list of workspaces.
    """
    workspaces = os.listdir(BASE_DIR)
    return {"workspaces": workspaces}

@router.get("/workspace/{workspace_name}/view/{file_name}")
async def get_view(workspace_name: str, file_name: str):
    """
    Fetch a specific file from a workspace.

    Args:
        workspace_name (str): The name of the workspace.
        file_name (str): The name of the file to retrieve.

    Returns:
        FileResponse: A response object containing the requested file.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    file_path = os.path.join(workspace_path, file_name)
    if not os.path.exists(workspace_path) or not os.path.exists(file_path):
        return {"error": "Workspace or file not found"}
    return FileResponse(file_path)

@router.post("/workspace/{workspace_name}")
async def create_workspace(workspace_name: str):
    """
    Create a new workspace.

    This endpoint creates a new directory in the base directory as a new workspace.

    Args:
        workspace_name (str): The name for the new workspace.

    Returns:
        dict: Confirmation message with the name of the created workspace.
    """
    os.makedirs(os.path.join(BASE_DIR, workspace_name), exist_ok=True)
    return {"message": f"Workspace '{workspace_name}' created"}

@router.delete("/workspace/{workspace_name}")
async def delete_workspace(workspace_name: str):
    """
    Delete an existing workspace.

    Args:
        workspace_name (str): The name of the workspace to delete.

    Returns:
        dict: Confirmation message with the name of the deleted workspace, or an error message.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    if os.path.exists(workspace_path):
        os.rmdir(workspace_path)
        return {"message": f"Workspace '{workspace_name}' deleted"}
    return {"error": "Workspace not found"}


@router.post("/workspace/{workspace_name}/create/{file_name}")
async def create_file(workspace_name: str, file_name: str, content: FileContent):
    """
    Create or update a file in a workspace.

    Args:
        workspace_name (str): The name of the workspace.
        file_name (str): The name of the file to create or update.
        content (FileContent): The content to write into the file.

    Returns:
        dict: Confirmation message with the name of the created/updated file.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    if not os.path.exists(workspace_path):
        return {"error": "Workspace not found"}
    path = os.path.join(workspace_path, file_name)
    with open(path, "w") as f:
        f.write(content.data)
    return {"message": f"File '{file_name}' created"}

@router.post("/workspace/{workspace_name}/upload")
async def upload_file(workspace_name: str, file: UploadFile = File(...)):
    """
    Upload a file to a workspace.

    Args:
        workspace_name (str): The name of the workspace.
        file (UploadFile, optional): The file to upload.

    Returns:
        dict: Confirmation message with the name of the uploaded file.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    if not os.path.exists(workspace_path):
        return {"error": "Workspace not found"}
    file_location = os.path.join(workspace_path, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return {"message": f"File '{file.filename}' uploaded"}

@router.post("/workspace/{workspace_name}/execute/{script_name}")
async def enqueue_script_execution(workspace_name: str, script_name: str):
    """
    Execute a script located in a workspace.

    Args:
        workspace_name (str): The name of the workspace containing the script.
        script_name (str): The name of the script to execute.

    Returns:
        dict: Information about the enqueued job including the job ID.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    if not os.path.exists(workspace_path) or not os.path.exists(os.path.join(workspace_path, script_name)):
        return {"error": "Workspace or script not found"}
    job = q.enqueue(utils.execute_script, workspace_path, script_name)
    return {"message": "Script execution started", "job_id": job.id}

@router.post("/workspace/{workspace_name}/execute/{script_name}/{function_name}")
async def enqueue_script_execution(workspace_name: str, script_name: str, function_name: str):
    """
    Execute a function from a script located in a workspace.

    Args:
        workspace_name (str): The name of the workspace containing the script.
        script_name (str): The name of the script to execute.
        function_name (str): The name of the function to execute.

    Returns:
        dict: Information about the enqueued job including the job ID.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    script_path = os.path.join(workspace_path, script_name)
    if not os.path.exists(workspace_path) or not os.path.exists(script_path):
        return {"error": "Workspace or script not found"}

    # Load the module from the script file
    spec = importlib.util.spec_from_file_location("module.name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get the function from the module
    function = getattr(module, function_name, None)
    if not function:
        return {"error": f"Function '{function_name}' not found in script '{script_name}'"}

    # Enqueue the function
    job = q.enqueue(function)
    return {"message": "Script execution started", "job_id": job.id}

@router.get("/workspace/{workspace_name}/files")
async def list_files(workspace_name: str):
    """
    List all files in a workspace.

    Args:
        workspace_name (str): The name of the workspace.

    Returns:
        dict: A list of files in the workspace.
    """
    workspace_path = os.path.join(BASE_DIR, workspace_name)
    if not os.path.exists(workspace_path):
        return {"error": "Workspace not found"}
    files = os.listdir(workspace_path)
    return {"files": files}

@router.get("/execution/{job_id}/status")
async def check_job_status(job_id: str):
    """
    Check the status of an enqueued job.

    Args:
        job_id (str): The unique identifier of the job.

    Returns:
        dict: The status of the job and its result if completed.
    """
    job = q.fetch_job(job_id)
    if job is None:
        return {"error": "Job not found"}
    return {"status": job.get_status(), "result": job.result}
