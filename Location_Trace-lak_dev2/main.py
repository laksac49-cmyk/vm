import os
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import psycopg2
from psycopg2.extras import RealDictCursor
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import logging
import math
from pydantic import BaseModel
from grid_location_analysis import run_grid_analysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "location_tracker"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "root")
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

def init_users_table_if_not_exists(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")
            if not cur.fetchone()[0]:
                logger.info("Users table not found, creating it...")
                cur.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL
                    );
                """)
                cur.execute("""
                    INSERT INTO users (username, hashed_password)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO NOTHING;
                """, ("lakmal@gmail.com", "$2b$12$88ctn7jtijH4KhIu8k/rJe6LL44Yk8wECnyi4cVZ.EOxsf/lUlVnC"))
                conn.commit()
                logger.info("Users table initialized with lakmal@gmail.com.")
    except psycopg2.Error as e:
        logger.error(f"Error initializing users table: {e}")
        conn.rollback()
        raise

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(conn, username: str):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    except psycopg2.Error as e:
        logger.error(f"Database error in get_user: {e}")
        return None

def authenticate_user(conn, username: str, password: str):
    init_users_table_if_not_exists(conn)
    user = get_user(conn, username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    try:
        user = authenticate_user(conn, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user["username"]}, expires_delta=token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")
    finally:
        conn.close()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    conn = get_db_connection()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = get_user(conn, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError as e:
        logger.error(f"JWT decoding error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Current user error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {e}")
    finally:
        conn.close()

class GridAnalysisParams(BaseModel):
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None
    distance_north: Optional[float] = None
    distance_south: Optional[float] = None
    distance_east: Optional[float] = None
    distance_west: Optional[float] = None
    grid_size: Optional[float] = None
    start_date: str
    end_date: str

async def get_grid_params_internal():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Use COALESCE to handle NULL values
            query = """
                SELECT
                    AVG(COALESCE(latitude, 0)) as center_latitude,
                    AVG(COALESCE(longitude, 0)) as center_longitude,
                    MIN(COALESCE(latitude, 0)) as min_latitude,
                    MAX(COALESCE(latitude, 0)) as max_latitude,
                    MIN(COALESCE(longitude, 0)) as min_longitude,
                    MAX(COALESCE(longitude, 0)) as max_longitude,
                    MIN(COALESCE(server_time, NOW() - INTERVAL '48 hours')) as start_date,
                    MAX(COALESCE(server_time, NOW())) as end_date
                FROM location_data
            """
            logger.info(f"Executing query: {query}")
            cur.execute(query)
            result = cur.fetchone()
            logger.info(f"Query result: {result}")
            if not result or result["center_latitude"] == 0 and result["center_longitude"] == 0 and result["start_date"] == (datetime.utcnow() - timedelta(hours=48)) and result["end_date"] == datetime.utcnow():
                logger.warning("No valid location data found, using fallback defaults")
                return {
                    "center_latitude": 0.0,
                    "center_longitude": 0.0,
                    "distance_north": 1000.0,
                    "distance_south": 1000.0,
                    "distance_east": 1000.0,
                    "distance_west": 1000.0,
                    "grid_size": 1000.0,
                    "start_date": (datetime.utcnow() - timedelta(hours=48)).isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                }

            center_lat = result["center_latitude"]
            center_lon = result["center_longitude"]
            distance_north = (result["max_latitude"] - center_lat) * 111000
            distance_south = (center_lat - result["min_latitude"]) * 111000
            distance_east = (result["max_longitude"] - center_lon) * 111000 * math.cos(math.radians(center_lat))
            distance_west = (center_lon - result["min_longitude"]) * 111000 * math.cos(math.radians(center_lat))

            max_distance = max(distance_north, distance_south, distance_east, distance_west)
            grid_size = max(1000, max_distance / 20)

            return {
                "center_latitude": round(center_lat, 6),
                "center_longitude": round(center_lon, 6),
                "distance_north": round(max(1000, distance_north), 2),
                "distance_south": round(max(1000, distance_south), 2),
                "distance_east": round(max(1000, distance_east), 2),
                "distance_west": round(max(1000, distance_west), 2),
                "grid_size": round(grid_size, 2),
                "start_date": result["start_date"].isoformat() if result["start_date"] else (datetime.utcnow() - timedelta(hours=48)).isoformat(),
                "end_date": result["end_date"].isoformat() if result["end_date"] else datetime.utcnow().isoformat()
            }
    except psycopg2.Error as e:
        logger.error(f"Database error in get_grid_params_internal: {e.pgerror}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.pgerror}")
    except Exception as e:
        logger.error(f"Unexpected error in get_grid_params_internal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()

@app.post("/api/grid-analysis")
async def run_grid_analysis_endpoint(params: GridAnalysisParams, current_user: dict = Depends(get_current_user)):
    try:
        # Fetch default parameters if any input is null
        defaults = await get_grid_params_internal()
        params_dict = params.dict()
        
        # Use defaults for null values
        params_dict["center_latitude"] = params_dict["center_latitude"] if params_dict["center_latitude"] is not None else defaults["center_latitude"]
        params_dict["center_longitude"] = params_dict["center_longitude"] if params_dict["center_longitude"] is not None else defaults["center_longitude"]
        params_dict["distance_north"] = params_dict["distance_north"] if params_dict["distance_north"] is not None else defaults["distance_north"]
        params_dict["distance_south"] = params_dict["distance_south"] if params_dict["distance_south"] is not None else defaults["distance_south"]
        params_dict["distance_east"] = params_dict["distance_east"] if params_dict["distance_east"] is not None else defaults["distance_east"]
        params_dict["distance_west"] = params_dict["distance_west"] if params_dict["distance_west"] is not None else defaults["distance_west"]
        params_dict["grid_size"] = params_dict["grid_size"] if params_dict["grid_size"] is not None else defaults["grid_size"]

        # Validate required fields
        if not params_dict["start_date"] or not params_dict["end_date"]:
            raise HTTPException(status_code=400, detail="Start and end dates are required")

        # Validate numeric fields
        numeric_fields = [
            "center_latitude",
            "center_longitude",
            "distance_north",
            "distance_south",
            "distance_east",
            "distance_west",
            "grid_size",
        ]
        for field in numeric_fields:
            if not isinstance(params_dict[field], (int, float)) or params_dict[field] is None:
                raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ')} must be a valid number")

        if params_dict["center_latitude"] < -90 or params_dict["center_latitude"] > 90:
            raise HTTPException(status_code=400, detail="Center latitude must be between -90 and 90")
        if params_dict["center_longitude"] < -180 or params_dict["center_longitude"] > 180:
            raise HTTPException(status_code=400, detail="Center longitude must be between -180 and 180")
        if params_dict["distance_north"] < 0:
            raise HTTPException(status_code=400, detail="Distance north must be non-negative")
        if params_dict["distance_south"] < 0:
            raise HTTPException(status_code=400, detail="Distance south must be non-negative")
        if params_dict["distance_east"] < 0:
            raise HTTPException(status_code=400, detail="Distance east must be non-negative")
        if params_dict["distance_west"] < 0:
            raise HTTPException(status_code=400, detail="Distance west must be non-negative")
        if params_dict["grid_size"] <= 0:
            raise HTTPException(status_code=400, detail="Grid size must be positive")

        logger.info(f"Running grid analysis with params: {params_dict}")
        results = run_grid_analysis(DB_CONFIG, params_dict)
        logger.info(f"Returning grid_visit_counts: {results}")
        return {"grid_visit_counts": results}
    except Exception as e:
        logger.error(f"Error in grid-analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Grid analysis failed: {str(e)}")

@app.get("/api/grid-params")
async def get_grid_params(current_user: dict = Depends(get_current_user)):
    return await get_grid_params_internal()

@app.get("/api/location-data-all")
def get_all_location_data(
    start_date: str = Query(..., description="Start date in ISO format (e.g., 2025-06-25T00:00:00Z)"),
    end_date: str = Query(..., description="End date in ISO format (e.g., 2025-06-27T23:59:59Z)"),
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM location_data
                WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
                AND server_time IS NOT NULL
                AND server_time >= %s AND server_time < %s
                ORDER BY server_time ASC
            """
            try:
                start_date_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end_date_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                if start_date_dt > end_date_dt:
                    raise ValueError("Start date must be before end date")
                params = [start_date_dt, end_date_dt]
            except ValueError as ve:
                logger.error(f"Invalid date format or range: {ve}")
                raise HTTPException(status_code=400, detail=f"Invalid date format or range: {ve}")

            logger.info(f"Executing query: {query} with params {params}")
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            logger.info(f"Found {len(rows)} rows in location_data")
            if not rows:
                logger.warning("No data found in location_data for the given date range")
                return []
            return rows
    except psycopg2.Error as e:
        logger.error(f"Database error in location-data-all: {e.pgerror}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.pgerror}")
    except Exception as e:
        logger.error(f"Unexpected error in location-data-all: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()

@app.get("/api/location-data")
def read_location_data(
    current_user: dict = Depends(get_current_user),
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    google_account: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[float] = None,
    in_circle: Optional[bool] = True,
    limit: Optional[int] = None
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            default_from = datetime.utcnow() - timedelta(hours=48)
            default_to = datetime.utcnow()
            
            try:
                from_time_dt = datetime.fromisoformat(from_time.replace("Z", "+00:00")) if from_time else default_from
                to_time_dt = datetime.fromisoformat(to_time.replace("Z", "+00:00")) if to_time else default_to
            except ValueError as ve:
                logger.error(f"Invalid time format provided: {ve}")
                raise HTTPException(status_code=400, detail=f"Invalid time format: {ve}")

            logger.info(f"API received from_time: {from_time_dt}, to_time: {to_time_dt}, google_account: {google_account}, latitude: {latitude}, longitude: {longitude}, radius: {radius}, in_circle: {in_circle}, limit: {limit}")

            query = """
                SELECT * FROM location_data 
                WHERE battery_level IS NOT NULL 
                AND server_time IS NOT NULL 
                AND google_account IS NOT NULL 
                AND latitude IS NOT NULL 
                AND longitude IS NOT NULL 
                AND server_time >= %s AND server_time < %s
            """
            params = [from_time_dt, to_time_dt]

            if google_account:
                query += " AND google_account = %s"
                params.append(google_account)
            
            if latitude is not None and longitude is not None and radius is not None:
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180 and radius > 0):
                    logger.error(f"Invalid circle parameters: latitude={latitude}, longitude={longitude}, radius={radius}")
                    raise HTTPException(status_code=400, detail="Invalid latitude, longitude, or radius")
                query += f" AND ST_DWithin(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s) = %s"
                params.extend([longitude, latitude, radius, in_circle])

            query += " ORDER BY server_time ASC"
            if limit is not None and limit > 0:
                query += " LIMIT %s"
                params.append(limit)

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            logger.info(f"Executed query: {query} with params {params}")
            logger.info(f"Found {len(rows)} rows in location_data.")

            if not rows:
                logger.warning("No data found for the given filters.")
                return []

            return rows
    except psycopg2.Error as e:
        logger.error(f"Database error in location-data: {e.pgerror}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.pgerror}")
    except Exception as e:
        logger.error(f"Unexpected error in location-data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()

@app.get("/api/local-time")
async def get_local_time(server_time: str, google_account: str = "", current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        server_time_dt = datetime.fromisoformat(server_time.replace("Z", "+00:00")) if "T" in server_time else datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")
        logger.info(f"Fetching local_time for server_time: {server_time_dt}, google_account: {google_account}")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT local_time 
                FROM location_data 
                WHERE server_time >= %s - INTERVAL '5 seconds' 
                AND server_time <= %s + INTERVAL '5 seconds' 
                AND (google_account = %s OR %s = '')
                AND local_time IS NOT NULL
                LIMIT 1;
            """
            cur.execute(query, (server_time_dt, server_time_dt, google_account, google_account))
            result = cur.fetchone()
            if result and "local_time" in result:
                local_time = result["local_time"]
                if isinstance(local_time, str):
                    try:
                        local_time = datetime.fromisoformat(local_time.replace("Z", "+00:00"))
                    except ValueError:
                        try:
                            local_time = datetime.strptime(local_time, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            logger.error(f"Could not parse local_time string: {result['local_time']}")
                            return {"local_time": server_time_dt.isoformat()} 

                local_time_utc = local_time if local_time.tzinfo else local_time.replace(tzinfo=None)
                logger.info(f"Found local_time: {local_time_utc}")
                return {"local_time": local_time_utc.isoformat()}
            logger.warning(f"No local_time found for server_time: {server_time_dt}")
            return {"local_time": server_time_dt.isoformat()}
    except (ValueError, psycopg2.Error) as e:
        logger.error(f"Database error in get_local_time: {e.pgerror if hasattr(e, 'pgerror') else str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.pgerror if hasattr(e, 'pgerror') else str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_local_time: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()

# Run using: uvicorn main:app --host 0.0.0.0 --port 8080