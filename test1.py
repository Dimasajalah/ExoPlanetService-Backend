import requests

url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
query = """
SELECT TOP 5
    kelt_sourceid, 
    kelt_field, 
    kelt_orientation, 
    proc_type, 
    ra, 
    dec, 
    bjdstart, 
    bjdstop, 
    obsstart, 
    obsstop, 
    kelt_mag, 
    npts, 
    minvalue, 
    maxvalue, 
    mean, 
    stddevwrtmean, 
    median, 
    stddevwrtmedian, 
    n5sigma, 
    f5sigma, 
    medabsdev, 
    chisquared, 
    range595 
FROM kelttimeseries 
"""

params = {
    "query": query,
    "format": "json"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print("Error:", response.status_code, response.text)



