# Validação e Testes - 12 Fatores

## 🧪 Como Testar as Melhorias Implementadas

### 1. Validação de Configuração (Fator III)

#### ✅ Com variáveis definidas

```bash
docker-compose up
# Sucesso: "Configuração validada com sucesso"
```

#### ❌ Sem variáveis (teste de falha rápida)

```bash
# Simular variáveis faltando
unset DB_HOST
python app.py
# Erro: ValueError: Variáveis obrigatórias faltando: ['DB_HOST', ...]
```

---

### 2. Structured Logging (Fator XI)

#### Checar logs estruturados

```bash
docker-compose up &
sleep 2
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "test_feature"}'
```

#### Saída esperada:

```
2026-06-21 10:30:45,123 - __main__ - INFO - Configuração validada com sucesso
2026-06-21 10:30:46,456 - __main__ - INFO - Conectando ao banco de dados
2026-06-21 10:30:46,789 - __main__ - INFO - Criando flag: test_feature (enabled=False)
2026-06-21 10:30:46,890 - __main__ - INFO - Flag 'test_feature' criada com sucesso
```

---

### 3. Graceful Shutdown (Fator IX)

#### Teste 1: SIGTERM

```bash
# Terminal 1
docker-compose up

# Terminal 2
docker-compose kill -s SIGTERM app

# Esperado em logs:
# "Recebido sinal 15, encerrando graciosamente..."
```

#### Teste 2: CTRL+C

```bash
# Pressionar CTRL+C enquanto aplicação roda
# Esperado em logs:
# "Recebido sinal 2, encerrando graciosamente..."
```

---

### 4. Concurrency (Fator VIII)

#### Teste de carga com múltiplos workers

```bash
# Usar Apache Bench ou similar
ab -n 100 -c 10 http://localhost:5000/health

# Saída esperada:
# Requests per second: ~40-50 (4 workers × ~10-12 req/worker)
```

#### Verificar workers do Gunicorn

```bash
docker-compose exec app ps aux | grep gunicorn

# Esperado:
# gunicorn [master]
# gunicorn [worker 0]
# gunicorn [worker 1]
# gunicorn [worker 2]
# gunicorn [worker 3]
```

---

### 5. Health Checks (Fator X - Dev/Prod Parity)

#### Health check do Docker

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"

# Esperado:
# NAME                   STATUS
# toggle-master-app-1    Up X minutes (healthy)
```

#### Health check manual

```bash
curl -w "\nHTTP Status: %{http_code}\n" http://localhost:5000/health

# Esperado:
# {"status":"ok"}
# HTTP Status: 200
```

---

### 6. Dev/Prod Parity (Fator X)

#### Validar arquivo .env.example

```bash
ls -la | grep env

# Esperado:
# .env.example
```

#### Criar .env local para desenvolvimento

```bash
cp .env.example .env

# Editar conforme necessário
# Depois iniciar:
docker-compose up
```

---

### 7. Admin Processes (Fator XII)

#### Executar tarefa admin

```bash
docker-compose exec app flask init-db

# Esperado em logs:
# Iniciando a inicialização da tabela 'flags'
# Tabela 'flags' inicializada com sucesso
```

---

### 8. Disposability - Timeout (Fator IX)

#### Verificar timeouts no Gunicorn

```bash
docker-compose exec app ps aux | grep gunicorn | grep -v grep

# Saída mostra configuração:
# gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 30 --graceful-timeout 5 app:app
```

---

## 📊 Checklist de Validação

```
✅ Configuração
  ☐ Validação de variáveis obrigatórias
  ☐ Arquivo .env.example existe
  ☐ Docker Compose usa variáveis corretamente

✅ Logging
  ☐ Logs têm timestamp
  ☐ Logs têm nível de severidade
  ☐ Erros incluem stack trace

✅ Shutdown
  ☐ SIGTERM é capturado
  ☐ SIGINT é capturado
  ☐ Aplicação encerra graciosamente

✅ Concurrency
  ☐ Múltiplos workers estão rodando
  ☐ Aplicação suporta requisições paralelas

✅ Health
  ☐ Endpoint /health responde com 200
  ☐ HEALTHCHECK do Docker funciona

✅ Robustez
  ☐ Retry loop para DB aguarda conexão
  ☐ Timeout definido para conexões
  ☐ Máximo de tentativas configurado
```

---

## 🚨 Testes de Falha

### Cenário 1: Banco de Dados Indisponível

```bash
# Terminal 1
docker-compose up

# Terminal 2 - parar o banco
docker-compose stop db

# Esperado:
# "Banco de dados indisponível - aguardando..."
# (retry loop continua até banco voltar)

# Terminal 2 - reiniciar banco
docker-compose start db

# Aplicação deve se recuperar automaticamente
```

### Cenário 2: Variável de Ambiente Faltando

```bash
# Remover DB_HOST do docker-compose
# Ao iniciar: erro que especifica qual variável falta
```

### Cenário 3: Flag Duplicada

```bash
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "feature_x"}'

# Segunda requisição com mesmo nome:
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "feature_x"}'

# Esperado: 409 Conflict
# Log: "Tentativa de criar flag duplicada: feature_x"
```

---

## 📈 Métricas de Produção

### Monitorar com Prometheus (exemplo)

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: "togglemaster"
    static_configs:
      - targets: ["localhost:5000"]
    metrics_path: "/metrics" # Adicionar endpoint de métricas
```

### Logs Centralizados (exemplo com ELK)

```python
# Integração futura com ElasticSearch
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
```
