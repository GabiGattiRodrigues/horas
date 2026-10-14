# Horas · quanto prometer de prazo de entrega

App em Streamlit que calibra a promessa de prazo de entrega pedido a pedido, com regressão quantílica em boosting (LightGBM), testada fora da amostra. Tem gráfico de controle pra monitorar e o desenho do teste A/B que mede o efeito na conversão.

## Como abrir

No Windows, é só dar dois cliques no `rodar.bat`. Ele cria o ambiente, instala as bibliotecas e abre o app no navegador. Os resultados do modelo já ficam na pasta `artifacts/`, então o app abre sem precisar da base.

Pra refazer tudo do zero, apague a pasta `artifacts/` e rode o `rodar.bat` de novo. Ele baixa a base da Olist, se faltar, e roda `scripts/gerar_artefatos.py`.

Na mão:

```
pip install -r requirements.txt -r requirements-notebook.txt
python scripts/gerar_artefatos.py   # só se quiser refazer os resultados (precisa dos CSVs em data/)
streamlit run app.py
```

## O que tem aqui

- `app.py` e `paginas/`: o app, com as abas O caso, Diagnóstico, Calibração, Simulador, Pedido a pedido, Monitoramento, Teste de conversão e Como funciona e glossário
- `horas_promessa_de_entrega.ipynb`: a análise completa, passo a passo
- `scripts/gerar_artefatos.py`: roda as funções do notebook, refaz os backtests e salva em `artifacts/` tudo que o app lê. Nenhum número do app é digitado à mão
- `artifacts/`: resultados, modelos de agosto/2018 (P85, P92 e P96), árvores, pedidos de exemplo e referências do simulador
- `site/`: versão em página estática do case

## Principais resultados (jan a ago/2018, fora da amostra)

- Com a mesma taxa no prazo da promessa atual (~91%), o LightGBM quantílico promete cerca de 1 dia a menos na média
- O ganho maior está por estado: SP e MG recebem 2 dias a menos, RJ, BA e Nordeste recebem promessa mais longa, e a diferença de pontualidade entre estados cai 54%
- Atraso de 8+ dias leva 79% das notas pra 1 ou 2. Chegar muito antes do prometido não melhora a nota

## Publicar no Streamlit Cloud

Apontar pro arquivo `app.py`. O `requirements.txt` só tem o que o app precisa.

Dados: Olist (CC BY-NC-SA 4.0), os CSVs não ficam no repositório. Pintura: *Horae Serenae*, Edward John Poynter (1894), domínio público.

---

# Horas · how long should a delivery promise be

Streamlit app that calibrates the delivery promise order by order, with boosted quantile regression (LightGBM), tested out of sample, plus a control chart for monitoring and the A/B test design that measures the effect on conversion. The app has a PT/EN switch.
