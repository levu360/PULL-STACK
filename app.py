from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Ejercicio, Rutina, RutinaEjercicio, Calentamiento, Encuesta

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
        if Usuario.query.filter_by(email=email).first():
            flash('Ese email ya está registrado', 'danger')
            return redirect(url_for('registro'))
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

# ─── CREAR ADMIN (temporal) ───────────────────────
@app.route('/crear-admin')
def crear_admin():
    if not Usuario.query.filter_by(email='admin@calistenia.com').first():
        admin = Usuario(
            nombre='Admin',
            email='admin@calistenia.com',
            password=generate_password_hash('admin123'),
            es_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        return 'Admin creado'
    return 'El admin ya existe'
# ─── DASHBOARD ADMIN ──────────────────────────────
@app.route('/admin')
@login_required
def dashboard_admin():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    
    total_usuarios    = Usuario.query.count()
    total_ejercicios  = Ejercicio.query.count()
    total_rutinas     = Rutina.query.count()
    total_encuestas   = Encuesta.query.count()
    
    # ========== DATOS PARA GRÁFICO DE SATISFACCIÓN ==========
    from sqlalchemy import func
    
    rutinas = Rutina.query.all()
    rutinas_nombres = []
    satisfaccion_promedio = []
    
    for rutina in rutinas:
        rutinas_nombres.append(rutina.nombre)
        promedio = db.session.query(func.avg(Encuesta.satisfaccion)).filter(Encuesta.rutina_id == rutina.id).scalar()
        satisfaccion_promedio.append(round(promedio or 0, 1))
    
    return render_template('dashboard_admin.html',
        total_usuarios=total_usuarios,
        total_ejercicios=total_ejercicios,
        total_rutinas=total_rutinas,
        total_encuestas=total_encuestas,
        rutinas_nombres=rutinas_nombres,
        satisfaccion_promedio=satisfaccion_promedio
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

# ─── VER USUARIOS (ADMIN) ─────────────────────────
@app.route('/admin/usuarios')
@login_required
def lista_usuarios():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    usuarios = Usuario.query.all()
    return render_template('usuarios_admin.html', usuarios=usuarios)

# ─── DASHBOARD USUARIO ────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard_usuario():
    if current_user.es_admin:
        return redirect(url_for('dashboard_admin'))
    
    total_rutinas = Rutina.query.count()
    mis_encuestas = Encuesta.query.filter_by(usuario_id=current_user.id).count()
    
    # DATOS PARA EL GRÁFICO DE PROGRESO
    mis_encuestas_detalle = Encuesta.query.filter_by(usuario_id=current_user.id).order_by(Encuesta.fecha).all()
    
    fechas = []
    satisfaccion_historial = []
    
    for encuesta in mis_encuestas_detalle:
        if encuesta.fecha:
            fechas.append(encuesta.fecha.strftime('%d/%m'))
            satisfaccion_historial.append(encuesta.satisfaccion)
    
    return render_template('dashboard_usuario.html',
        total_rutinas=total_rutinas,
        mis_encuestas=mis_encuestas,
        fechas=fechas,
        satisfaccion_historial=satisfaccion_historial
    )
# ─── CRUD CALENTAMIENTOS (ADMIN) ──────────────────
@app.route('/admin/calentamientos')
@login_required
def lista_calentamientos():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    calentamientos = Calentamiento.query.all()
    return render_template('calentamientos_admin.html', calentamientos=calentamientos)

@app.route('/admin/calentamientos/crear', methods=['POST'])
@login_required
def crear_calentamiento():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    nuevo = Calentamiento(
        nombre=request.form['nombre'],
        descripcion=request.form['descripcion'],
        duracion_minutos=request.form['duracion_minutos']
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Calentamiento creado correctamente', 'success')
    return redirect(url_for('lista_calentamientos'))

@app.route('/admin/calentamientos/borrar/<int:id>')
@login_required
def borrar_calentamiento(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    c = Calentamiento.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('Calentamiento borrado', 'success')
    return redirect(url_for('lista_calentamientos'))
#------------------------------------------------------------------------------------
# ─── CRUD RUTINAS (ADMIN) ─────────────────────────
@app.route('/admin/rutinas')
@login_required
def lista_rutinas():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    rutinas = Rutina.query.all()
    return render_template('rutinas_admin.html', rutinas=rutinas)

@app.route('/admin/rutinas/crear', methods=['POST'])
@login_required
def crear_rutina():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    nueva = Rutina(
        nombre=request.form['nombre'],
        nivel=request.form['nivel'],
        descripcion=request.form['descripcion']
    )
    db.session.add(nueva)
    db.session.commit()
    flash('Rutina creada correctamente', 'success')
    return redirect(url_for('lista_rutinas'))

@app.route('/admin/rutinas/borrar/<int:id>')
@login_required
def borrar_rutina(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    rutina = Rutina.query.get_or_404(id)
    db.session.delete(rutina)
    db.session.commit()
    flash('Rutina borrada', 'success')
    return redirect(url_for('lista_rutinas'))

@app.route('/admin/rutinas/<int:id>/ejercicios')
@login_required
def rutina_ejercicios(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    rutina = Rutina.query.get_or_404(id)
    ejercicios = Ejercicio.query.all()
    return render_template('rutina_ejercicios.html', rutina=rutina, ejercicios=ejercicios)

@app.route('/admin/rutinas/<int:id>/ejercicios/agregar', methods=['POST'])
@login_required
def agregar_ejercicio_rutina(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    nuevo = RutinaEjercicio(
        rutina_id=id,
        ejercicio_id=request.form['ejercicio_id'],
        orden=request.form['orden']
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Ejercicio agregado a la rutina', 'success')
    return redirect(url_for('rutina_ejercicios', id=id))

@app.route('/admin/rutinas/<int:rutina_id>/ejercicios/quitar/<int:re_id>')
@login_required
def quitar_ejercicio_rutina(rutina_id, re_id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    re = RutinaEjercicio.query.get_or_404(re_id)
    db.session.delete(re)
    db.session.commit()
    flash('Ejercicio quitado de la rutina', 'success')
    return redirect(url_for('rutina_ejercicios', id=rutina_id))

# ─── RUTINAS USUARIO ──────────────────────────────
@app.route('/rutinas')
@login_required
def lista_rutinas_usuario():
    principiante = Rutina.query.filter_by(nivel='Principiante').all()
    medio        = Rutina.query.filter_by(nivel='Medio').all()
    avanzado     = Rutina.query.filter_by(nivel='Avanzado').all()
    return render_template('rutinas_usuario.html',
        principiante=principiante, medio=medio, avanzado=avanzado)

@app.route('/rutinas/<int:id>')
@login_required
def detalle_rutina(id):
    rutina = Rutina.query.get_or_404(id)
    calentamientos = Calentamiento.query.all()
    return render_template('detalle_rutina.html', rutina=rutina, calentamientos=calentamientos)

@app.route('/rutinas/<int:id>/encuesta', methods=['POST'])
@login_required
def enviar_encuesta(id):
    from datetime import datetime
    nueva = Encuesta(
        usuario_id=current_user.id,
        rutina_id=id,
        satisfaccion=request.form['satisfaccion'],
        dificultad=request.form['dificultad'],
        duracion=request.form['duracion'],
        comentario=request.form['comentario'],
        fecha=datetime.now()
    )
    db.session.add(nueva)
    db.session.commit()
    flash('¡Gracias por tu opinión!', 'success')
    return redirect(url_for('lista_rutinas_usuario'))
#----------------------------------------------------------
# ─── VER ENCUESTAS (ADMIN) ────────────────────────
@app.route('/admin/encuestas')
@login_required
def lista_encuestas():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    encuestas = Encuesta.query.order_by(Encuesta.fecha.desc()).all()
    return render_template('encuestas_admin.html', encuestas=encuestas)

# ─── BACKUP BASE DE DATOS (ADMIN) ─────────────────
@app.route('/admin/backup')
@login_required
def backup_db():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    from flask import send_file
    from datetime import datetime
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        'instance/calistenia.db',
        as_attachment=True,
        download_name=f'backup_{fecha}.db'
    )

# ─── RESTAURAR BACKUP (ADMIN) ─────────────────────
@app.route('/admin/restaurar', methods=['POST'])
@login_required
def restaurar_backup():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    import shutil
    from datetime import datetime
    archivo = request.files.get('backup_file')
    if not archivo or not archivo.filename.endswith('.db'):
        flash('Por favor sube un archivo .db válido', 'danger')
        return redirect(url_for('dashboard_admin'))
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2('instance/calistenia.db', f'instance/antes_restaurar_{fecha}.db')
    archivo.save('instance/calistenia.db')
    flash('Base de datos restaurada correctamente', 'success')
    return redirect(url_for('dashboard_admin'))

# ─── ELIMINAR USUARIO (ADMIN) ─────────────────────
@app.route('/admin/usuarios/borrar/<int:id>')
@login_required
def borrar_usuario(id):
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    usuario = Usuario.query.get_or_404(id)
    if usuario.es_admin:
        flash('No puedes eliminar al administrador', 'danger')
        return redirect(url_for('lista_usuarios'))
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('lista_usuarios'))
# ─── CALENTAMIENTO ANTES DE RUTINA ────────────────
@app.route('/calentamiento/<int:rutina_id>')
@login_required
def calentamiento(rutina_id):
    return render_template('calentamiento.html', rutina_id=rutina_id)

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/admin/rutinas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_rutina():
    if not current_user.es_admin:
        return redirect(url_for('dashboard_usuario'))
    
    ejercicios = Ejercicio.query.order_by(Ejercicio.nombre).all()
    
    if request.method == 'POST':
        # Crear la rutina
        nombre = request.form['nombre']
        nivel = request.form['nivel']
        descripcion = request.form['descripcion']
        dia_semana = request.form['dia_semana']
        
        nueva_rutina = Rutina(
            nombre=nombre,
            nivel=nivel,
            descripcion=descripcion,
            dia_semana=dia_semana
        )
        db.session.add(nueva_rutina)
        db.session.flush()  # Para obtener el ID sin hacer commit aún
        
        # Asignar los ejercicios seleccionados
        ejercicios_ids = request.form.getlist('ejercicios')
        for i, ejercicio_id in enumerate(ejercicios_ids):
            re = RutinaEjercicio(
                rutina_id=nueva_rutina.id,
                ejercicio_id=int(ejercicio_id),
                orden=i+1
            )
            db.session.add(re)
        
        db.session.commit()
        flash('Rutina creada con ejercicios asignados', 'success')
        return redirect(url_for('lista_rutinas_admin'))
    
    return render_template('nueva_rutina.html', ejercicios=ejercicios)