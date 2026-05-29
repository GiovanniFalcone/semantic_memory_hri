import pandas as pd

import csv
import os
import time
import json
import datetime
import math

ids = []
mod = []
turns = []
time_play = []
avg_time_until_match = []
wrong_moves = []
board_chanded_times = []
token_geo = []
token_math = []
pairs_resolved_from_geo_robot = []
pairs_resolved_from_math_robot = []
number_of_curiosities_from_geo_robot = []
number_of_curiosities_from_math_robot = []


def get_turn_number(df):
    """
    get number of turns necessary to end a game for each user
    """
    
    tmp = df.loc[df['game_ended'] == True]      
    turns.append(tmp['turn_number'].iloc[0])

def get_time(df):
    # avg time to find a pair
    tmp = df.loc[df['match'] == True]
    tmp = tmp['time_until_match'].tolist()
    avg = (str(datetime.timedelta(seconds=math.trunc(sum(map(lambda f: int(f[0])*60 + int(f[1]), map(lambda f: f.split(':'), tmp)))/len(tmp)))))
    avg_time_until_match.append(avg)
    # time to finish the game
    mysum = datetime.timedelta()
    for i in tmp:
        (m, s) = i.split(':')
        d = datetime.timedelta(minutes=int(m), seconds=int(s))
        mysum += d
    time_play.append(str(mysum))

def get_number_of_wrong_cards_provided(df):
    """
    get number of wrong cards provided by the robot during the game
    """
    tmp = df.loc[df['wrong_card'] == True]      
    wrong_moves.append(len(tmp))

def get_board_changed_times(df):
    """
    get number of times the board changed during the game
    """
    tmp = df.loc[df['board_changed'] == True]      
    board_chanded_times.append(len(tmp))

def get_token_geo(df):
    """
    get number of times the robot David (geography) played during the game
    """
    tmp = df.loc[df['subject'] == 'geography']      
    token_geo.append(len(tmp))

def get_token_math(df):
    """
    get number of times the robot David (math) played during the game
    """
    tmp = df.loc[df['subject'] == 'math']      
    token_math.append(len(tmp))

def get_pairs_resolved_from_geo_robot(df):
    """
    get number of pairs resolved by the robot David (geography) during the game
    """
    tmp = df.loc[(df['turn_token'] == 'geography') & (df['match'] == True)]      
    pairs_resolved_from_geo_robot.append(len(tmp))

def get_pairs_resolved_from_math_robot(df):
    """
    get number of pairs resolved by the robot Michael (math) during the game
    """
    tmp = df.loc[(df['turn_token'] == 'math') & (df['match'] == True)]      
    pairs_resolved_from_math_robot.append(len(tmp))

def get_number_of_curiosities_from_geo_robot(df):
    """
    get number of curiosities provided by the robot David (geography) during the game
    """
    tmp = df.loc[(df['robot_speech'] == 'geography')]      
    number_of_curiosities_from_geo_robot.append(len(tmp))

def get_number_of_curiosities_from_math_robot(df):
    """
    get number of curiosities provided by the robot Michael (math) during the game
    """
    tmp = df.loc[(df['robot_speech'] == 'math')]      
    number_of_curiosities_from_math_robot.append(len(tmp))

# get all csv 
path =r"..\data\\"
df_append = pd.DataFrame()
for root, dirs, files in sorted(os.walk(path)):
    for file in files:
        if(file.endswith(".csv")):
            print(os.path.join(root,file))
            # one data frame for file
            df = pd.read_csv(os.path.join(root,file), sep=';')
            print(df)

            # get id and mod
            ids.append(df['id_player'].iloc[0])
            mod.append(df['experiment_condition'].iloc[0])

            # get turn number
            get_turn_number(df)

            # get time
            get_time(df)

            # get wrong cards
            get_number_of_wrong_cards_provided(df)

            # get board changed times
            get_board_changed_times(df)

            # get token geo
            get_token_geo(df)

            # get token math
            get_token_math(df)

            # get pairs resolved from geo robot
            get_pairs_resolved_from_geo_robot(df)

            # get pairs resolved from math robot
            get_pairs_resolved_from_math_robot(df)

            # get number of curiosities from geo robot
            get_number_of_curiosities_from_geo_robot(df)

            # get number of curiosities from math robot
            get_number_of_curiosities_from_math_robot(df)


csv_struct = {
    "id": ids, 
    "experiment_condition": mod, "turns": turns, 
    "time to finish": time_play,                                        # include anche i robot
    "average time to find a pair": avg_time_until_match,                # include anche i robot
    "wrong moves": wrong_moves,
    "board changed times": board_chanded_times,
    "token geo": token_geo,                                             # conta tutte le volte che l'umano ha cliccato il bottone (il robot potrebbe anche aver giocato 0 turni)
    "token math": token_math,
    "pairs resolved from geo robot": pairs_resolved_from_geo_robot,     # conta anche quelle che ha risolto casualmente (le carte non erano note -> clicca random -> match)
    "pairs resolved from math robot": pairs_resolved_from_math_robot,
    "number of curiosities from geo robot": number_of_curiosities_from_geo_robot,
    "number of curiosities from math robot": number_of_curiosities_from_math_robot
}

# write on excel the results
keys = csv_struct.keys()

# create dataframe
df_final = pd.DataFrame(csv_struct)
# order dataframe by id
df_final['id'] = df_final['id'].astype(int)
df_final.sort_values(by='id', inplace=True)
# handle time
df_final['time to finish'] = pd.to_timedelta(df_final['time to finish'])
df_final['time to finish'] = df_final['time to finish'].astype(str)
df_final['time to finish'] = df_final['time to finish'].apply(lambda x: str(x).split()[2]) # remove 0 days

# save it on excel
with pd.ExcelWriter("results.xlsx") as writer:
    df_final.to_excel(writer, index=False, float_format="%.2f")