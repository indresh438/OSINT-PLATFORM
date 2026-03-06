"""Elasticsearch indexing and search operations"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from loguru import logger

from app.models import OsintEntity, EntityType, SearchQuery, SearchResult
from app.database import db_manager


class ElasticsearchIndexer:
    """Handles Elasticsearch indexing and search operations"""
    
    def __init__(self):
        self.client: Elasticsearch = db_manager.get_elasticsearch_client()
        self.index_name = "osint_entities"
    
    def create_index(self):
        """Create Elasticsearch index with proper mappings"""
        
        # Index mapping for OSINT entities
        mapping = {
            "mappings": {
                "properties": {
                    "entity_id": {"type": "keyword"},
                    "entity_type": {"type": "keyword"},
                    "value": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "email": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "ip": {"type": "ip"},
                    "domain": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "username": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "phone": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "source_table": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "first_seen": {"type": "date"},
                    "last_seen": {"type": "date"},
                    "tags": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "metadata": {"type": "object", "enabled": True}
                }
            },
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 0,
                "refresh_interval": "5s",
                "analysis": {
                    "analyzer": {
                        "email_analyzer": {
                            "type": "custom",
                            "tokenizer": "uax_url_email",
                            "filter": ["lowercase"]
                        }
                    }
                }
            }
        }
        
        # Delete index if exists (for development)
        if self.client.indices.exists(index=self.index_name):
            logger.warning(f"Index {self.index_name} already exists")
            return
        
        # Create index (ES 8.x: use keyword args instead of deprecated body=)
        self.client.indices.create(
            index=self.index_name,
            mappings=mapping["mappings"],
            settings=mapping["settings"]
        )
        logger.info(f"Created Elasticsearch index: {self.index_name}")
    
    def index_entity(self, entity: OsintEntity) -> bool:
        """Index a single entity"""
        try:
            doc = entity.model_dump(mode='json')
            
            # Generate document ID
            doc_id = f"{entity.entity_type}_{entity.value}_{entity.source}"
            
            self.client.index(
                index=self.index_name,
                id=doc_id,
                document=doc
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index entity: {e}")
            return False
    
    def bulk_index_entities(self, entities: List[OsintEntity]) -> Dict[str, int]:
        """Bulk index multiple entities"""
        if not entities:
            return {"success": 0, "failed": 0}
        
        # Prepare bulk actions
        actions = []
        for entity in entities:
            doc = entity.model_dump(mode='json')
            doc_id = f"{entity.entity_type}_{entity.value}_{entity.source}"
            
            actions.append({
                "_index": self.index_name,
                "_id": doc_id,
                "_source": doc
            })
        
        try:
            success, failed = bulk(self.client, actions, raise_on_error=False)
            logger.info(f"Bulk indexed {success} entities, {len(failed)} failed")
            return {"success": success, "failed": len(failed)}
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return {"success": 0, "failed": len(entities)}
    
    def search(self, query: SearchQuery) -> SearchResult:
        """Execute search query"""
        start_time = datetime.utcnow()
        
        # Build Elasticsearch query
        must_clauses = []
        filter_clauses = []
        
        # Main search query
        if query.query:
            import re
            
            search_term = query.query.strip()
            
            # Detect if this looks like an exact identifier (email, phone, etc.)
            is_email = '@' in search_term and '.' in search_term
            is_phone = search_term.replace('+', '').replace('-', '').replace(' ', '').isdigit() and len(search_term) >= 7
            is_exact_search = is_email or is_phone or '.' in search_term
            
            if is_exact_search:
                # EXACT SEARCH MODE: For emails, phones, IPs - prioritize exact matches heavily
                should_clauses = []
                
                # HIGHEST: Exact keyword match (boost = 100)
                should_clauses.append({
                    "term": {
                        "value.keyword": {
                            "value": search_term,
                            "boost": 100
                        }
                    }
                })
                should_clauses.append({
                    "term": {
                        "email.keyword": {
                            "value": search_term,
                            "boost": 100
                        }
                    }
                })
                
                # HIGH: Phrase match (boost = 50)
                should_clauses.append({
                    "match_phrase": {
                        "value": {
                            "query": search_term,
                            "boost": 50
                        }
                    }
                })
                should_clauses.append({
                    "match_phrase": {
                        "email": {
                            "query": search_term,
                            "boost": 50
                        }
                    }
                })
                
                # MEDIUM: Prefix match for partial (boost = 10)
                if is_email:
                    # Extract username part of email for prefix search
                    email_user = search_term.split('@')[0]
                    should_clauses.append({
                        "prefix": {
                            "value.keyword": {
                                "value": email_user,
                                "boost": 10
                            }
                        }
                    })
                
                must_clauses.append({
                    "bool": {
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                })
            else:
                # FUZZY SEARCH MODE: For general text searches
                should_clauses = []
                
                # HIGHEST PRIORITY: Exact keyword matches (boost = 10)
                should_clauses.append({
                    "multi_match": {
                        "query": search_term,
                        "fields": [
                            "value.keyword^10",
                            "email.keyword^10",
                            "domain.keyword^8",
                            "username.keyword^8",
                            "phone^10"
                        ],
                        "type": "best_fields"
                    }
                })
                
                # HIGH PRIORITY: Exact text matches without fuzziness (boost = 5)
                should_clauses.append({
                    "multi_match": {
                        "query": search_term,
                        "fields": [
                            "value^5",
                            "email^5",
                            "domain^4",
                            "username^4"
                        ],
                        "type": "phrase"
                    }
                })
                
                # MEDIUM PRIORITY: Fuzzy text matching for typos (boost = 2)
                if len(search_term) > 5:
                    should_clauses.append({
                        "multi_match": {
                            "query": search_term,
                            "fields": [
                                "value^2",
                                "email^2",
                                "domain^2",
                                "username^2"
                            ],
                            "type": "best_fields",
                            "fuzziness": "1"
                        }
                    })
                
                # Check if query looks like an IP address
                ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                if re.match(ip_pattern, search_term):
                    should_clauses.append({
                        "match": {
                            "ip": search_term
                        }
                    })
                
                # LOW PRIORITY: Metadata fields - wildcard search (boost = 1)
                should_clauses.append({
                    "query_string": {
                        "query": f"*{search_term}*",
                        "fields": ["metadata.*"],
                        "default_operator": "OR",
                        "analyze_wildcard": True,
                        "lenient": True
                    }
                })
                
                must_clauses.append({
                    "bool": {
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                })
        
        # Entity type filter
        if query.entity_types:
            filter_clauses.append({
                "terms": {"entity_type": [et.value for et in query.entity_types]}
            })
        
        # Source filter
        if query.sources:
            filter_clauses.append({
                "terms": {"source": query.sources}
            })
        
        # Exclude specific source tables (e.g., notifications, logs)
        if query.exclude_tables:
            filter_clauses.append({
                "bool": {
                    "must_not": {"terms": {"source_table": query.exclude_tables}}
                }
            })
        
        # Exclude specific data sources
        if query.exclude_sources:
            filter_clauses.append({
                "bool": {
                    "must_not": {"terms": {"source": query.exclude_sources}}
                }
            })
        
        # Date range filter
        if query.date_from or query.date_to:
            date_range = {}
            if query.date_from:
                date_range["gte"] = query.date_from.isoformat()
            if query.date_to:
                date_range["lte"] = query.date_to.isoformat()
            
            filter_clauses.append({
                "range": {"timestamp": date_range}
            })
        
        # Build final query
        es_query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses
            }
        }
        
        # Execute search - sort by score first (relevance), then timestamp
        # NOTE: exceptions are intentionally NOT caught here so the router can fall back to MongoDB
        response = self.client.search(
            index=self.index_name,
            query=es_query,
            from_=query.offset,
            size=query.limit,
            track_total_hits=True,
            sort=[
                {"_score": {"order": "desc"}},
                {"timestamp": {"order": "desc"}}
            ],
            track_scores=True
        )

        # Parse results
        hits = response["hits"]
        total = hits["total"]["value"]

        results = []
        for hit in hits["hits"]:
            try:
                entity_data = hit["_source"]
                results.append(OsintEntity(**entity_data))
            except Exception as parse_err:
                logger.warning(f"Skipping unparseable ES hit: {parse_err}")

        # Calculate query time
        took = (datetime.utcnow() - start_time).total_seconds()

        return SearchResult(
            total=total,
            results=results,
            took=took,
            offset=query.offset,
            limit=query.limit
        )
    
    def get_entity_by_value(self, value: str, entity_type: Optional[EntityType] = None) -> List[OsintEntity]:
        """Get entities by exact value match"""
        query = {
            "bool": {
                "must": [
                    {"term": {"value.keyword": value}}
                ]
            }
        }
        
        if entity_type:
            query["bool"]["filter"] = [{"term": {"entity_type": entity_type.value}}]
        
        try:
            response = self.client.search(
                index=self.index_name,
                query=query,
                size=100
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append(OsintEntity(**hit["_source"]))
            
            return results
        except Exception as e:
            logger.error(f"Get entity by value failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            # Count by entity type (ES 8.x: use keyword args, track_total_hits for real count)
            response = self.client.search(
                index=self.index_name,
                size=0,
                track_total_hits=True,
                aggs={
                    "entity_types": {
                        "terms": {"field": "entity_type", "size": 100}
                    },
                    "sources": {
                        "terms": {"field": "source", "size": 100}
                    }
                }
            )
            
            stats = {
                "total_entities": response["hits"]["total"]["value"],
                "by_type": {},
                "by_source": {}
            }
            
            for bucket in response["aggregations"]["entity_types"]["buckets"]:
                stats["by_type"][bucket["key"]] = bucket["doc_count"]
            
            for bucket in response["aggregations"]["sources"]["buckets"]:
                stats["by_source"][bucket["key"]] = bucket["doc_count"]
            
            return stats
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return {"error": str(e)}
