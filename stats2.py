import math

import pandas as pd
import streamlit as st

def adjustedstats(data):

    final_results4 = data[data['Wickets at Entry'] >= 0]
    # final_results4 = final_results4[final_results4['Wickets at Entry'] <= 4]
    # final_results4 = final_results4[final_results4['New Batter'].isin(players)]

    # final_results4 = final_results4[~final_results4['Team'].isin(['ICC'])]
    final_results4['year'] = pd.to_datetime(final_results4['Start Date'], format='mixed').dt.year

    # Define the years of interest
    years_of_interest = list(range(2016, 2025))

    # final_results4 = final_results4[final_results4['year'].isin(years_of_interest)]
    final_results4['Fifties'] = 0
    final_results4['Centuries'] = 0
    final_results4.loc[(final_results4['Runs'] >= 50) & (final_results4['Runs'] <= 99), 'Fifties'] = 1
    final_results4.loc[(final_results4['Runs'] >= 100), 'Centuries'] = 1

    df_match_totals = final_results4.groupby(['New Batter', 'Team','year','Wickets at Entry']).agg(
        Inns=('I', 'sum'),
        Runs=('Runs', 'sum'),
        Outs=('Out', 'sum'),
        Balls=('BF', 'sum'),
        Fifties=('Fifties', 'sum'),
        Centuries=('Centuries', 'sum'),

    ).reset_index()

    # Group by Match_ID and Batter, then calculate the total runs and outs for each player in each match
    df_match_totals2 = final_results4.groupby(['year','Wickets at Entry']).agg(
        Inns=('I', 'sum'),
        Runs=('Runs', 'sum'),
        Outs=('Out', 'sum'),
        Balls=('BF', 'sum'),
        Fifties=('Fifties', 'sum'),
        Centuries=('Centuries', 'sum'),
    ).reset_index()

    df_match_totals3 = final_results4[final_results4['year'].isin(years_of_interest)]
    # Group by Match_ID and Batter, then calculate the total runs and outs for each player in each match
    df_match_totals3 = df_match_totals3.groupby(['Wickets at Entry']).agg(
        PresentInns=('I', 'sum'),
        PresentRuns=('Runs', 'sum'),
        PresentOuts=('Out', 'sum'),
        PresentBalls=('BF', 'sum'),
        PresentFifties=('Fifties', 'sum'),
        PresentCenturies=('Centuries', 'sum'),
    ).reset_index()

    batting = pd.merge(df_match_totals, df_match_totals2, on=['year','Wickets at Entry'], suffixes=('', '_grouped'))

    batting['run_diff'] = batting['Runs_grouped'] - batting['Runs']
    batting['out_diff'] = batting['Outs_grouped'] - batting['Outs']
    batting['ball_diff'] = batting['Balls_grouped'] - batting['Balls']
    batting['cen_diff'] = batting['Centuries_grouped'] - batting['Centuries']
    batting['Fifties_diff'] = batting['Fifties_grouped'] - batting['Fifties']
    batting['inn_diff'] = batting['Inns_grouped'] - batting['Inns']


    batting['BSR'] = batting['run_diff'] / batting['ball_diff']
    batting['OPB'] = batting['out_diff'] / batting['ball_diff']
    batting['FPI'] = batting['Fifties_diff'] / batting['inn_diff']
    batting['CPI'] = batting['cen_diff'] / batting['inn_diff']

    batting['Expected Runs'] = batting['Balls'] * batting['BSR']
    batting['Expected Outs'] = batting['Balls'] * batting['OPB']
    batting['Expected Fifties'] = batting['Inns'] * batting['FPI']
    batting['Expected Centuries'] = batting['Inns'] * batting['CPI']

    # batting.to_csv('toughruns.csv',index=False)
    # Group by Match_ID and Batter, then calculate the total runs and outs for each player in each match

    final_results5 = batting.groupby(['New Batter','Wickets at Entry'])[
        ['Inns', 'Runs', 'Balls', 'Outs', 'Fifties','Centuries', 'Expected Runs', 'Expected Outs', 'Expected Fifties','Expected Centuries']].sum().reset_index()

    batting = pd.merge(final_results5, df_match_totals3, on=['Wickets at Entry'], suffixes=('', '_grouped'))

    batting['BSR'] = batting['PresentRuns'] / batting['PresentBalls']
    batting['OPB'] = batting['PresentOuts'] / batting['PresentBalls']
    batting['FPI'] = batting['PresentFifties'] / batting['PresentInns']
    batting['CPI'] = batting['PresentCenturies'] / batting['PresentInns']

    batting['Expected Runs 2'] = batting['Balls'] * batting['BSR']
    batting['Expected Outs 2'] = batting['Balls'] * batting['OPB']
    batting['Expected Fifties 2'] = batting['Inns'] * batting['FPI']
    batting['Expected Centuries 2'] = batting['Inns'] * batting['CPI']

    final_results5 = batting.groupby(['New Batter',])[
        ['Inns', 'Runs', 'Balls', 'Outs', 'Fifties','Centuries', 'Expected Runs', 'Expected Outs', 'Expected Fifties','Expected Centuries','Expected Runs 2', 'Expected Outs 2','Expected Fifties 2','Expected Centuries 2']].sum().reset_index()

    final_results5['Ave'] = (final_results5['Runs']) / (final_results5['Outs'])
    final_results5['SR'] = (final_results5['Runs']) / (final_results5['Balls']) * 100
    final_results5['InnsPerCentury'] = (final_results5['Inns']) / (final_results5['Centuries'])

    final_results5['expected_ave'] = (final_results5['Expected Runs']) / (final_results5['Expected Outs'])
    final_results5['expected_sr'] = (final_results5['Expected Runs']) / (final_results5['Balls']) * 100
    final_results5['expinnsPerCentury'] = (final_results5['Inns']) / (final_results5['Expected Centuries'])

    final_results5['Ave Ratio'] = (final_results5['Ave']) / (final_results5['expected_ave'])
    final_results5['SR Ratio'] = (final_results5['SR']) / (final_results5['expected_sr'])
    final_results5['Cen Ratio'] = (final_results5['Centuries']) / (final_results5['Expected Centuries'])

    final_results5['expected_ave_present'] = (final_results5['Expected Runs 2']) / (final_results5['Expected Outs 2'])
    final_results5['expected_sr_present'] = (final_results5['Expected Runs 2']) / (final_results5['Balls']) * 100

    final_results5['Adjusted Ave'] = final_results5['expected_ave_present'] * final_results5['Ave Ratio']
    final_results5['Adjusted Sr'] = final_results5['expected_sr_present'] * final_results5['SR Ratio']
    final_results5['Present Centuries'] = final_results5['Expected Centuries 2'] * final_results5['Cen Ratio']

    final_results5 = final_results5.rename(columns={'New Batter':'Batter'})
    # final_results5 = final_results5[final_results5['New Batter'].isin(names)]
    return final_results5[['Batter','Inns', 'Runs', 'Balls', 'Outs','Fifties','Centuries','Ave','SR', 'Adjusted Ave','Adjusted Sr']].round(2)




