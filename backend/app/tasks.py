"""Celery tasks for async data processing"""
import os
import MySQLdb
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

from app.celery_app import celery_app
from app.config import settings
from app.database import db_manager
from app.normalizer import DataNormalizer
from app.elasticsearch_manager import ElasticsearchIndexer
from app.mongodb_manager import MongoDBManager
from app.neo4j_manager import Neo4jManager
from app.models import OsintEntity


@celery_app.task(bind=True, name="app.tasks.import_mysql_dump")
def import_mysql_dump(
    self,
    source_name: str,
    tables: List[str] = None,
    field_mapping: Dict[str, Dict[str, str]] = None,
    dump_file: str = None
):
    """
    Import data from MySQL database
    
    Args:
        source_name: Friendly name for the data source
        tables: List of tables to import (None = all tables)
        field_mapping: Dict mapping table names to field mappings
        dump_file: Path to MySQL dump file to import first
    """
    logger.info(f"Starting MySQL import job: {source_name}")
    
    # Initialize managers
    es_indexer = ElasticsearchIndexer()
    mongo_manager = MongoDBManager()
    neo4j_manager = Neo4jManager()
    normalizer = DataNormalizer()
    
    # Log job start
    job_data = {
        "job_id": self.request.id,
        "source_name": source_name,
        "status": "running",
        "started_at": datetime.utcnow(),
        "tables": tables,
        "total_records": 0,
        "processed_records": 0
    }
    job_log_id = mongo_manager.log_import_job(job_data)
    
    try:
        # Create a unique database name for this source
        source_db_name = f"osint_{source_name.replace('-', '_').replace(' ', '_')}"
        
        # If dump file provided, import it first into dedicated database
        if dump_file:
            # Check if path is absolute, otherwise construct path in /dumps directory
            if os.path.isabs(dump_file):
                dump_path = dump_file
            else:
                # In Docker, dumps are mounted at /dumps
                dump_path = os.path.join("/dumps", dump_file)
            
            if os.path.exists(dump_path):
                logger.info(f"Importing MySQL dump file: {dump_path} into {source_db_name}")
                _import_dump_file(dump_path, source_db_name)
            else:
                logger.error(f"Dump file not found: {dump_path}")
                raise FileNotFoundError(f"Dump file not found: {dump_path}")
        
        # Connect to the source-specific MySQL database
        # Try osint_ prefixed database first, fall back to original name if empty
        import MySQLdb
        
        try:
            conn = MySQLdb.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user="root",
                passwd=os.getenv('MYSQL_ROOT_PASSWORD', 'osint_root_pass'),
                db=source_db_name
            )
            # Check if database has tables
            cursor_test = conn.cursor()
            cursor_test.execute("SHOW TABLES")
            if cursor_test.fetchone() is None:
                # Empty database, try original name without osint_ prefix
                logger.info(f"{source_db_name} is empty, trying original database name: {source_name}")
                conn.close()
                conn = MySQLdb.connect(
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user="root",
                    passwd=os.getenv('MYSQL_ROOT_PASSWORD', 'osint_root_pass'),
                    db=source_name
                )
            cursor_test.close()
        except MySQLdb.OperationalError as e:
            # Database doesn't exist, try original name
            logger.info(f"{source_db_name} not found, trying: {source_name}")
            conn = MySQLdb.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user="root",
                passwd=os.getenv('MYSQL_ROOT_PASSWORD', 'osint_root_pass'),
                db=source_name
            )
        
        try:
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            
            # Get list of tables
            if tables is None:
                cursor.execute("SHOW TABLES")
                tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(tables)} tables to process")
            
            total_processed = 0
            
            # Process each table
            for idx, table_name in enumerate(tables):
                logger.info(f"Processing table {idx + 1}/{len(tables)}: {table_name}")
                
                # Update progress
                progress = (idx / len(tables)) * 100
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current_table": table_name,
                        "progress": progress,
                        "processed": total_processed
                    }
                )
                
                # Get table row count
                cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
                row_count = cursor.fetchone()["count"]
                
                if row_count == 0:
                    logger.info(f"Skipping empty table: {table_name}")
                    continue
                
                logger.info(f"Table {table_name} has {row_count} rows")
                
                # Get or auto-detect field mapping for this table
                table_field_mapping = {}
                if field_mapping and table_name in field_mapping:
                    table_field_mapping = field_mapping[table_name]
                else:
                    # Sample some records for auto-detection
                    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 10")
                    sample_records = cursor.fetchall()
                    if sample_records:
                        table_field_mapping = normalizer.auto_detect_field_mapping(
                            sample_records,
                            table_name
                        )
                
                # Process records in batches
                batch_size = settings.BATCH_SIZE
                offset = 0
                
                while offset < row_count:
                    # Fetch batch
                    cursor.execute(
                        f"SELECT * FROM `{table_name}` LIMIT {batch_size} OFFSET {offset}"
                    )
                    records = cursor.fetchall()
                    
                    if not records:
                        break
                    
                    # Store raw records in MongoDB
                    mongo_manager.bulk_store_raw_records(records, source_name, table_name)
                    
                    # Normalize records
                    all_entities = []
                    for record in records:
                        entities = normalizer.normalize_record(
                            record,
                            table_field_mapping,
                            source_name,
                            table_name
                        )
                        all_entities.extend(entities)
                    
                    if all_entities:
                        # Store in MongoDB
                        mongo_manager.bulk_store_entities(all_entities)
                        
                        # Index in Elasticsearch
                        es_indexer.bulk_index_entities(all_entities)
                        
                        # Create Neo4j nodes and relationships
                        for entity in all_entities:
                            neo4j_manager.create_entity_node(entity)
                            neo4j_manager.auto_create_relationships(entity)
                    
                    total_processed += len(records)
                    offset += batch_size
                    
                    logger.info(
                        f"Processed {offset}/{row_count} records from {table_name}"
                    )
            
            # Update job status
            mongo_manager.update_import_job(job_log_id, {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "total_records": total_processed,
                "processed_records": total_processed
            })
            
            logger.info(f"Import job completed: {source_name}, {total_processed} records")
            
            return {
                "status": "success",
                "source": source_name,
                "total_records": total_processed,
                "tables_processed": len(tables)
            }
        
        finally:
            # Close database connection
            conn.close()
            logger.info("MySQL connection closed")
    
    except Exception as e:
        logger.error(f"Import job failed: {e}", exc_info=True)
        
        # Update job status
        if job_log_id:
            mongo_manager.update_import_job(job_log_id, {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow()
            })
        
        raise


