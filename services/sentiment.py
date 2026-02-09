import os
import json
import time
import random

from dotenv import load_dotenv
import google.generativeai as genai


# Carrego as variáveis de ambiente aqui pra não sujar o app.py
# Assim a parte da interface fica mais limpa
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def analyze_batch(
    comments: list[str],
    model_name: str = "models/gemini-2.5-flash",
    max_retries: int = 5
) -> list[str]:
    """
    Envia vários comentários de uma vez para a API (lote).
    Retorna uma lista com: Positivo | Negativo | Neutro
    A ordem de saída é a mesma da entrada.
    """

    model = genai.GenerativeModel(model_name)

    # Coloco um id em cada comentário pra conseguir reorganizar depois
    payload = [{"id": i, "text": c} for i, c in enumerate(comments)]

    # Tento ser o mais explícito possível pra IA não inventar moda
    # Mesmo assim, ela às vezes desobedece (por isso o try/except depois)
    prompt = (
        "You are a sentiment classifier.\n"
        "Classify each item as exactly one of: Positivo, Negativo, Neutro.\n"
        "Return ONLY valid JSON. Do not add explanations.\n"
        "JSON schema:\n"
        "{\n"
        '  "results": [\n'
        '    {"id": 0, "sentiment": "Positivo" | "Negativo" | "Neutro"}\n'
        "  ]\n"
        "}\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    # Loop de tentativas pra lidar com erro 429 / quota / rate limit
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt)

            # A resposta vem como texto, então preciso tratar antes
            raw = (response.text or "").strip()

            # Às vezes a IA manda ```json ... ``` mesmo eu pedindo pra não mandar
            # Isso quebra o json.loads, então removo na mão
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.replace("json", "", 1).strip()

            # Se vier vazio, não adianta tentar converter
            if not raw:
                raise ValueError("Resposta vazia da IA")

            data = json.loads(raw)
            results = data.get("results", [])

            # Organizo por id pra garantir a ordem correta
            by_id = {}
            for r in results:
                if "id" in r and "sentiment" in r:
                    by_id[int(r["id"])] = str(r["sentiment"]).strip()

            # Se a IA devolver menos itens do que mandei, considero erro
            if len(by_id) != len(comments):
                raise ValueError(
                    f"Tamanho do lote incorreto. Esperado {len(comments)}, recebido {len(by_id)}"
                )

            # Retorno na ordem original
            return [by_id[i] for i in range(len(comments))]

        except Exception as e:
            msg = str(e).lower()

            # Esses erros normalmente indicam que dá pra tentar de novo
            retryable = (
                "429" in msg
                or "quota" in msg
                or "rate" in msg
                or "resource_exhausted" in msg
            )

            # Se não for erro recuperável ou acabou as tentativas, estoura
            if (not retryable) or (attempt == max_retries):
                raise

            # Backoff exponencial pra não ficar batendo na API igual maluco
            sleep_time = (2 ** attempt) + random.uniform(0.2, 0.8)
            time.sleep(sleep_time)

    # Tecnicamente não deveria chegar aqui
    raise RuntimeError("Erro inesperado no loop de tentativas")


def analyze_batch_safe(comments: list[str]) -> list[str]:
    """
    Wrapper de segurança.
    A interface nunca quebra por causa da API.
    Se der erro, marco o lote inteiro como erro e sigo o jogo.
    """
    try:
        return analyze_batch(comments)
    except Exception as e:
        # Prefiro devolver erro no resultado do que quebrar o app todo
        return [f"Erro: {e}"] * len(comments)
