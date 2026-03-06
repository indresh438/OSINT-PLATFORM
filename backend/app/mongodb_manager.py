"""MongoDB storage operations"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo.database import Database
from loguru import logger

from app.models import OsintEntity
from app.database import db_manager


class MongoDBManager:
    """Handles MongoDB storage operations for semi-structured data"""
    
    def __init__(self):
        self.db: Database = db_manager.get_mongodb_database()
        self.entities_collection = self.db["entities"]
        self.raw_records_collection = self.db["raw_records"]
        self.import_logs_collection = self.db["import_logs"]
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create MongoDB indexes for performance"""
        try:
            # Entities collection indexes
            self.entities_collection.create_index("entity_type")
            self.entities_collection.create_index("value")
            self.entities_collection.create_index("source")
            self.entities_collection.create_index("timestamp")
            self.entities_collection.create_index([("value", 1), ("entity_type", 1)], unique=False)
            
            # Raw records collection indexes
            self.raw_records_collection.create_index("source")
            self.raw_records_collection.create_index("source_table")
            self.raw_records_collection.create_index("import_timestamp")
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def store_entity(self, entity: OsintEntity) -> Optional[str]:
        """Store a single entity"""
        try:
            doc = entity.model_dump(mode='json')
            result = self.entities_collection.insert_one(doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to store entity: {e}")
            return None
    
    def bulk_store_entities(self, entities: List[OsintEntity]) -> int:
        """Bulk store multiple entities"""
        if not entities:
            return 0
        
        try:
            docs = [entity.model_dump(mode='json') for entity in entities]
            result = self.entities_collection.insert_many(docs, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            logger.error(f"Bulk store failed: {e}")
            return 0
    
    def store_raw_record(self, record: Dict[str, Any], source: str, source_table: str) -> Optional[str]:
        """Store raw database record for audit trail"""
        try:
            doc = {
                "data": record,
                "source": source,
                "source_table": source_table,
                "import_timestamp": datetime.utcnow()
            }
            result = self.raw_records_collection.insert_one(doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to store raw record: {e}")
            return None
    
    def bulk_store_raw_records(self, records: List[Dict[str, Any]], source: str, source_table: str) -> int:
        """Bulk store raw records"""
        if not records:
            return 0
        
        try:
            docs = [
                {
                    "data": record,
                    "source": source,
                    "source_table": source_table,
                    "import_timestamp": datetime.utcnow()
                }
                for record in records
            ]
            result = self.raw_records_collection.insert_many(docs, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            logger.error(f"Bulk store raw records failed: {e}")
            return 0
    
    def get_entity_by_value(self, value: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get entities by value"""
        query = {"value": value}
        if entity_type:
            query["entity_type"] = entity_type
        
        try:
            results = list(self.entities_collection.find(query).limit(100))
            # Convert ObjectId to string
            for result in results:
                result["_id"] = str(result["_id"])
            return results
        except Exception as e:
            logger.error(f"Get entity by value failed: {e}")
            return []
    
    def log_import_job(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Log import job information"""
        try:
            job_data["logged_at"] = datetime.utcnow()
            result = self.import_logs_collection.insert_one(job_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to log import job: {e}")
            return None
    
    def update_import_job(self, job_id: str, update_data: Dict[str, Any]) -> bool:
        """Update import job status"""
        try:
            from bson import ObjectId
            update_data["updated_at"] = datetime.utcnow()
            result = self.import_logs_collection.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update import job: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get MongoDB statistics"""
        try:
            total_entities = self.entities_collection.count_documents({})
            total_raw_records = self.raw_records_collection.count_documents({})
            
            # Count by entity type
            entity_types_pipeline = [
                {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            entity_types = list(self.entities_collection.aggregate(entity_types_pipeline))
            
            # Count by source
            sources_pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            sources = list(self.entities_collection.aggregate(sources_pipeline))
            
            return {
                "total_entities": total_entities,
                "total_raw_records": total_raw_records,
                "by_type": {item["_id"]: item["count"] for item in entity_types},
                "by_source": {item["_id"]: item["count"] for item in sources}
            }
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return {"error": str(e)}
