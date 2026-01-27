from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Game, Team, Round, Bet
import logic

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///betting_game_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    games = Game.query.all()
    return render_template('index.html', games=games)

@app.route('/create_game', methods=['POST'])
def create_game():
    name = request.form.get('name')
    starting_money = request.form.get('starting_money', type=float, default=1000.0)
    if name:
        new_game = Game(name=name, status='active', carryover_pool=0, starting_money=starting_money)
        db.session.add(new_game)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/game/<int:game_id>')
def game_dashboard(game_id):
    game = Game.query.get_or_404(game_id)
    teams = Team.query.filter_by(game_id=game_id).all()
    return render_template('game_dashboard.html', game=game, teams=teams)

@app.route('/game/<int:game_id>/add_team', methods=['POST'])
def add_team(game_id):
    name = request.form.get('name')
    game = Game.query.get_or_404(game_id)
    if name:
        new_team = Team(game_id=game_id, name=name, money=game.starting_money)
        db.session.add(new_team)
        db.session.commit()
    return redirect(url_for('game_dashboard', game_id=game_id))

@app.route('/game/<int:game_id>/round/setup')
def setup_round(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template('round_setup.html', game=game)

@app.route('/game/<int:game_id>/round/start', methods=['POST'])
def start_round(game_id):
    game = Game.query.get_or_404(game_id)
    teams = Team.query.filter_by(game_id=game_id).all()
    
    # Create the round immediately to store options
    new_round = Round(
        game_id=game_id,
        opt1=request.form.get('opt1', 'Option 1'),
        opt2=request.form.get('opt2', 'Option 2'),
        opt3=request.form.get('opt3', 'Option 3'),
        opt4=request.form.get('opt4', 'Option 4'),
        opt5=request.form.get('opt5', 'Option 5')
    )
    db.session.add(new_round)
    db.session.commit()
    
    return render_template('round.html', game=game, teams=teams, round_obj=new_round)

@app.route('/game/<int:game_id>/round/<int:round_id>/submit', methods=['POST'])
def submit_round(game_id, round_id):
    game = Game.query.get_or_404(game_id)
    round_obj = Round.query.get_or_404(round_id)
    teams = Team.query.filter_by(game_id=game_id).all()
    correct_option = int(request.form.get('correct_option'))
    
    round_obj.correct_option = correct_option
    
    # Create Bets
    for team in teams:
        amount_val = request.form.get(f'bet_{team.id}', '')
        amount = float(amount_val) if amount_val else 0
        option = int(request.form.get(f'option_{team.id}', 0))
        is_all_in = request.form.get(f'all_in_{team.id}') == 'on'
        
        if amount > 0:
            bet = Bet(round_id=round_obj.id, team_id=team.id, amount=amount, option_chosen=option, is_all_in=is_all_in)
            db.session.add(bet)
            team.money -= amount
    
    db.session.commit()
    
    # Calculate Results
    results, next_carryover = logic.calculate_round_results(round_obj, game.carryover_pool)
    
    # Apply Results
    game.carryover_pool = next_carryover
    for res in results:
        team = Team.query.get(res['team_id'])
        team.money += res['payout']
    
    db.session.commit()
    
    return render_template('results.html', game=game, results=results, next_carryover=next_carryover, correct_option=correct_option, round_obj=round_obj)

@app.route('/game/<int:game_id>/end')
def end_game(game_id):
    game = Game.query.get_or_404(game_id)
    game.status = 'finished'
    db.session.commit()
    
    top_teams = Team.query.filter_by(game_id=game_id).order_by(Team.money.desc()).limit(3).all()
    return render_template('leaderboard.html', game=game, top_teams=top_teams)

if __name__ == '__main__':
    app.run(debug=True)
