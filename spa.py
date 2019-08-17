#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 13:16:15 2019

@author: amar
"""

import json
import pandas as pd
import glob
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output
import plotly.graph_objs as go

    
#userID
def getUserID(dataframe):
    return dataframe['userID']

#find all the news article the user was exposed to and then count the number of
#articles from liberal and conservative media
def getInfluence(dataframe):
    column_to_explode = 'searchResults'
    if 'timestamp' in dataframe.columns:
        res1 = (dataframe[column_to_explode].apply(pd.Series).merge(dataframe,right_index=True,left_index=True).drop([column_to_explode],axis=1).melt(id_vars=['searchQueryPageNum','searchQueryString','timestamp'],value_name="site").drop("variable",axis=1).dropna())
        res1.sort_values(['searchQueryString','timestamp'],inplace=True)
    else:
        res1 = (dataframe[column_to_explode].apply(pd.Series).merge(dataframe,right_index=True,left_index=True).drop([column_to_explode],axis=1).melt(id_vars=['searchQueryPageNum','searchQueryString'],value_name="site").drop("variable",axis=1).dropna())
        res1.sort_values('searchQueryString',inplace=True)
    res1 = res1[res1.site != "www.google.com"] #remove unwanted data
    column_to_explode2 = 'site'
    res1 = (res1[column_to_explode2].apply(pd.Series).merge(res1,right_index=True,left_index=True).drop([column_to_explode2],axis=1))

    liberalInfluence = 0
    conservativeInfluence = 0
    totalSites = 0

    liberalOutlet = ["nytimes","pbs","bbc","npr","huffpost","cnn","politico"]
    conservativeOutlet = ["fox","wsj","bloomberg","breitbart","theblaze", "usatoday"]

    #compute liberal influence
    for outlet in liberalOutlet:
        liberalInfluence = liberalInfluence + res1['url'].str.count(outlet).astype(bool).sum(axis=0)

    #compute conservative influence
    for outlet in conservativeOutlet:
        conservativeInfluence = conservativeInfluence + res1['url'].str.count(outlet).astype(bool).sum(axis=0)
    
    totalSites = res1['url'].count()
    
    return (liberalInfluence,conservativeInfluence,totalSites)

#return the user's most favorite topic and the number of time she searched for it
def userFavTopic(dataframe):
    #query frequency (how many times did the user search for a query)
    if 'timestamp' in dataframe.columns:
        u1QueryFreq = dataframe.sort_values(['searchQueryString','timestamp'])['searchQueryString'].value_counts()
    else:
        u1QueryFreq = dataframe.sort_values('searchQueryString')['searchQueryString'].value_counts()
    #find the topic with most exposure over the time period
    return u1QueryFreq.idxmax(axis=0), u1QueryFreq.max()

#count the number of articles on a topic covered by liberal and conservative media
def topicCoverage(dataframe,u1FavTopic):
    column_to_explode = 'searchResults'
    if 'timestamp' in dataframe.columns:
        res1 = (dataframe[column_to_explode].apply(pd.Series).merge(dataframe,right_index=True,left_index=True).drop([column_to_explode],axis=1).melt(id_vars=['searchQueryPageNum','searchQueryString','timestamp'],value_name="site").drop("variable",axis=1).dropna())
        res1.sort_values(['searchQueryString','timestamp'],inplace=True)
    else:
        res1 = (dataframe[column_to_explode].apply(pd.Series).merge(dataframe,right_index=True,left_index=True).drop([column_to_explode],axis=1).melt(id_vars=['searchQueryPageNum','searchQueryString'],value_name="site").drop("variable",axis=1).dropna())
        res1.sort_values('searchQueryString',inplace=True)
    res1 = res1[res1.site != "www.google.com"] #remove unwanted data
    column_to_explode2 = 'site'
    res1 = (res1[column_to_explode2].apply(pd.Series).merge(res1,right_index=True,left_index=True).drop([column_to_explode2],axis=1))
    
    res1 = res1[res1.searchQueryString == u1FavTopic]
    
    liberalInfluence = 0
    conservativeInfluence = 0
    totalSites = 0
    
    liberalOutlet = ["nytimes","pbs","bbc","npr","huffpost","cnn","politico"]
    conservativeOutlet = ["fox","wsj","bloomberg","breitbart","theblaze", "usatoday"]
    
    #compute liberal influence
    for outlet in liberalOutlet:
        liberalInfluence = liberalInfluence + res1['url'].str.count(outlet).astype(bool).sum(axis=0)
    
    #compute conservative influence
    for outlet in conservativeOutlet:
        conservativeInfluence = conservativeInfluence + res1['url'].str.count(outlet).astype(bool).sum(axis=0)
    
    totalSites = res1['url'].count()
    
    return (liberalInfluence,conservativeInfluence,totalSites)

#read json file and call functions for each user
def processData(filename,userStatFrame,topicStatFrame):
    with open(filename,"r") as read_file:
        dataUser1 = json.load(read_file)
               
    #get userID
    userID1 = getUserID(dataUser1)
    
    #searchData
    df1 = pd.DataFrame(dataUser1['searchData'])
    
    #convert string to timestamp
    if 'timestamp' in df1.columns:
        df1['timestamp'] = pd.to_datetime(df1['timestamp'],infer_datetime_format=True)
    
    u1LiberalInf,u1ConservInf,totalSts = getInfluence(df1)
    u1FavTopic, searched = userFavTopic(df1)
#    print(userSecondFavTopic(df1))
    topicLiberalCov,topicConvCov,totalCov = topicCoverage(df1,u1FavTopic)
    
    userStatFrame = userStatFrame.append({'userID':userID1,'totalSites':totalSts,'liberalInfluence':u1LiberalInf,'conservativeInfluence':u1ConservInf,'favTopic':u1FavTopic,'searched':searched},ignore_index=True)
    topicStatFrame = topicStatFrame.append({'userID':userID1,'topic':u1FavTopic,'totalCoverage':totalCov,'liberalCoverage':topicLiberalCov,'conservativeCoverage':topicConvCov},ignore_index=True)
    
    return userStatFrame,topicStatFrame


userStat = pd.DataFrame(columns=['userID','totalSites','liberalInfluence','conservativeInfluence','favTopic','searched'])
topicStat = pd.DataFrame(columns=['userID','topic','totalCoverage','liberalCoverage','conservativeCoverage'])


for filename in glob.glob('*.json'):
    userStat,topicStat = processData(filename,userStat,topicStat)
    

#Diggin Deeper into John's data
with open("29a7a895-f806-4582-ab53-7602d77758ed.json","r") as read_file:
    dataUser = json.load(read_file)
    
#take only the searchData
df = pd.DataFrame(dataUser['searchData'])

#convert string to timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'],infer_datetime_format=True)

#find all the news article the user was exposed to
column_to_explode = 'searchResults'

res = (df[column_to_explode].apply(pd.Series).merge(df,right_index=True,left_index=True).drop([column_to_explode],axis=1).melt(id_vars=['searchQueryPageNum','searchQueryString','timestamp'],value_name="site").drop("variable",axis=1).dropna())

res.sort_values(['searchQueryString','timestamp'],inplace=True)

#remove unwanted data
res = res[res.site != "www.google.com"]

column_to_explode2 = 'site'

ress = (res[column_to_explode2].apply(pd.Series).merge(res,right_index=True,left_index=True).drop([column_to_explode2],axis=1))

#process the timestamp for visualisation
maxDate = ress['timestamp'].max().to_pydatetime()
minDate = ress['timestamp'].min().to_pydatetime()

if(maxDate.month == minDate.month):
    ress['timestamp'] = ress['timestamp'].dt.day
elif(maxDate.year == minDate.year):
    ress['timestamp'] = ress['timestamp'].dt.month
else:
    ress['timestamp'] = ress['timestamp'].dt.month



##############################################
#website stuff
##########################################    
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#text blocks

loudest = '''
        ### Who is the loudest?
        
        We counted the number of liberal and conservative media article each time
        the user searched google. We are trying to see if it is the liberal or the
        conservative media that has the strongest presence on the web.
        '''
        
favorite = '''
        ### What's hot?
        
        We tried to find each user's most (favorite?) searched topic. Unsurprisingly,
        our politically savvy users were more interested in the upcoming election.
        We counted each time a user searched for a specific topic.
        '''
        
coverage = '''
        ### Some are more Liberal than others
        
        So, is it the liberal or the conservative media that is more successful in
        reaching our users. Well, a quick comparison of number of articles shows
        that the liberal media is more successful (hover over each point to see the
        number of articles that reached each user). It also seems like user 29a7a...,
        okay, user John Smith is the most liberal of the bunch! That's is if google
        algorithm thinks he likes the liberal media more. He also has the most interst
        in the 2020 election. Maybe he is a political analyst...
        
        Note: How to read the data? (# of conservative articles, # of liberal articles) and # of total articles
        '''
        
digging = '''
        ### Digging Deeper
        
        John seems like an interesting fellow. Let's look at the topics that he
        searched for and how many liberal vs conservative media article he came across.
        In an ideal world, John's opinion might be fair if he read an equal number of
        articles from both the liberal and conservative media. So the points in the
        graph below would lie on a straignt diagonal line.
        
        If we drag the slider at the bottom of the graph to 22 (the 22nd day of the
        month) we see that he searched for 4 topics. The point smack at (0,0) represents
        the search about smartphone. Well, the liberal and conservative media
        are not too concerned with smartphone. At least, that's what the data tells
        us. 2020 Election was covered by more liberal media outlets than conservative
        outlets. 16 vs. 6 to be exact.
        
        The protests Puerto Rico seems to have been covered equally by the both sides.
        '''


#placing each components i.e. text blocks and graphs
app.layout = html.Div(children=[
        html.H1(children='Nobias',
                style={
                'textAlign': 'center'
                }
        ),
        
        html.Div(children='Reach of Liberal vs Conservative Media',style={
                'textAlign': 'center'
                }
        ),
        
        html.Div([dcc.Markdown(children=loudest)]),
        
#        totalExposure graph
        dcc.Graph(
        id='totalExposure',
        figure={
            'data': [
                {'x': userStat['userID'], 'y': userStat['liberalInfluence'], 'type': 'bar', 'name': 'Liberal Media'},
                {'x': userStat['userID'], 'y': userStat['conservativeInfluence'], 'type': 'bar', 'name': 'Conservative Media'},
                {'x': userStat['userID'], 'y': userStat['totalSites'], 'type': 'bar', 'name': 'Total Sites'},
            ],
            'layout': {
                'title': 'User\'s Media Exposure'
            }
        }
    ),
        
        html.Div([dcc.Markdown(children=favorite)]),
        
#        overall fav topic graph
        dcc.Graph(
        id='mostFavoriteTopic',
        figure={
            'data': [
                    {'x': userStat['userID'], 'y': userStat['searched'], 'type': 'bar', 'name':'election2020'},
            ],
            'layout': {
                'title': 'Hottest Topic: election 2020'
            }
        }
    ),
        
        html.Div([dcc.Markdown(children=coverage)]),
        
#        
        dcc.Graph(
        id='liberal-vs-conservative',
        figure={
            'data': [
                go.Scatter(
                    x=topicStat[topicStat['userID'] == i]['conservativeCoverage'],
                    y=topicStat[topicStat['userID'] == i]['liberalCoverage'],
                    text=topicStat[topicStat['userID'] == i]['totalCoverage'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=i
                ) for i in topicStat.userID.unique()
            ],
            'layout': go.Layout(
                xaxis={'type': 'linear', 'title': 'Conservative'},
                yaxis={'title': 'Liberal'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                legend={'x': 0, 'y': 1},
                hovermode='closest'
            )
        }
    ),
            
            html.Div([dcc.Markdown(children=digging)]),
            
            dcc.Graph(id='indicator-graphic'),

    dcc.Slider(
        id='date--slider',
        min=ress['timestamp'].min(),
        max=ress['timestamp'].max(),
        value=ress['timestamp'].max(),
        marks={str(d): str(d) for d in ress['timestamp'].unique()},
        step=None
    )
])
    
@app.callback(
        Output('indicator-graphic', 'figure'),
        [Input('date--slider', 'value')])

def update_figure(date):
    filteredRess = ress[ress.timestamp == date]
    statTopics = pd.DataFrame(columns=['topic','totalCoverage','liberalCoverage','conservativeCoverage'])
    traces = []
##    for each topic calculate the influences using filteredress and add it to traces
    for topic in filteredRess.searchQueryString.unique():
        filteredRessByTopic=filteredRess[filteredRess['searchQueryString'] == topic]
        liberalInfluence = 0
        conservativeInfluence = 0
        totalSites = 0
    
        liberalOutlet = ["nytimes","pbs","bbc","npr","huffpost","cnn","politico"]
        conservativeOutlet = ["fox","wsj","bloomberg","breitbart","theblaze", "usatoday"]
        
        #compute liberal influence
        for outlet in liberalOutlet:
            liberalInfluence = liberalInfluence + filteredRessByTopic['url'].str.count(outlet).astype(bool).sum(axis=0)
        
        #compute conservative influence
        for outlet in conservativeOutlet:
            conservativeInfluence = conservativeInfluence + filteredRessByTopic['url'].str.count(outlet).astype(bool).sum(axis=0)
        
        totalSites = filteredRessByTopic['url'].count()
#        topicLiberalCov,topicConvCov,totalCov = topicCoverage(filteredRessByTopic,topic)
        statTopics = statTopics.append({'topic':topic,'totalCoverage':totalSites,'liberalCoverage':liberalInfluence,'conservativeCoverage':conservativeInfluence},ignore_index=True)
#
#    for topic in statTopics.topic.unique():
    traces.append(go.Scatter(
##        go.Scatter(
        x=statTopics['conservativeCoverage'],
        y=statTopics['liberalCoverage'],
        text=statTopics['topic'],
        mode='markers',
        opacity=0.7,
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'white'}
        },
        name='name'
        )
    )
        
    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'type': 'linear', 'title': 'Coservative Coverage'},
            yaxis={'title': 'Liberal Coverage'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }
    

if __name__ == '__main__':
    app.run_server(debug=True)