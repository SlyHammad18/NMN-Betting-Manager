BETTING MANAGEMENT ENGINE
==========================

A dark, modern betting management system for moderators.

SETUP INSTRUCTIONS:
-------------------
1. Install dependencies:
   pip install -r requirements.txt

2. Run the application:
   python app.py

3. Open in browser:
   http://127.0.0.1:5000

FEATURES:
---------
- Create games with a default starting balance for teams.
- Add teams quickly (balance is automatically assigned).
- Set up rounds with 5 descriptive options.
- Enter bets for each team using a dropdown of options.
- Automatic payout calculations:
    - Winners share the pool proportional to their bets.
    - Max 4x reward cap.
    - 1.5x bonus for All-In winners.
    - Carryover pool for rounds with no winners.
- Leaderboard shows the top 3 teams when the game ends.
