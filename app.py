# app.py (updated)

import os
import requests
import pyvo
import numpy as np
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv
from config import Config
from extensions import mongo, jwt, cors, admin
from admin import init_admin
from urllib.parse import quote
# from routes.ml_analyzer import ml_analyzer_bp
from flask_pymongo import PyMongo
from routes.user_route import user_bp
from routes.auth_route import auth_bp
from routes.contact_route import contact_bp
from routes.admin_route import admin_bp  # ✅ import

load_dotenv()

# Serve static frontend from 'frontend/dist' (or 'frontend/build' depending on your framework)
frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/build"))

app = Flask(__name__, static_folder=frontend_folder, static_url_path="/")
app.config.from_object(Config)
app.config["MONGO_URI"] = os.environ.get("MONGO", "mongodb://localhost:27017/mydb")

# Allow requests from the frontend development server
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Initialize extensions
cors.init_app(app)
jwt.init_app(app)
mongo.init_app(app)

app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
# app.register_blueprint(ml_analyzer_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(admin_bp)  # ✅ pastikan ini ADA

# Global error handler
@app.errorhandler(Exception)
def handle_error(e):
    status_code = getattr(e, 'code', 500)
    message = str(e)
    return jsonify({
        "success": False,
        "statusCode": status_code,
        "message": message
    }), status_code

# Serve index.html for frontend routes (Single Page App)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(frontend_folder, path)):
        return send_from_directory(frontend_folder, path)
    else:
        return send_from_directory(frontend_folder, "index.html")
    
@app.route("/api/nasa", methods=["GET"])
def nasa_api():
    nasa_api_key = os.getenv("NASA_API_KEY")
    nasa_url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_api_key}"
    response = requests.get(nasa_url)
    if response.status_code == 200:
        return jsonify(response.json())
    return jsonify({"error": "Failed to fetch data from NASA API"}), response.status_code

# Route to list API routes (optional)
@app.route("/routes", methods=["GET"])
def list_routes():
    return jsonify([str(rule) for rule in app.url_map.iter_rules()])

