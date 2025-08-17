import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

class MetricsDashboard:
    """Dashboard interativo para visualização de métricas"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Configura o layout do dashboard"""
        self.app.layout = html.Div([
            html.H1("cAdvisor Metrics Dashboard", style={'textAlign': 'center'}),
            
            # Controles
            html.Div([
                html.Div([
                    html.Label("Selecionar Container:"),
                    dcc.Dropdown(
                        id='container-dropdown',
                        options=[{'label': container, 'value': container} 
                                for container in self.df['container_name'].unique()],
                        value=self.df['container_name'].unique()[0],
                        multi=True
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Período:"),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=self.df['timestamp'].min(),
                        end_date=self.df['timestamp'].max(),
                        display_format='DD/MM/YYYY'
                    )
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
            ], style={'margin': '20px'}),
            
            # Métricas principais
            html.Div([
                html.Div([
                    html.H3("CPU Usage"),
                    dcc.Graph(id='cpu-graph')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Memory Usage"),
                    dcc.Graph(id='memory-graph')
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            html.Div([
                html.Div([
                    html.H3("Network Traffic"),
                    dcc.Graph(id='network-graph')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Filesystem Usage"),
                    dcc.Graph(id='filesystem-graph')
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            # Tabela de estatísticas
            html.Div([
                html.H3("Container Statistics"),
                dash_table.DataTable(
                    id='stats-table',
                    columns=[
                        {"name": "Container", "id": "container_name"},
                        {"name": "Avg CPU", "id": "avg_cpu", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "Avg Memory (MB)", "id": "avg_memory", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "Total RX (MB)", "id": "total_rx", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "Total TX (MB)", "id": "total_tx", "type": "numeric", "format": {"specifier": ".2f"}}
                    ],
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ]
                )
            ], style={'margin': '20px'})
        ])
    
    def setup_callbacks(self):
        """Configura callbacks do dashboard"""
        
        @self.app.callback(
            [Output('cpu-graph', 'figure'),
             Output('memory-graph', 'figure'),
             Output('network-graph', 'figure'),
             Output('filesystem-graph', 'figure'),
             Output('stats-table', 'data')],
            [Input('container-dropdown', 'value'),
             Input('date-picker-range', 'start_date'),
             Input('date-picker-range', 'end_date')]
        )
        def update_dashboard(selected_containers, start_date, end_date):
            # Filtrar dados
            filtered_df = self.df[
                (self.df['container_name'].isin(selected_containers if isinstance(selected_containers, list) else [selected_containers])) &
                (self.df['timestamp'] >= start_date) &
                (self.df['timestamp'] <= end_date)
            ]
            
            # Gráfico de CPU
            cpu_fig = px.line(filtered_df, x='timestamp', y='cpu_total_usage', 
                             color='container_name', title='CPU Usage Over Time')
            
            # Gráfico de Memória
            memory_fig = px.line(filtered_df, x='timestamp', y='memory_usage_mb', 
                               color='container_name', title='Memory Usage Over Time')
            
            # Gráfico de Rede
            network_fig = go.Figure()
            for container in filtered_df['container_name'].unique():
                container_data = filtered_df[filtered_df['container_name'] == container]
                network_fig.add_trace(go.Scatter(
                    x=container_data['timestamp'], 
                    y=container_data['network_rx_mb'],
                    name=f'{container} RX',
                    line=dict(dash='solid')
                ))
                network_fig.add_trace(go.Scatter(
                    x=container_data['timestamp'], 
                    y=container_data['network_tx_mb'],
                    name=f'{container} TX',
                    line=dict(dash='dash')
                ))
            network_fig.update_layout(title='Network Traffic Over Time')
            
            # Gráfico de Sistema de Arquivos
            fs_fig = px.line(filtered_df, x='timestamp', y='filesystem_usage_gb', 
                           color='container_name', title='Filesystem Usage Over Time')
            
            # Tabela de estatísticas
            stats_data = filtered_df.groupby('container_name').agg({
                'cpu_total_usage': 'mean',
                'memory_usage_mb': 'mean',
                'network_rx_mb': 'sum',
                'network_tx_mb': 'sum'
            }).reset_index()
            
            stats_data.columns = ['container_name', 'avg_cpu', 'avg_memory', 'total_rx', 'total_tx']
            
            return cpu_fig, memory_fig, network_fig, fs_fig, stats_data.to_dict('records')
    
    def run(self, host='0.0.0.0', port=8050, debug=False):
        """Executa o dashboard"""
        self.app.run_server(host=host, port=port, debug=debug)