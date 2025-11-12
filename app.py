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
    
    # 1. Obtenemos la lista de notas conceptuales.
    lista_conceptual = notas_alumno.get("conceptual", []) 
    
    # 2. Verificamos si la lista NO está vacía.
    if lista_conceptual:
        # Si tiene notas, usamos la primera (asumimos una sola nota)
        nota_conceptual = lista_conceptual[0]
    else:
        # Si está vacía, la nota conceptual es 0
        nota_conceptual = 0

    nota_final = (promedio_parciales * ponderaciones["parciales"]) + \
                 (promedio_tps * ponderaciones["tps"]) + \
                 (nota_conceptual * ponderaciones["conceptual"])
    return nota_final
def procesar_notas_db(alumno_obj):
    """
    Toma un objeto Alumno de la DB y convierte su lista de notas
    en el diccionario que 'calcular_nota_final' espera.
    """
    notas_dict = {
        "parciales": [],
        "tps": [],
        "conceptual": []
    }
    # alumno_obj.notas es la lista de objetos Nota gracias a la 'relationship'
    for nota in alumno_obj.notas:
        if nota.tipo == 'parcial':
            notas_dict['parciales'].append(nota.valor)
        elif nota.tipo == 'tp':
            notas_dict['tps'].append(nota.valor)
        elif nota.tipo == 'conceptual':
            notas_dict['conceptual'].append(nota.valor)
    return notas_dict
# --- 3. Definimos una "Ruta" o "Endpoint" ---
# Esta es una URL que la gente puede visitar.
@app.route("/")
def inicio():
    # 1. Obtenemos TODOS los alumnos desde la base de datos
    alumnos_db = Alumno.query.all()
    
    alumnos_calculados = []
    for alumno in alumnos_db:
        # 2. Para cada alumno, procesamos sus notas
        notas_dict = procesar_notas_db(alumno)
        
        # 3. Calculamos su nota final
        nota_final = calcular_nota_final(notas_dict, PONDERACION_CURSO)
        
        # 4. Creamos un diccionario limpio para el template
        alumnos_calculados.append({
            "nombre": alumno.nombre,
            "id": alumno.id,
            "nota_final": nota_final
        })
        
    # 5. Se los pasamos al template HTML
    #    Pasamos 'alumnos_calculados' para la tabla
    #    Pasamos 'alumnos_db' para el dropdown del formulario
    return render_template(
        "index.html", 
        alumnos_calculados=alumnos_calculados,
        alumnos_db=alumnos_db 
    )

# --- RUTA AGREGAR ALUMNO (Sin cambios) ---
@app.route("/agregar_alumno", methods=["POST"])
def agregar_alumno():
    # 1. Obtenemos el nombre desde el formulario
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


# --- ¡NUEVA RUTA PARA AGREGAR NOTA! ---
@app.route("/agregar_nota", methods=["POST"])
def agregar_nota():
    # 1. Obtenemos todos los datos del formulario
    alumno_id = request.form.get("alumno_id")
    tipo_nota = request.form.get("tipo_nota")
    valor_nota = request.form.get("valor_nota")

    # 2. Verificamos que los datos existan
    if alumno_id and tipo_nota and valor_nota:
        # 3. Creamos el nuevo objeto Nota
        #    'alumno_id' es la clave foránea que lo vincula al alumno
        nueva_nota = Nota(
            tipo=tipo_nota,
            valor=float(valor_nota),
            alumno_id=int(alumno_id) 
        )
        
        # 4. Guardamos la nota en la base de datos
        db.session.add(nueva_nota)
        db.session.commit()
        
    # 5. Redirigimos al usuario de vuelta a la página principal
    return redirect(url_for("inicio"))
# --------------------------------------

@app.route("/alumno/<int:alumno_id>")
def detalle_alumno(alumno_id):
    # 1. Buscamos al alumno específico por su ID.
    # .get_or_404() es una función genial: 
    #   - Intenta encontrar el alumno.
    #   - Si no lo encuentra, automáticamente muestra una página de error 404.
    alumno = Alumno.query.get_or_404(alumno_id)
    
    # 2. Renderizamos el template "detalle_alumno.html"
    return render_template("detalle_alumno.html", alumno=alumno)

with app.app_context():
    db.create_all()
# Esto permite correr el servidor de desarrollo
if __name__ == '__main__':
    app.run(debug=True)