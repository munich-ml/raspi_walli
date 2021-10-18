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