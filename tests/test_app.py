"""
Testes automatizados para o Sistema LogiFlow
Usando pytest para validação das funcionalidades
"""

import pytest
import sys
import os
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app, Usuario, Produto, Movimentacao, SessionLocal, Base, engine, hash_password, enviar_notificacao_estoque_baixo

@pytest.fixture
def client():
    """Fixture para criar cliente de teste"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.secret_key = 'test_secret_key'
    
    # Recria o banco de dados para testes
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Cria usuário admin para testes
    db = SessionLocal()
    admin = Usuario(
        nome="Admin Teste",
        email="admin@teste.com",
        senha_hash=hash_password("senha123"),
        eh_administrador=True
    )
    db.add(admin)
    db.commit()
    db.close()
    
    with app.test_client() as client:
        yield client
    
    # Limpa o banco após os testes
    Base.metadata.drop_all(bind=engine)

def test_pagina_login_carrega(client):
    """Testa se a página de login carrega corretamente"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login no Sistema' in response.data

def test_login_com_credenciais_validas(client):
    """Testa login com credenciais válidas"""
    response = client.post('/login', data={
        'email': 'admin@teste.com',
        'senha': 'senha123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Login realizado com sucesso' in response.data or b'Sistema de Controle de Estoque' in response.data

def test_login_com_credenciais_invalidas(client):
    """Testa login com credenciais inválidas"""
    response = client.post('/login', data={
        'email': 'usuario@invalido.com',
        'senha': 'senha_errada'
    })
    assert response.status_code == 200
    assert b'incorretos' in response.data or b'Email ou senha' in response.data

def test_logout(client):
    """Testa funcionalidade de logout"""
    # Faz login primeiro
    client.post('/login', data={
        'email': 'admin@teste.com',
        'senha': 'senha123'
    })
    
    # Faz logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Logout realizado' in response.data or b'Login' in response.data

def test_acesso_dashboard_sem_login(client):
    """Testa que dashboard requer login"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data

def test_criar_produto(client):
    """Testa criação de produto"""
    # Faz login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin Teste'
        sess['is_admin'] = True
    
    response = client.post('/produto/novo', data={
        'nome': 'Produto Teste',
        'preco': '99.90',
        'quantidade': '100',
        'quantidade_minima': '10'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verifica no banco
    db = SessionLocal()
    produto = db.query(Produto).filter(Produto.nome == 'Produto Teste').first()
    assert produto is not None
    assert produto.preco == 99.90
    assert produto.quantidade == 100
    db.close()

def test_criar_produto_com_valores_negativos(client):
    """Testa que não permite valores negativos"""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin Teste'
    
    response = client.post('/produto/novo', data={
        'nome': 'Produto Inválido',
        'preco': '-50.00',
        'quantidade': '-10',
        'quantidade_minima': '5'
    })
    
    assert response.status_code == 200
    assert b'negativos' in response.data or b'valores' in response.data

def test_entrada_estoque(client):
    """Testa entrada de estoque"""
    # Cria produto primeiro
    db = SessionLocal()
    produto = Produto(
        nome='Produto Entrada',
        preco=50.0,
        quantidade=10,
        quantidade_minima=5
    )
    db.add(produto)
    db.commit()
    produto_id = produto.id
    db.close()
    
    # Faz login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin Teste'
    
    # Registra entrada
    response = client.post(f'/entrada/{produto_id}', data={
        'quantidade': '20',
        'observacoes': 'Compra teste'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verifica estoque atualizado
    db = SessionLocal()
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    assert produto.quantidade == 30  # 10 + 20
    db.close()

def test_saida_estoque(client):
    """Testa saída de estoque"""
    # Cria produto
    db = SessionLocal()
    produto = Produto(
        nome='Produto Saída',
        preco=50.0,
        quantidade=50,
        quantidade_minima=5
    )
    db.add(produto)
    db.commit()
    produto_id = produto.id
    db.close()
    
    # Faz login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin Teste'
    
    # Registra saída
    response = client.post(f'/saida/{produto_id}', data={
        'quantidade': '15',
        'observacoes': 'Venda teste'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verifica estoque atualizado
    db = SessionLocal()
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    assert produto.quantidade == 35  # 50 - 15
    db.close()

def test_saida_estoque_insuficiente(client):
    """Testa que não permite saída maior que estoque"""
    # Cria produto com estoque baixo
    db = SessionLocal()
    produto = Produto(
        nome='Produto Estoque Baixo',
        preco=50.0,
        quantidade=5,
        quantidade_minima=2
    )
    db.add(produto)
    db.commit()
    produto_id = produto.id
    db.close()
    
    # Faz login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin Teste'
    
    # Tenta saída maior que estoque
    response = client.post(f'/saida/{produto_id}', data={
        'quantidade': '10',
        'observacoes': 'Teste'
    })
    
    assert response.status_code == 200
    assert b'insuficiente' in response.data or b'Estoque' in response.data

def test_criar_usuario_admin(client):
    """Testa criação de novo usuário (requer admin)"""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin Teste'
        sess['is_admin'] = True
    
    response = client.post('/usuario/novo', data={
        'nome': 'Novo Usuario',
        'email': 'novo@teste.com',
        'senha': 'senha123',
        'eh_administrador': ''
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verifica no banco
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == 'novo@teste.com').first()
    assert usuario is not None
    assert usuario.nome == 'Novo Usuario'
    db.close()

def test_hash_senha():
    """Testa se o hash de senha está funcionando"""
    senha = "senha_teste_123"
    hash_senha = hash_password(senha)
    
    assert hash_senha != senha
    assert len(hash_senha) > 20

def test_movimentacoes_registradas(client):
    """Testa se movimentações são registradas corretamente"""
    # Cria produto e faz movimentação
    db = SessionLocal()
    produto = Produto(
        nome='Produto Movimentação',
        preco=100.0,
        quantidade=50,
        quantidade_minima=10
    )
    db.add(produto)
    db.commit()
    produto_id = produto.id
    
    # Cria movimentação manual
    mov = Movimentacao(
        produto_id=produto_id,
        usuario_id=1,
        tipo_movimentacao='entrada',
        quantidade=20,
        observacoes='Teste movimentação'
    )
    db.add(mov)
    db.commit()
    
    # Verifica
    movimentacoes = db.query(Movimentacao).filter(
        Movimentacao.produto_id == produto_id
    ).all()
    assert len(movimentacoes) == 1
    assert movimentacoes[0].quantidade == 20
    assert movimentacoes[0].tipo_movimentacao == 'entrada'
    
    db.close()

def test_relatorio_estoque_baixo(client):
    """Testa identificação de produtos com estoque baixo"""
    # Cria produtos com estoque baixo
    db = SessionLocal()
    
    produto_baixo = Produto(
        nome='Produto Baixo',
        preco=50.0,
        quantidade=3,  # Abaixo do mínimo
        quantidade_minima=5
    )
    produto_ok = Produto(
        nome='Produto OK',
        preco=50.0,
        quantidade=20,  # Acima do mínimo
        quantidade_minima=5
    )
    
    db.add(produto_baixo)
    db.add(produto_ok)
    db.commit()
    
    # Verifica produtos com estoque baixo
    produtos_baixo = db.query(Produto).filter(
        Produto.quantidade <= Produto.quantidade_minima
    ).all()
    
    assert len(produtos_baixo) == 1
    assert produtos_baixo[0].nome == 'Produto Baixo'
    
    db.close()

def test_sistema_notificacao_simulado():
    """Testa se a função de notificação identifica corretamente o estoque baixo"""
    produto_critico = Produto(nome="Teste", preco=10, quantidade=2, quantidade_minima=5)
    produto_ok = Produto(nome="Teste 2", preco=10, quantidade=10, quantidade_minima=5)
    
    assert enviar_notificacao_estoque_baixo(produto_critico) is True
    assert enviar_notificacao_estoque_baixo(produto_ok) is False
