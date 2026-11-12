const API_URL = '/api';
let listaPoltronas = [];

document.addEventListener('DOMContentLoaded', () => {
    carregarDados();
});

document.addEventListener('DOMContentLoaded', () => {
    if (sessionStorage.getItem('autenticado') === 'true') {
        document.getElementById('telaLogin').classList.remove('ativo');
        carregarDados();
    }
});

async function verificarSenha() {
    const senha = document.getElementById('senhaAcesso').value;
    const res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ senha })
    });

    if (res.ok) {
        sessionStorage.setItem('autenticado', 'true');
        document.getElementById('telaLogin').classList.remove('ativo');
        carregarDados();
    } else {
        alert('Senha incorreta!');
    }
}

async function carregarDados() {
    await carregarResumo();
    await carregarPoltronas();
}

async function carregarResumo() {
    try {
        const res = await fetch(`${API_URL}/resumo`);
        const dados = await res.json();

        document.getElementById('resumoLivres').innerText = dados.livres;
        document.getElementById('resumoOcupadas').innerText = `${dados.ocupadas} (${dados.parciais} parc. / ${dados.pagas} pagas)`;
        document.getElementById('resumoArrecadado').innerText = formatarMoeda(dados.total_arrecadado);
        document.getElementById('resumoReceber').innerText = formatarMoeda(dados.total_a_receber);
    } catch (erro) {
        console.error('Erro ao carregar resumo:', erro);
    }
}

async function carregarPoltronas() {
    try {
        const res = await fetch(`${API_URL}/poltronas`);
        listaPoltronas = await res.json();
        desenharOnibus(listaPoltronas);
    } catch (erro) {
        console.error('Erro ao carregar poltronas:', erro);
    }
}

function desenharOnibus(poltronas) {
    const mapa = document.getElementById('mapaPoltronas');
    mapa.innerHTML = '';

    // Agrupa de 4 em 4 para formar as fileiras (2 esquerda + corredor + 2 direita)
    for (let i = 0; i < poltronas.length; i += 4) {
        const fileira = document.createElement('div');
        fileira.className = 'fileira';

        const grupo = poltronas.slice(i, i + 4);

        grupo.forEach((p, idx) => {
            // Adiciona o espaço do corredor após a 2ª poltrona da fileira
            if (idx === 2) {
                const corredor = document.createElement('div');
                corredor.className = 'corredor';
                corredor.innerText = '|';
                fileira.appendChild(corredor);
            }

            const btn = document.createElement('div');
            btn.className = `poltrona ${p.status}`;
            btn.onclick = () => abrirModal(p.numero);

            const primeiroNome = p.passageiro ? p.passageiro.split(' ')[0] : 'Livre';

            btn.innerHTML = `
                <span class="num">${String(p.numero).padStart(2, '0')}</span>
                <span class="nome-curto">${primeiroNome}</span>
            `;
            fileira.appendChild(btn);
        });

        mapa.appendChild(fileira);
    }
}

function abrirModal(numero) {
    const p = listaPoltronas.find(item => item.numero === numero);
    if (!p) return;

    document.getElementById('poltronaNumero').value = p.numero;
    document.getElementById('modalNumero').innerText = String(p.numero).padStart(2, '0');
    document.getElementById('passageiro').value = p.passageiro;
    document.getElementById('telefone').value = p.telefone;
    document.getElementById('documento').value = p.documento;
    document.getElementById('valorTotal').value = p.valor_total.toFixed(2);
    document.getElementById('valorPago').value = p.valor_pago.toFixed(2);
    document.getElementById('novoPagamento').value = '';

    // Mostra botão de liberar apenas se a poltrona já estiver ocupada
    document.getElementById('btnLiberar').style.display = p.passageiro ? 'block' : 'none';

    recalcularRestante();
    document.getElementById('modalPoltrona').classList.add('ativo');
}

function fecharModal() {
    document.getElementById('modalPoltrona').classList.remove('ativo');
}

function adicionarParcela() {
    const campoNovo = document.getElementById('novoPagamento');
    const campoPago = document.getElementById('valorPago');

    const adicional = parseFloat(campoNovo.value) || 0;
    const atual = parseFloat(campoPago.value) || 0;

    if (adicional > 0) {
        campoPago.value = (atual + adicional).toFixed(2);
        campoNovo.value = '';
        recalcularRestante();
    }
}

function recalcularRestante() {
    const total = parseFloat(document.getElementById('valorTotal').value) || 0;
    const pago = parseFloat(document.getElementById('valorPago').value) || 0;
    const restante = Math.max(0, total - pago);

    const texto = document.getElementById('valorRestanteTexto');
    texto.innerText = restante === 0 && total > 0 ? 'QUITADO (R$ 0,00)' : formatarMoeda(restante);
    texto.className = restante === 0 && total > 0 ? 'quitado' : '';
}

async function salvarPoltrona(event) {
    event.preventDefault();

    const numero = document.getElementById('poltronaNumero').value;
    const payload = {
        passageiro: document.getElementById('passageiro').value,
        telefone: document.getElementById('telefone').value,
        documento: document.getElementById('documento').value,
        valor_total: parseFloat(document.getElementById('valorTotal').value) || 180.00,
        valor_pago: parseFloat(document.getElementById('valorPago').value) || 0.00
    };

    try {
        const res = await fetch(`${API_URL}/poltronas/${numero}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            fecharModal();
            carregarDados();
        }
    } catch (erro) {
        console.error('Erro ao salvar poltrona:', erro);
    }
}

async function liberarPoltrona() {
    const numero = document.getElementById('poltronaNumero').value;
    if (!confirm(`Deseja realmente remover o passageiro e liberar a poltrona ${numero}?`)) return;

    try {
        const res = await fetch(`${API_URL}/poltronas/${numero}/liberar`, {
            method: 'PUT'
        });

        if (res.ok) {
            fecharModal();
            carregarDados();
        }
    } catch (erro) {
        console.error('Erro ao liberar poltrona:', erro);
    }
}

function formatarMoeda(valor) {
    return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function exportarListaEmbarque() {
    window.location.href = `${API_URL}/exportar/embarque`;
}