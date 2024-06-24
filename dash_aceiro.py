import pandas as pd
import plotly.express as px
import dash_table
import plotly.graph_objs as go
from dash import Dash, html, dcc, Output, Input
import requests

# Carregue os arquivos CSV
df_ocorrencias = pd.read_csv('ocorrencias_rows.csv', encoding='utf8')
df_equipamentos = pd.read_csv('equipamentos_rows.csv')
df_recursos_equipamentos = pd.read_csv('recursos_equipamentos_rows.csv')
df_materiais = pd.read_csv('materiais_rows.csv')
df_recursos_materiais = pd.read_csv('recursos_materiais_rows.csv')
df_viaturas = pd.read_csv('viaturas_rows.csv')
df_ocorrencia_viatura = pd.read_csv('ocorrencia_viatura_rows.csv')

# Converta as colunas
df_ocorrencias['data'] = pd.to_datetime(df_ocorrencias['data'])
df_ocorrencias['mes'] = df_ocorrencias['data'].dt.strftime('%B')
df_ocorrencias['area'] = df_ocorrencias['urbano_rural'].map(
    {True: 'Rural', False: 'Urbano'})


# Agrupe os dados
ocorrencias_por_mes = df_ocorrencias.groupby(
    'mes').size().reset_index(name='quantidade')
ocorrencias_por_dia = df_ocorrencias.groupby(
    df_ocorrencias['data'].dt.date).size().reset_index(name='quantidade')
ocorrencias_por_municipio = df_ocorrencias.groupby(
    'municipio').size().reset_index(name='quantidade')
ocorrencias_por_area = df_ocorrencias.groupby(
    'area').size().reset_index(name='quantidade')


meses_ordem_ingles = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
ocorrencias_por_mes['mes'] = pd.Categorical(
    ocorrencias_por_mes['mes'], categories=meses_ordem_ingles, ordered=True)
ocorrencias_por_mes = ocorrencias_por_mes.sort_values('mes')

print(ocorrencias_por_mes)

# Faça a junção dos dados
df_joined = df_recursos_equipamentos.merge(
    df_equipamentos, left_on='equipamento_id', right_on='id', how='left')
equipamentos_uso = df_joined.groupby(
    'tipo_equipamento').size().reset_index(name='quantidade')
df_joined_materiais = df_recursos_materiais.merge(
    df_materiais, left_on='materiais_id', right_on='id', how='left')
materiais_uso = df_joined_materiais.groupby(
    'tipo_material').size().reset_index(name='quantidade')
df_joined_viaturas = df_ocorrencia_viatura.merge(
    df_viaturas, left_on='viatura_id', right_on='id', how='left')
viaturas_uso = df_joined_viaturas.groupby(
    'nome').size().reset_index(name='quantidade')

dados_efetivos = {
    'Categoria': ['Bombeiros', 'Brigadistas', 'Voluntários', 'Força Nacional', 'Outros'],
    'Quantidade': [50, 25, 50, 50, 25]
}

# Inicialize o aplicativo Dash
app = Dash(__name__)
server = app.server

# Defina o layout do aplicativo
app.layout = html.Div(style={'backgroundColor': '#1e1e1e', 'color': '#FFF'}, children=[
    html.H1('Dashboard de Ocorrências', style={
            'textAlign': 'center', 'margin': '10px'}),
    html.Div([
        html.Div([
            dcc.Graph(id='grafico_ocorrencias_por_mes', figure={}),
            dcc.Graph(id='grafico_ocorrencias_por_dia', figure={}),
            dcc.Graph(id='grafico_pizza_materiais', figure={}),
            dcc.Graph(id='grafico_pizza_urbano_rural', figure={}),
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'margin': '5px'}),

        html.Div([
            dcc.Graph(id='mapa_ocorrencias', figure={}),
            dcc.Graph(id='grafico_pizza_equipamentos', figure={}),
            dcc.Graph(id='grafico_ocorrencias_por_municipio', figure={}),
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'margin': '5px'}),

        html.Div([
            html.H3('Tabela de Ocorrências', style={
                    'color': 'white', 'textAlign': 'center'}),
            dash_table.DataTable(
                id='tabela_ocorrencias',
                columns=[{"name": i, "id": i} for i in df_ocorrencias.columns],
                data=df_ocorrencias.to_dict('records'),
                style_table={'overflowX': 'auto', 'maxHeight': '380px'},
                style_cell={
                    'backgroundColor': '#1e1e1e',
                    'color': 'white',
                    'textAlign': 'left',
                    'padding': '5px'
                },
                style_header={
                    'backgroundColor': '#262626',
                    'fontWeight': 'bold'
                }
            ),
            dcc.Graph(id='grafico_quantidade_efetivos', figure={}),
            dcc.Graph(id='grafico_pizza_viaturas', figure={}),
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'margin': '5px'}),
    ])
])
# Callback para o mapa de calor das ocorrências


