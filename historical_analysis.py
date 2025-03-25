import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from cricket_analysis import calculate_batting_match_factors, calculate_bowling_match_factors
import os

def calculate_historical_factors(data_file, min_games=5, years=5):
    """
    Calculate historical match factors for all players who have played in the last N years
    and have played at least min_games matches
    """
    print(f"Loading data from {data_file}...")
    data = pd.read_csv(data_file)
    
    # Convert date to datetime
    data['start_date'] = pd.to_datetime(data['start_date'], format='%Y-%m-%d')
    
    # Calculate cutoff date (N years ago from latest date)
    latest_date = data['start_date'].max()
    cutoff_date = latest_date - timedelta(days=years*365)
    
    print(f"Analyzing data from {cutoff_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}")
    
    # Filter data for the specified time period
    recent_data = data[data['start_date'] >= cutoff_date].copy()
    
    # Create output directory if it doesn't exist
    output_dir = 'historical_analysis'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Calculate batting match factors
    print("\nCalculating batting match factors...")
    batting_factors = calculate_batting_match_factors(recent_data, min_games=min_games)
    
    # Aggregate batting stats across matches for each player
    batting_stats = batting_factors.groupby('striker').agg({
        'match_id': 'count',  # Matches
        'runs_off_bat': 'sum',  # Total runs
        'ball': 'sum',  # Total balls faced
        'wicket_type': 'sum',  # Total dismissals
        'Match_Factor': 'mean'  # Average match factor
    }).reset_index()
    
    batting_stats.columns = ['Player', 'Matches', 'Runs', 'Balls', 'Dismissals', 'Avg_Match_Factor']
    
    # Calculate additional batting stats
    batting_stats['Average'] = batting_stats['Runs'] / batting_stats['Dismissals']
    batting_stats['Strike_Rate'] = (batting_stats['Runs'] / batting_stats['Balls']) * 100
    
    # Round numeric columns
    numeric_columns = ['Matches', 'Runs', 'Balls', 'Dismissals', 'Avg_Match_Factor', 'Average', 'Strike_Rate']
    batting_stats[numeric_columns] = batting_stats[numeric_columns].round(2)
    
    # Save batting stats
    batting_stats.to_csv(f'{output_dir}/batting_historical_factors.csv', index=False)
    print(f"Saved batting stats to {output_dir}/batting_historical_factors.csv")
    
    # Calculate bowling match factors
    print("\nCalculating bowling match factors...")
    bowling_factors = calculate_bowling_match_factors(recent_data, min_games=min_games)
    
    # Save bowling stats
    bowling_factors.to_csv(f'{output_dir}/bowling_historical_factors.csv', index=False)
    print(f"Saved bowling stats to {output_dir}/bowling_historical_factors.csv")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Total matches analyzed: {len(recent_data['match_id'].unique())}")
    print(f"Number of eligible batsmen: {len(batting_stats)}")
    print(f"Number of eligible bowlers: {len(bowling_factors)}")
    
    # Print top performers
    print("\nTop 10 Batsmen by Average Match Factor:")
    print(batting_stats.nlargest(10, 'Avg_Match_Factor')[['Player', 'Matches', 'Runs', 'Average', 'Strike_Rate', 'Avg_Match_Factor']])
    
    print("\nTop 10 Bowlers by Match Factor:")
    print(bowling_factors.nlargest(10, 'Match Factor')[['Bowler', 'Mat', 'Wickets', 'Ave', 'SR', 'Match Factor']])
    
    return batting_stats, bowling_factors

def analyze_player_history(data_file, player_name, min_games=5, years=5):
    """
    Analyze historical performance of a specific player
    """
    batting_stats, bowling_stats = calculate_historical_factors(data_file, min_games, years)
    
    # Check batting stats
    player_batting = batting_stats[batting_stats['Player'] == player_name]
    if not player_batting.empty:
        print(f"\nBatting History for {player_name}:")
        print(player_batting[['Player', 'Matches', 'Runs', 'Average', 'Strike_Rate', 'Avg_Match_Factor']])
    
    # Check bowling stats
    player_bowling = bowling_stats[bowling_stats['Bowler'] == player_name]
    if not player_bowling.empty:
        print(f"\nBowling History for {player_name}:")
        print(player_bowling[['Bowler', 'Mat', 'Wickets', 'Ave', 'SR', 'Match Factor']])
    
    if player_batting.empty and player_bowling.empty:
        print(f"\nNo data found for {player_name} in the specified time period")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate historical cricket match factors')
    parser.add_argument('--data', type=str, required=True, help='Path to the data file (e.g., ipl.csv)')
    parser.add_argument('--min_games', type=int, default=5, help='Minimum number of games required (default: 5)')
    parser.add_argument('--years', type=int, default=5, help='Number of years to analyze (default: 5)')
    parser.add_argument('--player', type=str, help='Player name for specific analysis (optional)')
    
    args = parser.parse_args()
    
    try:
        if args.player:
            analyze_player_history(args.data, args.player, args.min_games, args.years)
        else:
            calculate_historical_factors(args.data, args.min_games, args.years)
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main() 