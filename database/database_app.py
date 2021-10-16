from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class WalliStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, unique=True)
    Temp = db.Column(db.Float, nullable=False, unique=False)
    Power = db.Column(db.Integer, nullable=False, unique=False)
    
    def __repr__(self):
        return f"WalliStat(id:{self.id}, {self.datetime}: {self.Temp}°C, {self.Power}W)"

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False, unique=False)
    end = db.Column(db.DateTime, nullable=True, unique=False)
    interval = db.Column(db.Interval, nullable=False, unique=False)

    def __repr__(self):
        return f"Campaign(id:{self.id}, start={self.start}, end={self.end}, interval={self.interval}"
