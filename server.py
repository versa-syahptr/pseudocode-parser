import os
from pprint import pprint
import sys

import requests
from flask import Flask, render_template, request
from algo2go import Algorithm, auto_compile, Golang

app = Flask("algo2go", static_folder="frontend", static_url_path='', template_folder="frontend")


@app.route("/")
def root():
    if os.environ.get("env") == "prod":
        return
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
    pprint(request.json)
    r = requests.post(url, json=request.json)
    res = r.text
    pprint(res)
    return res


@app.route("/auto", methods=['POST'])
def auto():
    raw = request.form["algo"]
    success = False
    res, fname = "", ""
    try:
        res = auto_compile(str(raw))
        success = True
        if isinstance(res, Golang):
            fname = res.filename

    except Exception as e:
        res = f"{e.__class__.__name__}: {e}"

    return {
        "success": success,
        "res": res,
        "filename": fname
    }


if __name__ == '__main__':
    app.run(debug=True)
