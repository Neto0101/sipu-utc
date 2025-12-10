import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

DB_NAME = "sipu.db"

def main():
    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
        SELECT 
            u.matricula,
            u.carrera,
            u.plantel,
            a.grado,
            a.grupo,
            a.turno
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.rol = 'alumno'
    """, conn)

    conn.close()

    # ✅ Simular etiqueta de riesgo (por ahora)
    # Esto se reemplaza cuando ya tengas historial real
    df["riesgo"] = np.random.choice([0,1], size=len(df))

    # ✅ Convertir texto a número
    df = pd.get_dummies(df, columns=["carrera","plantel","turno","grupo","grado"])

    X = df.drop(["matricula","riesgo"], axis=1)
    y = df["riesgo"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    modelo = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo.fit(X_train, y_train)

    joblib.dump(modelo, "modelo_riesgo.pkl")

    print("✅ MODELO DE RIESGO ENTRENADO Y GUARDADO CORRECTAMENTE")

if __name__ == "__main__":
    main()
