"""Entity management endpoints"""
from fastapi import APIRouter, HTTPException, Path
from typing import Optional
from loguru import logger

from app.models import OsintEntity, EntityType
from app.neo4j_manager import Neo4jManager
from app.mongodb_manager import MongoDBManager

router = APIRouter()


@router.get("/entities/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: str = Path(..., description="Entity ID (format: type:value)"),
    depth: int = 1
):
    """Get all relationships for an entity"""
    try:
        neo4j_manager = Neo4jManager()
        relationships = neo4j_manager.get_entity_relationships(entity_id, depth)
        return {
            "entity_id": entity_id,
            "depth": depth,
            "relationships": relationships
        }
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.get("/entities/{entity_id}/connections/{target_id}")
async def find_connections(
    entity_id: str = Path(..., description="Source entity ID"),
    target_id: str = Path(..., description="Target entity ID"),
    max_depth: int = 3
):
    """Find connections between two entities"""
    try:
        neo4j_manager = Neo4jManager()
        paths = neo4j_manager.find_connections(entity_id, target_id, max_depth)
        return {
            "source": entity_id,
            "target": target_id,
            "max_depth": max_depth,
            "paths": paths
        }
    except Exception as e:
        logger.error(f"Failed to find connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find connections: {str(e)}")


@router.get("/entities/value/{value}")
async def get_entity_by_value(
    value: str = Path(..., description="Entity value"),
    entity_type: Optional[EntityType] = None
):
    """Get entity details from MongoDB by value"""
    try:
        mongo_manager = MongoDBManager()
        results = mongo_manager.get_entity_by_value(
            value,
            entity_type.value if entity_type else None
        )
        return {
            "value": value,
            "entity_type": entity_type.value if entity_type else None,
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to get entity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get entity: {str(e)}")


@router.post("/entities/enrich")
async def enrich_entity(entity: OsintEntity):
    """
    Enrich an entity with additional data
    (Placeholder for future online enrichment features)
    """
    return {
        "message": "Enrichment feature coming soon",
        "entity": entity
    }