@app.callback(
    Output('mapa_ocorrencias', 'figure'),
    [Input('mapa_ocorrencias', 'id')]
)
def update_map(_):
    # URL do arquivo GeoJSON para os estados do Brasil
    geojson_url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'

    # Crie um mapa do Brasil com as fronteiras dos estados
    fig = px.choropleth(
        geojson=geojson_url,
        locations=['AM'],  # Lista de siglas dos estados
        featureidkey="properties.sigla",
        projection="mercator"
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False
    )

    fig.update_layout(
        title='Mapa de Ocorrências',
        geo=dict(
            bgcolor='#1e1e1e',
            lakecolor='#1e1e1e',
            landcolor='rgb(243, 243, 243)',
            subunitcolor='white'
        ),
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )

    return fig.to_dict()


# Callback para o gráfico de barras de ocorrências por mês


@app.callback(
    Output('grafico_ocorrencias_por_mes', 'figure'),
    [Input('grafico_ocorrencias_por_mes', 'id')]
)
def update_ocorrencias_por_mes_chart(_):
    # Crie o gráfico usando os dados agrupados
    fig = px.bar(ocorrencias_por_mes, x='mes', y='quantidade',
                 title='Quantidade de Ocorrências por Mês')
    # Atualize o layout do gráfico para um tema escuro
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()

# Callback para o gráfico de ocorrências por dia


@app.callback(
    Output('grafico_ocorrencias_por_dia', 'figure'),
    [Input('grafico_ocorrencias_por_dia', 'id')]
)
def update_ocorrencias_por_dia_chart(_):
    # Crie o gráfico usando os dados agrupados
    fig = px.line(ocorrencias_por_dia, x='data', y='quantidade',
                  title='Quantidade de Ocorrências por Dia')
    # Atualize o layout do gráfico para um tema escuro e habilite o zoom
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label='1M', step='month', stepmode='backward'),
                    dict(count=6, label='6M', step='month', stepmode='backward'),
                    dict(step='all')
                ])
            ),
            type='date'
        ),
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


# Callback para o gráfico de pizza dos equipamentos
@app.callback(
    Output('grafico_pizza_equipamentos', 'figure'),
    [Input('grafico_pizza_equipamentos', 'id')]
)
def update_grafico_pizza_equipamentos(_):
    fig = px.pie(equipamentos_uso, values='quantidade',
                 names='tipo_equipamento', title='Uso dos Equipamentos')
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


# Callback para o gráfico fictício 'Quantidade de Efetivos'
@app.callback(
    Output('grafico_quantidade_efetivos', 'figure'),
    [Input('grafico_quantidade_efetivos', 'id')]
)
def update_grafico_quantidade_efetivos(_):
    fig = px.bar(dados_efetivos, x='Categoria', y='Quantidade',
                 title='Quantidade de Efetivos')
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


@app.callback(
    Output('grafico_pizza_materiais', 'figure'),
    [Input('grafico_pizza_materiais', 'id')]
)
def update_grafico_pizza_materiais(_):
    fig = px.pie(materiais_uso, values='quantidade',
                 names='tipo_material', title='Uso dos Materiais')
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


# Callback para o gráfico de ocorrências por município
@app.callback(
    Output('grafico_ocorrencias_por_municipio', 'figure'),
    [Input('grafico_ocorrencias_por_municipio', 'id')]
)
def update_grafico_ocorrencias_por_municipio(_):
    fig = px.bar(ocorrencias_por_municipio, x='municipio',
                 y='quantidade', title='Ocorrências por Município')
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


# Callback para o gráfico de pizza das viaturas
@app.callback(
    Output('grafico_pizza_viaturas', 'figure'),
    [Input('grafico_pizza_viaturas', 'id')]
)
def update_grafico_pizza_viaturas(_):
    fig = px.pie(viaturas_uso, values='quantidade',
                 names='nome', title='Uso das Viaturas')
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


# Callback para o gráfico de pizza Urbano/Rural
@app.callback(
    Output('grafico_pizza_urbano_rural', 'figure'),
    [Input('grafico_pizza_urbano_rural', 'id')]
)
def update_grafico_pizza_urbano_rural(_):
    fig = px.pie(ocorrencias_por_area, values='quantidade',
                 names='area', title='Ocorrências Urbano/Rural')
    fig.update_layout(
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )
    return fig.to_dict()


# Execute o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)
