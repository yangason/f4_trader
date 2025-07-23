import dash
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from vnpy.trader.constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType
from datetime import date
import os
import sys


parent_dir = os.path.abspath(os.path.join(os.getcwd(), "."))
sys.path.append(parent_dir)
from tools.database_tools import select_target_bars

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class Data():
    def __init__(self):
        self.bar_data_dict = defaultdict(pd.DataFrame)
        self.tech_data_dict = dict()
        self.trade_data_dict = defaultdict(pd.DataFrame)

        self.end = None
        self.start = None

    def update_bar_data(self, vt_symbol: str, df: pd.DataFrame):
        self.bar_data_dict[vt_symbol] = df

    def get_bar_data(self, vt_symbol: str) -> pd.DataFrame:
        pass

    def update_tech_data(self, vt_symbol: str, metric: str, df: pd.DataFrame):
        self.tech_data_dict[vt_symbol] = {metric: df}

    def get_tech_data(self, vt_symbol: str, metric:str) -> pd.DataFrame:
        pass

    def update_trade_data(self, vt_symbol: str, df: pd.DataFrame):
        self.trade_data_dict[vt_symbol] = df

    def show_candle(self, vt_symbol: str):
        pass

    def show_volumn(self, vt_symbol: str):
        pass

    def show_tech_metric(self, vt_symbol: str, metric: str):
        pass

data = Data()    

app = dash.Dash(__name__)
app.layout = html.Div([
    # html.H1("candle图", style={'textAlign': 'center'}),
    
    # 控制面板
    html.Div([
        html.Div([
            html.Label("选择标的:", style={'marginRight': '10px', 'font-size': '16px', 'display': 'inline-block'}),
            dcc.Dropdown(
                id='select-target',
                options=[], 
                style={'width': '100%', 'height': '100%', 'fontSize': '14px', 'display': 'inline-block'}
            )
        ], style={'width': '30%', 'height': '100%','margin': '20px', 'display': 'inline-block'}), 
        html.Div([
            html.Label("选择日期范围:", style={'marginRight': '10px', 'font-size': '16px', 'display': 'inline-block'}),
            dcc.DatePickerRange(
                id='date-picker-range',
                minimum_nights=0,  # 允许选择同一天
                initial_visible_month=date.today(),
                display_format='YYYY-MM-DD',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                calendar_orientation='horizontal',
                style={'width': '100%', 'height': '100%', 'fontSize': '14px', 'display': 'inline-block'}
            )
        ], style={'width': '30%', 'height': '100%','margin': '20px', 'display': 'inline-block'}),    
    ], 
    style={'width': '100%', 'padding': '20px', 'backgroundColor': '#f8f9fa'}),
    html.Div([
        dcc.Checklist(id='tech-chart-checklist',
                      options=['Total Pnl', 'Daily Pnl', 'Drawdown'],
                      value=[],
                      inline=True
                    )
        ],
        style={
            'margin': '20px',
            'padding': '10px'
        }
    ),
    dcc.Interval(id='interval-component', interval=10000),
    dcc.Graph(id='candlestick-volumn-chart'),
    html.Div(id='tech-chart',
        children=[]
    )
    # # 导出csv
    # dcc.Store(id='annotations-store', data=[])
])

