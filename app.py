from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Game, Team, Round, Bet
import logic

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment_engine.db'
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

@app.route('/game/<int:game_id>/delete', methods=['POST'])
def delete_game(game_id):
    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
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
        opt1=request.form.get('opt1', 'a'),
        opt2=request.form.get('opt2', 'b'),
        opt3=request.form.get('opt3', 'c'),
        opt4=request.form.get('opt4', 'd'),
        opt5=request.form.get('opt5', 'e')
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
    round_obj.previous_carryover = game.carryover_pool
    
    # Create Investments (formerly bets)
    bet_objs = {} # To keep track of created bets to update payouts later
    for team in teams:
        amount_val = request.form.get(f'bet_{team.id}', '')
        amount = float(amount_val) if amount_val else 0
        
        multiplier_val = request.form.get(f'multiplier_{team.id}', '1')
        try:
            multiplier = float(multiplier_val)
        except ValueError:
            multiplier = 1.0
            
        option = int(request.form.get(f'option_{team.id}', 0))
        
        if amount > 0:
            bet = Bet(round_id=round_obj.id, team_id=team.id, amount=amount, option_chosen=option, multiplier=multiplier)
            db.session.add(bet)
            team.money = round(team.money - amount, 2)
            bet_objs[team.id] = bet
    
    db.session.commit()
    
    # Calculate Results
    results, next_carryover = logic.calculate_round_results(round_obj, game.carryover_pool)
    
    # Apply Results
    game.carryover_pool = next_carryover
    for res in results:
        team_obj = Team.query.get(res['team_id'])
        team_obj.money += res['payout']
        if team_obj.id in bet_objs:
            bet_objs[team_obj.id].payout = res['payout']
    
    db.session.commit()
    
    return render_template('results.html', game=game, results=results, next_carryover=next_carryover, correct_option=correct_option, round_obj=round_obj)

@app.route('/team/<int:team_id>/edit_money', methods=['POST'])
def edit_team_money(team_id):
    team = Team.query.get_or_404(team_id)
    new_money = request.form.get('money')
    if new_money is not None:
        try:
            team.money = round(float(new_money), 2)
            db.session.commit()
        except ValueError:
            pass
    return redirect(url_for('game_dashboard', game_id=team.game_id))

@app.route('/game/<int:game_id>/round/undo', methods=['POST'])
def undo_round(game_id):
    game = Game.query.get_or_404(game_id)
    # Get the last completed round (one with a correct_option set)
    last_round = Round.query.filter(Round.game_id == game_id, Round.correct_option != None).order_by(Round.created_at.desc()).first()
    
    if last_round:
        # Revert carryover
        game.carryover_pool = last_round.previous_carryover
        
        # Revert team balances
        for bet in last_round.bets:
            team = Team.query.get(bet.team_id)
            if team:
                # Revert: Subtract payout, add back investment amount
                team.money = round(team.money - bet.payout + bet.amount, 2)
        
        # Delete the round (cascades will delete bets)
        db.session.delete(last_round)
        db.session.commit()
        
    return redirect(url_for('game_dashboard', game_id=game_id))

@app.route('/game/<int:game_id>/end')
def end_game(game_id):
    game = Game.query.get_or_404(game_id)
    game.status = 'finished'
    db.session.commit()
    
    all_teams = Team.query.filter_by(game_id=game_id).order_by(Team.money.desc()).all()
    
    ranked_teams = []
    current_rank = 0
    previous_money = None
    for i, team in enumerate(all_teams):
        if team.money != previous_money:
            current_rank = i + 1
        ranked_teams.append({'team': team, 'rank': current_rank})
        previous_money = team.money
        
    return render_template('leaderboard.html', game=game, ranked_teams=ranked_teams)

if __name__ == '__main__':
    app.run(debug=True)
