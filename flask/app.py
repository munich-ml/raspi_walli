# -*- coding: utf-8 -*-


import os, json
import re
from matplotlib.pyplot import title
from numpy import tile
import datetime as dt
import pandas as pd
from flask import Flask, render_template, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextField, TextAreaField, BooleanField
from wtforms.fields.html5 import IntegerField, DateField, TimeField
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


class CampaignForm(FlaskForm):
    id = IntegerField(render_kw={'readonly': True})
    title = TextAreaField(validators=[DataRequired()])
    active = BooleanField(default=True)
    start_date = DateField(format="%Y-%m-%d", validators=[DataRequired()], default=dt.datetime.now().date())
    start_time = TimeField(format="%H:%M", validators=[DataRequired()], default=dt.datetime.now().time())
    end_date = DateField(format="%Y-%m-%d", validators=[DataRequired()], default=dt.datetime.now().date())
    end_time = TimeField(format="%H:%M", validators=[DataRequired()], default=dt.datetime.now().time())
    interval = IntegerField(validators=[DataRequired()], default=3600)
    measure_walli = BooleanField(default=True)
    measure_light = BooleanField(default=True)
        
    def populate(self, cpn):
        self.id.data = cpn.id
        self.title.data = cpn.title
        self.active.data = cpn.is_active
        self.start_date.data = cpn.start.date()
        self.start_time.data = cpn.start.time()
        self.end_date.data = cpn.end.date()
        self.end_time.data = cpn.end.time()
        self.measure_walli.data = cpn.measure_walli
        self.measure_light.data = cpn.measure_light
        

class WalliStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    Temp = db.Column(db.Float)
    Power = db.Column(db.Integer)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f"WalliStat(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.Temp}°C, {self.Power}W)"


@app.route('/', methods=['GET'])
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
    if request.method == "GET": 
        form = CampaignForm()    
        if id is not None:
            cmp = Campaign.query.get(id)
            form.populate(cmp)
        return render_template('edit.html', form=form)    
    
    elif request.method == "POST":    
        print("### edit POST ###")
        print("method:", request.method, ", todo:", request.form["todo"])
        for key, value in request.form.items():
            print("-", key, value, type(value))

        if request.form["todo"] == "save":
            f = request.form
            if f["id"] == "":  # create a mew campaign
                cmp = Campaign(title = f["title"], 
                            is_active = "active" in f,
                            start = dt.datetime.strptime(f["start_date"]+f["start_time"], "%Y-%m-%d%H:%M"),
                            end = dt.datetime.strptime(f["end_date"]+f["end_time"], "%Y-%m-%d%H:%M"),
                            interval = dt.timedelta(seconds=int(f["interval"])),
                            measure_walli = "measure_walli" in f,
                            measure_light = "measure_light" in f)
                db.session.add(cmp)
                db.session.commit()
            else:
                print("to do: Modify campaign")
        
        elif request.form["todo"] == "delete":
            id = request.form["id"]
            if id == "":
                pass  # in case of a new campaign, there is no id, yet
            elif id == "0":
                flash("id=0 can't be deleted!")
            else: 
                cmp = Campaign.query.get(id)
                db.session.delete(cmp)
                db.session.commit()

        return redirect('/history/')

    else:
        print(f"Warning: Unsupported request.method '{request.method}'!")



if __name__ == "__main__":
    app.run(debug=True)