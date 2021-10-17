from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=False)
    is_active = db.Column(db.Boolean, default=True)
    start = db.Column(db.DateTime, nullable=False, unique=False)
    end = db.Column(db.DateTime, nullable=True, unique=False)
    interval = db.Column(db.Interval, nullable=False, unique=False)
    measure_walli = db.Column(db.Boolean, default=True)
    measure_light = db.Column(db.Boolean, default=True)
    walli_stats = db.relationship('WalliStat', backref='campaign', lazy=True)

    def __repr__(self):
        return f"Campaign(id:{self.id}, '{self.title}' is active:{self.is_active}, start:{self.start}, end:{self.end}, interval:{self.interval})"


class WalliStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, unique=True)
    Temp = db.Column(db.Float, nullable=False, unique=False)
    Power = db.Column(db.Integer, nullable=False, unique=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f"WalliStat(id:{self.id}-->campaign.id:{self.campaign_id}, {self.datetime}: {self.Temp}°C, {self.Power}W)"
