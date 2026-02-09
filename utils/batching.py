def chunk_list(items: list[str], chunk_size: int):
    # Gerador simples pra eu não criar uma lista gigante na memória de uma vez

    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]
