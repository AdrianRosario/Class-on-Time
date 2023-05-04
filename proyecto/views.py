from proyecto import app
from flask import Flask ,render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory
import psycopg2
import psycopg2.extras
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import os
import pathlib
import requests
import json
import proyecto.models

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "368978499153-t27vkp57mo8c01e3bqk92par70cfqs0i.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET= "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"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")


flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://localhost:3000/callback"
)

connection=psycopg2.connect(
            host='localhost',
            user='postgres',
            password='1234567890',
            database='registro',
            port='5432')
     

cursor=connection.cursor()



@app.route('/')
@app.route('/inicio', methods=['GET', 'POST'])
def inicio():
    cursor.execute('SELECT * FROM prueba')
    mostrar = cursor.fetchall()
        
    return render_template('inicio.html',mostrar=mostrar)
    
#login local  

@app.route('/login', methods=['GET','POST'])
def login_local():
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        print(password)
 
        
        cursor.execute('SELECT * FROM prueba WHERE email = %s', (email,))
        
        datos = cursor.fetchone()
 
        if datos:
            password_rs = datos['password']
            print(password_rs)
            
            if check_password_hash(password_rs, password):
                
                session['loggedin'] = True
                session['id'] = datos['id']
                session['email'] = datos['email']
                return redirect(url_for('tareas'))
            else:
                
                flash('Incorrect username/password')
        else:
            
            flash('Incorrect username/password')
       
 
    return render_template('login_local.html')


    

#registro de usuario local

@app.route('/registro_local', methods=['GET','POST'])
def registro_local():
    if request.method == 'POST' and 'nombre' in request.form and 'email' in request.form and 'password' in request.form:
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        _hashed_password = generate_password_hash(password)


        cursor.execute('SELECT * FROM prueba WHERE nombre=%s OR email=%s',(nombre,email,))
        yaexiste = cursor.fetchone()

        if yaexiste:
            flash('Nombre de usuario o correo electrónico ya existen')
            

        else:
            cursor.execute('INSERT INTO prueba (nombre, email, password) values (%s, %s, %s)', (nombre, email,  _hashed_password))
            connection.commit()
            flash('enviado')
        

    return render_template('registro_local.html')




@app.route('/vista')
def vista():
    cursor.execute('Select * from tareas')
    datos = cursor.fetchall()
    return render_template('vista.html',impresiondatos=datos )



@app.route('/logout')
def logout_local():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   return redirect(url_for('login_local'))


#login de inicio de session de google


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper



@app.route("/logingoogle")
def logingoogle():
    auth_url, state = flow.authorization_url(access_type='offline', prompt='select_account')
    session["state"] = state
    return redirect(auth_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["id"] = int(id_info.get("sub")) 
    session["name"] = id_info.get("name")
    session['loggedin'] = True
    session['email'] = id_info.get("email")
    return redirect("/protected_area")



@app.route("/logout")
def logout():
    if 'id_token' in session:
        idinfo = id_token.verify_oauth2_token(session['id_token'], requests.Request())
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return 'Error de autenticación'
        # Revoke the access token of Google
        requests.post(f"https://accounts.google.com/o/oauth2/revoke?token={session['state']}")
        # Clear the Flask session
        session.clear()
        return redirect(url_for('login_local'))
    else:
        return redirect(url_for('login_local'))


@app.route("/protected_area")
@login_is_required
def protected_area():
    return redirect("/tareas")

@app.route('/tareas', methods=['GET','POST'])
def tareas():
     if 'loggedin' in session:
        if request.method=='POST':
            nombre_tareas = request.form['nombre_tareas']
            descripcion = request.form['descripcion']
            tipos = request.form['tipos']

            cursor.execute('INSERT INTO tareas (idcreador,nombe_tareas,descripcion,tipos) values (%s, %s,%s,%s)', (session['id'],nombre_tareas, descripcion,tipos))
            connection.commit()
            return redirect(url_for('tareas'))

        cursor.execute('Select * from tareas where idcreador=%s order by idtareas asc',(session['id'],))
        datos = cursor.fetchall()

        cursor.execute('SELECT * FROM prueba where id=%s',(session['id'],))
        data = cursor.fetchall() 
        

        return render_template('tareas.html',impresiondatos=datos,username=session['email'], impresion=data)
    
     return redirect(url_for('login_local'))

# rutas de editar, eliminar, guardar tareas

@app.route('/delete/<int:id>', methods=['GET','POST'])
def delite(id):
    cursor.execute("DELETE FROM tareas WHERE idtareas = %s", [id])
    cursor.execute("DELETE FROM prueba WHERE id = %s", [id])
    connection.commit()
    return redirect(url_for('inicio'))



@app.route('/edit/<int:id>',methods=['GET','POST'])
def edit(id):
    cursor.execute('SELECT * FROM tareas where idtareas=%s',(id,))
    datos= cursor.fetchall()
    print(datos)

    return render_template('edit.html',impresiondatos=datos)

@app.route('/update/<int:idcreador>',methods=['POST'])
def guardaredit(idcreador):
    if request.method == 'POST':
       nombre_tareas = request.form['nombre_tareas']
       descripcion = request.form['descripcion']

       cursor.execute('update tareas set nombe_tareas=%s where idtareas=%s',(nombre_tareas, idcreador,))
       cursor.execute('update tareas set descripcion=%s where idtareas=%s',(descripcion, idcreador,))
       connection.commit()


    return redirect(url_for('tareas'))