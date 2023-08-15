import bcrypt
import pymysql


mysql = pymysql.connect(
    host='localhost',
    user='root',
    password='luis1473',
    database='datos_julia'
)

cur = mysql.cursor()
cur.execute('SELECT idAdministrador, Contraseña FROM Administrador')
administradores = cur.fetchall()

for admin in administradores:
    hashed_password = bcrypt.hashpw(admin[1].encode('utf-8'), bcrypt.gensalt())
    cur.execute('UPDATE Administrador SET Contraseña = %s WHERE idAdministrador = %s', (hashed_password, admin[0]))

mysql.commit()
cur.close()
mysql.close()
