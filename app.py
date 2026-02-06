import streamlit as st
import pandas as pd
import os
import time
import io  # Necessário para criar o Excel na memória
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega a senha do arquivo .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analyze_sentiment(text):
    """Função com proteção anti-bloqueio"""
    try:
        # PAUSA ESTRATÉGICA: 5 segundos para garantir que o Google não bloqueie o Projeto Novo
        time.sleep(5) 
        
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(
            f"Analise o sentimento deste comentário: '{text}'. "
            "Responda APENAS com uma destas palavras: Positivo, Negativo ou Neutro."
        )
        return response.text.strip()
    except Exception as e:
        return f"Erro: {e}"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sentiment Analyzer Pro", page_icon="🤖")
st.title("🤖 Sentiment Analyzer AI")

# Upload do arquivo
uploaded_file = st.file_uploader("Upload seu arquivo CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("Arquivo carregado!")
    st.subheader("Prévia dos Dados")
    st.dataframe(df.head())

    st.divider()

    if st.button("Analisar Sentimentos 🚀"):
        
        # Barra de progresso para acompanhar a lentidão necessária
        progress_text = "A IA está analisando (Modo Seguro)..."
        my_bar = st.progress(0, text=progress_text)
        
        total_rows = len(df)
        results = []
        
        # Loop manual para atualizar a barra
        for index, row in df.iterrows():
            res = analyze_sentiment(row['comentario'])
            results.append(res)
            
            # Atualiza barra de progresso
            percent_complete = int(((index + 1) / total_rows) * 100)
            my_bar.progress(percent_complete, text=f"Analisando linha {index+1} de {total_rows}...")

        df['sentiment'] = results
        my_bar.empty() # Limpa a barra quando acabar
        
        st.success("Análise Completa!")
        
        st.subheader("Resultados")
        st.dataframe(df)
        
        st.bar_chart(df['sentiment'].value_counts())

        st.divider()

        # --- O MÁGICO GERADOR DE EXCEL COLORIDO ---
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # 1. Joga os dados para o Excel
            df.to_excel(writer, sheet_name='Relatorio', index=False)
            
            # 2. Pega as ferramentas de desenho
            workbook = writer.book
            worksheet = writer.sheets['Relatorio']

            # 3. Cria as tintas (Formatos)
            vermelho = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            verde = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            amarelo = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})

            # 4. Aplica a Pintura Condicional na Coluna D (Sentiment)
            # D2:D1000 cobre até 1000 linhas
            worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'Negativo', 'format': vermelho})
            worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'Positivo', 'format': verde})
            worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'Neutro', 'format': amarelo})

            # 5. Ajusta largura das colunas para ficar bonito
            worksheet.set_column('A:A', 40) # Coluna Comentário bem larga
            worksheet.set_column('B:D', 15) # Outras colunas normais

        buffer.seek(0)
        
        st.download_button(
            label="💾 Baixar Relatório Excel (.xlsx)",
            data=buffer,
            file_name="relatorio_sentimentos_pro.xlsx",
            mime="application/vnd.ms-excel",
        )