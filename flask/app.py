# -*- coding: utf-8 -*-


from flask import Flask, render_template, flash, redirect, url_for, request, send_from_directory, session

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history/')
def history():
    return render_template('history.html')

@app.route('/config/')
def config():
    return render_template('config.html')

