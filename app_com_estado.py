import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
import os
import matplotlib.pyplot as plt

# Caminho do arquivo de estado
ARQUIVO_ESTADO = 'estado_fractalis.json'

# Cria arquivo de estado se não existir
if not os.path.exists(ARQUIVO_ESTADO):
    with open(ARQUIVO_ESTADO, 'w') as f:
        json.dump({}, f)

# Funções de utilidade
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
    try:
        if 'Close' not in dados.columns or len(dados['Close'].dropna()) < 10:
            return "Indefinido"
        vol = dados['Close'].pct_change().rolling(window=5).std().dropna()
        if vol.empty or pd.isna(vol.iloc[-1]):
            return "Indefinido"
        if vol.iloc[-1] < 0.01:
            return "Estável"
        elif vol.iloc[-1] > 0.03:
            return "Caótico"
        else:
            return "Transição"
    except:
        return "Indefinido"

def previsao_random_forest(dados):
    try:
        df = dados[['Close']].copy()
        df['Retorno'] = df['Close'].pct_change()
        df['Target'] = (df['Retorno'].shift(-1) > 0).astype(int)
        df.dropna(inplace=True)
        if df.shape[0] < 20 or df['Target'].nunique() < 2:
            return "Indefinido"
        X = df[['Close']]
        y = df['Target']
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X, y)
        X_pred = X.tail(1)
        if X_pred.isnull().values.any() or X_pred.shape[0] == 0:
            return "Indefinido"
        previsao = modelo.predict(X_pred)
        return "COMPRAR" if previsao[0] == 1 else "VENDER"
    except:
        return "Indefinido"

def plotar_grafico_colorido(dados):
    dados['Volatilidade'] = dados['Close'].pct_change().rolling(window=5).std()

    def regime_local(v):
        if pd.isna(v):
            return "Indefinido"
        elif v < 0.01:
            return "Estável"
        elif v > 0.03:
            return "Caótico"
        else:
            return "Transição"

    dados['Regime'] = dados['Volatilidade'].apply(regime_local)

    cor_regime = {
        "Estável": "green",
        "Transição": "orange",
        "Caótico": "red",
        "Indefinido": "gray"
    }

    fig, ax = plt.subplots(figsize=(10, 4))
    regimes_unicos = dados['Regime'].unique()

    for regime in regimes_unicos:
        segmento = dados[dados['Regime'] == regime]
        ax.plot(segmento.index, segmento['Close'], color=cor_regime.get(regime, 'gray'), label=regime)

    ax.set_title("📈 Tendência com Regimes Fractais")
    ax.set_ylabel("Preço de Fechamento")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

# Interface do app
st.title("📊 Corpus Fractalis – Inteligência Fractal de Mercado")

ativo = st.text_input("Digite o código do ativo (ex: WEGE3.SA)", "WEGE3.SA")

if st.button("Executar Análise"):
    with st.spinner("🔎 Consultando dados do Yahoo Finance..."):
        try:
            dados = yf.download(ativo, start="2023-01-01", interval="1d")
        except Exception as e:
            st.error("❌ Erro ao obter dados.")
            dados = pd.DataFrame()

    if dados.empty or 'Close' not in dados.columns:
        st.error("❌ Dados indisponíveis ou código inválido.")
    else:
        regime = classificar_regime(dados)

        st.subheader("📈 Gráfico de Tendência por Regime")
        plotar_grafico_colorido(dados)

        preco_atual = round(dados['Close'].dropna().iloc[-1], 2)
        data_hoje = datetime.today().strftime('%Y-%m-%d')
        estado = carregar_estado()
        registro = estado.get(ativo, {})
        posicao = registro.get("posição", "Fechada")
        nova_decisao = None

        if regime == "Estável":
            decisao = previsao_random_forest(dados)
            if decisao == "Indefinido":
                st.warning("⚠️ IA não conseguiu prever — dados insuficientes.")
            elif posicao == "Aberta" and registro.get("última_decisão") == decisao:
                st.info(f"✅ Recomendação mantida: {decisao}")
            elif posicao == "Aberta" and decisao == "VENDER":
                nova_decisao = "FECHAR"
                st.warning("🔄 Reversão: FECHAR posição")
                posicao = "Fechada"
            else:
                nova_decisao = decisao
                st.success(f"📌 Nova recomendação: {decisao}")
                posicao = "Aberta"
        elif regime == "Indefinido":
            st.warning("⚠️ Regime não pôde ser determinado.")
        else:
            st.warning(f"⚠️ Regime atual: {regime} — IA suspensa")

        estado[ativo] = {
            "última_data": str(data_hoje),
            "último_regime": str(regime),
            "última_decisão": str(nova_decisao or registro.get("última_decisão", "N/A")),
            "último_preço": float(preco_atual),
            "posição": str(posicao)
        }

        salvar_estado(estado)

        st.subheader("📘 Memória Tática do Ativo")
        st.json(estado[ativo])
