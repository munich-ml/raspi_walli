# -*- coding: utf-8 -*-

import json, logging, os
import datetime as dt
import pandas as pd
from flask import Flask, render_template, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField
from wtforms.fields.html5 import IntegerField, DateField, TimeField
from wtforms.validators import DataRequired
from sensors.sensors import SensorInterface

logger = logging.getLogger(__name__)

sensor_interface = SensorInterface()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trial.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False   # https://stackoverflow.com/questions/33738467/how-do-i-know-if-i-can-disable-sqlalchemy-track-modifications
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
    lux_values = db.relationship('LuxValue', backref='campaign', lazy=True)

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


class LuxValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    lux = db.Column(db.Float)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f"LuxValue(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.lux} lux"


def commit_lux_to_db(dct):
    """
    Commits lux value (from light sensor) to the database incl. campaign_id as reference.
    input <dct> dct
        dct["lux"]: light value in lux <float>
        dct["campaign_id"]: campaign_id <int> 
    """ 
    lv = LuxValue(datetime=dt.datetime.now(), lux=dct["lux"], campaign_id=dct["campaign_id"])
    logger.info(f"Committing {lv}")
    db.session.add(lv)
    db.session.commit()


@app.route('/')
def index():
    task = {"sensor": "light",
            "func": "capture",
            "campaign_id": 42, 
            "callback": commit_lux_to_db}
    sensor_interface.do_task(task)

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
        id = request.form["id"]
        if id == "0":
            flash("Campaign(id=0) can't be modified!")

        elif request.form["todo"] == "save":
            if id == "":
                cmp = Campaign()   # create a new campaign
            else:   
                cmp = Campaign.query.get(int(id))

            # do all the modifications
            f = request.form
            cmp.is_active = "active" in f
            cmp.title = f["title"]
            cmp.start = dt.datetime.strptime(f["start_date"]+f["start_time"], "%Y-%m-%d%H:%M")
            cmp.end = dt.datetime.strptime(f["end_date"]+f["end_time"], "%Y-%m-%d%H:%M")
            cmp.interval = dt.timedelta(seconds=int(f["interval"]))
            cmp.measure_walli = "measure_walli" in f
            cmp.measure_light = "measure_light" in f

            db.session.add(cmp)
            db.session.commit()

        elif request.form["todo"] == "delete" and id != "": 
            cmp = Campaign.query.get(id)
            db.session.delete(cmp)
            db.session.commit()

        return redirect('/history/')

    else:
        logger.warning(f"Unsupported request.method '{request.method}'!")


if __name__ == "__main__":         
    app.run(debug=False)