import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import math
from datetime import datetime

# Configuring logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection(db_config):
    """Establishing database connection"""
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

def meters_to_degrees_latitude(meters):
    """Converting meters to degrees latitude"""
    return meters / 111000  # Approx. 111 km per degree latitude

def meters_to_degrees_longitude(meters, latitude):
    """Converting meters to degrees longitude, accounting for latitude"""
    return meters / (111000 * math.cos(math.radians(latitude)))

def create_grid(params):
    """Creating grid of squares based on center point and distances"""
    grids = []
    
    # Extract parameters from frontend
    center_latitude = float(params["center_latitude"])
    center_longitude = float(params["center_longitude"])
    distance_north = float(params["distance_north"])
    distance_south = float(params["distance_south"])
    distance_east = float(params["distance_east"])
    distance_west = float(params["distance_west"])
    grid_size = float(params["grid_size"])
    
    # Calculating boundaries in degrees
    lat_diff_north = meters_to_degrees_latitude(distance_north)
    lat_diff_south = meters_to_degrees_latitude(distance_south)
    lon_diff_east = meters_to_degrees_longitude(distance_east, center_latitude)
    lon_diff_west = meters_to_degrees_longitude(distance_west, center_latitude)
    
    min_lat = center_latitude - lat_diff_south
    max_lat = center_latitude + lat_diff_north
    min_lon = center_longitude - lon_diff_west
    max_lon = center_longitude + lon_diff_east
    
    # Calculating grid size in degrees
    grid_size_lat = meters_to_degrees_latitude(grid_size)
    grid_size_lon = meters_to_degrees_longitude(grid_size, center_latitude)
    
    # Generating grid squares
    lat = min_lat
    while lat < max_lat:
        lon = min_lon
        while lon < max_lon:
            grids.append({
                "bottom_left_lat": lat,
                "bottom_left_lon": lon,
                "top_right_lat": lat + grid_size_lat,
                "top_right_lon": lon + grid_size_lon,
                "center_lat": lat + grid_size_lat / 2,
                "center_lon": lon + grid_size_lon / 2
            })
            lon += grid_size_lon
        lat += grid_size_lat
    
    logger.info(f"Created {len(grids)} grid squares")
    return grids

def count_visits_in_grid(conn, grids, start_date, end_date):
    """Counting location visits in each grid square"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT latitude, longitude
                FROM location_data
                WHERE server_time >= %s AND server_time <= %s
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
                AND google_account IS NOT NULL
            """
            cur.execute(query, (start_date, end_date))
            locations = cur.fetchall()
            logger.info(f"Fetched {len(locations)} location records")
            
            # Initializing visit counts for each grid
            grid_counts = {i: 0 for i in range(len(grids))}
            
            # Counting visits per grid square
            for loc in locations:
                lat = float(loc['latitude'])
                lon = float(loc['longitude'])
                for i, grid in enumerate(grids):
                    if (grid['bottom_left_lat'] <= lat < grid['top_right_lat'] and
                        grid['bottom_left_lon'] <= lon < grid['top_right_lon']):
                        grid_counts[i] += 1
                        break
            
            return grid_counts
    except psycopg2.Error as e:
        logger.error(f"Database error in count_visits_in_grid: {e}")
        raise

def save_to_database(conn, grids, grid_counts, params):
    """Saving grid visit counts to database"""
    try:
        results = []
        with conn.cursor() as cur:
            for i, grid in enumerate(grids):
                if grid_counts[i] > 0:  # Only save grids with visits
                    cur.execute("""
                        INSERT INTO grid_visit_counts (
                            id, center_latitude, center_longitude,
                            grid_bottom_left_latitude, grid_bottom_left_longitude,
                            grid_top_right_latitude, grid_top_right_longitude,
                            visit_count, start_date, end_date, created_at
                        ) VALUES (nextval('grid_visit_counts_id_seq'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *
                    """, (
                        grid['center_lat'],
                        grid['center_lon'],
                        grid['bottom_left_lat'],
                        grid['bottom_left_lon'],
                        grid['top_right_lat'],
                        grid['top_right_lon'],
                        grid_counts[i],
                        params["start_date"],
                        params["end_date"],
                        datetime.utcnow()
                    ))
                    results.append(cur.fetchone())  # Store the returned row
            conn.commit()
            logger.info(f"Saved {len(results)} grid squares with visits to database")
            return results
    except psycopg2.Error as e:
        logger.error(f"Database error in save_to_database: {e}")
        conn.rollback()
        raise

def run_grid_analysis(db_config, params):
    """Main function to execute grid analysis"""
    try:
        # Connecting to database
        conn = get_db_connection(db_config)
        
        # Parsing dates
        start_date = datetime.fromisoformat(params["start_date"].replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(params["end_date"].replace("Z", "+00:00"))
        
        # Creating grid
        grids = create_grid(params)
        
        # Counting visits in each grid square
        grid_counts = count_visits_in_grid(conn, grids, start_date, end_date)
        
        # Saving results to database and returning the saved rows
        results = save_to_database(conn, grids, grid_counts, params)
        
        # Format results to match the expected array structure
        formatted_results = [
            [
                row[0],  # id
                row[1],  # center_latitude
                row[2],  # center_longitude
                row[3],  # grid_bottom_left_latitude
                row[4],  # grid_bottom_left_longitude
                row[5],  # grid_top_right_latitude
                row[6],  # grid_top_right_longitude
                row[7],  # visit_count
                row[8],  # start_date
                row[9],  # end_date
                row[10], # created_at
                None     # null placeholder as per your log
            ] for row in results
        ]
        
        return {"grid_visit_counts": formatted_results if formatted_results else []}
    except Exception as e:
        logger.error(f"Error in run_grid_analysis: {e}")
        return {"grid_visit_counts": []}  # Return empty array on error
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")