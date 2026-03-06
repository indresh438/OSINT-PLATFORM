"""Import and data ingestion endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Optional, List, Dict
from loguru import logger
from pydantic import BaseModel

from app.models import ImportJob
from app.tasks import import_mysql_dump, initialize_indices

router = APIRouter()


class ImportJobRequest(BaseModel):
    """Request model for import job"""
    source_name: str
    tables: Optional[List[str]] = None
    field_mapping: Optional[Dict[str, Dict[str, str]]] = None
    dump_file: Optional[str] = None


@router.post("/import/mysql")
async def start_mysql_import(job_request: ImportJobRequest, background_tasks: BackgroundTasks):
    """
    Start MySQL import job
    
    - **source_name**: Friendly name for the data source
    - **tables**: List of table names to import (optional, imports all if not specified)
    - **field_mapping**: Mapping of table names to field mappings
    - **dump_file**: Path to MySQL dump file (optional)
    
    Example field_mapping:
    ```json
    {
        "users_table": {
            "email_addr": "email",
            "user_name": "username",
            "ip_address": "ip"
        }
    }
    ```
    """
    try:
        # Start Celery task
        task = import_mysql_dump.apply_async(
            kwargs={
                "source_name": job_request.source_name,
                "tables": job_request.tables,
                "field_mapping": job_request.field_mapping or {},
                "dump_file": job_request.dump_file
            }
        )
        
        logger.info(f"Started import job: {task.id}")
        
        return {
            "job_id": task.id,
            "status": "started",
            "message": f"Import job started for source: {job_request.source_name}"
        }
    except Exception as e:
        logger.error(f"Failed to start import job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start import: {str(e)}")


@router.get("/import/status/{job_id}")
async def get_import_status(job_id: str):
    """Get import job status"""
    from celery.result import AsyncResult
    
    try:
        task_result = AsyncResult(job_id)
        
        response = {
            "job_id": job_id,
            "status": task_result.state,
            "info": task_result.info if task_result.info else {}
        }
        
        if task_result.state == "PROGRESS":
            response["progress"] = task_result.info.get("progress", 0)
            response["current_table"] = task_result.info.get("current_table", "")
            response["processed"] = task_result.info.get("processed", 0)
        elif task_result.state == "SUCCESS":
            response["result"] = task_result.result
        elif task_result.state == "FAILURE":
            response["error"] = str(task_result.info)
        
        return response
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/import/initialize")
async def initialize_system():
    """Initialize all database indices and constraints"""
    try:
        task = initialize_indices.apply_async()
        
        return {
            "job_id": task.id,
            "status": "started",
            "message": "Initialization started"
        }
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize: {str(e)}")


@router.get("/import/jobs")
async def list_import_jobs(limit: int = 50):
    """List recent import jobs"""
    from app.mongodb_manager import MongoDBManager
    
    try:
        mongo_manager = MongoDBManager()
        jobs = list(
            mongo_manager.import_logs_collection
            .find({})
            .sort("logged_at", -1)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for job in jobs:
            job["_id"] = str(job["_id"])
        
        return {
            "total": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Failed to list import jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")