@app.route("/api/exoplanets", methods=["GET"])
def fetch_exoplanets():
    """
    Fetch data from NASA's Exoplanet Archive TAP service.
    """
    try:
        # Query the Planetary Systems Composite Parameters Table (pscomppars)
        query = """
        SELECT 
            pl_name, 
            discoverymethod, 
            pl_orbper, 
            pl_radj 
        FROM pscomppars 
        WHERE pl_orbper IS NOT NULL 
        ORDER BY pl_orbper ASC
        """
        # Construct the TAP service URL
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Make the HTTP GET request
        response = requests.get(tap_url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Return the data as JSON
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        # Handle request exceptions and return an error response
        print(f"Error fetching data from NASA's Exoplanet Archive TAP service: {e}")
        return jsonify({"error": "Failed to fetch data from NASA's Exoplanet Archive TAP service", "details": str(e)}), 500

@app.route("/api/tess-candidates", methods=["GET"])
def fetch_tess_candidates():
    """
    Fetch data from the TESS Objects of Interest (TOI) Table.
    """
    try:
        # Define the query for the TOI table
        query = """
        SELECT 
            tid, 
            toi, 
            pl_orbper, 
            pl_rade, 
            st_teff 
        FROM toi 
        WHERE st_teff IS NOT NULL 
        ORDER BY st_teff DESC
        """
        # Properly encode the query for the URL
        encoded_query = quote(query)
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Make the HTTP GET request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse and return the data as JSON
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        # Handle request exceptions and return an error response
        print(f"Error fetching TESS Candidates data: {e}")  # Debugging log
        return jsonify({"error": "Failed to fetch data from TESS Candidates Table", "details": str(e)}), 500
    except ValueError as e:
        # Handle JSON decoding errors
        print(f"Error parsing JSON response: {e}")  # Debugging log
        return jsonify({"error": "Failed to parse JSON response", "details": str(e)}), 500

    
@app.route("/api/planetary-systems", methods=["GET"])
def fetch_planetary_systems():
    """
    Fetch data from the Planetary Systems Composite Parameters Table.
    """
    try:
        query = "SELECT pl_name, hostname, discoverymethod, pl_orbper, pl_radj, pl_eqt FROM pscomppars WHERE pl_orbper IS NOT NULL ORDER BY pl_orbper ASC"
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={query}&format=json"
        response = requests.get(tap_url)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch data from Planetary Systems Table", "details": str(e)}), 500
    
@app.route("/api/microlensing", methods=["GET"])
def fetch_microlensing_data():
    """
    Fetch data from the Microlensing Table.
    """
    try:
        query = """
        SELECT 
            pl_name, 
            rastr, 
            decstr, 
            pl_massj, 
            pl_masse
        FROM ml
        WHERE pl_masse IS NOT NULL 
        ORDER BY pl_masse DESC
        """
        # Properly encode the query
        encoded_query = quote(query)
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"

        # Make the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        
        # Check if the request was successful
        response.raise_for_status()

        # Check if the response is JSON
        try:
            json_data = response.json()
        except ValueError as e:
            return jsonify({"error": "Failed to parse JSON response", "details": str(e)}), 500

        return jsonify(json_data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch data from Microlensing Table", "details": str(e)}), 500
    
@app.route("/api/stellar-hosts", methods=["GET"])
def fetch_stellar_hosts():
    """
    Fetch data from the Stellar Hosts Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            hostname, 
            sy_name, 
            hd_name, 
            hip_name, 
            tic_id, 
            gaia_id,
            sy_snum,
            sy_pnum,
            sy_mnum,
            cb_flag
        FROM stellarhosts 
        WHERE cb_flag IS NOT NULL 
        ORDER BY cb_flag DESC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            # Fallback query to fetch all available hostnames
            fallback_query = """
            SELECT DISTINCT hostname 
            FROM stellarhosts
            """
            encoded_fallback_query = quote(fallback_query.strip().replace("\n", " "))
            fallback_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_fallback_query}&format=json"
            print(f"Fetching available hostnames: {fallback_url}")  # Debugging log

            fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()

            return jsonify({
                "message": "No data found for stellar hosts.",
                "available_hostnames": fallback_data
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from Stellar Hosts service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Stellar Hosts service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to Stellar Hosts service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/tap-query", methods=["POST"]) 
def tap_query():
    """
    Execute a custom TAP query.
    """
    try:
        query = request.json.get("query")
        if not query:
            return jsonify({"error": "Query is required"}), 400
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={query}&format=json"
        response = requests.get(tap_url)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to execute TAP query", "details": str(e)}), 500

@app.route("/api/pscomppars", methods=["GET"])
def fetch_pscomppars():
    """
    Fetch data from the Planetary Systems Composite Parameters Table.
    """
    try:
        # Query the Planetary Systems Composite Parameters Table
        query = """
        SELECT 
            pl_name, 
            hostname, 
            discoverymethod, 
            pl_orbper, 
            pl_radj, 
            pl_eqt, 
            st_teff, 
            st_mass, 
            st_rad 
        FROM pscomppars 
        WHERE pl_orbper IS NOT NULL 
        ORDER BY pl_orbper ASC
        """
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log
        response = requests.get(tap_url)
        response.raise_for_status()  # Raise an error for bad status codes
        return jsonify(response.json())  # Return the data as JSON
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Planetary Systems Composite Parameters: {e}")  # Debugging log
        return jsonify({"error": "Failed to fetch data from Planetary Systems Composite Parameters Table", "details": str(e)}), 500
    
@app.route("/api/kepler-names", methods=["GET"])
def fetch_kepler_names():
    """
    Fetch data from the Kepler Confirmed Names Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT kepid, koi_name, kepler_name, pl_name 
        FROM keplernames 
        WHERE kepler_name IS NOT NULL 
        ORDER BY pl_name DESC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            # Fallback query to fetch all available kepler_name values
            fallback_query = """
            SELECT DISTINCT kepler_name 
            FROM keplernames
            """
            encoded_fallback_query = quote(fallback_query.strip().replace("\n", " "))
            fallback_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_fallback_query}&format=json"
            print(f"Fetching available kepler_name values: {fallback_url}")  # Debugging log

            fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()

            return jsonify({
                "message": "No data found for kepler_name.",
                "available_kepler_names": fallback_data
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from Kepler Names service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Kepler Names service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to Kepler Names service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/k2-names", methods=["GET"])
def fetch_k2_names():
    """
    Fetch data from the K2 Confirmed Names Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT epic_id, k2_name, pl_name 
        FROM k2names 
        WHERE k2_name = 'CONFIRMED' 
        ORDER BY pl_name DESC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            # Fallback query to fetch all available k2_name values
            fallback_query = """
            SELECT DISTINCT k2_name 
            FROM k2names
            """
            encoded_fallback_query = quote(fallback_query.strip().replace("\n", " "))
            fallback_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_fallback_query}&format=json"
            print(f"Fetching available k2_name values: {fallback_url}")  # Debugging log

            fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()

            return jsonify({
                "message": "No data found for k2_name = 'CONFIRMED'.",
                "available_k2_names": fallback_data
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from K2 Names service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to K2 Names service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to K2 Names service",
            "details": str(req_err)
        }), 502
    

@app.route("/api/k2-planets-candidates", methods=["GET"])
def fetch_k2_planets_candidates():
    """
    Fetch data from the K2 Planets and Candidates Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT pl_name, hostname, pl_letter, k2_name, cb_flag, discoverymethod, 
               disc_year, disc_telescope, pl_orbper, pl_orbsmax, pl_masse, 
               pl_msinie, st_mass, st_spectype 
        FROM k2pandc 
        LIMIT 5
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Return the JSON response
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        print(f"Error fetching K2 Planets and Candidates data: {e}")  # Debugging log
        return jsonify({
            "error": "Failed to fetch data from K2 Planets and Candidates Table",
            "details": str(e)
        }), 500
    
@app.route("/api/ukirt", methods=["GET"])
def fetch_ukirt_data():
    """
    Fetch data from the UKIRT Time Series Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT TOP 100 sourceid, obs_year, bulge, field, ccdid, k2c9_flag, ukirt_id, 
                       moa_id, statnpts, minvalue, maxvalue, median 
        FROM ukirttimeseries 
        WHERE statnpts IS NOT NULL 
        ORDER BY median ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Configure retries
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))

        # Send the request with retries
        headers = {"User-Agent": "my-api-client"}
        response = session.get(tap_url, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        try:
            data = response.json()
        except ValueError:
            return jsonify({"error": "Invalid JSON received from UKIRT service."}), 502

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from UKIRT service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to UKIRT service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to UKIRT service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/kelt", methods=["GET"])
def fetch_kelt_data():
    """
    Fetch data from the KELT Time Series Table using the TAP service.
    """
    try:
        # Get sourceID from query parameters or use default
        kelt_sourceid = request.args.get("sourceID", default="KELT_N12_lc_000141_V01_east")

        # Validate that sourceID is a string and not empty
        if not kelt_sourceid:
            return jsonify({"error": "sourceID is required."}), 400

        # Preliminary query to check if the kelt_sourceid exists
        check_query = f"""
        SELECT kelt_sourceid 
        FROM kelttimeseries 
        WHERE kelt_sourceid = '{kelt_sourceid}'
        """
        encoded_check_query = quote(check_query.strip().replace("\n", " "))
        check_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_check_query}&format=json"
        print(f"Checking if kelt_sourceid exists: {check_url}")  # Debugging log

        # Send the preliminary request
        headers = {"User-Agent": "my-api-client"}
        check_response = requests.get(check_url, headers=headers, timeout=30)
        check_response.raise_for_status()

        # Parse the response to check if the kelt_sourceid exists
        check_data = check_response.json()
        if not check_data:  # If no data is returned
            # Fallback query to fetch all available kelt_sourceid values
            fallback_query = """
            SELECT TOP 10 kelt_sourceid 
            FROM kelttimeseries
            """
            encoded_fallback_query = quote(fallback_query.strip().replace("\n", " "))
            fallback_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_fallback_query}&format=json"
            print(f"Fetching available kelt_sourceid values: {fallback_url}")  # Debugging log

            fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()

            return jsonify({
                "message": f"No data found for kelt_sourceid '{kelt_sourceid}'.",
                "available_sourceIDs": fallback_data
            }), 404

        # Define the main SQL query
        query = f"""
        SELECT TOP 100 kelt_sourceid, kelt_field, kelt_orientation, proc_type, ra, dec, 
                       bjdstart, bjdstop, obsstart, obsstop, kelt_mag, npts, minvalue, 
                       maxvalue, mean, stddevwrtmean, median, stddevwrtmedian, n5sigma, 
                       f5sigma, medabsdev, chisquared, range595 
        FROM kelttimeseries 
        WHERE kelt_sourceid = '{kelt_sourceid}' 
        ORDER BY bjdstart ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the main request
        response = requests.get(tap_url, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        try:
            data = response.json()
        except ValueError:
            return jsonify({"error": "Invalid JSON received from KELT service."}), 502

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KELT service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KELT service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KELT service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/superwasp", methods=["GET"])
def fetch_superwasp_data():
    """
    Fetch data from the SuperWASP Time Series Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT TOP 100 sourceid, ra, dec, hjdstart, hjdstop 
        FROM superwasptimeseries 
        WHERE hjdstart IS NOT NULL 
        ORDER BY hjdstart ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        try:
            data = response.json()
        except ValueError:
            return jsonify({"error": "Invalid JSON received from SuperWASP service."}), 502

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from SuperWASP service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to SuperWASP service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to SuperWASP service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/hwo-stars", methods=["GET"]) #failed
def fetch_hwo_stars():
    """
    Fetch data from the HWO ExEP Precursor Science Stars Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            star_name, 
            ra, 
            dec, 
            sy_dist, 
            st_mass, 
            st_rad, 
            st_teff 
        FROM di_stars_exep 
        WHERE sy_dist IS NOT NULL 
        ORDER BY sy_dist ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            # Fallback query to fetch all available star names
            fallback_query = """
            SELECT DISTINCT star_name 
            FROM di_stars_exep
            """
            encoded_fallback_query = quote(fallback_query.strip().replace("\n", " "))
            fallback_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_fallback_query}&format=json"
            print(f"Fetching available star names: {fallback_url}")  # Debugging log

            fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()

            return jsonify({
                "message": "No data found for HWO stars.",
                "available_star_names": fallback_data
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from HWO Stars service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to HWO Stars service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to HWO Stars service",
            "details": str(req_err)
        }), 502

@app.route("/api/transiting-planets", methods=["GET"])
def fetch_transiting_planets():
    """
    Fetch data from the Transiting Planets Table.
    """
    try:
        # Query the Transiting Planets Table
        query = """
        SELECT 
            pl_name, 
            hostname, 
            pl_orbper, 
            pl_radj, 
            pl_trandep, 
            pl_trandur, 
            pl_tranmid 
        FROM TD 
        WHERE pl_orbper IS NOT NULL 
        ORDER BY pl_orbper ASC
        """
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log
        response = requests.get(tap_url)
        response.raise_for_status()  # Raise an error for bad status codes
        return jsonify(response.json())  # Return the data as JSON
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Transiting Planets data: {e}")  # Debugging log
        return jsonify({"error": "Failed to fetch data from Transiting Planets Table", "details": str(e)}), 500
    
@app.route("/api/koi-cumulative", methods=["GET"])
def fetch_koi_cumulative():
    """
    Fetch data from the KOI Cumulative Delivery Table.
    """
    try:
        # Query the KOI Cumulative Delivery Table
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_disposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM cumulative 
        WHERE koi_disposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log
        response = requests.get(tap_url)
        response.raise_for_status()  # Raise an error for bad status codes
        return jsonify(response.json())  # Return the data as JSON
    except requests.exceptions.RequestException as e:
        print(f"Error fetching KOI Cumulative Delivery data: {e}")  # Debugging log
        return jsonify({"error": "Failed to fetch data from KOI Cumulative Delivery Table", "details": str(e)}), 500
    
@app.route("/api/koi-q1q6", methods=["GET"])
def fetch_koi_q1q6():
    """
    Fetch data from the KOI Q1-Q6 Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_disposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q6_koi 
        WHERE koi_disposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q6 Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q6 Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q6 Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q6 Delivery Table service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/koi-q1q8", methods=["GET"])
def fetch_koi_q1q8():
    """
    Fetch data from the KOI Q1-Q8 Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_disposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q8_koi 
        WHERE koi_disposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q8 Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q8 Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q8 Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q8 Delivery Table service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/koi-q1q12", methods=["GET"])
def fetch_koi_q1q12():
    """
    Fetch data from the KOI Q1-Q12 Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_pdisposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q12_koi 
        WHERE koi_pdisposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q12 Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q12 Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q12 Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q12 Delivery Table service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/koi-q1q16", methods=["GET"])
def fetch_koi_q1q16():
    """
    Fetch data from the KOI Q1-Q16 Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_disposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q16_koi 
        WHERE koi_disposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q16 Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q16 Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q16 Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q16 Delivery Table service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/koi-q1q17-dr24", methods=["GET"])
def fetch_koi_q1q17_dr24():
    """
    Fetch data from the KOI Q1-Q17 DR24 Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_pdisposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q17_dr24_koi 
        WHERE koi_pdisposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q17 DR24 Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q17 DR24 Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q17 DR24 Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q17 DR24 Delivery Table service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/koi-q1q17-dr25", methods=["GET"])
def fetch_koi_q1q17_dr25():
    """
    Fetch data from the KOI Q1-Q17 DR25 Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_disposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q17_dr25_koi 
        WHERE koi_disposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q17 DR25 Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q17 DR25 Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q17 DR25 Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q17 DR25 Delivery Table service",
            "details": str(req_err)
        }), 502
    
@app.route("/api/koi-q1q17-dr25-supplemental", methods=["GET"])
def fetch_koi_q1q17_dr25_supplemental():
    """
    Fetch data from the KOI Q1-Q17 DR25 Supplemental Delivery Table.
    """
    try:
        # Define the SQL query
        query = """
        SELECT 
            kepid, 
            kepoi_name, 
            koi_disposition, 
            koi_period, 
            koi_prad, 
            koi_smass, 
            koi_srad, 
            koi_steff 
        FROM q1_q17_dr25_sup_koi 
        WHERE koi_disposition IN ('CANDIDATE', 'CONFIRMED') 
        ORDER BY koi_period ASC
        """
        # Encode the query for the URL
        encoded_query = quote(query.strip().replace("\n", " "))
        tap_url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={encoded_query}&format=json"
        print(f"Querying TAP URL: {tap_url}")  # Debugging log

        # Send the request
        headers = {"User-Agent": "my-api-client"}
        response = requests.get(tap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        data = response.json()
        if not data:  # If no data is returned
            return jsonify({
                "message": "No data found for KOI Q1-Q17 DR25 Supplemental Delivery Table.",
                "available_columns": [
                    "kepid", "kepoi_name", "koi_disposition", "koi_period",
                    "koi_prad", "koi_smass", "koi_srad", "koi_steff"
                ]
            }), 404

        return jsonify(data)

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "error": "HTTP error from KOI Q1-Q17 DR25 Supplemental Delivery Table service",
            "details": str(http_err),
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to KOI Q1-Q17 DR25 Supplemental Delivery Table service timed out"}), 504

    except requests.exceptions.RequestException as req_err:
        return jsonify({
            "error": "General connection error to KOI Q1-Q17 DR25 Supplemental Delivery Table service",
            "details": str(req_err)
        }), 502


@app.route("/api/exoplanet-eu", methods=["GET"])
def fetch_exoplanet_eu():
    """
    Fetch data from the Exoplanet.eu API using pyvo.
    """
    try:
        # Initialize the TAP service for Exoplanet.eu
        service = pyvo.dal.TAPService("http://voparis-tap-planeto.obspm.fr/tap")

        # Define the ADQL query
        query = """
        SELECT 
            target_name, 
            mass, 
            radius, 
            semi_major_axis, 
            period, 
            star_name, 
            star_distance, 
            star_mass, 
            star_radius, 
            star_teff 
        FROM exoplanet.epn_core 
        WHERE semi_major_axis < 5
        """

        # Execute the query
        results = service.search(query)

        # Convert results to a list of dictionaries for JSON response
        data = [
            {field: row[field] for field in results.fieldnames}
            for row in results
        ]

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch data from Exoplanet.eu API",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)




