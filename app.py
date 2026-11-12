import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import io
from flask import Flask, jsonify, request, Response, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')
SENHA_SISTEMA = os.environ.get('SENHA_SISTEMA', 'aparecida2027')
TOTAL_POLTRONAS = 46
VALOR_PADRAO = 180.00

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
    cursor.close()
    conn.close()

init_db()

# ---------------------------------------------------------
# ROTA PRINCIPAL (INTERFACE WEB) E LOGIN
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    if dados.get('senha') == SENHA_SISTEMA:
        return jsonify({'status': 'ok'}), 200
    return jsonify({'erro': 'Senha inválida'}), 401

# ---------------------------------------------------------
# ROTAS DA API REST
# ---------------------------------------------------------

@app.route('/api/poltronas', methods=['GET'])
def listar_poltronas():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM poltronas ORDER BY numero ASC')
    rows = cursor.fetchall()
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
def atualizar_poltrona(numero):
    dados = request.get_json()
    passageiro = dados.get('passageiro', '').strip()
    telefone = dados.get('telefone', '').strip()
    documento = dados.get('documento', '').strip()
    valor_total = float(dados.get('valor_total', VALOR_PADRAO))
    valor_pago = float(dados.get('valor_pago', 0.0))

    conn, is_pg = get_db()
    cursor = conn.cursor()
    ph = '%s' if is_pg else '?'

    cursor.execute(f'''
        UPDATE poltronas
        SET passageiro = {ph}, telefone = {ph}, documento = {ph}, valor_total = {ph}, valor_pago = {ph}
        WHERE numero = {ph}
    ''', (passageiro, telefone, documento, valor_total, valor_pago, numero))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'mensagem': f'Poltrona {numero} atualizada!'}), 200

@app.route('/api/poltronas/<int:numero>/liberar', methods=['PUT'])
def liberar_poltrona(numero):
    conn, is_pg = get_db()
    cursor = conn.cursor()
    ph = '%s' if is_pg else '?'

    cursor.execute(f'''
        UPDATE poltronas
        SET passageiro = '', telefone = '', documento = '', valor_total = {ph}, valor_pago = 0.0
        WHERE numero = {ph}
    ''', (VALOR_PADRAO, numero))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'mensagem': f'Poltrona {numero} liberada!'}), 200

@app.route('/api/resumo', methods=['GET'])
def resumo_viagem():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM poltronas')
    rows = cursor.fetchall()
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
def exportar_lista_embarque():
    conn, is_pg = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT numero, passageiro, documento, telefone, valor_total, valor_pago 
        FROM poltronas 
        WHERE TRIM(passageiro) != '' 
        ORDER BY numero ASC
    ''')
    rows = cursor.fetchall()
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
            item['passageiro'],
            item['documento'],
            item['telefone'],
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
    app.run(host='0.0.0.0', port=port, debug=True)