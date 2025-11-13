from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)
# ---------------------------------------------------------------------
# ¡IMPORTANTE! 
# PEGA AQUÍ LA NUEVA "EXTERNAL DATABASE URL" DE TU BASE DE DATOS RE-CREADA
# ---------------------------------------------------------------------
DB_URL = "postgresql://db_calificaciones_gmzd_user:tm8gwVnQqe3mJbwoEuhjncehmHELtXiP@dpg-d4asktje5dus73f4t820-a.oregon-postgres.render.com/db_calificaciones_gmzd" 

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Materia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    alumnos = db.relationship('Alumno', backref='materia', lazy=True, cascade="all, delete-orphan")

class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    notas = db.relationship('Nota', backref='alumno', lazy=True, cascade="all, delete-orphan")
    
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'), nullable=False)

class Nota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False) # ej: "parcial", "tp"
    valor = db.Column(db.Float, nullable=False)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)

PONDERACION_CURSO = {
    "parciales": 0.60,
    "tps": 0.20,
    "conceptual": 0.20
}

def calcular_promedio_lista(lista_notas):
    if not lista_notas:
        return 0
    return sum(lista_notas) / len(lista_notas)

def calcular_nota_final(notas_alumno, ponderaciones):
    promedio_parciales = calcular_promedio_lista(notas_alumno.get("parciales", []))
    promedio_tps = calcular_promedio_lista(notas_alumno.get("tps", []))
    lista_conceptual = notas_alumno.get("conceptual", []) 
    if lista_conceptual:
        nota_conceptual = lista_conceptual[0]
    else:
        nota_conceptual = 0
    nota_final = (promedio_parciales * ponderaciones["parciales"]) + \
                 (promedio_tps * ponderaciones["tps"]) + \
                 (nota_conceptual * ponderaciones["conceptual"])
    return nota_final

def procesar_notas_db(alumno_obj):
    notas_dict = {"parciales": [], "tps": [], "conceptual": []}
    for nota in alumno_obj.notas:
        if nota.tipo == 'parcial':
            notas_dict['parciales'].append(nota.valor)
        elif nota.tipo == 'tp':
            notas_dict['tps'].append(nota.valor)
        elif nota.tipo == 'conceptual':
            notas_dict['conceptual'].append(nota.valor)
    return notas_dict

@app.route("/")
def inicio():
    materias = Materia.query.all()
    return render_template("index.html", materias=materias)

@app.route("/agregar_materia", methods=["POST"])
def agregar_materia():
    nombre = request.form.get("nombre_materia")
    if nombre:
        nueva_materia = Materia(nombre=nombre)
        db.session.add(nueva_materia)
        db.session.commit()
    return redirect(url_for("inicio"))

@app.route("/materia/<int:materia_id>")
def detalle_materia(materia_id):
    materia = Materia.query.get_or_404(materia_id)
    
    alumnos_db = materia.alumnos 
    
    alumnos_calculados = []
    for alumno in alumnos_db:
        notas_dict = procesar_notas_db(alumno)
        nota_final = calcular_nota_final(notas_dict, PONDERACION_CURSO)
        alumnos_calculados.append({
            "nombre": alumno.nombre,
            "id": alumno.id,
            "nota_final": nota_final
        })
        
    return render_template(
        "detalle_materia.html", 
        materia=materia,
        alumnos_calculados=alumnos_calculados,
        alumnos_db=alumnos_db 
    )

@app.route("/agregar_alumno", methods=["POST"])
def agregar_alumno():
    nombre = request.form.get("nombre_alumno")
    materia_id = request.form.get("materia_id") 
    
    if nombre and materia_id:
        nuevo_alumno = Alumno(nombre=nombre, materia_id=int(materia_id))
        db.session.add(nuevo_alumno)
        db.session.commit()
        
    return redirect(url_for("detalle_materia", materia_id=materia_id))

@app.route("/agregar_nota", methods=["POST"])
def agregar_nota():
    alumno_id = request.form.get("alumno_id")
    tipo_nota = request.form.get("tipo_nota")
    valor_nota = request.form.get("valor_nota")
    
    materia_id_redirect = None 

    if alumno_id and tipo_nota and valor_nota:
        alumno = Alumno.query.get(int(alumno_id))
        if alumno:
            materia_id_redirect = alumno.materia_id
            nueva_nota = Nota(
                tipo=tipo_nota,
                valor=float(valor_nota),
                alumno_id=int(alumno_id) 
            )
            db.session.add(nueva_nota)
            db.session.commit()
            
    if materia_id_redirect:
        return redirect(url_for("detalle_materia", materia_id=materia_id_redirect))
    else:
        return redirect(url_for("inicio"))

@app.route("/borrar_alumno/<int:alumno_id>", methods=["POST"])
def borrar_alumno(alumno_id):
    alumno_a_borrar = Alumno.query.get_or_404(alumno_id)
    materia_id_redirect = alumno_a_borrar.materia_id # Guardamos el ID
    
    db.session.delete(alumno_a_borrar)
    db.session.commit()
    
    return redirect(url_for("detalle_materia", materia_id=materia_id_redirect))


@app.route("/alumno/<int:alumno_id>")
def detalle_alumno(alumno_id):
    alumno = Alumno.query.get_or_404(alumno_id)
    return render_template("detalle_alumno.html", alumno=alumno)

@app.route("/borrar_nota/<int:nota_id>", methods=["POST"])
def borrar_nota(nota_id):
    nota_a_borrar = Nota.query.get_or_404(nota_id)
    alumno_id_redirect = nota_a_borrar.alumno_id
    db.session.delete(nota_a_borrar)
    db.session.commit()
    return redirect(url_for('detalle_alumno', alumno_id=alumno_id_redirect))

@app.route("/editar_nota/<int:nota_id>", methods=["GET"])
def editar_nota(nota_id):
    nota = Nota.query.get_or_404(nota_id)
    return render_template("editar_nota.html", nota=nota)

@app.route("/actualizar_nota/<int:nota_id>", methods=["POST"])
def actualizar_nota(nota_id):
    nota_a_actualizar = Nota.query.get_or_404(nota_id)
    if request.method == 'POST':
        nuevo_tipo = request.form.get("tipo_nota")
        nuevo_valor = request.form.get("valor_nota")
        if nuevo_tipo and nuevo_valor:
            nota_a_actualizar.tipo = nuevo_tipo
            nota_a_actualizar.valor = float(nuevo_valor)
            db.session.commit()
    return redirect(url_for('detalle_alumno', alumno_id=nota_a_actualizar.alumno_id))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)