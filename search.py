"""Search endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from loguru import logger

from app.models import SearchQuery, SearchResult, EntityType
from app.elasticsearch_manager import ElasticsearchIndexer

router = APIRouter()


@router.post("/search", response_model=SearchResult)
async def search_entities(query: SearchQuery):
    """
    Search OSINT entities
    
    Primary search uses Elasticsearch (645k+ indexed records)
    Falls back to MongoDB if Elasticsearch fails
    
    - **query**: Search query string
    - **entity_types**: Filter by entity types (email, ip, domain, username, phone)
    - **sources**: Filter by data sources
    - **date_from/date_to**: Date range filter
    - **limit/offset**: Pagination
    """
    from datetime import datetime

    try:
        # PRIMARY: Use Elasticsearch for search
        indexer = ElasticsearchIndexer()
        results = indexer.search(query)
        logger.info(f"Elasticsearch search returned {results.total} results for query: {query.query}")

        # If ES returned results, use them directly
        if results.total > 0:
            return results

        # ES returned 0 results — fall through to MongoDB for verification
        logger.info(f"ES returned 0 results for '{query.query}', trying MongoDB fallback")

    except Exception as es_error:
        logger.error(f"Elasticsearch search failed: {es_error}")
        results = None

    # FALLBACK: MongoDB search (used when ES returns 0 OR throws an error)
    from app.mongodb_manager import MongoDBManager
    from app.models import OsintEntity
    import re

    try:
        mongo_manager = MongoDBManager()

        # Build MongoDB query
        mongo_query = {}
        must_conditions = []
        query_conditions = []

        if query.query:
            search_term = query.query.strip()

            if "@" in search_term:
                query_conditions.append({"email": search_term})
                query_conditions.append({"email": {"$regex": re.escape(search_term), "$options": "i"}})
                query_conditions.append({"value": search_term})
                query_conditions.append({"value": {"$regex": re.escape(search_term), "$options": "i"}})
            elif search_term.replace(".", "").replace("-", "").isdigit():
                query_conditions.append({"phone": search_term})
                query_conditions.append({"ip": search_term})
                query_conditions.append({"value": search_term})
            else:
                regex_pattern = {"$regex": re.escape(search_term), "$options": "i"}
                query_conditions.append({"value": regex_pattern})
                query_conditions.append({"email": regex_pattern})
                query_conditions.append({"username": regex_pattern})
                query_conditions.append({"domain": regex_pattern})

            if query_conditions:
                must_conditions.append({"$or": query_conditions})

        if query.entity_types:
            must_conditions.append({"entity_type": {"$in": [et.value for et in query.entity_types]}})

        if query.sources:
            must_conditions.append({"source": {"$in": query.sources}})

        if query.exclude_tables:
            must_conditions.append({"source_table": {"$nin": query.exclude_tables}})

        if query.exclude_sources:
            must_conditions.append({"source": {"$nin": query.exclude_sources}})

        if query.date_from or query.date_to:
            date_filter = {}
            if query.date_from:
                date_filter["$gte"] = query.date_from
            if query.date_to:
                date_filter["$lte"] = query.date_to
            must_conditions.append({"timestamp": date_filter})

        if must_conditions:
            if len(must_conditions) == 1:
                mongo_query = must_conditions[0]
            else:
                mongo_query = {"$and": must_conditions}

        start_time = datetime.utcnow()

        if query.deduplicate:
            pipeline = [
                {"$match": mongo_query},
                {"$sort": {"timestamp": -1}},
                {
                    "$group": {
                        "_id": {
                            "value": "$value",
                            "source_table": "$source_table",
                            "source": "$source"
                        },
                        "doc": {"$first": "$$ROOT"},
                        "count": {"$sum": 1}
                    }
                },
                {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", {"duplicate_count": "$count"}]}}},
                {"$sort": {"timestamp": -1}},
                {"$skip": query.offset},
                {"$limit": query.limit}
            ]

            cursor = mongo_manager.entities_collection.aggregate(pipeline)
            total_pipeline = [
                {"$match": mongo_query},
                {
                    "$group": {
                        "_id": {
                            "value": "$value",
                            "source_table": "$source_table",
                            "source": "$source"
                        }
                    }
                },
                {"$count": "total"}
            ]
            total_result = list(mongo_manager.entities_collection.aggregate(total_pipeline))
            total = total_result[0]["total"] if total_result else 0
        else:
            total = mongo_manager.entities_collection.count_documents(mongo_query)
            cursor = mongo_manager.entities_collection.find(mongo_query).sort("timestamp", -1).skip(query.offset).limit(query.limit)

        mongo_results = []
        for doc in cursor:
            doc.pop("_id", None)
            duplicate_count = doc.pop("duplicate_count", 1)

            try:
                entity = OsintEntity(**doc)
                if query.deduplicate and duplicate_count > 1:
                    entity.metadata["duplicate_count"] = duplicate_count
                    entity.metadata["note"] = f"Showing 1 of {duplicate_count} identical records"
                mongo_results.append(entity)
            except Exception as parse_err:
                logger.warning(f"Failed to convert MongoDB document to entity: {parse_err}")
                continue

        took = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"MongoDB fallback returned {total} results for query: {query.query}")

        return SearchResult(
            total=total,
            results=mongo_results,
            took=took,
            offset=query.offset,
            limit=query.limit
        )

    except Exception as mongo_error:
        logger.error(f"MongoDB fallback also failed: {mongo_error}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(mongo_error)}")


@router.get("/search/quick")
async def quick_search(
    q: str = Query(..., description="Search query"),
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum results")
):
    """Quick search with simple parameters"""
    try:
        query = SearchQuery(
            query=q,
            entity_types=[entity_type] if entity_type else None,
            limit=limit
        )
        
        indexer = ElasticsearchIndexer()
        results = indexer.search(query)
        return results
    except Exception as e:
        logger.error(f"Quick search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/by-value/{value}")
async def search_by_value(
    value: str,
    entity_type: Optional[EntityType] = None
):
    """Search for exact value match"""
    try:
        indexer = ElasticsearchIndexer()
        results = indexer.get_entity_by_value(value, entity_type)
        return {
            "value": value,
            "entity_type": entity_type.value if entity_type else None,
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Search by value failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/exact/{value}")
async def exact_search(
    value: str,
    search_in: str = Query("all", description="Where to search: all, elasticsearch, mongodb")
):
    """
    Exact match search - checks both Elasticsearch and MongoDB
    Returns detailed information about whether the entity exists
    """
    from app.mongodb_manager import MongoDBManager
    
    try:
        results = {
            "query": value,
            "search_in": search_in,
            "found": False,
            "elasticsearch": {"found": False, "count": 0, "results": []},
            "mongodb": {"found": False, "count": 0, "results": []}
        }
        
        if search_in in ["all", "elasticsearch"]:
            try:
                indexer = ElasticsearchIndexer()
                es_results = indexer.get_entity_by_value(value)
                if es_results:
                    results["elasticsearch"]["found"] = True
                    results["elasticsearch"]["count"] = len(es_results)
                    results["elasticsearch"]["results"] = es_results
                    results["found"] = True
            except Exception as e:
                logger.error(f"Elasticsearch exact search failed: {e}")
                results["elasticsearch"]["error"] = str(e)
        
        if search_in in ["all", "mongodb"]:
            try:
                mongo_manager = MongoDBManager()
                mongo_results = list(mongo_manager.entities_collection.find({
                    "$or": [
                        {"value": value},
                        {"email": value},
                        {"username": value},
                        {"phone": value},
                        {"domain": value}
                    ]
                }).limit(100))
                
                for doc in mongo_results:
                    doc["_id"] = str(doc["_id"])
                
                if mongo_results:
                    results["mongodb"]["found"] = True
                    results["mongodb"]["count"] = len(mongo_results)
                    results["mongodb"]["results"] = mongo_results[:10]
                    results["found"] = True
                    
            except Exception as e:
                logger.error(f"MongoDB exact search failed: {e}")
                results["mongodb"]["error"] = str(e)
        
        return results
        
    except Exception as e:
        logger.error(f"Exact search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Exact search failed: {str(e)}")


@router.get("/search/pattern/{pattern}")
async def pattern_search(
    pattern: str,
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum results")
):
    """
    Pattern/wildcard search - searches Elasticsearch with wildcard matching
    Useful for partial matches like 'satush' to find 'satush005@gmail.com'
    """
    try:
        # Use Elasticsearch for pattern search
        indexer = ElasticsearchIndexer()
        
        query = SearchQuery(
            query=pattern,
            entity_types=[entity_type] if entity_type else None,
            limit=limit
        )
        
        results = indexer.search(query)
        
        return {
            "pattern": pattern,
            "entity_type": entity_type.value if entity_type else "all",
            "total": results.total,
            "results": [r.model_dump() for r in results.results],
            "took": results.took,
            "note": "Searches Elasticsearch with pattern matching"
        }
        
    except Exception as e:
        logger.error(f"Pattern search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern search failed: {str(e)}")
