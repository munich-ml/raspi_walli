# -*- coding: utf-8 -*-


import os, json
from numpy import tile
import datetime as dt
import pandas as pd
from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trial.db'
db = SQLAlchemy(app)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime)
    interval = db.Column(db.Interval, nullable=False)
    measure_walli = db.Column(db.Boolean, default=True)
    measure_light = db.Column(db.Boolean, default=True)
    walli_stats = db.relationship('WalliStat', backref='campaign', lazy=True)

    def __repr__(self):
        return f"Campaign(id:{self.id}, '{self.title}' is active:{self.is_active}, start:{self.start}, end:{self.end}, interval:{self.interval})"


class WalliStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    Temp = db.Column(db.Float)
    Power = db.Column(db.Integer)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f"WalliStat(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.Temp}°C, {self.Power}W)"


class CampaignForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    start_date = DateField("Start date", format="%Y-%m-%d", validators=[DataRequired()])

    def pre_populate(self):
        self.title.data = "Esmiralda"
        self.start_date.data = dt.datetime.today().date()


@app.route('/', methods=['GET', 'POST'])
def index():
    print("at home")
    return render_template('index.html')


@app.route('/history/')
def history():
    campaigns = Campaign.query.all()
    for campaign in campaigns:
        print(campaign)

    return render_template('history.html', campaigns=campaigns)


@app.route('/config/')
def config():
    # load register table from .json file and create a pandas DataFrame from it
    p = os.path.join("..", "modbus", "docs", "HeidelbergWallboxEnergyControl_ModbusRegisterTable.json")
    with open(p, "r") as file:
        regs = json.load(file)

    df = pd.DataFrame(columns=regs["columns"], data=regs["data"])
    desired_cols = ['Bus-Adr.', 'R/W', 'Description', 'Range', 'Values / examples']
    df = df[desired_cols]

    return render_template('config.html', columns=df.columns, data=list(df.values.tolist()))


@app.route('/modify_campaign/', methods=['GET', 'POST'])
def modify_campaign():
    if request.method == "GET":
        form=CampaignForm()
        form.pre_populate()
        return render_template('modify_campaign.html', form=form)
    
    print("in modify, method=", request.method)
    for key, value in request.form.items():
        print(key, value, type(value))

    return redirect('/')