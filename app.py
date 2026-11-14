import os
import math
import time
from collections import defaultdict
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import io
from functools import wraps
from flask import Flask, jsonify, request, Response, render_template, session

app = Flask(__name__)

# 1. Configurações e Variáveis de Ambiente Obrigatórias
DATABASE_URL = os.environ.get('DATABASE_URL')
SENHA_SISTEMA = os.environ.get('SENHA_SISTEMA')
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SENHA_SISTEMA:
    raise RuntimeError("ERRO DE SEGURANÇA: A variável SENHA_SISTEMA não foi configurada.")

if not SECRET_KEY:
    raise RuntimeError("ERRO DE SEGURANÇA: A variável SECRET_KEY não foi configurada.")

app.secret_key = SECRET_KEY

# Configuração rigorosa de Cookies de Sessão (HTTPS obrigatório em produção via Render)
session_secure_env = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=session_secure_env
)

TOTAL_POLTRONAS = 46
VALOR_PADRAO = 180.00

# Controle leve e nativo de tentativas de login (Anti-Brute Force com purga exata de memória)
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_WINDOW = 300  # 5 minutos em segundos
MAX_STORED_IPS = 1000 # Limite máximo de chaves no dicionário para evitar consumo excessivo de RAM

def clean_old_attempts(now):
    """Remove IPs cujos registros expiraram completamente e remove apenas o excedente exato se passar do teto."""
    expired_ips = []
    for ip, timestamps in login_attempts.items():
        valid_timestamps = [t for t in timestamps if now - t < LOCKOUT_WINDOW]
        if valid_timestamps:
            login_attempts[ip] = valid_timestamps
        else:
            expired_ips.append(ip)
    
    for ip in expired_ips:
        del login_attempts[ip]

    # Se o dicionário ultrapassar o limite, remove estritamente a quantidade necessária
    if len(login_attempts) > MAX_STORED_IPS:
        sorted_ips = sorted(
            login_attempts.keys(),
            key=lambda k: login_attempts[k][-1] if login_attempts[k] else 0
        )
        quantidade_remover = len(login_attempts) - MAX_STORED_IPS
        for ip in sorted_ips[:quantidade_remover]:
            del login_attempts[ip]

