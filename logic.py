def calculate_round_results(round_obj, carryover_pool):
    bets = round_obj.bets
    correct_option = round_obj.correct_option
    
    current_round_pool = sum(bet.amount for bet in bets) + carryover_pool
    winning_bets = [bet for bet in bets if bet.option_chosen == correct_option]
    
    total_winning_bet_amount = sum(bet.amount for bet in winning_bets)
    
    results = []
    total_payout = 0
    
    if total_winning_bet_amount > 0:
        for bet in winning_bets:
            # Base Proportional Payout
            base_payout = (bet.amount / total_winning_bet_amount) * current_round_pool
            
            # Cap at 4x
            capped_payout = min(base_payout, 4 * bet.amount)
            
            # All-in bonus
            if bet.is_all_in:
                final_payout = capped_payout * 1.5
            else:
                final_payout = capped_payout
            
            results.append({
                'team_id': bet.team_id,
                'payout': final_payout,
                'is_winner': True
            })
            total_payout += final_payout
        
        next_carryover = max(0, current_round_pool - total_payout)
    else:
        # No winners, entire pool carries over
        next_carryover = current_round_pool
        for bet in bets:
            results.append({
                'team_id': bet.team_id,
                'payout': 0,
                'is_winner': False
            })

    return results, next_carryover
