import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import argparse

def calculate_batting_match_factors(data, min_games=None, time_window=None):
    """
    Calculate batting match factors with time period and minimum games filters
    """
    # Convert date to datetime
    data['start_date'] = pd.to_datetime(data['start_date'], format='%Y-%m-%d')
    
    # Apply time window if specified
    if time_window:
        end_date = data['start_date'].max()
        window_start = end_date - pd.Timedelta(days=time_window)
        data = data[data['start_date'] >= window_start]
        print(f"Analyzing batting stats for last {time_window} days from {window_start.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Calculate match totals for each player
    player_match_totals = data.groupby(['match_id', 'start_date', 'striker']).agg({
        'runs_off_bat': 'sum',
        'ball': 'count',
        'wicket_type': 'count'
    }).reset_index()
    
    # Filter by minimum games if specified
    if min_games:
        player_match_counts = player_match_totals.groupby('striker')['match_id'].nunique()
        eligible_players = player_match_counts[player_match_counts >= min_games].index
        player_match_totals = player_match_totals[player_match_totals['striker'].isin(eligible_players)]
        print(f"Filtering batting stats for players with at least {min_games} games")
    
    # Calculate average for each player in each match
    player_match_totals['average'] = np.where(
        player_match_totals['wicket_type'] > 0,
        player_match_totals['runs_off_bat'] / player_match_totals['wicket_type'],
        player_match_totals['runs_off_bat']
    )
    
    # For each match, get the top 6 batting averages
    def get_top_6_averages(group):
        top_6 = group.nlargest(6, 'runs_off_bat')
        return top_6['runs_off_bat'].sum() / top_6['wicket_type'].sum() if top_6['wicket_type'].sum() > 0 else np.inf
    
    match_top_6_avg = player_match_totals.groupby('match_id').apply(get_top_6_averages).reset_index()
    match_top_6_avg.columns = ['match_id', 'top_6_avg']
    
    # Merge back to get match context
    player_stats = pd.merge(
        player_match_totals,
        match_top_6_avg,
        on='match_id'
    )
    
    # Calculate match factor
    player_stats['Match_Factor'] = np.where(
        player_stats['wicket_type'] > 0,
        player_stats['average'] / player_stats['top_6_avg'],
        player_stats['runs_off_bat'] / player_stats['top_6_avg']
    )
    
    # Round numeric columns
    numeric_columns = ['runs_off_bat', 'ball', 'wicket_type', 'average', 'top_6_avg', 'Match_Factor']
    player_stats[numeric_columns] = player_stats[numeric_columns].round(2)
    
    return player_stats

def calculate_bowling_match_factors(data, min_games=None, time_window=None):
    """
    Calculate bowling match factors with time period and minimum games filters
    """
    # Convert date to datetime
    data['start_date'] = pd.to_datetime(data['start_date'], format='%Y-%m-%d')
    
    # Apply time window if specified
    if time_window:
        end_date = data['start_date'].max()
        window_start = end_date - pd.Timedelta(days=time_window)
        data = data[data['start_date'] >= window_start]
        print(f"Analyzing bowling stats for last {time_window} days from {window_start.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Calculate match totals for each bowler
    bowler_match_totals = data.groupby(['match_id', 'start_date', 'bowler']).agg({
        'runs_off_bat': 'sum',  # runs conceded
        'ball': 'count',        # balls bowled
        'wicket_type': 'count'  # wickets taken
    }).reset_index()
    
    # Filter by minimum games if specified
    if min_games:
        bowler_match_counts = bowler_match_totals.groupby('bowler')['match_id'].nunique()
        eligible_bowlers = bowler_match_counts[bowler_match_counts >= min_games].index
        bowler_match_totals = bowler_match_totals[bowler_match_totals['bowler'].isin(eligible_bowlers)]
        print(f"Filtering bowling stats for players with at least {min_games} games")
    
    # Calculate match totals for all bowlers in each match
    match_totals = data.groupby(['match_id', 'start_date']).agg({
        'runs_off_bat': 'sum',
        'ball': 'count',
        'wicket_type': 'count'
    }).reset_index()
    
    # Merge to get match context
    bowler_stats = pd.merge(
        bowler_match_totals,
        match_totals,
        on=['match_id', 'start_date'],
        suffixes=('', '_match')
    )
    
    # Calculate differences from match totals
    bowler_stats['run_diff'] = bowler_stats['runs_off_bat_match'] - bowler_stats['runs_off_bat']
    bowler_stats['ball_diff'] = bowler_stats['ball_match'] - bowler_stats['ball']
    bowler_stats['wickets_diff'] = bowler_stats['wicket_type_match'] - bowler_stats['wicket_type']
    
    # Aggregate across matches for each bowler
    bowling2 = bowler_stats.groupby('bowler').agg({
        'match_id': 'count',  # Matches
        'runs_off_bat': 'sum',  # Runs
        'ball': 'sum',  # Balls
        'wicket_type': 'sum',  # Wickets
        'run_diff': 'sum',
        'ball_diff': 'sum',
        'wickets_diff': 'sum'
    }).reset_index()
    
    bowling2.columns = ['Bowler', 'Mat', 'Runs', 'Balls', 'Wickets', 'run_diff', 'ball_diff', 'wickets_diff']
    
    # Calculate bowling statistics
    bowling2['Ave'] = bowling2['Runs'] / bowling2['Wickets']
    bowling2['SR'] = bowling2['Balls'] / bowling2['Wickets']
    bowling2['BPM'] = bowling2['Balls'] / bowling2['Mat']
    bowling2['Mean Ave'] = bowling2['run_diff'] / bowling2['wickets_diff']
    bowling2['Mean SR'] = bowling2['ball_diff'] / bowling2['wickets_diff']
    
    # Calculate match factors
    bowling2['Match Factor'] = bowling2['Mean Ave'] / bowling2['Ave']
    bowling2['SR Factor'] = bowling2['Mean SR'] / bowling2['SR']
    
    # Round all numeric columns to 2 decimal places
    numeric_columns = ['Mat', 'Runs', 'Balls', 'Wickets', 'Ave', 'SR', 'BPM', 'Mean Ave', 'Mean SR', 'Match Factor', 'SR Factor']
    bowling2[numeric_columns] = bowling2[numeric_columns].round(2)
    
    return bowling2[['Bowler', 'Mat', 'Runs', 'Balls', 'Wickets', 'Ave', 'SR', 'BPM', 'Match Factor', 'SR Factor']]

def calculate_entry_points(data):
    """
    Calculate entry points for batters
    """
    # Convert over to decimal
    data['over_decimal'] = data['ball'].apply(lambda x: x / 6)
    
    # Get first appearance for each batter in each match
    entry_points = data.groupby(['match_id', 'striker']).agg({
        'over_decimal': 'min'
    }).reset_index()
    
    # Calculate average entry point for each batter
    avg_entry_points = entry_points.groupby('striker').agg({
        'over_decimal': 'mean'
    }).reset_index()
    
    return avg_entry_points

def calculate_true_values(data):
    """
    Calculate true values (expected vs actual performance)
    """
    # Calculate match averages
    match_averages = data.groupby('match_id').agg({
        'runs_off_bat': 'mean',
        'ball': 'count'
    }).reset_index()
    
    # Calculate player performance
    player_performance = data.groupby(['match_id', 'striker']).agg({
        'runs_off_bat': 'sum',
        'ball': 'count',
        'wicket_type': 'count'
    }).reset_index()
    
    # Merge to get context
    player_stats = pd.merge(
        player_performance,
        match_averages,
        on='match_id',
        suffixes=('', '_match')
    )
    
    # Calculate true values
    player_stats['True_Value'] = (player_stats['runs_off_bat'] / player_stats['ball']) - \
                                (player_stats['runs_off_bat_match'] / player_stats['ball_match'])
    
    return player_stats

def analyze_player_form(data, player_name, window_size=5):
    """
    Analyze player form over time
    """
    player_data = data[data['striker'] == player_name].copy()
    
    # Calculate match-by-match performance
    match_performance = player_data.groupby(['match_id', 'start_date']).agg({
        'runs_off_bat': 'sum',
        'ball': 'count',
        'wicket_type': 'count'
    }).reset_index()
    
    # Calculate rolling statistics
    match_performance['Rolling_Avg'] = match_performance['runs_off_bat'].rolling(window=window_size, min_periods=1).mean()
    match_performance['Rolling_SR'] = (match_performance['runs_off_bat'] / match_performance['ball'] * 100).rolling(window=window_size, min_periods=1).mean()
    
    return match_performance

def plot_player_form(player_data):
    """
    Plot player form over time
    """
    plt.figure(figsize=(12, 6))
    plt.plot(player_data['start_date'], player_data['Rolling_Avg'], label='Rolling Average')
    plt.plot(player_data['start_date'], player_data['Rolling_SR'], label='Rolling Strike Rate')
    plt.title('Player Form Over Time')
    plt.xlabel('Date')
    plt.ylabel('Rate')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def analyze_data(data_file, analysis_type, player_name=None, start_date=None, end_date=None, min_games=None, time_window=None):
    """
    Analyze cricket data based on specified type and time period
    """
    print(f"Loading data from {data_file}...")
    data = pd.read_csv(data_file)
    
    # Convert date to datetime
    data['start_date'] = pd.to_datetime(data['start_date'], format='%Y-%m-%d')
    
    # Filter data by date range if specified
    if start_date:
        start_date = pd.to_datetime(start_date)
        data = data[data['start_date'] >= start_date]
        print(f"Filtering data from {start_date.strftime('%Y-%m-%d')}")
    
    if end_date:
        end_date = pd.to_datetime(end_date)
        data = data[data['start_date'] <= end_date]
        print(f"Filtering data until {end_date.strftime('%Y-%m-%d')}")
    else:
        end_date = data['start_date'].max()
        print(f"Using data until {end_date.strftime('%Y-%m-%d')}")
    
    if data.empty:
        print("No data found for the specified time period")
        return
    
    print(f"Analyzing {len(data['match_id'].unique())} matches")
    
    if analysis_type == 'batting_match_factors':
        print("\nCalculating batting match factors...")
        match_factors = calculate_batting_match_factors(data, min_games, time_window)
        
        if player_name:
            print(f"\nStats for {player_name}:")
            player_stats = match_factors[match_factors['striker'] == player_name]
            if not player_stats.empty:
                print(player_stats[['striker', 'Match_Factor', 'average', 'top_6_avg']])
            else:
                print(f"No batting data found for {player_name}")
        else:
            print("\nTop 10 batting performances by match factor:")
            print(match_factors.nlargest(10, 'Match_Factor')[['striker', 'Match_Factor', 'average', 'top_6_avg']])
        
    elif analysis_type == 'bowling_match_factors':
        print("\nCalculating bowling match factors...")
        match_factors = calculate_bowling_match_factors(data, min_games, time_window)
        
        if player_name:
            print(f"\nStats for {player_name}:")
            player_stats = match_factors[match_factors['Bowler'] == player_name]
            if not player_stats.empty:
                print(player_stats[['Bowler', 'Mat', 'Runs', 'Balls', 'Wickets', 'Ave', 'SR', 'BPM', 'Match Factor', 'SR Factor']])
            else:
                print(f"No bowling data found for {player_name}")
        else:
            print("\nTop 10 bowling performances by match factor:")
            print(match_factors.nlargest(10, 'Match Factor')[['Bowler', 'Mat', 'Runs', 'Balls', 'Wickets', 'Ave', 'SR', 'BPM', 'Match Factor', 'SR Factor']])
        
    elif analysis_type == 'entry_points':
        print("\nCalculating entry points...")
        entry_points = calculate_entry_points(data)
        
        # Filter by minimum games if specified
        if min_games:
            player_match_counts = data.groupby('striker')['match_id'].nunique()
            eligible_players = player_match_counts[player_match_counts >= min_games].index
            entry_points = entry_points[entry_points['striker'].isin(eligible_players)]
            print(f"\nFiltering for players with at least {min_games} games")
        
        if player_name:
            print(f"\nEntry points for {player_name}:")
            player_stats = entry_points[entry_points['striker'] == player_name]
            if not player_stats.empty:
                print(player_stats[['striker', 'over_decimal']])
            else:
                print(f"No entry point data found for {player_name}")
        else:
            print("\nTop 10 players by earliest average entry point:")
            print(entry_points.nsmallest(10, 'over_decimal'))
        
    elif analysis_type == 'true_values':
        print("\nCalculating true values...")
        true_values = calculate_true_values(data)
        
        # Filter by minimum games if specified
        if min_games:
            player_match_counts = data.groupby('striker')['match_id'].nunique()
            eligible_players = player_match_counts[player_match_counts >= min_games].index
            true_values = true_values[true_values['striker'].isin(eligible_players)]
            print(f"\nFiltering for players with at least {min_games} games")
        
        if player_name:
            print(f"\nTrue values for {player_name}:")
            player_stats = true_values[true_values['striker'] == player_name]
            if not player_stats.empty:
                print(player_stats[['striker', 'True_Value']])
            else:
                print(f"No true value data found for {player_name}")
        else:
            print("\nTop 10 players by true value:")
            print(true_values.nlargest(10, 'True_Value')[['striker', 'True_Value']])
        
    elif analysis_type == 'player_form':
        if not player_name:
            raise ValueError("Player name must be specified for player form analysis")
        print(f"\nAnalyzing form for {player_name}...")
        player_form = analyze_player_form(data, player_name)
        plot_player_form(player_form)
        
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")

def main():
    parser = argparse.ArgumentParser(description='Cricket Data Analysis')
    parser.add_argument('--data', type=str, required=True, help='Path to the data file (e.g., ipl.csv)')
    parser.add_argument('--analysis', type=str, required=True, 
                      choices=['batting_match_factors', 'bowling_match_factors', 'entry_points', 'true_values', 'player_form'],
                      help='Type of analysis to perform')
    parser.add_argument('--player', type=str, help='Player name for analysis (optional)')
    parser.add_argument('--start_date', type=str, help='Start date in YYYY-MM-DD format (optional)')
    parser.add_argument('--end_date', type=str, help='End date in YYYY-MM-DD format (optional)')
    parser.add_argument('--min_games', type=int, help='Minimum number of games required for analysis (optional)')
    parser.add_argument('--time_window', type=int, help='Number of days to look back from end_date (optional)')
    
    args = parser.parse_args()
    
    try:
        analyze_data(args.data, args.analysis, args.player, args.start_date, args.end_date, args.min_games, args.time_window)
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main() 