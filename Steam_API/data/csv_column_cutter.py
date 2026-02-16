import pandas as pd
import argparse

def eliminar_columnas_csv(archivo_entrada, archivo_salida, columnas_a_borrar):
    """
    Lee un archivo CSV, elimina las columnas indicadas y guarda el resultado.
    
    :param archivo_entrada: Ruta del archivo CSV original.
    :param archivo_salida: Ruta donde se guardará el nuevo archivo CSV.
    :param columnas_a_borrar: Lista (array) de strings con los nombres de las columnas a eliminar.
    """
    try:
        # 1. Cargar el CSV en un DataFrame
        df = pd.read_csv(archivo_entrada)
        
        print(f"Columnas originales ({len(df.columns)}): {list(df.columns)}")
        
        # 2. Eliminar las columnas
        # errors='ignore' hace que si te equivocas en el nombre de una columna o no existe, 
        # el script no falle y simplemente la ignore.
        df = df.drop(columns=columnas_a_borrar, errors='ignore')
        
        # 3. Guardar el DataFrame modificado en un nuevo archivo CSV
        df.to_csv(archivo_salida, index=False)
        
        print(f"\n¡Éxito! Archivo guardado en '{archivo_salida}'.")
        print(f"Columnas resultantes ({len(df.columns)}): {list(df.columns)}")
        
    except FileNotFoundError:
        print(f"Error: No se ha encontrado el archivo '{archivo_entrada}'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    # Configurar argparse
    parser = argparse.ArgumentParser(description="Elimina columnas específicas de un archivo CSV.")
    
    # Argumento para el archivo de entrada
    parser.add_argument(
        "-i", "--input", 
        type=str, 
        required=True, 
        help="Ruta del archivo CSV original (ej. steam_games.csv)"
    )
    
    # Argumento para el archivo de salida
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        required=True, 
        help="Ruta donde se guardará el nuevo CSV (ej. steam_limpio.csv)"
    )
    
    # Argumento para las columnas a borrar (nargs='+' permite pasar múltiples valores separados por espacio)
    parser.add_argument(
        "-c", "--columns", 
        type=str, 
        nargs='+', 
        required=True, 
        help="Lista de columnas a eliminar separadas por espacios (ej. website support_url movies)"
    )
    
    # Parsear los argumentos introducidos en la terminal
    args = parser.parse_args()
    
    # Ejecutar la función con los argumentos recibidos
    eliminar_columnas_csv(args.input, args.output, args.columns)