from db import conectar_banco

def registrar_alerta(tipo: str, valor: float):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alertas (tipo, valor, horario) VALUES (%s, %s, NOW())",
        (tipo, valor)
    )
    conn.commit()
    conn.close()
