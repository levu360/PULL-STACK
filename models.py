from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    encuestas = db.relationship('Encuesta', backref='usuario', lazy=True)

class Calentamiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    duracion_minutos = db.Column(db.Integer)

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    nivel_dificultad = db.Column(db.String(20))
    series_sugeridas = db.Column(db.Integer)
    repeticiones_sugeridas = db.Column(db.Integer)
    imagen_url = db.Column(db.String(200))

class Rutina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)  # Principiante, Medio, Avanzado
    descripcion = db.Column(db.Text)
    ejercicios = db.relationship('RutinaEjercicio', backref='rutina', lazy=True)
    encuestas = db.relationship('Encuesta', backref='rutina', lazy=True)

class RutinaEjercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rutina_id = db.Column(db.Integer, db.ForeignKey('rutina.id'), nullable=False)
    ejercicio_id = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), nullable=False)
    orden = db.Column(db.Integer)
    ejercicio = db.relationship('Ejercicio')

class Encuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    rutina_id = db.Column(db.Integer, db.ForeignKey('rutina.id'), nullable=False)
    satisfaccion = db.Column(db.Integer)   # 1 al 5
    dificultad = db.Column(db.Integer)     # 1 al 5
    duracion = db.Column(db.Integer)       # 1 al 5
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime)