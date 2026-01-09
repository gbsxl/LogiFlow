"""
Testes automatizados para o Sistema LogiFlow
Usando pytest para validação das funcionalidades
"""

import pytest
import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app, Usuario, Produto, Movimentacao, SessionLocal, Base, engine


@pytest.fixture(scope='function')
def client():
    """Fixture para criar cliente de teste"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.secret_key = 'test_secret_key'
    
    # Recria o banco de dados para testes
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Cria usuário admin para testes diretamente no banco
    db = SessionLocal()
    try:
        from passlib.hash import bcrypt
        admin = Usuario(
            nome="Admin Teste",
            email="admin@teste.com",
            senha_hash=bcrypt.hash("senha123"),
            eh_administrador=True
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()
    
    with app.test_client() as test_client:
        yield test_client
    
    # Limpa o banco após os testes
    Base.metadata.drop_all(bind=engine)


class TestLogin:
    """Testes relacionados ao login"""
    
    def test_pagina_login_carrega(self, client):
        """Testa se a página de login carrega corretamente"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_login_credenciais_validas(self, client):
        """Testa login com credenciais válidas"""
        response = client.post('/login', data={
            'email': 'admin@teste.com',
            'senha': 'senha123'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_credenciais_invalidas(self, client):
        """Testa login com credenciais inválidas"""
        response = client.post('/login', data={
            'email': 'invalido@teste.com',
            'senha': 'errada'
        })
        assert response.status_code == 200
        assert b'incorretos' in response.data or b'Email' in response.data
    
    def test_logout(self, client):
        """Testa funcionalidade de logout"""
        # Login primeiro
        client.post('/login', data={
            'email': 'admin@teste.com',
            'senha': 'senha123'
        })
        # Logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestProdutos:
    """Testes relacionados a produtos"""
    
    def test_criar_produto(self, client):
        """Testa criação de produto"""
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
        db.close()
    
    def test_dashboard_requer_login(self, client):
        """Testa que dashboard requer login"""
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data


class TestEstoque:
    """Testes relacionados a movimentações de estoque"""
    
    def test_entrada_estoque(self, client):
        """Testa entrada de estoque"""
        # Cria produto
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
        
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Admin Teste'
        
        response = client.post(f'/entrada/{produto_id}', data={
            'quantidade': '20',
            'observacoes': 'Compra'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        db = SessionLocal()
        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        assert produto.quantidade == 30
        db.close()
    
    def test_saida_estoque(self, client):
        """Testa saída de estoque"""
        db = SessionLocal()
        produto = Produto(
            nome='Produto Saida',
            preco=50.0,
            quantidade=50,
            quantidade_minima=5
        )
        db.add(produto)
        db.commit()
        produto_id = produto.id
        db.close()
        
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Admin Teste'
        
        response = client.post(f'/saida/{produto_id}', data={
            'quantidade': '15',
            'observacoes': 'Venda'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        db = SessionLocal()
        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        assert produto.quantidade == 35
        db.close()


class TestModelos:
    """Testes dos modelos de dados"""
    
    def test_criar_produto_modelo(self, client):
        """Testa criação de produto via modelo"""
        db = SessionLocal()
        produto = Produto(
            nome='Teste Modelo',
            preco=25.50,
            quantidade=100,
            quantidade_minima=10
        )
        db.add(produto)
        db.commit()
        
        assert produto.id is not None
        assert produto.nome == 'Teste Modelo'
        db.close()
    
    def test_criar_movimentacao(self, client):
        """Testa criação de movimentação"""
        db = SessionLocal()
        produto = Produto(
            nome='Produto Mov',
            preco=10.0,
            quantidade=50,
            quantidade_minima=5
        )
        db.add(produto)
        db.commit()
        
        mov = Movimentacao(
            produto_id=produto.id,
            usuario_id=1,
            tipo_movimentacao='entrada',
            quantidade=10,
            observacoes='Teste'
        )
        db.add(mov)
        db.commit()
        
        assert mov.id is not None
        assert mov.quantidade == 10
        db.close()


class TestNotificacao:
    """Testes do sistema de notificação"""
    
    def test_funcao_notificacao_estoque_baixo(self, client):
        """Testa função de notificação de estoque baixo"""
        from app import enviar_notificacao_estoque_baixo
        
        # Cria produto com estoque crítico (sem persistir)
        produto_critico = Produto(
            nome="Critico",
            preco=10.0,
            quantidade=2,
            quantidade_minima=5
        )
        
        produto_ok = Produto(
            nome="OK",
            preco=10.0,
            quantidade=10,
            quantidade_minima=5
        )
        
        assert enviar_notificacao_estoque_baixo(produto_critico) is True
        assert enviar_notificacao_estoque_baixo(produto_ok) is False
