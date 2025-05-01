import subprocess
import winsound
import os
import shutil
from datetime import datetime
import argparse

dont_save = ["save_scenarios.py"]

def main():
    parser = argparse.ArgumentParser(description="Process some flags.")
    # Define a flag
    parser.add_argument('-t', '--test', action='store_true', help='A testing flag (True/False)')
    args = parser.parse_args()

    name = ""
    description = ""
    if args.test:
        name = "Test Model"
        description = "Delete this testing after use"
        method = "solve"
    else:
        # Pide el nombre del usuario
        name = input("Por favor, ingresa el nombre con el que se guardará este modelo:\n")
        description = input("Ingresa la descripción de este modelo:\n")
        method = input("Ingresa el método de resolución (solve, solve-scenarios):\n")
    print(f"Ejecutando {name}, por favor espera...")

    # Ejecuta un comando en la línea de comandos
    comando = f'switch {method}'
    
    try:
        # Ejecuta el comando y espera a que termine
        resultado = subprocess.run(comando, shell=True, check=True)
        
        # Comprueba si el comando se ejecutó sin errores
        if resultado.returncode == 0:
            finished = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            model_path = f"../models/{name}/{finished}"
            print("Terminó la ejecución!")

            # Guardar el Modelo
            if not args.test:
                copiar_todo_excepto(model_path, dont_save)
                with open(model_path+"/description.txt","w") as file:
                    file.write(description)    
                print(f"¡El modelo {name} ha sido guardado éxitosamente!")
            
                # Guardar logs de las ejecuciones
                with open("../private/models_log.txt","a") as file:
                    file.write(f"{finished} Model Name: {name} | Description: {description}\n")

            # Sonido para avisar que la ejecución terminó exitosamente
            winsound.PlaySound("../private/victory.wav", winsound.SND_FILENAME)            
        else:
            print("Hubo un problema con la ejecución del comando.")
            
    except Exception as e:
        # Maneja las excepciones, como errores de ejecución de comandos
        print(f"Error al ejecutar el comando: {e}")
        print(f"¡Asegurate de estar en el ambiente de switch!")
        print(f"Para ver los ambientes: conda env list")
        print(f"Para activar el ambiente: conda activate <tu_ambiente>")
        # Opcional: Hace sonar un sonido de error.
        winsound.MessageBeep(winsound.MB_ICONHAND)  # Sonido de error

def copiar_todo_excepto(target_folder, not_save):
    source_folder = os.getcwd() # Obtiene el directorio actual de ejecución del script

    # Asegurarse de que la carpeta destino existe, si no, se crea
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    for root, dirs, files in os.walk(source_folder):
        # Calculamos la ruta relativa de la carpeta actual en relación a la carpeta de origen
        relative_path = os.path.relpath(root, source_folder)
        target_path = os.path.join(target_folder, relative_path)
        
        # Verificamos si la ruta relativa actual o alguna de sus "partes" está en not_save
        if any(part in not_save for part in relative_path.split(os.path.sep)):
            print(f"Omitiendo {relative_path} y su contenido.")
            continue

        # Para evitar copiar la carpeta destino dentro de sí misma
        if target_folder.startswith(root):
            print(f"Omitiendo la carpeta destino.")
            continue

        # Crear la carpeta en la ubicación de destino si no existe
        if not os.path.exists(target_path) and relative_path not in not_save:
            os.makedirs(target_path)
        
        print(f"Copiando archivos...")
        for file in files:
            # Omitir archivos en not_save
            if file not in not_save:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_path, file)
                shutil.copy(src_file, dst_file)
                # print(f"Copiando {src_file} a {dst_file}...")
            else:
                print(f"Omitiendo archivo {file}")

if __name__ == "__main__":
    main()