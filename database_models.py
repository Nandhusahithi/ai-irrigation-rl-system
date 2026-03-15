from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    farm_location = db.Column(db.String(200), nullable=True)
    farm_size = db.Column(db.Float, nullable=True) # in acres or hectares
    preferred_crops = db.Column(db.String(200), nullable=True) # comma separated list
    
    # Relationships
    history = db.relationship('FarmHistory', backref='farmer', lazy=True)

class FarmHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Inputs
    crop_type = db.Column(db.String(50), nullable=False)
    soil_moisture = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    rainfall_level = db.Column(db.Float, nullable=False)
    weather_type = db.Column(db.String(50), nullable=False)
    
    # Outputs/Recommendations
    irrigation_decision = db.Column(db.String(50), nullable=False) # 'Irrigate' or 'Do not irrigate'
    water_amount = db.Column(db.Float, nullable=True) # Recommended water amount
    reward = db.Column(db.Float, nullable=True) # RL reward obtained for this state-action
