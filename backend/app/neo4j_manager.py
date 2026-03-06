"""Neo4j graph database operations for relationship mapping"""
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models import OsintEntity, EntityRelationship
from app.database import db_manager


class Neo4jManager:
    """Handles Neo4j graph database operations for entity relationships"""
    
    def __init__(self):
        self.driver = db_manager.get_neo4j_driver()
    
    def create_constraints(self):
        """Create Neo4j constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
            "CREATE INDEX entity_value IF NOT EXISTS FOR (e:Entity) ON (e.value)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
        ]
        
        with db_manager.get_neo4j_session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint/index already exists or failed: {e}")
        
        logger.info("Neo4j constraints and indexes created")
    
    def create_entity_node(self, entity: OsintEntity) -> bool:
        """Create or update an entity node"""
        query = """
        MERGE (e:Entity {entity_id: $entity_id})
        SET e.entity_type = $entity_type,
            e.value = $value,
            e.email = $email,
            e.ip = $ip,
            e.domain = $domain,
            e.username = $username,
            e.phone = $phone,
            e.source = $source,
            e.timestamp = $timestamp,
            e.updated_at = datetime()
        RETURN e
        """
        
        # Generate entity_id if not present
        entity_id = f"{entity.entity_type}:{entity.value}"
        
        params = {
            "entity_id": entity_id,
            "entity_type": entity.entity_type.value,
            "value": entity.value,
            "email": entity.email,
            "ip": entity.ip,
            "domain": entity.domain,
            "username": entity.username,
            "phone": entity.phone,
            "source": entity.source,
            "timestamp": entity.timestamp.isoformat() if entity.timestamp else None
        }
        
        try:
            with db_manager.get_neo4j_session() as session:
                session.run(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to create entity node: {e}")
            return False
    
    def create_relationship(self, relationship: EntityRelationship) -> bool:
        """Create relationship between two entities"""
        query = """
        MATCH (source:Entity {entity_id: $source_id})
        MATCH (target:Entity {entity_id: $target_id})
        MERGE (source)-[r:RELATED_TO {type: $rel_type}]->(target)
        SET r.weight = $weight,
            r.metadata = $metadata,
            r.created_at = datetime()
        RETURN r
        """
        
        params = {
            "source_id": relationship.source_entity_id,
            "target_id": relationship.target_entity_id,
            "rel_type": relationship.relationship_type,
            "weight": relationship.weight,
            "metadata": relationship.metadata
        }
        
        try:
            with db_manager.get_neo4j_session() as session:
                session.run(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False
    
    def auto_create_relationships(self, entity: OsintEntity) -> int:
        """
        Automatically create relationships based on entity data
        For example: email -> domain, username -> email, etc.
        """
        relationships_created = 0
        
        entity_id = f"{entity.entity_type}:{entity.value}"
        
        # Email -> Domain relationship
        if entity.email and entity.domain:
            email_id = f"email:{entity.email}"
            domain_id = f"domain:{entity.domain}"
            
            if self._create_simple_relationship(email_id, domain_id, "HAS_DOMAIN"):
                relationships_created += 1
        
        # Username -> Email relationship
        if entity.username and entity.email:
            username_id = f"username:{entity.username}"
            email_id = f"email:{entity.email}"
            
            if self._create_simple_relationship(username_id, email_id, "HAS_EMAIL"):
                relationships_created += 1
        
        # IP -> Domain relationship (if both exist)
        if entity.ip and entity.domain:
            ip_id = f"ip:{entity.ip}"
            domain_id = f"domain:{entity.domain}"
            
            if self._create_simple_relationship(domain_id, ip_id, "RESOLVES_TO"):
                relationships_created += 1
        
        return relationships_created
    
    def _create_simple_relationship(self, source_id: str, target_id: str, rel_type: str) -> bool:
        """Create a simple relationship between two entity IDs"""
        query = """
        MATCH (source:Entity {entity_id: $source_id})
        MATCH (target:Entity {entity_id: $target_id})
        MERGE (source)-[r:RELATED_TO {type: $rel_type}]->(target)
        SET r.created_at = datetime()
        RETURN r
        """
        
        try:
            with db_manager.get_neo4j_session() as session:
                result = session.run(query, {
                    "source_id": source_id,
                    "target_id": target_id,
                    "rel_type": rel_type
                })
                return result.single() is not None
        except Exception as e:
            logger.debug(f"Relationship creation skipped or failed: {e}")
            return False
    
    def get_entity_relationships(self, entity_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get all relationships for an entity up to specified depth"""
        query = f"""
        MATCH path = (e:Entity {{entity_id: $entity_id}})-[r:RELATED_TO*1..{depth}]-(related:Entity)
        RETURN path
        LIMIT 100
        """
        
        try:
            with db_manager.get_neo4j_session() as session:
                result = session.run(query, {"entity_id": entity_id})
                
                relationships = []
                for record in result:
                    path = record["path"]
                    relationships.append({
                        "nodes": [dict(node) for node in path.nodes],
                        "relationships": [dict(rel) for rel in path.relationships]
                    })
                
                return relationships
        except Exception as e:
            logger.error(f"Failed to get entity relationships: {e}")
            return []
    
    def find_connections(self, entity_id_1: str, entity_id_2: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Find connections between two entities"""
        query = f"""
        MATCH path = shortestPath(
            (e1:Entity {{entity_id: $entity_id_1}})-[r:RELATED_TO*1..{max_depth}]-(e2:Entity {{entity_id: $entity_id_2}})
        )
        RETURN path
        LIMIT 10
        """
        
        try:
            with db_manager.get_neo4j_session() as session:
                result = session.run(query, {
                    "entity_id_1": entity_id_1,
                    "entity_id_2": entity_id_2
                })
                
                paths = []
                for record in result:
                    path = record["path"]
                    paths.append({
                        "nodes": [dict(node) for node in path.nodes],
                        "relationships": [dict(rel) for rel in path.relationships],
                        "length": len(path.relationships)
                    })
                
                return paths
        except Exception as e:
            logger.error(f"Failed to find connections: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Neo4j graph statistics"""
        queries = {
            "total_nodes": "MATCH (n:Entity) RETURN count(n) as count",
            "total_relationships": "MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count",
            "nodes_by_type": """
                MATCH (n:Entity)
                RETURN n.entity_type as type, count(n) as count
                ORDER BY count DESC
            """
        }
        
        stats = {}
        
        try:
            with db_manager.get_neo4j_session() as session:
                # Total nodes
                result = session.run(queries["total_nodes"])
                stats["total_nodes"] = result.single()["count"]
                
                # Total relationships
                result = session.run(queries["total_relationships"])
                stats["total_relationships"] = result.single()["count"]
                
                # Nodes by type
                result = session.run(queries["nodes_by_type"])
                stats["by_type"] = {record["type"]: record["count"] for record in result}
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
