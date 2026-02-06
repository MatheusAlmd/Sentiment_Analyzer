 🤖 Analisador de Sentimentos com IA

Fiz esse projeto para estudar integração de Python com APIs de Inteligência Artificial. É uma ferramenta web simples onde você sobe uma planilha de comentários e a IA diz se o cliente está feliz, bravo ou neutro.

Usei o **Google Gemini** (versão Flash) porque é rápido e tem um plano gratuito bom para estudos.

## 🚀 O que o projeto faz?
- **Upload de CSV:** Aceita arquivos com lista de comentários.
- **Análise Inteligente:** Lê cada linha e classifica como "Positivo", "Negativo" ou "Neutro".
- **Modo Seguro (Anti-Bloqueio):** Implementei um *timer* de 5 segundos entre cada análise para respeitar os limites da API gratuita do Google e não dar erro 429.
- **Excel Colorido:** No final, ele gera um relatório `.xlsx` formatado (Verde = Bom, Vermelho = Ruim) pronto para baixar.

## 🛠️ Tecnologias usadas
- Python
- Streamlit (para a interface web)
- Google Gemini API
- Pandas & XlsxWriter (para tratar os dados e gerar o Excel)

## 📦 Como rodar na sua máquina

1. Clone o repositório:
```bash
git clone [https://github.com/MatheusAlmd/Sentiment_Analyzer.git](https://github.com/MatheusAlmd/Sentiment_Analyzer.git)