def _import_dump_file(dump_file: str, database_name: str):
    """Import MySQL dump file into a specific database"""
    # Create database if it doesn't exist
    create_db_cmd = (
        f"mysql -h {settings.MYSQL_HOST} "
        f"-P {settings.MYSQL_PORT} "
        f"-u root "
        f"-p{os.getenv('MYSQL_ROOT_PASSWORD', 'osint_root_pass')} "
        f"--skip-ssl "
        f"-e 'CREATE DATABASE IF NOT EXISTS `{database_name}`;'"
    )
    
    logger.info(f"Creating database: {database_name}")
    result = os.system(create_db_cmd)
    
    if result != 0:
        raise Exception(f"Failed to create database: {database_name}")
    
    # Import dump with DEFINER removal to avoid permission errors
    # Use sed to remove DEFINER clauses on-the-fly
    cmd = (
        f"sed 's/DEFINER[ ]*=[ ]*[^ ]*//g' {dump_file} | "
        f"mysql -h {settings.MYSQL_HOST} "
        f"-P {settings.MYSQL_PORT} "
        f"-u root "
        f"-p{os.getenv('MYSQL_ROOT_PASSWORD', 'osint_root_pass')} "
        f"--skip-ssl "
        f"--force "  # Continue on errors
        f"--max_allowed_packet=512M "
        f"{database_name}"
    )
    
    logger.info(f"Importing dump file into {database_name} (removing DEFINER clauses)...")
    result = os.system(cmd)
    
    if result != 0:
        logger.warning(f"Import completed with errors for: {dump_file}")
    else:
        logger.info(f"Dump file imported successfully into {database_name}")


@celery_app.task(name="app.tasks.process_batch")
def process_batch(
    records: List[Dict[str, Any]],
    field_mapping: Dict[str, str],
    source: str,
    source_table: str
):
    """Process a batch of records"""
    
    es_indexer = ElasticsearchIndexer()
    mongo_manager = MongoDBManager()
    neo4j_manager = Neo4jManager()
    normalizer = DataNormalizer()
    
    # Normalize records
    all_entities = []
    for record in records:
        entities = normalizer.normalize_record(
            record,
            field_mapping,
            source,
            source_table
        )
        all_entities.extend(entities)
    
    if all_entities:
        # Store in MongoDB
        mongo_manager.bulk_store_entities(all_entities)
        
        # Index in Elasticsearch
        es_indexer.bulk_index_entities(all_entities)
        
        # Create Neo4j nodes and relationships
        for entity in all_entities:
            neo4j_manager.create_entity_node(entity)
            neo4j_manager.auto_create_relationships(entity)
    
    return {
        "status": "success",
        "records_processed": len(records),
        "entities_created": len(all_entities)
    }


@celery_app.task(name="app.tasks.initialize_indices")
def initialize_indices():
    """Initialize all database indices and constraints"""
    try:
        es_indexer = ElasticsearchIndexer()
        neo4j_manager = Neo4jManager()
        
        # Create Elasticsearch index
        es_indexer.create_index()
        
        # Create Neo4j constraints
        neo4j_manager.create_constraints()
        
        logger.info("All indices initialized successfully")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to initialize indices: {e}")
        raise


@celery_app.task(name="app.tasks.get_statistics")
def get_statistics():
    """Get statistics from all data stores"""
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
