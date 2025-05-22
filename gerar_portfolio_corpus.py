import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ativos = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "B3SA3.SA", "ABEV3.SA", "WEGE3.SA", "BBAS3.SA", "BBDC4.SA", "GGBR4.SA", "RAIZ4.SA",
    "RENT3.SA", "EQTL3.SA", "SUZB3.SA", "LREN3.SA", "ENEV3.SA", "EMBR3.SA", "HAPV3.SA", "TOTS3.SA", "CPLE6.SA", "PRIO3.SA",
    "ELET3.SA", "KLBN11.SA", "CYRE3.SA", "ASAI3.SA", "SBSP3.SA", "VBBR3.SA", "MRVE3.SA", "UGPA3.SA", "CMIG4.SA", "PETZ3.SA",
    "YDUQ3.SA", "COGN3.SA", "CRFB3.SA", "BRFS3.SA", "AMER3.SA", "ARZZ3.SA", "MULT3.SA", "ENBR3.SA", "CSAN3.SA", "SOMA3.SA",
    "ALPA4.SA", "GOAU4.SA", "IGTI11.SA", "AZUL4.SA", "CCRO3.SA", "DXCO3.SA", "MOVI3.SA", "ECOR3.SA", "CVCB3.SA", "MRFG3.SA"
]

resultado = []

def classificar_regime(dados):
    vol = dados['Close'].pct_change().rolling(window=5).std().dropna()
    if vol.empty or pd.isna(vol.iloc[-1]):
        return "Indefinido"
    if vol.iloc[-1] < 0.01:
        return "Estável"
    elif vol.iloc[-1] > 0.03:
        return "Caótico"
    else:
        return "Transição"

def avaliar_previsibilidade(dados):
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
    return round(modelo.score(X, y), 3)

for ticker in ativos:
    try:
        dados = yf.download(ticker, start="2023-01-01", interval="1d", progress=False)
        if dados.empty or dados['Close'].isna().sum() > 10:
            continue
        regime = classificar_regime(dados)
        score = avaliar_previsibilidade(dados)
        volume = round(dados['Volume'].dropna().tail(30).mean(), 2)
        if regime != "Indefinido" and score >= 0.52 and volume >= 1_000_000:
            resultado.append({
                "Ticker": ticker,
                "Regime": regime,
                "Acurácia_IA": score,
                "Volume_Médio": volume
            })
    except:
        continue

df = pd.DataFrame(resultado)
df.to_csv("portfolio_corpus_fractalis.csv", index=False)
print("✅ Portfólio gerado com sucesso.")
print(df)
