# Exemplos de Requisições - ToggleMaster Melhorado

## 🧪 Testar a Aplicação com Curl

### 1. Health Check (Fator VII - Port Binding)

```bash
curl -w "\nHTTP Status: %{http_code}\n" http://localhost:5000/health

# Resposta esperada:
# {"status":"ok"}
# HTTP Status: 200
```

---

## 2. Criar Flag (Fator XI - Logs Estruturados)

### ✅ Sucesso - Criar flag

```bash
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "new_feature", "is_enabled": false}'

# Resposta:
# {"message":"Flag 'new_feature' criada com sucesso"}

# Logs esperados:
# INFO - Criando flag: new_feature (enabled=False)
# INFO - Flag 'new_feature' criada com sucesso
```

### ❌ Erro - Campo faltando

```bash
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{}'

# Resposta:
# {"error":"O campo 'name' é obrigatório"}

# Logs esperados:
# WARNING - POST /flags: campo 'name' faltando
```

### ❌ Erro - Flag duplicada (Validação no DB)

```bash
# Primeira requisição
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "duplicate_test"}'

# Segunda requisição (mesmo nome)
curl -X POST http://localhost:5000/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "duplicate_test"}'

# Resposta:
# {"error":"A flag 'duplicate_test' já existe"}

# Logs esperados:
# WARNING - Tentativa de criar flag duplicada: duplicate_test
```

---

## 3. Listar Flags (Fator VI - Processes Stateless)

```bash
curl http://localhost:5000/flags

# Resposta:
# [
#   {"name":"feature_a","is_enabled":true},
#   {"name":"feature_b","is_enabled":false},
#   {"name":"new_feature","is_enabled":false}
# ]

# Logs esperados:
# DEBUG - Buscando todas as flags
# INFO - Retornadas 3 flags
```

---

## 4. Obter Flag Específica

### ✅ Sucesso - Flag existe

```bash
curl http://localhost:5000/flags/new_feature

# Resposta:
# {"name":"new_feature","is_enabled":false}

# Logs esperados:
# DEBUG - Buscando status da flag: new_feature
# INFO - Flag 'new_feature' encontrada: enabled=False
```

### ❌ Erro - Flag não existe

```bash
curl http://localhost:5000/flags/nonexistent

# Resposta:
# {"error":"Flag não encontrada"}

# Logs esperados:
# WARNING - Flag não encontrada: nonexistent
```

---

## 5. Atualizar Flag (Fator IX - Disposability)

### ✅ Sucesso - Atualizar para enabled

```bash
curl -X PUT http://localhost:5000/flags/new_feature \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": true}'

# Resposta:
# {"message":"Flag 'new_feature' atualizada"}

# Logs esperados:
# INFO - Atualizando flag 'new_feature' para enabled=True
# INFO - Flag 'new_feature' atualizada com sucesso
```

### ❌ Erro - Campo faltando

```bash
curl -X PUT http://localhost:5000/flags/new_feature \
  -H "Content-Type: application/json" \
  -d '{}'

# Resposta:
# {"error":"O campo 'is_enabled' (booleano) é obrigatório"}

# Logs esperados:
# WARNING - PUT /flags/new_feature: campo 'is_enabled' inválido
```

### ❌ Erro - Flag não existe

```bash
curl -X PUT http://localhost:5000/flags/nonexistent \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": true}'

# Resposta:
# {"error":"Flag não encontrada"}

# Logs esperados:
# WARNING - Tentativa de atualizar flag inexistente: nonexistent
```

---

## 6. Script de Teste Automático

### Bash Script - test_api.sh

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

echo "=========================================="
echo "1. Health Check"
echo "=========================================="
curl -w "\nHTTP %{http_code}\n" $BASE_URL/health

echo -e "\n=========================================="
echo "2. Criar 3 flags"
echo "=========================================="

curl -X POST $BASE_URL/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "dark_mode", "is_enabled": false}' | jq .

curl -X POST $BASE_URL/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "new_ui", "is_enabled": true}' | jq .

curl -X POST $BASE_URL/flags \
  -H "Content-Type: application/json" \
  -d '{"name": "beta_features", "is_enabled": false}' | jq .

echo -e "\n=========================================="
echo "3. Listar todas as flags"
echo "=========================================="
curl $BASE_URL/flags | jq .

echo -e "\n=========================================="
echo "4. Obter status individual"
echo "=========================================="
curl $BASE_URL/flags/dark_mode | jq .

