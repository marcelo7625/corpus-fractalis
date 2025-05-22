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

        # Mostra o gráfico após garantir que os dados existem
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