@st.cache_data
def load_data(filename):
    data = pd.read_csv(filename, low_memory=False)
    return data

def main():
    st.title('Adjusted ODI Stats')

    data = load_data('odientrypoints.csv')

    data2 = data.groupby('New Batter')[['Runs']].sum().reset_index()
    run = max((data2['Runs']).astype(int))

    # Selectors for user input
    options = ['Overall',]

    # Create a select box
    choice2 = st.selectbox('Individual Player or Everyone:', ['Individual', 'Everyone'])
    # choice3 = st.multiselect('Home or Away:', ['Home', 'Away'])
    # choice5 = st.multiselect('Team:', data['Team'].unique())
    #    Filtering data based on the user's Date selection


    start_runs, end_runs = st.slider('Select Minimum Runs:', min_value=1, max_value=run, value=(1, run))

    data['year'] = pd.to_datetime(data['Start Date'], format='mixed').dt.year

    if choice2 == 'Individual':
        players = data['New Batter'].unique()
        player = st.multiselect("Select Players:", players)
        # name = st.selectbox('Choose the Player From the list', data['striker'].unique())

    # A button to trigger the analysis

    if st.button('Analyse'):
        # Call a hypothetical function to analyze data

        results = adjustedstats(data)
        results = results[
            (results['Runs'] >= start_runs) & (results['Runs'] <= end_runs)]

        if choice2 == 'Individual':
            temp = []
            for i in player:
                if i in results['Batter'].unique():
                    temp.append(i)
                else:
                    st.subheader(f'{i} not in this list')
            results = results[results['Batter'].isin(temp)]
            results = results.rename(columns={'Batter': 'Batsman'})

            st.dataframe(results.round(2))
        else:
            results = results.rename(columns={'Batter': 'Batsman'})

            results = results.sort_values(by=['Runs'], ascending=False)
            st.dataframe(results.round(2))



# Run the main function
if __name__ == '__main__':
    main()