def is_rate_limited(ip):
    now = time.time()
    clean_old_attempts(now)
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < LOCKOUT_WINDOW]
    return len(login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS

def record_failed_login(ip):
    now = time.time()
    clean_old_attempts(now)
    login_attempts[ip].append(now)

def get_db():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn, True
    else:
        conn = sqlite3.connect('excursao.db')
        conn.row_factory = sqlite3.Row
        return conn, False

def init_db():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poltronas (
                numero INTEGER PRIMARY KEY,
                passageiro TEXT DEFAULT '',
                telefone TEXT DEFAULT '',
                documento TEXT DEFAULT '',
                valor_total REAL DEFAULT 180.00,
                valor_pago REAL DEFAULT 0.00
            )
        ''')

        cursor.execute('SELECT COUNT(*) AS total FROM poltronas')
        row = cursor.fetchone()
        contagem = row['total'] if is_pg else row[0]

        if contagem == 0:
            placeholder = '%s' if is_pg else '?'
            for num in range(1, TOTAL_POLTRONAS + 1):
                cursor.execute(f'''
                    INSERT INTO poltronas (numero, valor_total) VALUES ({placeholder}, {placeholder})
                ''', (num, VALOR_PADRAO))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('autenticado'):
            return jsonify({'erro': 'Acesso não autorizado. Faça login primeiro.'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Função de sanitização avançada contra CSV Injection
def sanitize_csv_field(val):
    if val is None:
        return ''
    val_str = str(val)
    stripped_val = val_str.lstrip()
    if stripped_val and stripped_val[0] in ('=', '+', '-', '@', '\t', '\r', '\n'):
        return "'" + val_str
    return val_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    client_ip = request.remote_addr or 'unknown'
    
    if is_rate_limited(client_ip):
        return jsonify({'erro': 'Muitas tentativas incorretas. Tente novamente em alguns minutos.'}), 429

    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({'erro': 'Formato JSON inválido.'}), 400
        
    if dados.get('senha') == SENHA_SISTEMA:
        # Limpa o histórico de falhas do IP e reseta a sessão completamente
        if client_ip in login_attempts:
            del login_attempts[client_ip]
        session.clear()
        session['autenticado'] = True
        return jsonify({'status': 'ok'}), 200
    
    record_failed_login(client_ip)
    return jsonify({'erro': 'Senha inválida'}), 401

@app.route('/api/status-auth', methods=['GET'])
def status_auth():
    return jsonify({'autenticado': bool(session.get('autenticado'))}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'desconectado'}), 200

@app.route('/api/poltronas', methods=['GET'])
@login_required
def listar_poltronas():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM poltronas ORDER BY numero ASC')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    resultado = []
    for r in rows:
        item = dict(r)
        item['valor_restante'] = max(0.0, float(item['valor_total']) - float(item['valor_pago']))

        if not item['passageiro'].strip():
            item['status'] = 'livre'
        elif float(item['valor_pago']) >= float(item['valor_total']) and float(item['valor_total']) > 0:
            item['status'] = 'pago'
        else:
            item['status'] = 'parcial'

        resultado.append(item)

    return jsonify(resultado), 200

@app.route('/api/poltronas/<int:numero>', methods=['PUT'])
@login_required
def atualizar_poltrona(numero):
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({'erro': 'Payload JSON inválido ou ausente.'}), 400

    passageiro_raw = dados.get('passageiro', '')
    telefone_raw = dados.get('telefone', '')
    documento_raw = dados.get('documento', '')

    if not isinstance(passageiro_raw, str) or not isinstance(telefone_raw, str) or not isinstance(documento_raw, str):
        return jsonify({'erro': 'Os campos de texto devem ser strings válidas.'}), 400

    passageiro = passageiro_raw.strip()
    telefone = telefone_raw.strip()
    documento = documento_raw.strip()

    if not passageiro:
        return jsonify({'erro': 'O nome do passageiro é obrigatório.'}), 400

    if len(passageiro) > 120 or len(telefone) > 20 or len(documento) > 30:
        return jsonify({'erro': 'Tamanho máximo excedido (Passageiro: 120, Telefone: 20, Documento: 30).'}), 400

    valor_total_raw = dados.get('valor_total', VALOR_PADRAO)
    valor_pago_raw = dados.get('valor_pago', 0.0)

    if (
        isinstance(valor_total_raw, bool)
        or not isinstance(valor_total_raw, (int, float))
        or isinstance(valor_pago_raw, bool)
        or not isinstance(valor_pago_raw, (int, float))
    ):
        return jsonify({'erro': 'Os valores financeiros devem ser estritamente numéricos.'}), 400

    valor_total = float(valor_total_raw)
    valor_pago = float(valor_pago_raw)

    if not math.isfinite(valor_total) or not math.isfinite(valor_pago):
        return jsonify({'erro': 'Valores numéricos inválidos.'}), 400

    if valor_pago < 0 or valor_total < 0 or valor_pago > valor_total:
        return jsonify({'erro': 'Valores financeiros inválidos.'}), 400

    conn, is_pg = get_db()
    cursor = conn.cursor()
    try:
        ph = '%s' if is_pg else '?'
        cursor.execute(f'''
            UPDATE poltronas
            SET passageiro = {ph}, telefone = {ph}, documento = {ph}, valor_total = {ph}, valor_pago = {ph}
            WHERE numero = {ph}
        ''', (passageiro, telefone, documento, valor_total, valor_pago, numero))

        if cursor.rowcount == 0:
            return jsonify({'erro': 'Poltrona não encontrada.'}), 404

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return jsonify({'mensagem': f'Poltrona {numero} atualizada com sucesso!'}), 200

@app.route('/api/poltronas/<int:numero>/liberar', methods=['PUT'])
@login_required
def liberar_poltrona(numero):
    conn, is_pg = get_db()
    cursor = conn.cursor()
    try:
        ph = '%s' if is_pg else '?'
        cursor.execute(f'''
            UPDATE poltronas
            SET passageiro = '', telefone = '', documento = '', valor_total = {ph}, valor_pago = 0.0
            WHERE numero = {ph}
        ''', (VALOR_PADRAO, numero))

        if cursor.rowcount == 0:
            return jsonify({'erro': 'Poltrona não encontrada.'}), 404

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return jsonify({'mensagem': f'Poltrona {numero} liberada!'}), 200

@app.route('/api/resumo', methods=['GET'])
@login_required
def resumo_viagem():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM poltronas')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    livres = parciais = pagas = 0
    total_arrecadado = total_a_receber = 0.0

    for r in rows:
        item = dict(r)
        passageiro = item['passageiro'].strip()
        v_total = float(item['valor_total'])
        v_pago = float(item['valor_pago'])

        if not passageiro:
            livres += 1
        else:
            total_arrecadado += v_pago
            total_a_receber += max(0.0, v_total - v_pago)
            if v_pago >= v_total and v_total > 0:
                pagas += 1
            else:
                parciais += 1

    return jsonify({
        'livres': livres,
        'parciais': parciais,
        'pagas': pagas,
        'ocupadas': parciais + pagas,
        'total_arrecadado': total_arrecadado,
        'total_a_receber': total_a_receber
    }), 200

@app.route('/api/exportar/embarque', methods=['GET'])
@login_required
def exportar_lista_embarque():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT numero, passageiro, documento, telefone, valor_total, valor_pago 
            FROM poltronas 
            WHERE TRIM(passageiro) != '' 
            ORDER BY numero ASC
        ''')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Poltrona', 'Nome do Passageiro', 'Documento (RG/CPF)', 
        'Telefone', 'Valor Total (R$)', 'Valor Pago (R$)', 'Falta Pagar (R$)', 'Status'
    ])

    for r in rows:
        item = dict(r)
        restante = max(0.0, float(item['valor_total']) - float(item['valor_pago']))
        status = 'Quitado' if restante == 0 else 'Parcial'
        
        writer.writerow([
            f"{item['numero']:02d}",
            sanitize_csv_field(item['passageiro']),
            sanitize_csv_field(item['documento']),
            sanitize_csv_field(item['telefone']),
            f"{float(item['valor_total']):.2f}".replace('.', ','),
            f"{float(item['valor_pago']):.2f}".replace('.', ','),
            f"{restante:.2f}".replace('.', ','),
            status
        ])

    conteudo_csv = output.getvalue().encode('utf-8-sig')
    response = Response(conteudo_csv, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=lista_embarque_aparecida.csv'
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)