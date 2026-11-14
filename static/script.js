const API_URL = '';

// Verificação única de sessão ao carregar a página
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch(`${API_URL}/api/status-auth`);
        const data = await res.json();
        if (data.autenticado) {
            const loginEl = document.getElementById('telaLogin');
            loginEl.classList.remove('ativo');
            loginEl.style.display = 'none';
            carregarDados();
        }
    } catch (e) {
        console.error('Erro ao verificar autenticação', e);
    }
});

// Função para limpar dados sensíveis da tela ao deslogar ou expirar a sessão
function limparDadosTela() {
    document.getElementById('mapaPoltronas').innerHTML = '';

    document.getElementById('resumoLivres').textContent = '0';
    document.getElementById('resumoOcupadas').textContent = '0';
    document.getElementById('resumoArrecadado').textContent = 'R$ 0,00';
    document.getElementById('resumoReceber').textContent = 'R$ 0,00';

    document.getElementById('senhaAcesso').value = '';
    fecharModal();
}

// Função auxiliar centralizada para requisições com tratamento de 401 (Sessão Expirada)
async function apiFetch(url, options = {}) {
    const res = await fetch(url, options);
    if (res.status === 401) {
        limparDadosTela();

        const loginEl = document.getElementById('telaLogin');
        loginEl.classList.add('ativo');
        loginEl.style.display = 'flex';

        alert('Sua sessão expirou. Faça login novamente.');
        throw new Error('Não autorizado');
    }
    return res;
}

