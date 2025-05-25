
import streamlit as st
import os
import json
import pandas as pd
import numpy as np
from diagnostico_erro import diagnosticar_erro
from validador_simetria import validar_simetria
from dados_reais import obter_serie_fechamento

st.set_page_config(layout="wide")
st.title("🧠 Corpus Fractalis — Painel com Dados Reais")

CAMINHO_MEMORIA = "./memoria"
ativos_disponiveis = [f.replace(".json", "") for f in os.listdir(CAMINHO_MEMORIA) if f.endswith(".json")]
ativo_selecionado = st.sidebar.selectbox("Selecione um ativo:", ativos_disponiveis)

ticker_yahoo = ativo_selecionado + ".SA"
serie_real = obter_serie_fechamento(ticker=ticker_yahoo, periodo='6mo')

if len(serie_real) > 20:
    simetria = validar_simetria(serie_real)
    col1, col2, col3 = st.columns(3)
    col1.metric("Hurst", simetria['hurst'])
    col2.metric("Entropia", simetria['entropia'])
    col3.metric("Classificação", simetria['classificacao'])
else:
    st.warning("Série insuficiente para análise de simetria.")
    simetria = {"classificacao": "INDEFINIDO"}

with open(os.path.join(CAMINHO_MEMORIA, f"{ativo_selecionado}.json")) as f:
    historico = json.load(f)
df = pd.DataFrame(historico)
df['data'] = pd.to_datetime(df['data'])

ultima = df.iloc[-1]
st.subheader(f"📌 Última decisão para {ativo_selecionado}")
col1, col2, col3 = st.columns(3)
with col1: st.metric("Regime", ultima['regime'])
with col2: st.metric("Decisão", ultima['decisao'])
with col3: st.metric("Resultado Real (%)", f"{ultima['resultado_real']}%")

previsto = 100
real = 100 + ultima['resultado_real']
diagnostico = diagnosticar_erro(previsto, real)
st.markdown(f"### 🩺 Diagnóstico de Erro: `{diagnostico}`")

st.subheader("📊 Pesos dos Preditores")
pesos = {k: v['peso'] for k, v in ultima['preditores'].items()}
df_pesos = pd.DataFrame.from_dict(pesos, orient='index', columns=["peso"])
st.bar_chart(df_pesos)

st.subheader("📜 Histórico completo")
st.dataframe(df[['data', 'regime', 'decisao', 'resultado_real']].sort_values(by='data', ascending=False))