echo -e "\n=========================================="
echo "5. Atualizar flag"
echo "=========================================="
curl -X PUT $BASE_URL/flags/dark_mode \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": true}' | jq .

echo -e "\n=========================================="
echo "6. Verificar atualização"
echo "=========================================="
curl $BASE_URL/flags/dark_mode | jq .

echo -e "\n=========================================="
echo "Teste concluído!"
echo "=========================================="
```

### Executar o script

```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 7. Teste de Concorrência (Fator VIII)

### Teste com Apache Bench

```bash
# Instalar ab (se necessário)
# macOS: brew install httpd
# Linux: apt-get install apache2-utils

# Teste: 100 requisições, 10 simultâneas
ab -n 100 -c 10 http://localhost:5000/health

# Saída esperada:
# Requests per second:    50.00 [#/sec] (mean)
# Time per request:       200.000 [ms] (mean)
# Concurrency Level:      10
```

### Teste com WRK (mais realista)

```bash
# Instalar wrk: https://github.com/wg/wrk

wrk -t4 -c100 -d30s http://localhost:5000/health

# Saída esperada:
# Running 30s test @ http://localhost:5000/health
#   4 threads and 100 connections
# Requests/sec:   500.00
# Avg latency:    200ms
```

---

## 8. Teste de Erro - Variáveis de Ambiente Faltando

### Terminal 1 - Remover DB_HOST

```bash
# Simular erro de configuração
unset DB_HOST

docker-compose up

# Saída esperada:
# ValueError: Variáveis obrigatórias faltando: ['DB_HOST']
```

---

## 9. Teste de Shutdown Gracioso (Fator IX)

### Terminal 1

```bash
docker-compose up
# Aplicação rodando...
```

### Terminal 2 - Enviar SIGTERM

```bash
# Obter container ID
docker ps | grep togglemaster

# Parar graciosamente
docker stop <CONTAINER_ID>

# Esperado em Terminal 1:
# Recebido sinal 15, encerrando graciosamente...
```

---

## 10. Monitorar Logs em Real-time

```bash
# Ver logs estruturados
docker-compose logs -f app

# Ver apenas erros
docker-compose logs -f app | grep ERROR

# Ver apenas warnings
docker-compose logs -f app | grep WARNING

# Ver com timestamp
docker-compose logs -f --timestamps app
```

---

## 11. Teste de Integração Completo

```bash
#!/bin/bash

# test_complete.sh
BASE_URL="http://localhost:5000"

# 1. Criar features
for feature in "feature_1" "feature_2" "feature_3"; do
  curl -s -X POST $BASE_URL/flags \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$feature\"}" > /dev/null
  echo "✓ Criada: $feature"
done

# 2. Listar
TOTAL=$(curl -s $BASE_URL/flags | jq length)
echo "✓ Total de flags: $TOTAL"

# 3. Ativar a primeira
curl -s -X PUT $BASE_URL/flags/feature_1 \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": true}' > /dev/null
echo "✓ Ativada: feature_1"

# 4. Desativar a segunda
curl -s -X PUT $BASE_URL/flags/feature_2 \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": false}' > /dev/null
echo "✓ Desativada: feature_2"

# 5. Contar ativas
ACTIVE=$(curl -s $BASE_URL/flags | jq '[.[] | select(.is_enabled == true)] | length')
echo "✓ Flags ativas: $ACTIVE"

echo "✅ Teste integrado concluído com sucesso!"
```

---

## 📋 Checklist de Testes

```
✅ Health Check
  ☐ Status 200 OK
  ☐ Response: {"status":"ok"}

✅ Criar Flag
  ☐ Status 201 Created
  ☐ Logs estruturados
  ☐ Duplicata retorna 409

✅ Listar Flags
  ☐ Status 200
  ☐ Array JSON
  ☐ Ordenado por nome

✅ Obter Flag
  ☐ Status 200 se existe
  ☐ Status 404 se não existe

✅ Atualizar Flag
  ☐ Status 200 se sucesso
  ☐ Status 404 se não existe

✅ Logs
  ☐ Timestamp presente
  ☐ Nível (INFO, WARNING, ERROR)
  ☐ Mensagem descritiva

✅ Performance
  ☐ Suporta 10+ requisições simultâneas
  ☐ Tempo de resposta < 100ms

✅ Graceful Shutdown
  ☐ SIGTERM capturado
  ☐ Mensagem de shutdown logada
```
