# Skyflix - Addon Stremio (modificado)
====================================

Resumo
------
Este repositório contém uma versão modificada do addon "skyflix" (Stremio). Alterei o projeto para agregar múltiplas fontes de conteúdo (web-scrapers) e expor endpoints locais compatíveis com o protocolo de add-ons do Stremio.

Principais mudanças
-------------------
- `netcine.py`:
	- Adição da lista `HOSTS` com várias fontes (netcine.icu, anroll.net, redecanais.lc, animesdrive.blog, ultracine.org, megaflix.store, top-flix.yachts, etc.).
	- Implementação de agregadores multi-fonte: busca de catálogo e agregação de streams entre hosts.
	- Fallbacks e heurísticas extras para torná-lo mais tolerante a variações de HTML entre sites.
	- Implementações originais preservadas como `_orig_*` para fallback seguro.

- `app.py`:
	- Substituído o redirecionamento anterior por endpoints Stremio mínimos:
		- GET `/manifest.json` — manifest do addon
		- POST `/catalog` — aceita body JSON com `{"query": "..."}` e retorna `{"metas": [...]}`
		- POST `/meta` — aceita `{"type":"movie","id":"skyflix:..."}` e retorna metadados
		- POST `/stream` — aceita `{"type":"movie","id":"skyflix:..."}` e retorna `{"streams":[...]}`
		- GET `/healthz` — status básico

- `test_sources.py`:
	- Script de smoke-test que consulta cada host da lista `HOSTS` com queries simples para verificar compatibilidade.

Como rodar (no VSCode terminal)
------------------------------
1) Instale dependências:

```powershell
cd "C:\Users\Asus Vivobook\Downloads\skyflix-main"
python -m pip install -r requirements.txt
```

2) Rodar o servidor FastAPI (UVicorn):

```powershell
cd "C:\Users\Asus Vivobook\Downloads\skyflix-main"
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

3) Testes rápidos
- Manifest: abrir `http://127.0.0.1:8000/manifest.json`
- Health: `http://127.0.0.1:8000/healthz`

- Catalog (exemplo com curl / HTTP client):
	POST `http://127.0.0.1:8000/catalog`
	Body JSON: `{"query":"matrix"}`

- Meta:
	POST `http://127.0.0.1:8000/meta`
	Body JSON: `{"type":"movie","id":"skyflix:<base64>"}`

- Stream:
	POST `http://127.0.0.1:8000/stream`
	Body JSON: `{"type":"movie","id":"skyflix:<base64>"}`

Testes automáticos
------------------
- Rode `test_sources.py` para obter um relatório rápido sobre quais hosts retornam resultados:

```powershell
python -u test_sources.py
```

Isso imprimirá, por host e por query, quantos itens foram retornados e uma amostra (id/title) quando houver.

Notas/limitações
----------------
- Alguns sites têm HTML e estruturas diferentes; implementei heurísticas e fallbacks nas funções de scraping, mas pode ser necessário ajustar seletores específicos se um domínio usar markup incomum.
- Para desativar/editar fontes, edite a lista `HOSTS` no arquivo `netcine.py`.
- Todas as mudanças mantêm compatibilidade com os IDs e respostas originais do addon: IDs `skyflix:` continuam funcionando.
- As mudanças são feitas com muitos `try/except` para evitar que sites offline quebrem o addon.

Próximos passos sugeridos
------------------------
- Rodar `test_sources.py` e, se houver hosts com 0 resultados ou tracebacks, eu ajusto seletores específicos por domínio.
- (Opcional) Ativar logging mais detalhado para debug de fontes.
- (Opcional) Adicionar configuração dinâmica (variáveis de ambiente) para habilitar/desabilitar hosts sem editar o código.

Changelog resumido
------------------
- Adição de suporte multi-fonte e endpoints locais. Código original preservado como fallback.

Licença
-------
Mantive os mesmos arquivos de licença presentes no repositório original (ver `LICENSE`).

Contato
-------
Se precisar de ajustes extras (polimento de seletores por domínio, logging, ou empacotamento Docker), diga e eu aplico as mudanças.
