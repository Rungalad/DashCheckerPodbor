#!flask/bin/python
from flask import Flask, jsonify, abort, request
from collections import OrderedDict
from reg_extractor_Lena import RegExpsLena

import os, sys
import pandas as pd
import pymorphy3

app = Flask(__name__)
# Running on http://127.0.0.1:5000

file_path = "LenaZenkoDash/n_grams.xls"

morph = pymorphy3.MorphAnalyzer()
class_ecz = RegExpsLena(morph)
key_words = class_ecz.get_regexps(file_path)

# requests.get(r"http://127.0.0.1:5000/get_filters", json={"sentence": "кандидаты из кадровых агентств с запланированными интервью"}).json()
@app.route('/get_filters', methods=['GET'])
def get_filters():
    if not request.json or 'sentence' not in request.json:
        abort(400)
    sent = request.json['sentence']
    result = class_ecz.extractNERS(sent, key_words)
    return jsonify({'output': result}), 201
    
app.run(debug=True)