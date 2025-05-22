import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import json
from datetime import datetime

# Lista inicial de ações da B3
ativos = [
    "WEGE3.SA", "VALE3.SA", "PETR4.SA", "ITUB4.SA", "B3SA3.SA",
    "BBAS3.SA", "RENT3.SA", "GGBR4.SA", "BRFS3.SA", "EQTL3.SA"
]

# Lista final
watchlist = []

# Classificação de regime
def classificar_regime_geral(dados):
    try:
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

# Avaliação da IA
def avaliar_previsibilidade(dados):
    try:
        df = dados[['Close']].copy()
        df['Retorno'] = df['Close'].pct_change()
        df['Target'] = (df['Retorno'].shift(-1) > 0).astype(int)
        df.dropna(inplace=True)
        if df.shape[0] < 50 or df['Target'].nunique() < 2:
            return 0
        X = df[['Close']]
        y = df['Target']
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X, y)
        score = modelo.score(X, y)
        return round(score, 3)
    except:
        return 0

# Coleta e análise
for ativo in ativos:
    try:
        dados = yf.download(ativo, start="2023-01-01", interval="1d", progress=False)
        if dados.empty or dados['Close'].isna().sum() > 10:
            status = "Inválido ou Sem Dados"
        else:
            regime = classificar_regime_geral(dados)
            score = avaliar_previsibilidade(dados)
            volume_medio = round(dados['Volume'].dropna().tail(30).mean(), 2)

            if volume_medio < 1000000:
                status = "Ilíquido"
            elif score < 0.52:
                status = "Sinal fraco"
            elif regime == "Indefinido":
                status = "Ruído / Volatilidade baixa"
            else:
                status = "Operável"

            watchlist.append({
                "ticker": ativo,
                "regime_atual": regime,
                "acuracia_IA": score,
                "volume_medio": volume_medio,
                "status": status
            })
    except:
        watchlist.append({
            "ticker": ativo,
            "regime_atual": "Erro",
            "acuracia_IA": 0,
            "volume_medio": 0,
            "status": "Falha ao processar"
        })

# Exporta para arquivo JSON e CSV
with open("watchlist.json", "w") as f:
    json.dump(watchlist, f, indent=4)

pd.DataFrame(watchlist).to_csv("watchlist.csv", index=False)
print("✅ Watchlist gerada com sucesso!")