async function verificarSenha() {
    const senha = document.getElementById('senhaAcesso').value;
    if (!senha) {
        alert('Digite a senha de acesso.');
        return;
    }

    try {
        const res = await fetch(`${API_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ senha })
        });

        if (res.ok) {
            document.getElementById('senhaAcesso').value = '';
            const loginEl = document.getElementById('telaLogin');
            loginEl.classList.remove('ativo');
            loginEl.style.display = 'none';
            carregarDados();
        } else {
            alert('Senha incorreta!');
        }
    } catch (e) {
        alert('Erro ao conectar com o servidor.');
    }
}

async function fazerLogout() {
    try {
        const res = await fetch(`${API_URL}/api/logout`, { method: 'POST' });
        if (!res.ok) throw new Error('Falha ao encerrar sessão.');

        limparDadosTela();

        const loginEl = document.getElementById('telaLogin');
        loginEl.classList.add('ativo');
        loginEl.style.display = 'flex';
    } catch (e) {
        console.error('Erro ao encerrar sessão', e);
        alert('Não foi possível encerrar a sessão com segurança.');
    }
}

// Carregamento otimizado com requisições paralelas independentes
async function carregarDados() {
    await Promise.all([
        carregarResumo(),
        carregarPoltronas()
    ]);
}

async function carregarResumo() {
    try {
        const res = await apiFetch(`${API_URL}/api/resumo`);
        const data = await res.json();

        document.getElementById('resumoLivres').textContent = data.livres;
        document.getElementById('resumoOcupadas').textContent = `${data.ocupadas} (${data.parciais} parc. / ${data.pagas} pagas)`;
        document.getElementById('resumoArrecadado').textContent = `R$ ${data.total_arrecadado.toFixed(2).replace('.', ',')}`;
        document.getElementById('resumoReceber').textContent = `R$ ${data.total_a_receber.toFixed(2).replace('.', ',')}`;
    } catch (e) {
        console.error('Erro ao carregar resumo', e);
    }
}

async function carregarPoltronas() {
    try {
        const res = await apiFetch(`${API_URL}/api/poltronas`);
        const poltronas = await res.json(); // Array com as 46 poltronas

        const container = document.getElementById('mapaPoltronas');
        container.innerHTML = ''; // Limpa o mapa anterior

        // Agrupa as poltronas em fileiras de 4 (2 à esquerda e 2 à direita)
        for (let i = 0; i < poltronas.length; i += 4) {
            const fileiraDiv = document.createElement('div');
            fileiraDiv.className = 'fileira';

            // Pega o lote de até 4 poltronas para esta fileira
            const subset = poltronas.slice(i, i + 4);
            const p1 = subset[0] || null;
            const p2 = subset[1] || null;
            const p3 = subset[2] || null;
            const p4 = subset[3] || null;

            // Função auxiliar para renderizar a poltrona ou um espaço vazio
            const criarBotaoOuEspaco = (p) => {
                if (!p) {
                    const vazio = document.createElement('div');
                    return vazio;
                }
                const btn = document.createElement('button');
                btn.className = `poltrona ${p.status}`;
                btn.onclick = () => abrirModal(p);

                const spanNum = document.createElement('span');
                spanNum.className = 'num';
                spanNum.textContent = String(p.numero).padStart(2, '0');

                const spanNome = document.createElement('span');
                spanNome.className = 'nome-curto';
                spanNome.textContent = p.passageiro ? p.passageiro.split(' ')[0] : 'Livre';
                if (!p.passageiro) {
                    spanNome.style.color = '#999';
                }

                btn.appendChild(spanNum);
                btn.appendChild(spanNome);
                return btn;
            };

            // Adiciona as 2 poltronas da esquerda
            fileiraDiv.appendChild(criarBotaoOuEspaco(p1));
            fileiraDiv.appendChild(criarBotaoOuEspaco(p2));

            // Adiciona o corredor central
            const corredorDiv = document.createElement('div');
            corredorDiv.className = 'corredor';
            corredorDiv.textContent = '';
            fileiraDiv.appendChild(corredorDiv);

            // Adiciona as 2 poltronas da direita
            fileiraDiv.appendChild(criarBotaoOuEspaco(p3));
            fileiraDiv.appendChild(criarBotaoOuEspaco(p4));

            // Adiciona a fileira completa ao mapa do autocarro
            container.appendChild(fileiraDiv);
        }

    } catch (e) {
        console.error('Erro ao carregar poltronas', e);
    }
}

let poltronaAtual = null;

function abrirModal(p) {
    poltronaAtual = p.numero;
    document.getElementById('modalNumero').textContent = String(p.numero).padStart(2, '0');
    document.getElementById('poltronaNumero').value = p.numero;
    document.getElementById('passageiro').value = p.passageiro || '';
    document.getElementById('telefone').value = p.telefone || '';
    document.getElementById('documento').value = p.documento || '';
    document.getElementById('valorTotal').value = p.valor_total;
    document.getElementById('valorPago').value = p.valor_pago;

    recalcularRestante();
    document.getElementById('modalPoltrona').style.display = 'flex';
}

function fecharModal() {
    document.getElementById('modalPoltrona').style.display = 'none';
    poltronaAtual = null;
}

function recalcularRestante() {
    const total = parseFloat(document.getElementById('valorTotal').value) || 0;
    const pago = parseFloat(document.getElementById('valorPago').value) || 0;
    const restante = Math.max(0, total - pago);
    document.getElementById('valorRestanteTexto').textContent = `R$ ${restante.toFixed(2).replace('.', ',')}`;
}

function adicionarParcela() {
    const inputParcela = document.getElementById('novoPagamento');
    const valorParcela = parseFloat(inputParcela.value);

    if (isNaN(valorParcela) || valorParcela <= 0) {
        alert('Digite um valor numérico válido para somar.');
        return;
    }

    const inputPago = document.getElementById('valorPago');
    const inputTotal = document.getElementById('valorTotal');
    const pagoAtual = parseFloat(inputPago.value);
    const total = parseFloat(inputTotal.value);

    if (isNaN(pagoAtual) || isNaN(total)) {
        alert('Os campos de valor total ou valor pago possuem dados inválidos.');
        return;
    }

    const novoPago = pagoAtual + valorParcela;
    if (novoPago > total) {
        alert('O valor pago não pode ultrapassar o total da passagem.');
        return;
    }

    inputPago.value = novoPago.toFixed(2);
    inputParcela.value = '';
    recalcularRestante();
}

async function salvarPoltrona(event) {
    event.preventDefault();
    if (!poltronaAtual) return;

    const passageiroVal = document.getElementById('passageiro').value.trim();
    const telefoneVal = document.getElementById('telefone').value.trim();
    const documentoVal = document.getElementById('documento').value.trim();
    
    const valorTotalInput = document.getElementById('valorTotal').value;
    const valorPagoInput = document.getElementById('valorPago').value;

    const valor_total = parseFloat(valorTotalInput);
    const valor_pago = parseFloat(valorPagoInput);

    // Validação estricta contra entradas inválidas (NaN, infinitas ou negativas)
    if (isNaN(valor_total) || isNaN(valor_pago) || !isFinite(valor_total) || !isFinite(valor_pago)) {
        alert('Erro: Insira valores numéricos válidos nos campos financeiros.');
        return;
    }

    if (valor_pago < 0 || valor_total < 0 || valor_pago > valor_total) {
        alert('Atenção: O valor pago não pode ser negativo nem maior que o valor total.');
        return;
    }

    const dados = {
        passageiro: passageiroVal,
        telefone: telefoneVal,
        documento: documentoVal,
        valor_total: valor_total,
        valor_pago: valor_pago
    };

    try {
        const res = await apiFetch(`${API_URL}/api/poltronas/${poltronaAtual}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        if (res.ok) {
            fecharModal();
            carregarDados();
        } else {
            const err = await res.json();
            alert(err.erro || 'Erro ao salvar poltrona');
        }
    } catch (e) {
        console.error('Erro ao salvar', e);
    }
}

async function liberarPoltrona() {
    if (!poltronaAtual) return;
    if (!confirm(`Deseja realmente liberar a poltrona ${poltronaAtual}?`)) return;

    try {
        const res = await apiFetch(`${API_URL}/api/poltronas/${poltronaAtual}/liberar`, {
            method: 'PUT'
        });

        if (res.ok) {
            fecharModal();
            carregarDados();
        } else {
            alert('Erro ao liberar poltrona');
        }
    } catch (e) {
        console.error('Erro ao liberar', e);
    }
}

async function exportarListaEmbarque() {
    try {
        const res = await apiFetch(`${API_URL}/api/exportar/embarque`);
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'lista_embarque_aparecida.csv';
            document.body.appendChild(a);
            a.click();
            a.remove();
            
            // Libera o objeto da memória do navegador após o download (Evita Memory Leak)
            window.URL.revokeObjectURL(url);
        } else {
            alert('Erro ao exportar lista.');
        }
    } catch (e) {
        console.error('Erro ao exportar', e);
    }
}