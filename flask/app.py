# -*- coding: utf-8 -*-


import os, json
from numpy import tile
import datetime as dt
import pandas as pd
from flask import Flask, render_template, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextField, TextAreaField
from wtforms.fields.html5 import DateField, DateTimeField, TimeField
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
    title = TextAreaField(validators=[DataRequired()])
    start_date = DateField(format="%Y-%m-%d", validators=[DataRequired()], default=dt.datetime.now().date())
    start_time = TimeField(format="%H:%M", validators=[DataRequired()], default=dt.datetime.now().time())
    end_date = DateField(format="%Y-%m-%d", validators=[DataRequired()], default=dt.datetime.now().date())
    end_time = TimeField(format="%H:%M", validators=[DataRequired()], default=dt.datetime.now().time())

    def populate(self, cpn):
        self.title.data = cpn.title
        self.start_date.data = cpn.start.date()
        self.start_time.data = cpn.start.time()
        self.end_date.data = cpn.end.date()
        self.end_time.data = cpn.end.time()


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


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


@app.route('/history/')
def history():
    campaigns = Campaign.query.all()
    return render_template('history.html', campaigns=campaigns)


@app.route('/history/edit/', methods=['GET', 'POST'], defaults={"id": None})
@app.route('/history/edit/<id>/', methods=['GET', 'POST'])
def edit(id=None):
    form = CampaignForm()    
    if form.validate_on_submit():    
        print("in modify, method=", request.method)
        for key, value in request.form.items():
            print(key, value, type(value))

        return redirect('/history/')

    if id is not None:
        cpn = Campaign.query.get(id)
        form.populate(cpn)

    return render_template('edit.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)