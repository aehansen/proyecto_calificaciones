from flask import Flask, render_template, request, redirect, url_for
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
    # 1. Obtenemos TODOS los alumnos desde la base de datos
    alumnos_db = Alumno.query.all()
    
    # 2. Se los pasamos al template HTML
    # (Por ahora, la tabla estará vacía, ¡y eso está bien!)
    return render_template("index.html", alumnos=alumnos_db)

with app.app_context():
    db.create_all()
    
# --- 4. Ruta para AGREGAR ALUMNO ---
@app.route("/agregar_alumno", methods=["POST"])
def agregar_alumno():
    # 1. Obtenemos el nombre desde el formulario
    # El 'name="nombre_alumno"' del <input> se vuelve la clave aquí
    nombre = request.form.get("nombre_alumno")
    
    # 2. Verificamos que no esté vacío
    if nombre:
        # 3. Creamos un nuevo objeto Alumno
        nuevo_alumno = Alumno(nombre=nombre)
        
        # 4. Lo guardamos en la base de datos
        db.session.add(nuevo_alumno)
        db.session.commit()
        
    # 5. Redirigimos al usuario de vuelta a la página principal
    return redirect(url_for("inicio"))
# --------------------------------------

# Esto permite correr el servidor de desarrollo
if __name__ == '__main__':
    app.run(debug=True)