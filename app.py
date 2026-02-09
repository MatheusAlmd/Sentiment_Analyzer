import streamlit as st
import pandas as pd
import io

from utils.files import read_csv_smart, require_column
from utils.batching import chunk_list
from services.sentiment import analyze_batch_safe


# Config básica do app (nome + ícone)
st.set_page_config(page_title="Sentiment Analyzer Pro", page_icon="🤖")
st.title("🤖 Sentiment Analyzer AI")

# Upload do CSV (só aceito csv pra não dar dor de cabeça)
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Garanto que o ponteiro do arquivo tá no começo
        uploaded_file.seek(0)

        # Leitura "smart" (tenta descobrir se é , ou ;)
        df = read_csv_smart(uploaded_file)

        # Só pra pessoa ver se o arquivo veio certo
        st.subheader("Data preview")
        st.dataframe(df)

    except Exception as e:
        # Se o CSV estiver zoado, paro aqui com uma mensagem clara
        st.error("❌ Could not read this file.")
        st.warning("The CSV might be malformed. See error below:")
        st.info(f"Error: {e}")
        st.info("Tip: Open in Excel and save again as CSV (comma-separated).")
        st.stop()

    st.divider()

    # Só começo a gastar API quando clicar no botão
    if st.button("Analyze Sentiments 🚀"):
        # Esse projeto depende da coluna 'comentario'
        require_column(df, "comentario")

        # Barra de progresso pra não parecer que travou
        progress_text = "Analyzing (Batch + Retry)..."
        bar = st.progress(0, text=progress_text)

        # Transformo a coluna em lista (fica mais fácil pra trabalhar com lotes)
        comments = df["comentario"].astype(str).tolist()
        total = len(comments)

        # Começo baixo pra evitar 429 (se estiver tranquilo, dá pra aumentar depois)
        CHUNK_SIZE = 10

        results: list[str] = []
        processed = 0

        # Aqui eu faço em lotes pra não mandar 1 request por linha (isso explode quota)
        for batch in chunk_list(comments, CHUNK_SIZE):
            # Essa função já tenta de novo se der 429 e devolve "Erro: ..." se falhar
            batch_labels = analyze_batch_safe(batch)
            results.extend(batch_labels)

            # Atualizo progresso
            processed += len(batch)
            percent = int((processed / total) * 100)
            bar.progress(percent, text=f"Analyzing {processed} of {total}...")

        # Coloco o resultado de volta no dataframe
        df["sentiment"] = results
        bar.empty()

        st.success("Analysis complete!")
        st.subheader("Results")
        st.dataframe(df)

        # Gráfico simples só pra ficar visual
        st.bar_chart(df["sentiment"].value_counts())

        st.divider()

        # ===== Exporta Excel bonitinho (com cores) =====
        buffer = io.BytesIO()

        # Eu gero o arquivo em memória pra depois o botão baixar
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Report", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Report"]

            # Cores pra destacar o sentimento no Excel
            red = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
            green = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
            yellow = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})

            # A coluna D é onde fica "sentiment" (D2:D1000 cobre bastante linha)
            worksheet.conditional_format(
                "D2:D1000",
                {"type": "text", "criteria": "containing", "value": "Negativo", "format": red},
            )
            worksheet.conditional_format(
                "D2:D1000",
                {"type": "text", "criteria": "containing", "value": "Positivo", "format": green},
            )
            worksheet.conditional_format(
                "D2:D1000",
                {"type": "text", "criteria": "containing", "value": "Neutro", "format": yellow},
            )

            # Dou uma ajustada na largura pra não ficar tudo espremido
            worksheet.set_column("A:A", 40)  # comentario
            worksheet.set_column("B:D", 15)  # outras colunas

        # Volto o ponteiro pro começo antes de mandar pro botão
        buffer.seek(0)

        st.download_button(
            label="💾 Download arquivo excel",
            data=buffer,
            file_name="sentiment_report.xlsx",
            mime="application/vnd.ms-excel",
        )
