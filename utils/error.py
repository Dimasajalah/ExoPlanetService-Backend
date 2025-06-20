from flask import jsonify

def error_handler(status_code, message):
    response = jsonify({
        "success": False,
        "statusCode": status_code,
        "message": message
    })
    response.status_code = status_code
    return response