# -*- coding: utf-8 -*-

import json, logging, math, os, pickle, threading
import pandas as pd
import numpy as np
import plotly
import plotly.express as px
import plotly.graph_objs as go  
import datetime as dt
from flask import Flask, render_template, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField
from wtforms.fields import IntegerField, DateField, TimeField
from wtforms.validators import DataRequired
from sensors.sensors import SensorInterface

# configure plotly
plotly.io.templates.default = "plotly_white" # available templates "plotly_dark" "plotly_white" 

# configure logging
logging.getLogger().setLevel(logging.NOTSET)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | %(funcName)s() %(filename)s line=%(lineno)s thread=%(thread)s | %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///walli.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False   # https://stackoverflow.com/questions/33738467/how-do-i-know-if-i-can-disable-sqlalchemy-track-modifications
db = SQLAlchemy(app)


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    previous = db.Column(db.DateTime)
    interval = db.Column(db.Interval, nullable=False)
    measure_walli = db.Column(db.Boolean, default=True)
    measure_light = db.Column(db.Boolean, default=True)
    walli_stats = db.relationship('WalliStat', backref='campaign', lazy=True, cascade="all, delete")
    lux_values = db.relationship('LuxValue', backref='campaign', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"Campaign(id:{self.id} '{self.title}' act={self.is_active} start={self.start}, end={self.end}, int={self.interval})"


class CampaignForm(FlaskForm):
    id = IntegerField(render_kw={'readonly': True})
    title = TextAreaField(validators=[DataRequired()])
    active = BooleanField(default=True)
    start_date = DateField(format="%Y-%m-%d", validators=[DataRequired()], default=lambda: dt.datetime.now().date())
    start_time = TimeField(format="%H:%M", validators=[DataRequired()], default=lambda: dt.datetime.now().time())
    end_date = DateField(format="%Y-%m-%d", validators=[DataRequired()], default=lambda: dt.datetime.now().date())
    end_time = TimeField(format="%H:%M", validators=[DataRequired()], default=lambda: dt.datetime.now().time())
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
        self.interval.data = int(cpn.interval / dt.timedelta(seconds=1))
        self.measure_walli.data = cpn.measure_walli
        self.measure_light.data = cpn.measure_light
        

class WalliStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    charging_state = db.Column(db.Integer) 
    I_L1 = db.Column(db.Float)
    I_L2 = db.Column(db.Float)
    I_L3 = db.Column(db.Float)
    temperature = db.Column(db.Float)
    V_L1 = db.Column(db.Integer)
    V_L2 = db.Column(db.Integer)
    V_L3 = db.Column(db.Integer)
    extern_lock_state = db.Column(db.Integer)
    power_kW = db.Column(db.Float)
    energy_pwr_on = db.Column(db.Float)
    energy_kWh = db.Column(db.Float)
    I_max_cfg = db.Column(db.Integer)
    I_min_cfg = db.Column(db.Integer)
    modbus_watchdog_timeout = db.Column(db.Integer)
    remote_lock = db.Column(db.Integer)
    I_max_cmd = db.Column(db.Float)
    I_fail_safe = db.Column(db.Float)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    
    def __repr__(self):
        return f"WalliStat(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.temperature}°C, {self.power_kW}kW)"

    @classmethod
    def from_series(cls, series):
        """ Creates a WalliStat from a Pandas Series """
        try:
            ws = cls(datetime = series.datetime,
                    charging_state = int(series.charge_state), 
                    I_L1 = series.I_L1 / 10.,
                    I_L2 = series.I_L2 / 10.,
                    I_L3 = series.I_L3 / 10.,
                    temperature = series.Temp / 10.,
                    V_L1 = int(series.V_L1),
                    V_L2 = int(series.V_L2),
                    V_L3 = int(series.V_L3),
                    extern_lock_state = int(series.ext_lock),
                    power_kW = series.P / 1000.,
                    energy_pwr_on = ((int(series.E_cyc_hb) << 16) + series.E_cyc_lb) / 1000.,
                    energy_kWh = ((int(series.E_hb) << 16) + series.E_lb) / 1000.,
                    I_max_cfg = int(series.I_max),
                    I_min_cfg = int(series.I_max),
                    modbus_watchdog_timeout = int(series.watchdog),
                    remote_lock = int(series.remote_lock),
                    I_max_cmd = series.max_I_cmd / 10.,
                    I_fail_safe = series.FailSafe_I / 10., 
                    campaign_id = int(series.campaign_id))
            return ws
        
        except Exception as e:
            print("Exception:", e, series.datetime)
            return cls(datetime = series.datetime)

    @classmethod
    def commit(cls, dct):
        """
        Commits walli status (from the wallbox) to the database incl. campaign_id as reference.
        """
        ws = cls.from_series(pd.Series(dct))
        # Commit new data-point to the (global) database 
        logger.debug(f"Committing {ws}")
        db.session.add(ws)   
        db.session.commit()    
        
    def to_series(self):
        """ Converts a WalliStat object into a Pandas Series """
        keys = ["id", "datetime", "charging_state", "I_L1", "I_L2", "I_L3", "temperature", "V_L1", "V_L2", "V_L3", 
                "extern_lock_state", "power_kW", "energy_pwr_on", "energy_kWh", "I_max_cfg", "I_min_cfg", 
                "modbus_watchdog_timeout", "remote_lock", "I_max_cmd", "I_fail_safe", "campaign_id"]       
        return pd.Series({key: getattr(self, key) for key in keys})
     
    @staticmethod
    def to_dataframe(list_of_wallistat):
        """ Converts a list of WalliStat objects into a Pandas DataFrame """
        return pd.concat([WalliStat.to_series(ws) for ws in list_of_wallistat], axis=1).T.set_index("id")
        

class LuxValue(db.Model):
    """Database Model class for storing light sensor data"""
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    lux = db.Column(db.Float)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f"LuxValue(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.lux} lux)"

    def to_dict(self):
        return {'datetime': self.datetime,
                "lux": self.lux}
        

    @classmethod
    def commit(cls, dct):
        """
        Commits lux value (from light sensor) to the database incl. campaign_id as reference.
        input <dct> dct
            dct["lux"]: light value in lux <float>
            dct["campaign_id"]: campaign_id <int> 
        """ 
        # Create a new data-point of this class. Assuming the data-point was captured right now.
        ndp = cls(datetime=dt.datetime.now())
        
        # Populate the new data-point with all common attributes of the class and the input dictionary.
        common_keys = set(dir(cls)).intersection(set(dct.keys()))
        for key in common_keys:
            setattr(ndp, key, dct[key])
        
        # Commit new data-point to the (global) database 
        logger.debug(f"Committing {ndp}")
        db.session.add(ndp)   
        db.session.commit()


class CaptureTimer():
    """Class to scheduling sensor captures based on campaigns within the Campaign database"""
    def __init__(self, sensor_interface):
        self.sensor_interface = sensor_interface
        self.timer = threading.Timer(interval=0, function=lambda: logger.error("no Timer defined, yet"))
        self.update_timer()  # initial capturing kick-off
        
    @staticmethod
    def _get_next_capture(campaigns=None):
        """
        Computes which campaign out of a list of campaigns is due to capture next.
        
        Returns <tuple> of for the next capture, with two items:
            time <float> in seconds to sleep until this capture
            campaign <Campaign> of the next captur

        Args:
            campaigns <list>: List of campaigns <Campaign>
                if campaigns is None, a Campaign.query is conducted
        """
        pending = {}   # pending captures with sleeptime <float> as keys and <Campaign> values
        now = dt.datetime.now()
        
        if campaigns is None:
            campaigns = db.session.query(Campaign).filter(Campaign.is_active==True).filter(Campaign.end > now).all()
            
        for cmp in campaigns:
            if now > cmp.start:  # Overdue detection for immidiate capture
                if cmp.previous is None:   # Case 1: First capture of a campaign is overdue
                    return 0, cmp  
                else:
                    next = cmp.previous + cmp.interval
                    if now >= next:   # Case 2: A regular captuire within a campaign is overdue
                        return 0, cmp
                
            if now <= cmp.start:   # Case 3: Wait for first capture in the future
                seconds_until_capture = (cmp.start - now) / dt.timedelta(seconds=1.0)
            else:   # Case 4: Ongoing campaign
                # Round to the next complete interval. This avoids drifting over time
                next_capture = cmp.start + math.ceil((now - cmp.start) / cmp.interval) * cmp.interval 
                seconds_until_capture = (next_capture - now) / dt.timedelta(seconds=1.0)
            pending[seconds_until_capture] = cmp
                
        min_seconds, next_cmp = sorted(pending.items())[0]
        return min_seconds, next_cmp
    
    
    def update_timer(self):
        """
        Schedules a timer to exetue the next due capture.
        Cancels an ongoing timer, if there is one.
        """
        self.timer.cancel()  # cancal current timer
        t, campaign = self._get_next_capture()
        logger.debug(f"Scheduling a Timer in {t=:.1f}s for {campaign}")
        self.timer = threading.Timer(interval=t, function=self.capture, kwargs={"campaign":campaign})
        self.timer.start()
    
           
    def capture(self, campaign):
        """
        Generates capture tasks for the campaign and sends them to the appropriate sensors 
        Args: 
            campaign (Campaign): Campain which to capture
        """
        logger.debug(campaign)
        # send task(s) to the sensor_interface for capturing                
        for flag, sensor, callback in zip([campaign.measure_light, campaign.measure_walli],
                                          ["light",                "walli"               ],
                                          [LuxValue.commit,        WalliStat.commit      ]):
            if flag:
                task = {"func": "capture", 
                        "campaign_id": campaign.id,
                        "sensor": sensor,
                        "callback": callback}
                self.sensor_interface.do_task(task)
            
        # set campaign.previous to now
        now = dt.datetime.now()
        db.session.query(Campaign).filter(Campaign.id==campaign.id).update({"previous": now})
        db.session.commit()
        
        # update capture_timer
        self.update_timer()
      
    
@app.route('/')
@app.route('/home/')
@app.route('/home/<year>/')
def home(year=None):
    """ View function for home page 
    
    Args:
        year <int>: Year of which statistics are shown on the home page.
    """ 
    def calc_walli_stats(year):
        UNUSED = ['I_L1', 'I_L2', 'I_L3', 'V_L1', 'V_L2', 'V_L3', 'extern_lock_state', 'charging_state', 
                'energy_pwr_on', 'I_max_cfg', 'I_min_cfg', 'modbus_watchdog_timeout', 'power_kW', 
                'remote_lock', 'I_max_cmd', 'I_fail_safe', 'campaign_id']
        ws_list = db.session.query(WalliStat).filter(WalliStat.campaign_id==0,
                                                     WalliStat.datetime>=dt.date(int(year),1,1),
                                                     WalliStat.datetime< dt.date(int(year),12,31)).all()
        df = WalliStat.to_dataframe(ws_list).drop(UNUSED, axis=1).set_index("datetime") 
        df["charged_kWh"] = df["energy_kWh"].diff()
        df["date"] = [idx.date() for idx in df.index]
        df["weekday"] = [idx.day_of_week for idx in df.index]
        df["week"] = [idx.weekofyear for idx in df.index]

        zeros = pd.DataFrame(columns=np.arange(1, 53, dtype=int), data=np.zeros(shape=(7, 52)))
        wks = df.pivot_table(index="weekday", columns="week", values="charged_kWh", aggfunc="sum") + zeros

        temps = df[["temperature", "date"]].groupby(by="date").agg(["max", "mean", "min"])
        temps.columns = [f"temperature {c}" for c in temps.columns.droplevel()]

        kwh = df[["date", "charged_kWh"]].groupby("date").agg("sum")
        kwh["rolling_mean"] = kwh["charged_kWh"].rolling(10, win_type="triang", center=True).mean()
        kwh["mean"] = [kwh.charged_kWh.mean()] * kwh.shape[0]
        
        return kwh, wks, temps
    
    def generate_plotly_fig(df, **kwargs):
        """ Generate the plotly figure """
        fig = go.Figure()
        for col in df.columns:
            scatter_kwargs = dict(mode="lines")  # scatter defaults
            if "scatter" in kwargs:
                if col in kwargs["scatter"]:
                    scatter_kwargs.update(kwargs["scatter"][col])
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, **scatter_kwargs))
        
        # Layout modifications
        layout_kwargs = dict(width=800, height=190, margin=dict(l=0, r=0, b=10, t=15)) # defaults
        if "layout" in kwargs:
            layout_kwargs.update(kwargs["layout"])    
        fig.update_layout(**layout_kwargs)      
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def generate_plotly_weekly(df):
        """ Generate the plotly image of daily/weekly charged_kWh """
        fig = px.imshow(df, labels=dict(color="charged_kWh"), color_continuous_scale='Greens')
        fig.update_layout(width=800, height=180, 
                        margin=dict(l=0, r=0, b=0, t=0),
                        xaxis={"title": "calender week"},
                        yaxis={"tickmode": 'array',
                                "tickvals": [ 0,    1,    2,    3,    4,    5,    6  ],
                                "ticktext": ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']})
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def generate_fresh_plots(year):
        logger.info(f"generating fresh plots for {year}")
        kwh, wks, tmp = calc_walli_stats(year)
        plots = {"wks_json": generate_plotly_weekly(wks),
                "kwh_json": generate_plotly_fig(kwh, layout={"yaxis":{"title":"[kWh]"}},
                                                scatter={"charged_kWh": {"mode":"markers"}}),
                "tmp_json": generate_plotly_fig(tmp, layout={"yaxis":{"title":"Temp [°C]"}})}
        return plots
    
    def load_cached_plots(fn):
        logger.info(f"Loading cached plots '{fn}'")
        with open(os.path.join("cache", fn), "rb") as file:
            plots = pickle.load(file)  
        return plots      
    
    def store_cached_plots(plots, fn):
        logger.info(f"Storing cached plots to '{fn}'")
        with open(os.path.join("cache", fn), "wb") as file:
            pickle.dump(plots, file)
    
    def remove_expired_caches():
        """ 
        Removes expired 'home-plotly-cache.pkl' files from the 'cache' directory.
        A .pkl file is expired if a later .pkl file exsists from the same year.
        """
        caches = dict()
        for fn in os.listdir("cache"):
            if fn.endswith('home-plotly-cache.pkl'):
                year = fn[:4]
                if year in caches.keys():
                    caches[year].append(fn)
                else:
                    caches[year] = [fn]
        latest = [sorted(fns)[-1] for fns in caches.values()]
        expired = set(os.listdir("cache")).difference(set(latest))
        for fn in expired:
            os.remove(os.path.join("cache", fn))
            
    today = dt.datetime.now().date()  #.strftime("%Y-%m-%d")
    
    # create a dictionary 'cached_plots' with items like ('2021': '2021-12-01_home-plotly-cache.json')
    cached_plots = dict()
    for fn in os.listdir("cache"):
        if fn.endswith('home-plotly-cache.pkl'):
            cached_plots[fn[:4]] = fn
    logger.info(f"cached_plots: {cached_plots}")
        
    # allow evalutaion for all years in 'available'
    first_year_of_logging = 2021
    available = [str(y) for y in range(first_year_of_logging, today.year+1)]
    
    # error checking of user input of year
    default_year = str(dt.date.today().year)
    year = str(year)
    if year is None:
        year = default_year
    elif year.isdecimal():
        if year not in available:
            year = default_year
    else:
        year = default_year    

    # use cached plots data or generate fresh plots    
    if year == default_year:
        desired_fn = today.strftime("%Y-%m-%d") + "_home-plotly-cache.pkl"  # cache of today?
    else:
        desired_fn = year + "-12-31" + "_home-plotly-cache.pkl"  # create cache with all the data of a year

    if year in cached_plots.keys():
        if desired_fn == cached_plots[year]:
            plots = load_cached_plots(cached_plots[year])
    
    if "plots" not in dir():
        plots = generate_fresh_plots(year)
        
        # Store new cache and remove expired caches after serving the client 
        threading.Timer(interval=1., function=store_cached_plots, args=(plots, desired_fn)).start()
        threading.Timer(interval=2., function=remove_expired_caches).start()
            
    return render_template('home.html', plots=plots, year=year, avail=sorted(available))


@app.route('/config/')
def config():
    """ View function for config page """
    # load register table from .json file and create a pandas DataFrame from it
    p = os.path.join("..", "modbus", "docs", "HeidelbergWallboxEnergyControl_ModbusRegisterTable.json")
    with open(p, "r") as file:
        regs = json.load(file)

    df = pd.DataFrame(columns=regs["columns"], data=regs["data"])
    desired_cols = ['Adr', 'R/W', 'Description', 'Range', 'Values / examples']
    df = df[desired_cols]

    return render_template('config.html', columns=df.columns, data=list(df.values.tolist()))


@app.route('/campaigns/')
def campaigns():
    """ View function for campaigns page """
    campaigns = db.session.query(Campaign).all()
    return render_template('campaigns.html', campaigns=campaigns)


@app.route('/campaigns/edit/', methods=['GET', 'POST'], defaults={"id": None})
@app.route('/campaigns/edit/<id>/', methods=['GET', 'POST'])
def edit(id=None):   
    """ View function for campaigns edit page """
    if request.method == "GET": 
        form = CampaignForm()    
        if id is not None:
            cmp = db.session.query(Campaign).get(id)
            print("campaigns.GET", cmp)
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
                cmp = db.session.query(Campaign).get(int(id))

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
            capture_timer.update_timer()  # necessary, because a the new or modified campaign could be next to capture.   

        elif request.form["todo"] == "delete" and id != "": 
            cmp = db.session.query(Campaign).get(id)
            logger.debug(f"{id=}, {request.method=}, {cmp=}")
            db.session.delete(cmp)
            db.session.commit()
            capture_timer.update_timer()  # necessary, because the deleted campaign could be scheduled for next capture.

        return redirect('/campaigns/')

    else:
        logger.warning(f"Unsupported '{request.method=}'!")


@app.route('/data/', methods=['GET'], defaults={"campaign_id": 0})
@app.route('/data/<campaign_id>/', methods=['GET'])
def data(campaign_id=0):
    """ View function for data page """
    return render_template('data.html', campaign_id=campaign_id)


@app.route('/api/data/light/<campaign_id>/', methods=['GET'])
def api_get_light_data(campaign_id):
    """provides sensor data for ajax DataTable"""
    query = db.session.query(LuxValue).filter(LuxValue.campaign_id==campaign_id)
    return {'data': [item.to_dict() for item in query]}


    

if __name__ == "__main__":    
    sensor_interface = SensorInterface()     
    capture_timer = CaptureTimer(sensor_interface)
    app.run(host="0.0.0.0", port=5000, debug=False)