"""Database clients and connection managers"""
import MySQLdb
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
import redis
from typing import Optional
from contextlib import contextmanager
from loguru import logger

from app.config import settings


class DatabaseManager:
    """Centralized database connection manager"""
    
    def __init__(self):
        self._mysql_conn: Optional[MySQLdb.Connection] = None
        self._mongodb_client: Optional[MongoClient] = None
        self._elasticsearch_client: Optional[Elasticsearch] = None
        self._neo4j_driver: Optional[GraphDatabase.driver] = None
        self._redis_client: Optional[redis.Redis] = None
    
    # MySQL
    @contextmanager
    def get_mysql_connection(self):
        """Get MySQL connection context manager"""
        conn = None
        try:
            conn = MySQLdb.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                passwd=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                charset='utf8mb4'
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"MySQL error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    # MongoDB
    def get_mongodb_client(self) -> MongoClient:
        """Get or create MongoDB client"""
        if self._mongodb_client is None:
            self._mongodb_client = MongoClient(settings.mongodb_url)
            logger.info("MongoDB client connected")
        return self._mongodb_client
    
    def get_mongodb_database(self):
        """Get MongoDB database"""
        client = self.get_mongodb_client()
        return client[settings.MONGODB_DATABASE]
    
    # Elasticsearch
    def get_elasticsearch_client(self) -> Elasticsearch:
        """Get or create Elasticsearch client"""
        if self._elasticsearch_client is None:
            self._elasticsearch_client = Elasticsearch([settings.elasticsearch_url])
            logger.info("Elasticsearch client connected")
        return self._elasticsearch_client
    
    # Neo4j
    def get_neo4j_driver(self):
        """Get or create Neo4j driver"""
        if self._neo4j_driver is None:
            self._neo4j_driver = GraphDatabase.driver(
                se🏠 COMMAND CENTER
ttings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info("Neo4j driver connected")
        return self._neo4j_driver
    
    @contextmanager
    def get_neo4j_session(self):
        """Get Neo4j session context manager"""
        driver = self.get_neo4j_driver()
        session = driver.session()
        try:
            yield session
        finally:
            session.close()
    
    # Redis
    def get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            logger.info("Redis client connected")
        return self._redis_client
    
    # Cleanup
    def close_all(self):
        """Close all database connections"""
        if self._mongodb_client:
            self._mongodb_client.close()
            logger.info("MongoDB client closed")
        
        if self._neo4j_driver:
            self._neo4j_driver.close()
            logger.info("Neo4j driver closed")
        
        if self._redis_client:
            self._redis_client.close()
            logger.info("Redis client closed")
        
        if self._elasticsearch_client:
            self._elasticsearch_client.close()
            logger.info("Elasticsearch client closed")


# Global database manager instance
db_manager = DatabaseManager()
