import math

import pandas as pd
import streamlit as st



@st.cache_data
def load_data(filename):
    data = pd.read_csv(filename, low_memory=False)
    return data

def main():
    st.title('Adjusted ODI Stats')

    data = load_data('OdiEraFactor2.csv')

    # data2 = data.groupby('New Batter')[['Runs']].sum().reset_index()
    # run = max((data2['Runs']).astype(int))

    # Selectors for user input
    options = ['Overall',]

    # Create a select box
    choice2 = st.selectbox('Individual Player or Everyone:', ['Individual', 'Everyone'])
    # choice3 = st.multiselect('Home or Away:', ['Home', 'Away'])
    # choice5 = st.multiselect('Team:', data['Team'].unique())
    #    Filtering data based on the user's Date selection


    start_runs, end_runs = st.slider('Select Minimum Runs:', min_value=1, max_value=18426, value=(1, 18426))

    if choice2 == 'Individual':
        players = data['Batter'].unique()
        player = st.multiselect("Select Players:", players)
        # name = st.selectbox('Choose the Player From the list', data['striker'].unique())

    # A button to trigger the analysis
    if st.button('Analyse'):
        # Call a hypothetical function to analyze data

        results = data[
            (data['Runs'] >= start_runs) & (data['Runs'] <= end_runs)]

        if choice2 == 'Individual':
            temp = []
            for i in player:
                if i in results['Batter'].unique():
                    temp.append(i)
                else:
                    st.subheader(f'{i} not in this list')
            results = results[results['Batter'].isin(temp)]
            results = results.rename(columns={'Batter': 'Batsman'})

            st.dataframe(results[['Batsman','Inns', 'Runs', 'Balls', 'Outs','Fifties','Centuries','Ave','SR', 'Adjusted Ave','Adjusted Sr']].round(2))
        else:
            results = results.rename(columns={'Batter': 'Batsman'})

            results = results.sort_values(by=['Runs'], ascending=False)
            st.dataframe(results[['Batsman','Inns', 'Runs', 'Balls', 'Outs','Fifties','Centuries','Ave','SR', 'Adjusted Ave','Adjusted Sr']].round(2))



# Run the main function
if __name__ == '__main__':
    main()
