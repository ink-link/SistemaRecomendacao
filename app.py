from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Usuario, Avaliacao
import folium
import os
import csv

print("Iniciando app Flask...")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'segredo'
db.init_app(app)

# Inicializa banco de dados
with app.app_context():
    try:
        db.create_all()
        print("Banco de dados inicializado com sucesso.")
    except Exception as e:
        print("Erro ao criar o banco de dados:", e)

def salvar_usuario_csv(usuario):
    import csv
    import os
    
    caminho_csv = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')
    arquivo_existe = os.path.isfile(caminho_csv)
    
    with open(caminho_csv, mode='a', newline='', encoding='utf-8') as arquivo_csv:
        escritor = csv.writer(arquivo_csv)
        
        # Escrever cabeçalho só se o arquivo não existir
        if not arquivo_existe:
            escritor.writerow(['id', 'nome', 'email', 'senha', 'dist_max_km', 'preferencias', 'latitude', 'longitude'])
        
        escritor.writerow([
            usuario.id,
            usuario.nome,
            usuario.email,
            usuario.senha,
            usuario.dist_max_km,
            usuario.preferencias,  # aqui já está string com ';'?
            usuario.latitude,
            usuario.longitude
        ])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/avaliar', methods=['GET', 'POST'])
def avaliar():
    if not session.get('usuario_id'):
        flash('Você precisa estar logado para acessar esta página.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        produtor = request.form['produtor']
        nota = int(request.form['nota'])
        comentario = request.form['comentario']
        avaliacao = Avaliacao(nome_usuario=nome, produtor=produtor, nota=nota, comentario=comentario)
        db.session.add(avaliacao)
        db.session.commit()
        return redirect('/')
    return render_template('avaliar.html')

@app.route('/avaliacoes')
def avaliacoes():
    if not session.get('usuario_id'):
        flash('Você precisa estar logado para acessar esta página.')
        return redirect(url_for('login'))
    todas = Avaliacao.query.all()
    return render_template('avaliacoes.html', avaliacoes=todas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email, senha=senha).first()
        if usuario:
            session['usuario_id'] = usuario.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas.', 'danger')
    return render_template('login.html')

@app.route('/cadastrar', methods=['GET'])
def cadastrar_user():
    return render_template('cadastro_user.html')

@app.route('/registrar', methods=['POST'])
def registrar_usuario():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    dist_max_km = float(request.form['dist_max_km'])
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    preferencias = request.form.getlist('preferencias')
    preferencias_str = ','.join(preferencias).lower()
    
    if not nome or not email or not senha or not latitude or not longitude:
        flash('Todos os campos devem ser preenchidos.')
        return redirect(url_for('cadastrar_user'))
    
    if Usuario.query.filter_by(email=email).first():
        flash('Email já cadastrado.', 'warning')
        return redirect(url_for('cadastrar_user'))

    usuario = Usuario(
        nome=nome,
        email=email,
        senha=senha,
        preferencias=preferencias_str,
        latitude=latitude,
        longitude=longitude,
        dist_max_km=dist_max_km
    )

    db.session.add(usuario)
    db.session.commit()

    print("Escrevendo no CSV:", usuario.id, usuario.nome)
    caminho_csv = os.path.join(os.path.dirname(__file__), 'users.csv')
    salvar_usuario_csv(usuario)

    flash('Registro realizado! Faça login.', 'success')
    return redirect(url_for('login'))


@app.route('/mapa')
def mapa():
    if not session.get('usuario_id'):
        flash('Você precisa estar logado para acessar esta página.')
        return redirect(url_for('login'))
    
    mapa = folium.Map(location=[-15.8, -47.9], zoom_start=11)

    with open('data/markets.csv', newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile)
        for linha in leitor:
            nome = linha['nome']
            produtos = linha['produtos']
            lat = float(linha['latitude'])
            lon = float(linha['longitude'])

            folium.Marker(
                location=[lat, lon],
                popup=f"<strong>{nome}</strong><br>Produtos: {produtos}",
                icon=folium.Icon(color='blue')
            ).add_to(mapa)

    os.makedirs('static/mapas', exist_ok=True)
    mapa.save('static/mapas/mapa.html')

    return render_template('mapa.html')


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

print("Finalizando app Flask...")