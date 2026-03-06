"""Health check endpoints"""
from fastapi import APIRouter
from loguru import logger
from datetime import datetime

from app.models import HealthCheck
from app.database import db_manager

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Check system health and service availability"""
    services = {
        "mysql": False,
        "mongodb": False,
        "elasticsearch": False,
        "neo4j": False,
        "redis": False
    }
    
    # Check MySQL
    try:
        with db_manager.get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            services["mysql"] = True
    except Exception as e:
        logger.error(f"MySQL health check failed: {e}")
    
    # Check MongoDB
    try:
        client = db_manager.get_mongodb_client()
        client.admin.command("ping")
        services["mongodb"] = True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    # Check Elasticsearch
    try:
        es = db_manager.get_elasticsearch_client()
        if es.ping():
            services["elasticsearch"] = True
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
    
    # Check Neo4j
    try:
        with db_manager.get_neo4j_session() as session:
            session.run("RETURN 1")
            services["neo4j"] = True
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
    
    # Check Redis
    try:
        redis_client = db_manager.get_redis_client()
        redis_client.ping()
        services["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Overall status
    all_healthy = all(services.values())
    status = "healthy" if all_healthy else "degraded"
    
    return HealthCheck(
        status=status,
        services=services,
        timestamp=datetime.utcnow()
    )


@router.get("/stats")
async def get_statistics():
    """Get system statistics"""
    from app.elasticsearch_manager import ElasticsearchIndexer
    from app.mongodb_manager import MongoDBManager
    from app.neo4j_manager import Neo4jManager
    
    try:
        es_indexer = ElasticsearchIndexer()
        mongo_manager = MongoDBManager()
        neo4j_manager = Neo4jManager()
        
        stats = {
            "elasticsearch": es_indexer.get_statistics(),
            "mongodb": mongo_manager.get_statistics(),
            "neo4j": neo4j_manager.get_statistics(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return {"error": str(e)}
