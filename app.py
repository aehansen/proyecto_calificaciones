from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 

# Creamos la instancia de la aplicación
app = Flask(__name__)
DB_URL = "postgresql://db_calificaciones_user:tPCTKWaZbM7E0zi6pOYJHfYmXcz2crLm@dpg-d4aa0r49c44c73e5qjp0-a.oregon-postgres.render.com/db_calificaciones" 

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Desactiva avisos
db = SQLAlchemy(app) # Ahora esto funciona
# Modelo para los Alumnos
class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Relación: Un alumno puede tener muchas notas
    notas = db.relationship('Nota', backref='alumno', lazy=True)

# Modelo para las Notas
class Nota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False) # ej: "parcial", "tp"
    valor = db.Column(db.Float, nullable=False)
    # Clave foránea: Esta nota pertenece a un alumno
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)
# --- 1. Definimos las Reglas del Curso ---
# Por ahora, las ponemos aquí. Luego las moveremos.
PONDERACION_CURSO = {
    "parciales": 0.60,
    "tps": 0.20,
    "conceptual": 0.20
}

# --- 2. Lógica de Cálculo (la que ya teníamos) ---
def calcular_promedio_lista(lista_notas):
    if not lista_notas:
        return 0
    return sum(lista_notas) / len(lista_notas)

def calcular_nota_final(notas_alumno, ponderaciones):
    promedio_parciales = calcular_promedio_lista(notas_alumno.get("parciales", []))
    promedio_tps = calcular_promedio_lista(notas_alumno.get("tps", []))
    nota_conceptual = notas_alumno.get("conceptual", [0])[0]

    nota_final = (promedio_parciales * ponderaciones["parciales"]) + \
                 (promedio_tps * ponderaciones["tps"]) + \
                 (nota_conceptual * ponderaciones["conceptual"])
    return nota_final

# --- 3. Definimos una "Ruta" o "Endpoint" ---
# Esta es una URL que la gente puede visitar.
@app.route("/")
def inicio():
    alumno_ejemplo = {
        "parciales": [8, 10],
        "tps": [9],
        "conceptual": [10]
    }
    nota = calcular_nota_final(alumno_ejemplo, PONDERACION_CURSO)

    # ¡Ahora usamos el template!
    # Le pasamos la variable 'nota' a HTML como 'nota_calculada'
    return render_template("index.html", nota_calculada=f"{nota:.2f}")

with app.app_context():
    db.create_all()
# --------------------------------------

# Esto permite correr el servidor de desarrollo
if __name__ == '__main__':
    app.run(debug=True)