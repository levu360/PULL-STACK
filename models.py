from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    progresos = db.relationship('Progreso', backref='usuario', lazy=True)

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    nivel_dificultad = db.Column(db.String(20))
    series_sugeridas = db.Column(db.Integer)
    repeticiones_sugeridas = db.Column(db.Integer)
    imagen_url = db.Column(db.String(200))
    progresos = db.relationship('Progreso', backref='ejercicio', lazy=True)

class Progreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    ejercicio_id = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), nullable=False)
    series_hechas = db.Column(db.Integer)
    repeticiones_hechas = db.Column(db.Integer)
    fecha = db.Column(db.DateTime)
    nota = db.Column(db.Text)