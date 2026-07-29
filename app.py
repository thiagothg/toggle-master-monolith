import os
import signal
import sys
import logging
import json
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Validar variáveis de ambiente obrigatórias
def validate_config():
    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Variáveis obrigatórias faltando: {missing}")
        raise ValueError(f"Variáveis obrigatórias faltando: {missing}")
    logger.info("Configuração validada com sucesso")

validate_config()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.debug("Conexão com banco de dados estabelecida")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Erro de conexão ao banco de dados: {e}", exc_info=True)
        raise

def init_db():
    logger.info("Iniciando a inicialização da tabela 'flags'")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                is_enabled BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Tabela 'flags' inicializada com sucesso")
    except psycopg2.OperationalError as e:
        logger.error(f"Erro de conexão ao inicializar banco de dados: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Erro inesperado durante inicialização do DB: {e}", exc_info=True)
        raise

@app.cli.command("init-db")
def init_db_command():
    init_db()

# Graceful shutdown handlers (Fator IX)
def graceful_shutdown(signum, frame):
    logger.info(f"Recebido sinal {signum}, encerrando graciosamente...")
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)

@app.route('/health', methods=['GET'])
def health_check():
    logger.debug("Health check solicitado")
    return jsonify({"status": "ok"}), 200

@app.route('/flags', methods=['POST'])
def create_flag():
    data = request.get_json()
    if not data or 'name' not in data:
        logger.warning("POST /flags: campo 'name' faltando")
        return jsonify({"error": "O campo 'name' é obrigatório"}), 400
    
    name = data['name']
    is_enabled = data.get('is_enabled', False)
    
    logger.info(f"Criando flag: {name} (enabled={is_enabled})")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO flags (name, is_enabled) VALUES (%s, %s)", (name, is_enabled))
        conn.commit()
        logger.info(f"Flag '{name}' criada com sucesso")
    except psycopg2.IntegrityError:
        logger.warning(f"Tentativa de criar flag duplicada: {name}")
        return jsonify({"error": f"A flag '{name}' já existe"}), 409
    except Exception as e:
        logger.error(f"Erro ao criar flag '{name}': {e}", exc_info=True)
        return jsonify({"error": "Erro interno no servidor ao criar a flag", "details": str(e)}), 500
    finally:
        if 'cur' in locals() and not cur.closed:
            cur.close()
        if 'conn' in locals() and not conn.closed:
            conn.close()
            
    return jsonify({"message": f"Flag '{name}' criada com sucesso"}), 201

@app.route('/flags', methods=['GET'])
def get_flags():
    logger.debug("Buscando todas as flags")
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT name, is_enabled FROM flags ORDER BY name")
        flags = cur.fetchall()
        logger.info(f"Retornadas {len(flags)} flags")
    except Exception as e:
        logger.error(f"Erro ao buscar flags: {e}", exc_info=True)
        return jsonify({"error": "Erro interno no servidor ao buscar as flags", "details": str(e)}), 500
    finally:
        if 'cur' in locals() and not cur.closed:
            cur.close()
        if 'conn' in locals() and not conn.closed:
            conn.close()

    return jsonify(flags), 200

@app.route('/flags/<string:name>', methods=['GET'])
def get_flag_status(name):
    logger.debug(f"Buscando status da flag: {name}")
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT name, is_enabled FROM flags WHERE name = %s", (name,))
        flag = cur.fetchone()
    except Exception as e:
        logger.error(f"Erro ao buscar flag '{name}': {e}", exc_info=True)
        return jsonify({"error": "Erro interno no servidor ao buscar a flag", "details": str(e)}), 500
    finally:
        if 'cur' in locals() and not cur.closed:
            cur.close()
        if 'conn' in locals() and not conn.closed:
            conn.close()
    
    if flag:
        logger.info(f"Flag '{name}' encontrada: enabled={flag['is_enabled']}")
        return jsonify(flag), 200
    
    logger.warning(f"Flag não encontrada: {name}")
    return jsonify({"error": "Flag não encontrada"}), 404

@app.route('/flags/<string:name>', methods=['PUT'])
def update_flag(name):
    data = request.get_json()
    if data is None or 'is_enabled' not in data or not isinstance(data['is_enabled'], bool):
        logger.warning(f"PUT /flags/{name}: campo 'is_enabled' inválido")
        return jsonify({"error": "O campo 'is_enabled' (booleano) é obrigatório"}), 400
        
    is_enabled = data['is_enabled']
    logger.info(f"Atualizando flag '{name}' para enabled={is_enabled}")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE flags SET is_enabled = %s WHERE name = %s", (is_enabled, name))
        
        if cur.rowcount == 0:
            logger.warning(f"Tentativa de atualizar flag inexistente: {name}")
            return jsonify({"error": "Flag não encontrada"}), 404
            
        conn.commit()
        logger.info(f"Flag '{name}' atualizada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao atualizar flag '{name}': {e}", exc_info=True)
        return jsonify({"error": "Erro interno no servidor ao atualizar a flag", "details": str(e)}), 500
    finally:
        if 'cur' in locals() and not cur.closed:
            cur.close()
        if 'conn' in locals() and not conn.closed:
            conn.close()
    
    return jsonify({"message": f"Flag '{name}' atualizada"}), 200

if __name__ == '__main__':
    logger.info("Iniciando aplicação ToggleMaster")
    app.run(host='0.0.0.0', port=5000)
