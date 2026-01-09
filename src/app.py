from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, get_flashed_messages
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, create_engine, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from passlib.context import CryptContext

app = Flask(__name__)
app.secret_key = 'chave_secreta_estoque_sistema_2024'

URL_BANCO_DADOS = "sqlite:///estoque.db"
engine = create_engine(URL_BANCO_DADOS, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    preco = Column(Float, nullable=False)
    quantidade = Column(Integer, nullable=False)
    quantidade_minima = Column(Integer, nullable=False, default=5)
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    senha_hash = Column(String(100), nullable=False)
    eh_administrador = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.now)


class Movimentacao(Base):
    __tablename__ = 'movimentacoes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tipo_movimentacao = Column(String(20), nullable=False)
    quantidade = Column(Integer, nullable=False)
    observacoes = Column(String(255))
    data_movimentacao = Column(DateTime, default=datetime.now)

    produto = relationship("Produto")
    usuario = relationship("Usuario")


Base.metadata.create_all(bind=engine)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_admin_user():
    db = SessionLocal()
    try:
        existing_admin = db.query(Usuario).filter(Usuario.eh_administrador == True).first()
        if not existing_admin:
            admin = Usuario(
                nome="Administrador",
                email="admin@sistema.com",
                senha_hash=hash_password("admin123"),
                eh_administrador=True
            )
            db.add(admin)
            db.commit()
            print("Usuário admin criado: admin@sistema.com / admin123")
    finally:
        db.close()



create_admin_user()


def enviar_notificacao_estoque_baixo(produto):
    """
    Simula o envio de e-mail para o administrador quando o estoque está baixo.
    Esta função seria chamada por um agendador ou job assíncrono.
    """
    if produto.quantidade <= produto.quantidade_minima:
        print(f"ALERTA [EMAIL]: O produto '{produto.nome}' está com estoque CRÍTICO!")
        print(f"Estoque Atual: {produto.quantidade} | Mínimo: {produto.quantidade_minima}")
        # Simulação de envio SMTP
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.sendmail(...)
        return True
    return False


def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Acesso negado.', 'error')
            return redirect(url_for('login'))

        db = SessionLocal()
        try:
            user = db.query(Usuario).filter(Usuario.id == session['user_id']).first()
            if not user or not user.eh_administrador:
                flash('Acesso restrito para administradores.', 'error')
                return redirect(url_for('dashboard'))
        finally:
            db.close()
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


