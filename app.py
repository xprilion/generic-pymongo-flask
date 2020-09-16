import os
from flask import Flask, jsonify, request, abort, make_response
from flask_pymongo import PyMongo, ObjectId
from flask_cors import CORS, cross_origin
import datetime
import json
from bson.json_util import dumps

app = Flask(__name__)
CORS(app)

# HTTP status code constants
HTTP_SUCCESS_GET_OR_UPDATE          =   200
HTTP_SUCCESS_CREATED                =   201
HTTP_SUCCESS_DELETED                =   204
HTTP_SERVER_ERROR                   =   500
HTTP_NOT_FOUND                      =   404
HTTP_BAD_REQUEST                    =   400

# Put your MongoDB connection URL here. Use authSource only if you're authentication against
# a different database than the one you shall be querying for data.
app.config["MONGO_URI"] = "mongodb://username:password@host:port/database?authSource=admin"
mongo = PyMongo(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def send(data, status_code):
    """
        Create a Flask response based on the data and status_code received.
    """
    return make_response(dumps(data), status_code)

@app.route('/')
def home():
    """
        Say Hello to the world!
    """
    return send('Hello World!', HTTP_SUCCESS_GET_OR_UPDATE)

@app.route('/time', methods=['GET'])
def server_time():
    """
        Return server time. Can be useful in situations where your client wants to sync time.
    """
    data = {"time": datetime.datetime.now()}
    return send(data, HTTP_SUCCESS_GET_OR_UPDATE)

@app.route('/<collection_name>', methods=['POST'])
def post_item(collection_name):
    """
        Post one item in collection_name.
    """
    collection = getattr(mongo.db, collection_name)
    formdata = request.json
    try:
        insert_id = str(collection.insert_one(formdata).inserted_id)
        output = {'message': 'new item created', "_id": insert_id}
        return send(output, HTTP_SUCCESS_CREATED)
    except Exception as e:
        output = {'error' : str(e)}
        return send(output, HTTP_BAD_REQUEST)

@app.route('/<collection_name>/count', methods=['GET'])
def collection_name_count(collection_name):
    """
        Count of number of documents in a collection_name.
    """
    collection = getattr(mongo.db, collection_name)
    results = collection.find()
    output = {
        "count": results.count()
    }
    return send(output, HTTP_SUCCESS_GET_OR_UPDATE)

@app.route('/<collection_name>', methods=['GET'])
def get_all_items(collection_name):
    """
        Documents in a collection_name.
    """
    collection = getattr(mongo.db, collection_name)
    output = []
    for q in collection.find():
        q["_id"] = str(q["_id"])
        output.append(q)
    return send(output, HTTP_SUCCESS_GET_OR_UPDATE)

@app.route('/<collection_name>/<id>', methods=['GET'])
def get_one_item(collection_name, id):
    """
        Get one item from a collection_name.
    """
    collection = getattr(mongo.db, collection_name)
    r = collection.find_one({'_id': ObjectId(id)})
    if r:
        return send(r, HTTP_SUCCESS_GET_OR_UPDATE)
    else:
        return send({'error' : 'item not found'}, HTTP_NOT_FOUND)

@app.route('/<collection_name>/<id>', methods=['PUT'])
def update_item(collection_name, id):
    """
        Update one item in collection_name.
    """
    collection = getattr(mongo.db, collection_name)
    r = collection.find_one({'_id': ObjectId(id)})
    if r:
        for key in request.json.keys():
            r[key] = request.json[key]
        try:
            collection.replace_one({"_id": ObjectId(id)}, r)
            output = {'message' : 'item updated'}
            return send(output, HTTP_SUCCESS_GET_OR_UPDATE)
        except Exception as e:
            output = {'error' : str(e)}
            return send(output, HTTP_BAD_REQUEST)
    else:
        output = {'error' : 'item not found'}
        return send(output, HTTP_NOT_FOUND)

@app.route('/<collection_name>/<id>', methods=['DELETE'])
def delete_item(collection_name, id):
    """
        Delete one item from collection_name.
    """
    collection = getattr(mongo.db, collection_name)
    r = collection.find_one({'_id': ObjectId(id)})
    if r:
        try:
            collection.remove(r["_id"])
            return send("", HTTP_SUCCESS_DELETED)
        except Exception as e:
            output = {'error' : str(e)}
            return send(output, HTTP_BAD_REQUEST)
    else:
        output = {'error' : 'item not found'}
        return send(output, HTTP_NOT_FOUND)

# Error Handler 404
@app.errorhandler(404)
def not_found(error):
    return send({'error': 'Not found'}, HTTP_NOT_FOUND)

# Error Handler 500
@app.errorhandler(500)
def internal_server_error(error):
    return send({'error': 'Internal Server Error'}, HTTP_SERVER_ERROR)

# Exception
@app.errorhandler(Exception)
def unhandled_exception(error):
    try:
        return send({'error': str(error)}, HTTP_SERVER_ERROR)
    except:
        return send({'error': "Unknown error"}, HTTP_SERVER_ERROR)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
