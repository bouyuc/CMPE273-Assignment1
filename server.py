import os
import sys
from flask import Flask, request
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import StringIO
import contextlib

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = set(['py'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
client = MongoClient("localhost:27017")
db = client.test

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/v1/scripts', methods = ['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'data' not in request.files:
            print('No file part')
            return 'No file part'
        file = request.files['data']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            result = db.test.insert_one(
                {
                    "location" : filename
                }
            )

            scriptId = "201 Created\n{\n    \"script-id\":" + ' "' + str(result.inserted_id) + '"' + "\n}"

            return(scriptId)
    return ''

@app.route('/api/v1/scripts/<id>', methods = ['GET'])
def invoke_file(id):
    # Using code found from https://stackoverflow.com/questions/3906232/python-get-the-print-output-in-an-exec-statement
    with stdoutIO() as s:
        try:
            exec(open(str(db.test.find_one({'_id': ObjectId(id) })['location'])).read())
        except:
            print("Something wrong with the code")
    return "200 OK\n" + s.getvalue()

if __name__ == '__main__':
     app.run(port='8000')
