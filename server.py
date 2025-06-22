#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of algo2go.
# Copyright (C) 2022 Versa Syahputra

import os
from pprint import pprint
import sys
import requests
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()

from algo2go import Algorithm, auto_compile, Golang

app = Flask("algo2go", static_folder="frontend", static_url_path='', template_folder="frontend")

DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class History(db.Model):
    __tablename__ = 'algo2go_history'
    id = db.Column(db.Integer, primary_key=True)
    algoritma = db.Column(db.Text, nullable=False)
    golang = db.Column(db.Text, nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<History {self.id} - {self.created_at}>"


@app.route("/")
def root():
    if os.environ.get("env") == "prod":
        return ""
    else:
        return render_template("index.html")


@app.route("/api.php", methods=['POST'])
def parse():
    raw = request.form["algo"]
    print(raw)
    algo = Algorithm.fullparse(raw)
    return Golang(algo)


@app.route("/pass.php", methods=['POST'])
def passer():
    url = "https://onecompiler.com/api/code/exec"
    r = requests.post(url, json=request.json)
    res = r.text
    return res


@app.route("/auto", methods=['POST'])
def auto():
    raw = request.form["algo"]
    success, runnable = False, False
    res, fname = "", ""
    try:
        res = auto_compile(str(raw))
        success = True
        if isinstance(res, Golang):
            fname = res.filename
            runnable = True

    except Exception as e:
        res = f"{e.__class__.__name__}: {e}"
    
    # Save to history
    try:
        history = History(algoritma=raw, golang=res if runnable else None, error=None if success else res) # type: ignore
        db.session.add(history)
        db.session.commit()
    
    # skip if database is not available
    except Exception as e:
        print(f"Failed to save history: {e}", file=sys.stderr)

    return {
        "success": success,
        "res": res,
        "filename": fname,
        "runnable": runnable,
    }

@app.route("/history", methods=['GET'])
def history():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    histories = History.query.order_by(History.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    # return render_template("history.html", histories=histories)
    return {
        "histories": [
            {
                "id": h.id,
                "algoritma": h.algoritma,
                "golang": h.golang,
                "error": h.error,
                "created_at": h.created_at.isoformat()
            } for h in histories.items
        ],
        "total": histories.total,
        "pages": histories.pages,
        "page": page
    }



if __name__ == '__main__':
    if os.environ.get("env") == "prod":
        from gunicorn.app.wsgiapp import run
        sys.argv = ['gunicorn', 'server:app', '--bind', '0.0.0.0:5000']
        run()
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)
