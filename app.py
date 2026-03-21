from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Ejercicio, Progreso

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calistenia.db'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ─── INICIO ───────────────────────────────────────
@app.route('/')
def inicio():
    return redirect(url_for('login'))

# ─── REGISTRO ─────────────────────────────────────
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre   = request.form['nombre']
        email    = request.form['email']
        password = request.form['password']

        # Verifico si el email ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('Ese email ya está registrado', 'danger')
            return redirect(url_for('registro'))

        # Guardo el usuario con la contraseña encriptada
        nuevo = Usuario(
            nombre=nombre,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Cuenta creada, ya puedes iniciar sesión', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

# ─── LOGIN ────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        usuario  = Usuario.query.filter_by(email=email).first()

        if not usuario or not check_password_hash(usuario.password, password):
            flash('Email o contraseña incorrectos', 'danger')
            return redirect(url_for('login'))

        login_user(usuario)

        # Si es admin lo mando al dashboard admin, si no al de usuario
        if usuario.es_admin:
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('dashboard_usuario'))

    return render_template('login.html')

# ─── LOGOUT ───────────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ─── DASHBOARD ADMIN ──────────────────────────────
@app.route('/admin')
@login_required
def dashboard_admin():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    total_usuarios   = Usuario.query.count()
    total_ejercicios = Ejercicio.query.count()
    total_progresos  = Progreso.query.count()
    return render_template('dashboard_admin.html',
        total_usuarios=total_usuarios,
        total_ejercicios=total_ejercicios,
        total_progresos=total_progresos
    )
# ─── CRUD EJERCICIOS (ADMIN) ──────────────────────
@app.route('/admin/ejercicios')
@login_required
def lista_ejercicios():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    ejercicios = Ejercicio.query.all()
    return render_template('ejercicios_admin.html', ejercicios=ejercicios)

@app.route('/admin/ejercicios/crear', methods=['POST'])
@login_required
def crear_ejercicio():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    nuevo = Ejercicio(
        nombre=request.form['nombre'],
        descripcion=request.form['descripcion'],
        nivel_dificultad=request.form['nivel_dificultad'],
        series_sugeridas=request.form['series_sugeridas'],
        repeticiones_sugeridas=request.form['repeticiones_sugeridas'],
        imagen_url=request.form['imagen_url']
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Ejercicio creado correctamente', 'success')
    return redirect(url_for('lista_ejercicios'))

@app.route('/admin/ejercicios/borrar/<int:id>')
@login_required
def borrar_ejercicio(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    ejercicio = Ejercicio.query.get_or_404(id)
    db.session.delete(ejercicio)
    db.session.commit()
    flash('Ejercicio borrado', 'success')
    return redirect(url_for('lista_ejercicios'))
@app.route('/admin/ejercicios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ejercicio(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    ejercicio = Ejercicio.query.get_or_404(id)
    if request.method == 'POST':
        ejercicio.nombre = request.form['nombre']
        ejercicio.descripcion = request.form['descripcion']
        ejercicio.nivel_dificultad = request.form['nivel_dificultad']
        ejercicio.series_sugeridas = request.form['series_sugeridas']
        ejercicio.repeticiones_sugeridas = request.form['repeticiones_sugeridas']
        ejercicio.imagen_url = request.form['imagen_url']
        db.session.commit()
        flash('Ejercicio actualizado correctamente', 'success')
        return redirect(url_for('lista_ejercicios'))
    return render_template('editar_ejercicio.html', ejercicio=ejercicio)
# ─── VER USUARIOS (ADMIN) ─────────────────────────
@app.route('/admin/usuarios')
@login_required
def lista_usuarios():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    usuarios = Usuario.query.all()
    return render_template('usuarios_admin.html', usuarios=usuarios)
#---------------------------------------------------------------------------
# ─── DASHBOARD USUARIO ────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard_usuario():
    if current_user.es_admin:
        return redirect(url_for('dashboard_admin'))
    total_ejercicios = Ejercicio.query.count()
    total_progresos  = Progreso.query.filter_by(usuario_id=current_user.id).count()
    return render_template('dashboard_usuario.html',
        total_ejercicios=total_ejercicios,
        total_progresos=total_progresos
    )

# ─── CRUD PROGRESO (USUARIO) ──────────────────────
@app.route('/progreso')
@login_required
def lista_progreso():
    ejercicios = Ejercicio.query.all()
    progresos  = Progreso.query.filter_by(usuario_id=current_user.id).order_by(Progreso.fecha.desc()).all()
    return render_template('progreso.html', ejercicios=ejercicios, progresos=progresos)

@app.route('/progreso/crear', methods=['POST'])
@login_required
def crear_progreso():
    from datetime import datetime
    nuevo = Progreso(
        usuario_id=current_user.id,
        ejercicio_id=request.form['ejercicio_id'],
        series_hechas=request.form['series_hechas'],
        repeticiones_hechas=request.form['repeticiones_hechas'],
        nota=request.form['nota'],
        fecha=datetime.now()
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Progreso registrado', 'success')
    return redirect(url_for('lista_progreso'))

@app.route('/progreso/borrar/<int:id>')
@login_required
def borrar_progreso(id):
    progreso = Progreso.query.get_or_404(id)
    if progreso.usuario_id != current_user.id:
        flash('No tienes permiso para borrar este registro', 'danger')
        return redirect(url_for('lista_progreso'))
    db.session.delete(progreso)
    db.session.commit()
    flash('Registro borrado', 'success')
    return redirect(url_for('lista_progreso'))
if __name__ == "__main__":
    app.run(debug=True)