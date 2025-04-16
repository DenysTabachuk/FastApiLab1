"""
PostgreSQL repository module that uses direct psycopg2 connections
for advanced PostgreSQL features not available in SQLAlchemy.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database import get_psycopg_conn

logger = logging.getLogger(__name__)

class PgRepository:
    """Repository for direct PostgreSQL operations"""
    
    @staticmethod
    def search_apartments(
        query: str, 
        min_price: Optional[int] = None, 
        max_price: Optional[int] = None,
        city: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Full-text search for apartments using PostgreSQL's full-text search capabilities
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            # Build the WHERE clause with parameters
            where_clauses = []
            params = []
            
            # Add full-text search condition if query is provided
            if query and query.strip():
                where_clauses.append("search_vector @@ plainto_tsquery('english', %s)")
                params.append(query)
            
            # Add price range conditions
            if min_price is not None:
                where_clauses.append("price >= %s")
                params.append(min_price)
            
            if max_price is not None:
                where_clauses.append("price <= %s")
                params.append(max_price)
            
            # Add city condition
            if city:
                where_clauses.append("location_id IN (SELECT id FROM locations WHERE city ILIKE %s)")
                params.append(f"%{city}%")
            
            # Combine all conditions
            where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"
            
            # Build the complete SQL query with ranking
            sql = f"""
            SELECT a.*, 
                   l.city, l.street, l.house_number,
                   u.first_name, u.last_name, u.email,
                   CASE WHEN %s <> '' THEN ts_rank_cd(a.search_vector, plainto_tsquery('english', %s)) ELSE 0 END AS rank
            FROM apartments a
            JOIN locations l ON a.location_id = l.id
            JOIN users u ON a.owner_id = u.id
            WHERE {where_clause} AND a.status = 'approved'
            ORDER BY rank DESC, a.created_at DESC
            LIMIT %s OFFSET %s
            """
            
            # Add query parameters for ts_rank_cd
            exec_params = [query or '', query or ''] + params + [limit, offset]
            
            cur.execute(sql, exec_params)
            results = cur.fetchall()
            
            return results
        except Exception as e:
            logger.error(f"Error in search_apartments: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_apartments_with_jsonb_features(features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find apartments with specific features using JSONB querying
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            # Build a query that searches for apartments with matching features
            conditions = []
            params = []
            
            for key, value in features.items():
                conditions.append(f"features->>%s = %s")
                params.append(key)
                params.append(str(value))
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            sql = f"""
            SELECT a.*, l.city, l.street, l.house_number
            FROM apartments a
            JOIN locations l ON a.location_id = l.id
            WHERE {where_clause} AND a.status = 'approved'
            """
            
            cur.execute(sql, params)
            results = cur.fetchall()
            
            return results
        except Exception as e:
            logger.error(f"Error in get_apartments_with_jsonb_features: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_apartment_features(apartment_id: int, features: Dict[str, Any]) -> bool:
        """
        Update apartment features using JSONB operations
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            # Update using JSONB concatenation operator
            sql = """
            UPDATE apartments
            SET features = features || %s::jsonb
            WHERE id = %s
            RETURNING id
            """
            
            cur.execute(sql, (features, apartment_id))
            result = cur.fetchone()
            conn.commit()
            
            return result is not None
        except Exception as e:
            logger.error(f"Error in update_apartment_features: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_apartment_statistics() -> Dict[str, Any]:
        """
        Get advanced statistics about apartments using PostgreSQL aggregations
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            sql = """
            SELECT
                COUNT(*) as total_count,
                ROUND(AVG(price), 2) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
                COUNT(DISTINCT owner_id) as unique_owners,
                COUNT(DISTINCT location_id) as unique_locations,
                COUNT(*) FILTER (WHERE status = 'approved') as approved_count,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
                MODE() WITHIN GROUP (ORDER BY location_id) as most_common_location_id
            FROM apartments
            """
            
            cur.execute(sql)
            result = cur.fetchone()
            
            # Get the most common city
            if result.get('most_common_location_id'):
                cur.execute("""
                SELECT city FROM locations WHERE id = %s
                """, (result['most_common_location_id'],))
                city_result = cur.fetchone()
                result['most_common_city'] = city_result['city'] if city_result else None
            
            return dict(result)
        except Exception as e:
            logger.error(f"Error in get_apartment_statistics: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_user_activity_statistics() -> List[Dict[str, Any]]:
        """
        Get statistics about user activity using PostgreSQL window functions
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            sql = """
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                COUNT(a.id) as apartment_count,
                MAX(a.created_at) as last_apartment_created,
                MIN(a.created_at) as first_apartment_created,
                ROUND(AVG(a.price), 2) as avg_price,
                COUNT(a.id) FILTER (WHERE a.status = 'approved') as approved_count,
                COUNT(a.id) FILTER (WHERE a.status = 'rejected') as rejected_count,
                RANK() OVER (ORDER BY COUNT(a.id) DESC) as rank_by_count
            FROM 
                users u
            LEFT JOIN 
                apartments a ON u.id = a.owner_id
            GROUP BY 
                u.id, u.email, u.first_name, u.last_name
            ORDER BY 
                apartment_count DESC
            LIMIT 20
            """
            
            cur.execute(sql)
            results = cur.fetchall()
            
            return results
        except Exception as e:
            logger.error(f"Error in get_user_activity_statistics: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_nearby_apartments(lat: float, lon: float, radius_km: float = 5) -> List[Dict[str, Any]]:
        """
        Find apartments near a specific location using PostgreSQL's geospatial capabilities.
        Requires the coordinates field to be populated in the locations table.
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            # Note: This assumes the coordinates JSONB field has lat and lon keys
            sql = """
            SELECT 
                a.*,
                l.city, l.street, l.house_number,
                (l.coordinates->>'lat')::float as lat,
                (l.coordinates->>'lon')::float as lon,
                (6371 * acos(
                    cos(radians(%s)) * 
                    cos(radians((l.coordinates->>'lat')::float)) * 
                    cos(radians((l.coordinates->>'lon')::float) - radians(%s)) + 
                    sin(radians(%s)) * 
                    sin(radians((l.coordinates->>'lat')::float))
                )) as distance
            FROM apartments a
            JOIN locations l ON a.location_id = l.id
            WHERE l.coordinates IS NOT NULL
            AND a.status = 'approved'
            HAVING distance <= %s
            ORDER BY distance
            """
            
            cur.execute(sql, (lat, lon, lat, radius_km))
            results = cur.fetchall()
            
            return results
        except Exception as e:
            logger.error(f"Error in get_nearby_apartments: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def set_location_coordinates(location_id: int, lat: float, lon: float) -> bool:
        """
        Update location coordinates using JSONB
        """
        try:
            conn = get_psycopg_conn()
            cur = conn.cursor()
            
            sql = """
            UPDATE locations
            SET coordinates = jsonb_build_object('lat', %s, 'lon', %s)
            WHERE id = %s
            RETURNING id
            """
            
            cur.execute(sql, (lat, lon, location_id))
            result = cur.fetchone()
            conn.commit()
            
            return result is not None
        except Exception as e:
            logger.error(f"Error in set_location_coordinates: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close() 