@callback(
        Output('tech-chart', 'children'),
        Input('tech-chart-checklist', 'value'),
        Input('select-target', 'value'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date'),
        Input('candlestick-volumn-chart', 'hoverData')
)
def show_tech_chart(value, vt_symbol, start_date, end_date, hover_data):
    print(f'hover_data {hover_data}')
    children = []
    symbol_tech_dict: pd.DataFrame = data.tech_data_dict.get(vt_symbol, dict())
    daily_df = symbol_tech_dict.get('daily_df', None)
    if daily_df is not None:
        if 'Total Pnl' in value:
            total_pnl = go.Figure()
            total_pnl.add_trace(go.Bar(
                x=daily_df.index,
                y=daily_df['total_pnl'],
            ))
            if hover_data is not None and 'points' in hover_data and hover_data['points']:
                time = hover_data['points'][0]['x']
                total_pnl.add_shape(
                    type="line",
                    x0=time, x1=time,
                    y0=0, y1=1,
                    xref="x", yref="paper",
                    line=dict(color="gray", width=2, dash="dot"),
                    opacity=0.8
                )
            total_pnl.update_xaxes(range=[start_date, end_date])
            total_pnl.update_layout(
                margin=dict(t=10, b=10),
                height=300,
                width=800,
            )
            children.append(dcc.Graph(figure=total_pnl, style={
                'margin': '10px',
                'padding': '0'
            }))
        if 'Daily Pnl' in value:
            net_pnl = go.Figure()
            net_pnl.add_trace(go.Bar(
                x=daily_df.index,
                y=daily_df['net_pnl'],
            ))
            if hover_data is not None and 'points' in hover_data and hover_data['points']:
                time = hover_data['points'][0]['x']
                net_pnl.add_shape(
                    type="line",
                    x0=time, x1=time,
                    y0=0, y1=1,
                    xref="x", yref="paper",
                    line=dict(color="gray", width=2, dash="dot"),
                    opacity=0.8
                )
            net_pnl.update_xaxes(range=[start_date, end_date])
            net_pnl.update_layout(
                margin=dict(t=10, b=10),
                height=300,
                width=800,
            )
            children.append(dcc.Graph(figure=net_pnl, style={
                'margin': '10px', 
                'padding': '0'
            }))
        if 'Drawdown' in value:
            drawdown = go.Figure()
            drawdown.add_trace(go.Scatter(
                x=daily_df.index,
                y=daily_df['drawdown'],
            ))
            if hover_data is not None and 'points' in hover_data and hover_data['points']:
                time = hover_data['points'][0]['x']
                drawdown.add_shape(
                    type="line",
                    x0=time, x1=time,
                    y0=0, y1=1,
                    xref="x", yref="paper",
                    line=dict(color="gray", width=2, dash="dot"),
                    opacity=0.8
                )
            drawdown.update_xaxes(range=[start_date, end_date])
            drawdown.update_layout(
                margin=dict(t=10, b=10),
                height=300,
                width=800,
            )
            children.append(dcc.Graph(figure=drawdown, style={
                'margin': '10px', 
                'padding': '0'
            }))
    return children

@callback(
    Output('candlestick-volumn-chart', 'figure'),
    Input('select-target', 'value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def select_time_range(vt_symbol, start_date, end_date):
    bar_fig = go.Figure()
    bar_df = None
    if not vt_symbol:
        return bar_fig
    elif not start_date or not end_date:
        bar_df: pd.DataFrame = data.bar_data_dict.get(vt_symbol, None)
    else:
        print(f'start date: {start_date}, end date: {end_date}, symbol: {vt_symbol}')
        bar_df = select_target_bars(vt_symbol, Interval.DAILY, start_date, end_date)

    bar_fig = draw_bar(bar_df)
    data.start = bar_df.index[0]
    data.end = bar_df.index[bar_df.index.size - 1]

    trade_df = data.trade_data_dict.get(vt_symbol, None)
    if trade_df is not None:
        for i in range(len(trade_df)):
            color = 'yellow' if trade_df['direction'].iloc[i] == Direction.LONG else 'blue'
            arrowhead = 1 if trade_df['offset'].iloc[i] == Offset.OPEN else 2
            bar_fig.add_annotation(
                x=trade_df.index[i],
                y=trade_df['price'].iloc[i],
                arrowhead=arrowhead,
                arrowcolor=color,
                arrowwidth=3,
                arrowsize=1,
                row=1,
                col=1,
                ax=0,
                ay=-40,
                text=f"price [{trade_df['price'].iloc[i]}]\n volume [{trade_df['volume'].iloc[i]}]",
                valign="top",
            )        
    return bar_fig

@callback(
    Output('select-target', 'options'),
    Input('interval-component', 'n_intervals')
)
def trigger_data_update(n_intervals):
    options = list(data.bar_data_dict.keys())
    return options

def draw_bar(bar_df: pd.DataFrame) -> go.Figure:
    bar_fig = make_subplots(row_heights=[0.75, 0.25], 
                            vertical_spacing=0.05, 
                            shared_xaxes=True,
                            rows=2, 
                            cols=1)
    if bar_df is not None:
        bar_fig.add_trace(go.Candlestick(
            name='Candle',
            x=bar_df.index,
            open=bar_df['open_price'],
            high=bar_df['high_price'],
            low=bar_df['low_price'],
            close=bar_df['close_price'],
            increasing_line_color='red',
            decreasing_line_color='green',
            increasing_fillcolor='red',
            decreasing_fillcolor='green',
        ), row=1, col=1)

        color=['blue']
        color = ['green' if close < open else 'red' 
                for close, open in zip(bar_df['close_price'], bar_df['open_price'])]
        bar_fig.add_trace(go.Bar(
            x=bar_df.index,
            y=bar_df['volume'],
            name='Volume',
            marker_color=color
        ), row=2, col=1)
        bar_fig.update_layout(
            height=600, 
            width=800,
            xaxis_rangeslider_visible = False,
            xaxis2_rangeslider=dict(
                visible=True,
                thickness=0.02,  # 减小滑块厚度
                bgcolor="lightgray"
            )
        )
    return bar_fig

# 运行应用
if __name__ == '__main__':
    app.run_server(debug=True, port=8880)
