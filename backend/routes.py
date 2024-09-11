from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))


# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def health():
    return {"status":"OK"}, 200


@app.route("/count", methods=["GET"])
def count():
    """return length of data"""
    if songs_list:
        return jsonify(length=len(songs_list)), 200

    return {"message": "Internal server error"}, 500

######################################################################
# GET ALL SONGS
######################################################################
def format_song(song):
    """Convert ObjectId to string in each song document."""
    song['_id'] = str(song['_id'])
    return song

@app.route("/song", methods=["GET"])
def get_song():
    """return data"""

    all_songs = db.songs.find({})
    
    # Convert cursor to a list and format the response
    song_list = [format_song(song) for song in all_songs]
    #song_list = dumps(all_songs)
    
    if song_list:
        return jsonify({"songs": song_list}), 200

    return {"message": "Internal server error"}, 500

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """return data"""

    all_songs = db.songs.find({})
    
    # Convert cursor to a list and format the response
    song_list = [format_song(song) for song in all_songs]
    #song_list = dumps(all_songs)
    
    for song in song_list:
        if song["id"] == id:
            return jsonify(song), 200

    return {"message": "song with id not found!"}, 404

######################################################################
# CREATE A SONG
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    # Extract new song data from the request body
    new_song = request.get_json()

    # Fetch all songs from the database
    all_songs = db.songs.find({})
    
    # Convert the cursor to a list and format the response
    song_list = [format_song(song) for song in all_songs]

    # Verify if the ID already exists
    for song in song_list:
        if str(song["id"]) == str(new_song["id"]):
            return {"message": f"Song with id {song['id']} already present"}, 302

    # Insert the new song into the database
    try:
        db.songs.insert_one(new_song)
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500

    # Return success response
    return jsonify({"message": f"Inserted song with id {new_song['id']}"}), 201


######################################################################
# UPDATE A SONG
######################################################################
@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    updated_song = request.get_json()
    

    # Fetch all songs from the database
    all_songs = db.songs.find({})
    
    # Convert the cursor to a list and format the response
    song_list = [format_song(song) for song in all_songs]

    # Find the song by ID
    for song in song_list:
        if song["id"] == id:          
            if song["lyrics"] == updated_song["lyrics"]:
                return jsonify({"message": "song found, but nothing updated"}), 200
            try:
                # Update the song with the incoming data
                db.songs.update_one(
                    {"id": id},
                    {"$set": updated_song}
                )
                return jsonify({"message": f"Song with id {id} updated successfully"}), 200
            except Exception as e:
                return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    
    # If song is not found
    return jsonify({"message": "Song not found"}), 404

######################################################################
# DELETE A SONG
######################################################################
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    # Find the song by ID
    
    # Fetch all songs from the database
    all_songs = db.songs.find({})
    
    # Convert the cursor to a list and format the response
    song_list = [format_song(song) for song in all_songs]

    # Find the song by ID
    for song in song_list:
        if song["id"] == id:
            # Delete the picture
            db.songs.delete_one({"id": id})
            return '', 204
    
    # If picture is not found
    return jsonify({"message": "Song not found"}), 404