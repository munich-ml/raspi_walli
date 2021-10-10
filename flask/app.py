# -*- coding: utf-8 -*-


import os, json
import pandas as pd
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
    p = os.path.join("..", "modbus", "docs", "HeidelbergWallboxEnergyControl_ModbusRegisterTable.json")
    with open(p, "r") as file:
        regs = json.load(file)

    df = pd.DataFrame(columns=regs["columns"], data=regs["data"])
    desired_cols = ['Bus-Adr.', 'R/W', 'Description', 'Range', 'Values / examples']
    df = df[desired_cols]

    return render_template('config.html', column_names=df.columns.values, row_data=list(df.values.tolist()), zip=zip)

