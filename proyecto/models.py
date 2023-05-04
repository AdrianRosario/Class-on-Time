from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify
from proyecto import app
import yagmail
import psycopg2
import random
import requests
from werkzeug.security import generate_password_hash, check_password_hash





connection = psycopg2.connect(database='registro', user='postgres', password='1234567890', host='localhost', port='5432')
cursor = connection.cursor()



@app.route('/forgot_password', methods=['GET', 'POST'])
def recuperar_contraseña():
    if request.method == 'POST':
        email = request.form['email']
        
        cursor.execute('SELECT * FROM prueba WHERE email=%s', (email,))
        user = cursor.fetchone()
        if user:
            contraseña = random.randint(0000000,9999999)
            nueva_contraseña = generate_password_hash(str(contraseña))
            cursor.execute('UPDATE prueba set password=%s WHERE email=%s', (nueva_contraseña,email,))
            connection.commit()
            yag = yagmail.SMTP('adrianrosario660@gmail.com', 'gqnwijttnvoppxod')
            body = 'Saludos, tu nueva contraseña es: ' + str(contraseña)
            yag.send(to=email, subject='Contraseña olvidada', contents=body)
            yag.close()
            flash('correo enviado')
        else:
          flash('No se encontró una cuenta con ese correo electrónico.')
    return render_template('recuperar_contraseña.html')




@app.route('/cambiar_password', methods=['GET'])
def mostrar_formulario():
    return render_template('cambiar_password.html')


@app.route('/cambiar_password', methods=['POST'])
def cambiar_password():
    usuario = request.form['nombre']
    nueva_contraseña = request.form['nueva_password']
    _hashed_password = generate_password_hash(nueva_contraseña)

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM prueba WHERE nombre = %s", (usuario,))
    resultado = cursor.fetchone()

    if resultado:
        cursor.execute("UPDATE prueba SET password = %s WHERE nombre = %s", (_hashed_password, usuario))
        connection.commit()
        cursor.close()
        return jsonify({'mensaje': 'Contraseña restablecida correctamente'})
    else:
        return jsonify({'error': 'El usuario no existe'})
       