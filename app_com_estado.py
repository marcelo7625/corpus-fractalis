import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
import os

ARQUIVO_ESTADO = 'estado_fractalis.json'

# Garantir que o arquivo existe na primeira execução
if not os.path.exists(ARQUIVO_ESTADO):
    with open(ARQUIVO_ESTADO, 'w') as f:
        json.dump({}, f)

def carregar_estado():
    try:
        with open(ARQUIVO_ESTADO, 'r') as f:
            return json.load(f)
    except:
        return {}

def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, 'w') as f:
        json.dump(estado, f, indent=4)

def classificar_regime(dados):
    if 'Close' not in dados.columns or len(dados['Close'].dropna()) < 10:
        return "Indefinido"

    volatilidade = dados['Close'].pct_change().rolling(window=5).std().dropna()
    if len(volatilidade) == 0:
        return "Indefinido"

    ultimo_valor = volatilidade.iloc[-1]
    if pd.isna(ultimo_valor):
        return "Indefinido"

    if ultimo_valor < 0.01:
        return "Estável"
    elif ultimo_valor > 0.03:
        return "Caótico"
    else:
        return "Transição"

def previsao_random_forest(dados):
    df = dados[['Close']].copy()
    df['Retorno'] = df['Close'].pct_change()
    df['Target'] = (df['Retorno'].shift(-1) > 0).astype(int)
    df.dropna(inplace=True)

    if len(df) < 10:
        return "Indefinido"

    X = df[['Close']]
    y = df['Target']

    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    previsao = modelo.predict(X.tail(1))
    return "COMPRAR" if previsao[0] == 1 else "VENDER"

st.title("📊 Corpus Fractalis – Inteligência Fractal de Mercado")

ativo = st.text_input("Digite o código do ativo (ex: WEGE3.SA)", "WEGE3.SA")

if st.button("Executar Análise"):
    with st.spinner("🔎 Carregando dados..."):
        dados = yf.download(ativo, period="6mo", interval="1d")

    if dados.empty or 'Close' not in dados.columns:
        st.error("❌ Dados indisponíveis ou código inválido.")
    else:
        regime = classificar_regime(dados)
        preco_atual = round(dados['Close'].dropna().iloc[-1], 2)
        data_hoje = datetime.today().strftime('%Y-%m-%d')

        estado = carregar_estado()
        registro = estado.get(ativo, {})
        posicao = registro.get("posição", "Fechada")
        nova_decisao = None

        if regime == "Estável":
            decisao = previsao_random_forest(dados)

            if decisao == "Indefinido":
                st.warning("⚠️ Dados insuficientes para prever")
            elif posicao == "Aberta" and registro.get("última_decisão") == decisao:
                st.info(f"✅ Recomendação mantida: {decisao} (posição já aberta)")
            elif posicao == "Aberta" and decisao == "VENDER":
                nova_decisao = "FECHAR"
                st.warning("🔄 Reversão: Recomendação de FECHAR posição")
                posicao = "Fechada"
            else:
                nova_decisao = decisao
                st.success(f"📌 Nova recomendação: {decisao}")
                posicao = "Aberta"
        elif regime == "Indefinido":
            st.warning("⚠️ Regime não pôde ser determinado")
        else:
            st.warning(f"⚠️ Regime atual: {regime} – IA suspensa")

        estado[ativo] = {
            "última_data": data_hoje,
            "último_regime": regime,
            "última_decisão": nova_decisao or registro.get("última_decisão", "N/A"),
            "último_preço": preco_atual,
            "posição": posicao
        }

        salvar_estado(estado)

        st.subheader("📘 Memória Tática do Ativo")
        st.json(estado[ativo])
