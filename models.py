from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active') # active, finished
    carryover_pool = db.Column(db.Float, default=0.0)
    starting_money = db.Column(db.Float, default=1000.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teams = db.relationship('Team', backref='game', lazy=True)
    rounds = db.relationship('Round', backref='game', lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    money = db.Column(db.Float, nullable=False)
    bets = db.relationship('Bet', backref='team', lazy=True)

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    correct_option = db.Column(db.Integer, nullable=True) # 1-5
    opt1 = db.Column(db.String(200))
    opt2 = db.Column(db.String(200))
    opt3 = db.Column(db.String(200))
    opt4 = db.Column(db.String(200))
    opt5 = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bets = db.relationship('Bet', backref='round', lazy=True)

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    option_chosen = db.Column(db.Integer, nullable=False) # 1-5
    is_all_in = db.Column(db.Boolean, default=False)