def get_base_template(content, active_page=''):
    return f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LogiFlow</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; 
                 box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }}
        .nav {{ display: flex; gap: 15px; margin: 20px 0; }}
        .nav a {{ background: #007bff; color: white; padding: 12px 20px; text-decoration: none; 
                border-radius: 6px; transition: background 0.3s; }}
        .nav a:hover {{ background: #0056b3; }}
        .nav a.active {{ background: #28a745; }}
        .card {{ background: white; padding: 25px; border-radius: 8px; margin: 15px 0; 
               box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .btn {{ display: inline-block; padding: 10px 20px; margin: 5px; text-decoration: none; 
              border-radius: 5px; cursor: pointer; border: none; font-size: 14px; }}
        .btn-primary {{ background: #007bff; color: white; }}
        .btn-success {{ background: #28a745; color: white; }}
        .btn-warning {{ background: #ffc107; color: #212529; }}
        .btn-danger {{ background: #dc3545; color: white; }}
        .btn:hover {{ opacity: 0.9; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .form-group {{ margin: 15px 0; }}
        .form-group label {{ display: block; margin-bottom: 5px; font-weight: 600; }}
        .form-group input, .form-group select {{ width: 100%; padding: 10px; border: 1px solid #ced4da; 
                                               border-radius: 4px; font-size: 14px; }}
        .alert {{ padding: 12px; margin: 15px 0; border-radius: 4px; }}
        .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .alert-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .alert-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
        .estoque-baixo {{ background: #fff3cd !important; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                     gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                    padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        ''' + ("" if "user_id" not in session else f'''
        <div class="header">
            <h1>Sistema de Controle de Estoque</h1>
            <div>
                Usuário: <strong>{session.get("user_name", "")}</strong>
                ''' + ('<span style="color: #28a745;">(Admin)</span>' if session.get("is_admin") else "") + f'''
                <a href="{url_for("logout")}" class="btn btn-danger">Sair</a>
            </div>
        </div>

        <div class="nav">
            <a href="{url_for("dashboard")}" ''' + ('class="active"' if active_page == "dashboard" else "") + f'''>Produtos</a>
            <a href="{url_for("movimentacoes")}" ''' + ('class="active"' if active_page == "movimentacoes" else "") + f'''>Movimentações</a>
            ''' + (f'<a href="{url_for("usuarios")}" ' + ('class="active"' if active_page == "usuarios" else "") + '>Usuários</a>' if session.get("is_admin") else "") + f'''
            <a href="{url_for("relatorio")}" ''' + ('class="active"' if active_page == "relatorio" else "") + f'''>Relatórios</a>
        </div>
        ''') + '''

        ''' + "".join([f'<div class="alert alert-{"error" if category == "error" else "success"}">{message}</div>' for category, message in get_flashed_messages(with_categories=True)]) + f'''

        {content}
    </div>
</body>
</html>
    '''


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = request.form['senha']

        if not email or not senha:
            flash('Email e senha são obrigatórios.', 'error')
        else:
            db = SessionLocal()
            try:
                user = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()
                if user and verify_password(senha, user.senha_hash):
                    session['user_id'] = user.id
                    session['user_name'] = user.nome
                    session['is_admin'] = user.eh_administrador
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Email ou senha incorretos.', 'error')
            finally:
                db.close()

    content = '''
    <div class="card" style="max-width: 400px; margin: 100px auto;">
        <h2 style="text-align: center; margin-bottom: 30px; color: #333;">Login no Sistema</h2>
        <form method="POST">
            <div class="form-group">
                <label>Email:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Senha:</label>
                <input type="password" name="senha" required>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%;">Entrar</button>
        </form>
        <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
            Credenciais padrão: admin@sistema.com / admin123
        </div>
    </div>
    '''

    return render_template_string(get_base_template(content))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    db = SessionLocal()
    try:
        produtos = db.query(Produto).all()
    finally:
        db.close()

    produtos_html = ''.join([f'''
        <tr {"class=\"estoque-baixo\"" if produto.quantidade <= produto.quantidade_minima else ""}>
            <td>{produto.id}</td>
            <td>{produto.nome}</td>
            <td>R$ {produto.preco:.2f}</td>
            <td>{produto.quantidade}</td>
            <td>{produto.quantidade_minima}</td>
            <td>
                {"<span style=\"color: #856404; font-weight: bold;\">BAIXO</span>" if produto.quantidade <= produto.quantidade_minima else "<span style=\"color: #28a745; font-weight: bold;\">OK</span>"}
            </td>
            <td>
                <a href="{url_for("entrada_estoque", produto_id=produto.id)}" class="btn btn-success">Entrada</a>
                <a href="{url_for("saida_estoque", produto_id=produto.id)}" class="btn btn-warning">Saída</a>
                {f'<a href="{url_for("produto_editar", produto_id=produto.id)}" class="btn btn-primary">Editar</a>' if session.get("is_admin") else ""}
            </td>
        </tr>
    ''' for produto in produtos])

    content = f'''
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2>Gerenciar Produtos</h2>
            <a href="{url_for('produto_novo')}" class="btn btn-primary">Novo Produto</a>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Nome</th><th>Preço</th><th>Estoque</th><th>Mín.</th><th>Status</th><th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {produtos_html}
            </tbody>
        </table>
    </div>
    '''

    return render_template_string(get_base_template(content, 'dashboard'))


@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def produto_novo():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        preco = request.form['preco']
        quantidade = request.form['quantidade']
        quantidade_minima = request.form.get('quantidade_minima', 5)

        if not nome:
            flash('Nome do produto é obrigatório.', 'error')
        else:
            try:
                preco = float(preco)
                quantidade = int(quantidade)
                quantidade_minima = int(quantidade_minima)

                if preco < 0 or quantidade < 0 or quantidade_minima < 0:
                    flash('Valores não podem ser negativos.', 'error')
                else:
                    db = SessionLocal()
                    try:
                        produto = Produto(
                            nome=nome,
                            preco=preco,
                            quantidade=quantidade,
                            quantidade_minima=quantidade_minima
                        )
                        db.add(produto)
                        db.commit()
                        flash('Produto cadastrado com sucesso!', 'success')
                        return redirect(url_for('dashboard'))
                    finally:
                        db.close()
            except ValueError:
                flash('Por favor, insira valores válidos.', 'error')

    content = f'''
    <div class="card">
        <h2>Cadastrar Novo Produto</h2>
        <form method="POST">
            <div class="form-group">
                <label>Nome do Produto *:</label>
                <input type="text" name="nome" required>
            </div>
            <div class="form-group">
                <label>Preço (R$) *:</label>
                <input type="number" step="0.01" name="preco" min="0" required>
            </div>
            <div class="form-group">
                <label>Quantidade Inicial *:</label>
                <input type="number" name="quantidade" min="0" required>
            </div>
            <div class="form-group">
                <label>Quantidade Mínima:</label>
                <input type="number" name="quantidade_minima" value="5" min="0">
            </div>
            <div style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">Cadastrar</button>
                <a href="{url_for('dashboard')}" class="btn btn-danger">Cancelar</a>
            </div>
        </form>
    </div>
    '''

    return render_template_string(get_base_template(content, 'dashboard'))


@app.route('/produto/editar/<int:produto_id>', methods=['GET', 'POST'])
@admin_required
def produto_editar(produto_id):
    db = SessionLocal()
    try:
        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            flash('Produto não encontrado.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            nome = request.form['nome'].strip()
            preco = request.form['preco']
            quantidade_minima = request.form['quantidade_minima']

            if not nome:
                flash('Nome do produto é obrigatório.', 'error')
            else:
                try:
                    preco = float(preco)
                    quantidade_minima = int(quantidade_minima)

                    if preco < 0 or quantidade_minima < 0:
                        flash('Valores não podem ser negativos.', 'error')
                    else:
                        produto.nome = nome
                        produto.preco = preco
                        produto.quantidade_minima = quantidade_minima
                        produto.atualizado_em = datetime.now()
                        db.commit()
                        flash('Produto atualizado com sucesso!', 'success')
                        return redirect(url_for('dashboard'))
                except ValueError:
                    flash('Por favor, insira valores válidos.', 'error')
    finally:
        db.close()

    content = f'''
    <div class="card">
        <h2>Editar Produto</h2>
        <form method="POST">
            <div class="form-group">
                <label>Nome do Produto:</label>
                <input type="text" name="nome" value="{produto.nome}" required>
            </div>
            <div class="form-group">
                <label>Preço (R$):</label>
                <input type="number" step="0.01" name="preco" value="{produto.preco}" min="0" required>
            </div>
            <div class="form-group">
                <label>Estoque Atual (somente leitura):</label>
                <input type="number" value="{produto.quantidade}" disabled>
            </div>
            <div class="form-group">
                <label>Quantidade Mínima:</label>
                <input type="number" name="quantidade_minima" value="{produto.quantidade_minima}" min="0">
            </div>
            <div style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">Salvar</button>
                <a href="{url_for('dashboard')}" class="btn btn-danger">Cancelar</a>
            </div>
        </form>
    </div>
    '''

    return render_template_string(get_base_template(content, 'dashboard'))


@app.route('/entrada/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def entrada_estoque(produto_id):
    db = SessionLocal()
    try:
        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            flash('Produto não encontrado.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            quantidade = request.form['quantidade']
            observacoes = request.form.get('observacoes', '').strip()

            try:
                quantidade = int(quantidade)
                if quantidade <= 0:
                    flash('Quantidade deve ser maior que zero.', 'error')
                else:
                    produto.quantidade += quantidade
                    produto.atualizado_em = datetime.now()

                    mov = Movimentacao(
                        produto_id=produto_id,
                        usuario_id=session['user_id'],
                        tipo_movimentacao='entrada',
                        quantidade=quantidade,
                        observacoes=observacoes
                    )
                    db.add(mov)
                    db.commit()

                    flash(f'Entrada de {quantidade} unidades registrada com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
            except ValueError:
                flash('Por favor, insira uma quantidade válida.', 'error')
    finally:
        db.close()

    content = f'''
    <div class="card">
        <h2>Entrada de Estoque</h2>
        <div class="alert alert-warning">
            <strong>Produto:</strong> {produto.nome}<br>
            <strong>Estoque Atual:</strong> {produto.quantidade} unidades
        </div>

        <form method="POST">
            <div class="form-group">
                <label>Quantidade a Adicionar *:</label>
                <input type="number" name="quantidade" min="1" required>
            </div>
            <div class="form-group">
                <label>Observações:</label>
                <input type="text" name="observacoes" placeholder="Ex: Compra, devolução, etc.">
            </div>
            <div style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">Confirmar Entrada</button>
                <a href="{url_for('dashboard')}" class="btn btn-danger">Cancelar</a>
            </div>
        </form>
    </div>
    '''

    return render_template_string(get_base_template(content, 'dashboard'))


@app.route('/saida/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def saida_estoque(produto_id):
    db = SessionLocal()
    try:
        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            flash('Produto não encontrado.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            quantidade = request.form['quantidade']
            observacoes = request.form.get('observacoes', '').strip()

            try:
                quantidade = int(quantidade)
                if quantidade <= 0:
                    flash('Quantidade deve ser maior que zero.', 'error')
                elif quantidade > produto.quantidade:
                    flash('Estoque insuficiente para esta saída.', 'error')
                else:
                    produto.quantidade -= quantidade
                    produto.atualizado_em = datetime.now()

                    mov = Movimentacao(
                        produto_id=produto_id,
                        usuario_id=session['user_id'],
                        tipo_movimentacao='saida',
                        quantidade=quantidade,
                        observacoes=observacoes
                    )
                    db.add(mov)
                    db.commit()

                    flash(f'Saída de {quantidade} unidades registrada com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
            except ValueError:
                flash('Por favor, insira uma quantidade válida.', 'error')
    finally:
        db.close()

    content = f'''
    <div class="card">
        <h2>Saída de Estoque</h2>
        <div class="alert alert-warning">
            <strong>Produto:</strong> {produto.nome}<br>
            <strong>Estoque Disponível:</strong> {produto.quantidade} unidades
        </div>

        <form method="POST">
            <div class="form-group">
                <label>Quantidade a Retirar *:</label>
                <input type="number" name="quantidade" min="1" max="{produto.quantidade}" required>
            </div>
            <div class="form-group">
                <label>Observações:</label>
                <input type="text" name="observacoes" placeholder="Ex: Venda, uso interno, etc.">
            </div>
            <div style="margin-top: 20px;">
                <button type="submit" class="btn btn-warning">Confirmar Saída</button>
                <a href="{url_for('dashboard')}" class="btn btn-danger">Cancelar</a>
            </div>
        </form>
    </div>
    '''

    return render_template_string(get_base_template(content, 'dashboard'))


@app.route('/movimentacoes')
@login_required
def movimentacoes():
    db = SessionLocal()
    try:
        movs = db.query(Movimentacao).order_by(Movimentacao.data_movimentacao.desc()).limit(100).all()
    finally:
        db.close()

    movs_html = ''.join([f'''
        <tr>
            <td>{mov.data_movimentacao.strftime('%d/%m/%Y %H:%M')}</td>
            <td>{mov.produto.nome}</td>
            <td>
                <span style="color: {'#28a745' if mov.tipo_movimentacao == 'entrada' else '#ffc107'}; font-weight: bold;">
                    {mov.tipo_movimentacao.upper()}
                </span>
            </td>
            <td>{mov.quantidade}</td>
            <td>{mov.usuario.nome}</td>
            <td>{mov.observacoes or '-'}</td>
        </tr>
    ''' for mov in movs])

    content = f'''
    <div class="card">
        <h2>Histórico de Movimentações</h2>
        <p style="color: #666; margin-bottom: 20px;">Últimas 100 movimentações</p>

        <table>
            <thead>
                <tr>
                    <th>Data/Hora</th><th>Produto</th><th>Tipo</th><th>Quantidade</th><th>Usuário</th><th>Observações</th>
                </tr>
            </thead>
            <tbody>
                {movs_html}
            </tbody>
        </table>
    </div>
    '''

    return render_template_string(get_base_template(content, 'movimentacoes'))


@app.route('/usuarios')
@admin_required
def usuarios():
    db = SessionLocal()
    try:
        users = db.query(Usuario).filter(Usuario.ativo == True).all()
    finally:
        db.close()

    users_html = ''.join([f'''
        <tr>
            <td>{user.id}</td>
            <td>{user.nome}</td>
            <td>{user.email}</td>
            <td>
                <span style="color: {'#28a745' if user.eh_administrador else '#007bff'}; font-weight: bold;">
                    {'ADMIN' if user.eh_administrador else 'COMUM'}
                </span>
            </td>
            <td>{user.criado_em.strftime('%d/%m/%Y')}</td>
        </tr>
    ''' for user in users])

    content = f'''
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2>Gerenciar Usuários</h2>
            <a href="{url_for('usuario_novo')}" class="btn btn-primary">Novo Usuário</a>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Nome</th><th>Email</th><th>Tipo</th><th>Criado em</th>
                </tr>
            </thead>
            <tbody>
                {users_html}
            </tbody>
        </table>
    </div>
    '''

    return render_template_string(get_base_template(content, 'usuarios'))


@app.route('/usuario/novo', methods=['GET', 'POST'])
@admin_required
def usuario_novo():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        email = request.form['email'].strip().lower()
        senha = request.form['senha']
        eh_admin = 'eh_administrador' in request.form

        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios.', 'error')
        else:
            db = SessionLocal()
            try:
                existing_user = db.query(Usuario).filter(Usuario.email == email).first()
                if existing_user:
                    flash('Este email já está cadastrado.', 'error')
                else:
                    user = Usuario(
                        nome=nome,
                        email=email,
                        senha_hash=hash_password(senha),
                        eh_administrador=eh_admin
                    )
                    db.add(user)
                    db.commit()
                    flash('Usuário cadastrado com sucesso!', 'success')
                    return redirect(url_for('usuarios'))
            finally:
                db.close()

    content = f'''
    <div class="card">
        <h2>Cadastrar Novo Usuário</h2>
        <form method="POST">
            <div class="form-group">
                <label>Nome Completo *:</label>
                <input type="text" name="nome" required>
            </div>
            <div class="form-group">
                <label>Email *:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Senha *:</label>
                <input type="password" name="senha" required>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="eh_administrador" style="width: auto; margin-right: 8px;">
                    Usuário Administrador
                </label>
            </div>
            <div style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">Cadastrar</button>
                <a href="{url_for('usuarios')}" class="btn btn-danger">Cancelar</a>
            </div>
        </form>
    </div>
    '''

    return render_template_string(get_base_template(content, 'usuarios'))


@app.route('/relatorio')
@login_required
def relatorio():
    db = SessionLocal()
    try:
        total_produtos = db.query(Produto).count()
        produtos_baixo = db.query(Produto).filter(
            Produto.quantidade <= Produto.quantidade_minima
        ).all()

        todos_produtos = db.query(Produto).all()
        valor_total_estoque = sum([p.preco * p.quantidade for p in todos_produtos])

        movs_hoje = db.query(Movimentacao).filter(
            Movimentacao.data_movimentacao >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
    finally:
        db.close()

    produtos_baixo_html = ''.join([f'''
        <tr class="estoque-baixo">
            <td><strong>{produto.nome}</strong></td>
            <td>{produto.quantidade}</td>
            <td>{produto.quantidade_minima}</td>
            <td style="color: #dc3545; font-weight: bold;">
                {produto.quantidade_minima - produto.quantidade} unidades
            </td>
            <td>
                <a href="{url_for('entrada_estoque', produto_id=produto.id)}" class="btn btn-success">Repor</a>
            </td>
        </tr>
    ''' for produto in produtos_baixo])

    produtos_baixo_section = f'''
        <div style="margin-top: 30px;">
            <h3 style="color: #856404;">⚠️ Produtos com Estoque Baixo</h3>
            <table>
                <thead>
                    <tr>
                        <th>Produto</th><th>Estoque Atual</th><th>Estoque Mínimo</th><th>Diferença</th><th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    {produtos_baixo_html}
                </tbody>
            </table>
        </div>
    ''' if produtos_baixo else '''
        <div class="alert alert-success" style="margin-top: 20px;">
            <strong>✅ Parabéns!</strong> Todos os produtos estão com estoque adequado.
        </div>
    '''

    content = f'''
    <div class="card">
        <h2>Relatório do Sistema</h2>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_produtos}</div>
                <div>Total de Produtos</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                <div class="stat-number">R$ {valor_total_estoque:.2f}</div>
                <div>Valor do Estoque</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333;">
                <div class="stat-number">{len(produtos_baixo)}</div>
                <div>Estoque Baixo</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333;">
                <div class="stat-number">{movs_hoje}</div>
                <div>Movimentações Hoje</div>
            </div>
        </div>

        {produtos_baixo_section}

        <div style="margin-top: 30px;">
            <h3>Resumo por Status</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
                <div class="card" style="background: #d4edda; border: 1px solid #c3e6cb;">
                    <h4 style="color: #155724; margin-bottom: 10px;">Produtos com Estoque OK</h4>
                    <div style="font-size: 2em; font-weight: bold; color: #155724;">
                        {total_produtos - len(produtos_baixo)}
                    </div>
                </div>
                <div class="card" style="background: #fff3cd; border: 1px solid #ffeaa7;">
                    <h4 style="color: #856404; margin-bottom: 10px;">Produtos com Estoque Baixo</h4>
                    <div style="font-size: 2em; font-weight: bold; color: #856404;">
                        {len(produtos_baixo)}
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''

    return render_template_string(get_base_template(content, 'relatorio'))


if __name__ == '__main__':
    print("=" * 60)
    print("SISTEMA DE CONTROLE DE ESTOQUE")
    print("=" * 60)
    print("🌐 Interface Web: http://localhost:1531")
    print("📧 Login padrão: admin@sistema.com")
    print("🔑 Senha padrão: admin123")
    print("=" * 60)
    print("✅ Sistema iniciado com sucesso!")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=1531)
