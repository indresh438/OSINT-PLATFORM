"""Data normalization and transformation utilities"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from app.models import OsintEntity, EntityType


class DataNormalizer:
    """Normalizes raw database records into standard OSINT entity format"""
    
    # Regex patterns for entity detection
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    IP_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    
    @staticmethod
    def detect_entity_type(value: str) -> EntityType:
        """Detect entity type from value"""
        if not value:
            return EntityType.UNKNOWN
        
        value = value.strip()
        
        if DataNormalizer.EMAIL_PATTERN.match(value):
            return EntityType.EMAIL
        elif DataNormalizer.IP_PATTERN.match(value):
            return EntityType.IP
        elif DataNormalizer.DOMAIN_PATTERN.match(value):
            return EntityType.DOMAIN
        elif DataNormalizer.PHONE_PATTERN.match(value.replace('-', '').replace(' ', '')):
            return EntityType.PHONE
        elif len(value) in [32, 40, 64, 128]:  # Common hash lengths
            if re.match(r'^[a-fA-F0-9]+$', value):
                return EntityType.HASH
        
        return EntityType.UNKNOWN
    
    @staticmethod
    def extract_domain_from_email(email: str) -> Optional[str]:
        """Extract domain from email address"""
        if '@' in email:
            return email.split('@')[1].lower()
        return None
    
    @staticmethod
    def normalize_record(
        raw_record: Dict[str, Any],
        field_mapping: Dict[str, str],
        source: str,
        source_table: str
    ) -> List[OsintEntity]:
        """
        Normalize a raw database record into standard OSINT entities
        
        Args:
            raw_record: Raw record from source database
            field_mapping: Mapping of source fields to standard fields
                          e.g., {'email_addr': 'email', 'ip_address': 'ip'}
            source: Source identifier
            source_table: Source table name
        
        Returns:
            List of normalized OsintEntity objects
        """
        entities = []
        
        # Extract standard fields using mapping
        standard_fields = {}
        metadata = {}
        
        for source_field, value in raw_record.items():
            if value is None or value == '':
                continue
            
            # Convert value to string
            str_value = str(value).strip()
            
            # Check if field is mapped to a standard field
            standard_field = field_mapping.get(source_field)
            
            if standard_field in ['email', 'ip', 'domain', 'username', 'phone']:
                standard_fields[standard_field] = str_value
            else:
                # Store unmapped fields in metadata
                metadata[source_field] = str_value
        
        # Create entities for each standard field found
        primary_entity = None
        
        for field_name, field_value in standard_fields.items():
            entity_type = DataNormalizer._map_field_to_entity_type(field_name, field_value)
            
            entity = OsintEntity(
                entity_type=entity_type,
                value=field_value,
                source=source,
                source_table=source_table,
                metadata=metadata.copy(),
                **{field_name: field_value}  # Set the specific field
            )
            
            # Extract additional information
            if field_name == 'email':
                entity.email = field_value
                entity.domain = DataNormalizer.extract_domain_from_email(field_value)
            elif field_name == 'domain':
                entity.domain = field_value
            elif field_name == 'ip':
                entity.ip = field_value
            elif field_name == 'username':
                entity.username = field_value
            elif field_name == 'phone':
                entity.phone = field_value
            
            entities.append(entity)
            
            if primary_entity is None:
                primary_entity = entity
        
        # If no standard fields found, create a generic entity with metadata
        if not entities and metadata:
            # Try to find a value field
            value = metadata.get('value') or metadata.get('data') or list(metadata.values())[0]
            
            entity = OsintEntity(
                entity_type=DataNormalizer.detect_entity_type(str(value)),
                value=str(value),
                source=source,
                source_table=source_table,
                metadata=metadata
            )
            entities.append(entity)
        
        return entities
    
    @staticmethod
    def _map_field_to_entity_type(field_name: str, value: str) -> EntityType:
        """Map field name to entity type"""
        field_mapping = {
            'email': EntityType.EMAIL,
            'ip': EntityType.IP,
            'domain': EntityType.DOMAIN,
            'username': EntityType.USERNAME,
            'phone': EntityType.PHONE
        }
        
        entity_type = field_mapping.get(field_name)
        
        # If no direct mapping, try to detect from value
        if entity_type is None:
            entity_type = DataNormalizer.detect_entity_type(value)
        
        return entity_type
    
    @staticmethod
    def auto_detect_field_mapping(
        sample_records: List[Dict[str, Any]],
        table_name: str
    ) -> Dict[str, str]:
        """
        Auto-detect field mapping by analyzing sample records
        
        Args:
            sample_records: Sample records from the table
            table_name: Table name for context
        
        Returns:
            Suggested field mapping
        """
        if not sample_records:
            return {}
        
        field_mapping = {}
        
        # Get all field names from first record
        field_names = list(sample_records[0].keys())
        
        # Common field name patterns
        patterns = {
            'email': ['email', 'e_mail', 'mail', 'email_address', 'emailaddress'],
            'ip': ['ip', 'ip_address', 'ipaddress', 'ip_addr', 'ipaddr'],
            'domain': ['domain', 'domain_name', 'domainname', 'host', 'hostname'],
            'username': ['username', 'user_name', 'user', 'login', 'nickname', 'nick'],
            'phone': ['phone', 'phone_number', 'phonenumber', 'tel', 'telephone', 'mobile']
        }
        
        for field_name in field_names:
            field_lower = field_name.lower()
            
            # Check against patterns
            for standard_field, pattern_list in patterns.items():
                if any(pattern in field_lower for pattern in pattern_list):
                    field_mapping[field_name] = standard_field
                    break
        
        logger.info(f"Auto-detected field mapping for {table_name}: {field_mapping}")
        return field_mapping
