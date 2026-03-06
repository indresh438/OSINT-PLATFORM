"""Pydantic models for OSINT entities"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Entity types in OSINT system"""
    EMAIL = "email"
    IP = "ip"
    DOMAIN = "domain"
    USERNAME = "username"
    PHONE = "phone"
    HASH = "hash"
    URL = "url"
    UNKNOWN = "unknown"


class OsintEntity(BaseModel):
    """Normalized OSINT entity model"""
    
    # Core fields
    entity_id: Optional[str] = Field(None, description="Unique entity identifier")
    entity_type: EntityType = Field(..., description="Type of entity")
    value: str = Field(..., description="Primary value of the entity")
    
    # Standard fields
    email: Optional[str] = Field(None, description="Email address")
    ip: Optional[str] = Field(None, description="IP address")
    domain: Optional[str] = Field(None, description="Domain name")
    username: Optional[str] = Field(None, description="Username")
    phone: Optional[str] = Field(None, description="Phone number")
    
    # Metadata
    source: str = Field(..., description="Data source identifier")
    source_table: Optional[str] = Field(None, description="Original table name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Ingestion timestamp")
    first_seen: Optional[datetime] = Field(None, description="First appearance timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last appearance timestamp")
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Tags/labels")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Data confidence score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "email",
                "value": "user@example.com",
                "email": "user@example.com",
                "domain": "example.com",
                "source": "leaked_db_2023",
                "timestamp": "2024-10-29T12:00:00Z",
                "tags": ["breach", "verified"]
            }
        }


class EntityRelationship(BaseModel):
    """Relationship between two entities"""
    
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Type of relationship")
    weight: float = Field(1.0, description="Relationship strength/weight")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Relationship metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchQuery(BaseModel):
    """Search query model"""
    
    query: str = Field(..., description="Search query string")
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter by entity types")
    sources: Optional[List[str]] = Field(None, description="Filter by sources")
    exclude_tables: Optional[List[str]] = Field(None, description="Exclude specific source tables (e.g., 'notifications')")
    exclude_sources: Optional[List[str]] = Field(None, description="Exclude specific data sources")
    deduplicate: bool = Field(False, description="Show only unique records (deduplicate by value+source_table)")
    group_by_table: bool = Field(False, description="Group results by source table")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(100, ge=1, le=10000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SearchResult(BaseModel):
    """Search result response"""
    
    total: int = Field(..., description="Total matching entities")
    results: List[OsintEntity] = Field(..., description="Entity results")
    took: float = Field(..., description="Query execution time in seconds")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Results per page")


class ImportJob(BaseModel):
    """MySQL import job model"""
    
    job_id: Optional[str] = Field(None, description="Job identifier")
    dump_file: Optional[str] = Field(None, description="MySQL dump file path")
    source_name: str = Field(..., description="Friendly source name")
    tables: Optional[List[str]] = Field(None, description="Specific tables to import")
    field_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Field mapping from source to standard schema"
    )
    status: str = Field("pending", description="Job status")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthCheck(BaseModel):
    """System health check response"""
    
    status: str = Field(..., description="Overall status")
    services: Dict[str, bool] = Field(..., description="Service availability")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
