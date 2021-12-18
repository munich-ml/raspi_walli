import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
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
    charging_state = db.Column(db.Integer) 
    I_L1 = db.Column(db.Float)
    I_L2 = db.Column(db.Float)
    I_L3 = db.Column(db.Float)
    temperature = db.Column(db.Float)
    V_L1 = db.Column(db.Integer)
    V_L2 = db.Column(db.Integer)
    V_L3 = db.Column(db.Integer)
    extern_lock_state = db.Column(db.Integer)
    power = db.Column(db.Integer)
    energy_pwr_on = db.Column(db.Integer)
    energy_total = db.Column(db.Integer)
    I_max_cfg = db.Column(db.Integer)
    I_min_cfg = db.Column(db.Integer)
    modbus_watchdog_timeout = db.Column(db.Integer)
    remote_lock = db.Column(db.Integer)
    I_max_cmd = db.Column(db.Integer)
    I_fail_safe = db.Column(db.Integer)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    
    def __repr__(self):
        return f"WalliStat(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.temperature}°C, {self.power}W)"

    @classmethod
    def from_series(cls, series):
        """ Creates a WalliStat from a Pandas Series """
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
                 power = int(series.P),
                 energy_pwr_on = int((series.E_cyc_hb << 16) + series.E_cyc_lb),
                 energy_total = int((series.E_hb << 16) + series.E_lb),
                 I_max_cfg = int(series.I_max),
                 I_min_cfg = int(series.I_max),
                 modbus_watchdog_timeout = int(series.watchdog),
                 remote_lock = int(series.remote_lock),
                 I_max_cmd = int(series.max_I_cmd),
                 I_fail_safe = int(series.FailSafe_I), 
                 campaign_id = int(series.campaign_id))
        return ws
    
    
    @staticmethod
    def to_series(ws):
        """ Converts a WalliStat object into a Pandas Series """
        keys = ["id", "datetime", "charging_state", "I_L1", "I_L2", "I_L3", "temperature", "V_L1", "V_L2", "V_L3", 
                "extern_lock_state", "power", "energy_pwr_on", "energy_total", "I_max_cfg", "I_min_cfg", 
                "modbus_watchdog_timeout", "remote_lock", "I_max_cmd", "I_fail_safe", "campaign_id"]       
        return pd.Series({key: getattr(ws, key) for key in keys})
    
    
    @staticmethod
    def to_dataframe(list_of_wallistat):
        """ Converts a list of WalliStat objects into a Pandas DataFrame """
        return pd.concat([WalliStat.to_series(ws) for ws in list_of_wallistat], axis=1).T