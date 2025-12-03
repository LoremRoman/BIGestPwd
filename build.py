import os
import subprocess
import shutil
import time
from pathlib import Path


def build_final():
    print("INICIANDO COMPILACIÓN DE BIGestPwd 2.4...")

    # 1. Configurar rutas
    base_dir = Path(__file__).parent
    main_script = base_dir / "main.py"
    icon_file = base_dir / "icon.ico"
    license_file = base_dir / "LICENSE.txt"
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"

    # 2. Verificaciones
    if not main_script.exists():
        print("❌ Error: No se encuentra main.py")
        return

    if not icon_file.exists():
        print("⚠️ Advertencia: No se encuentra icon.ico (Se usará icono por defecto)")
        icon_arg = []
        data_arg_icon = []
    else:
        print("✅ Icono encontrado.")
        icon_arg = [f"--icon={icon_file}"]
        data_arg_icon = [f"--add-data={icon_file};."]

    if license_file.exists():
        print("✅ Licencia encontrada.")
        data_arg_license = [f"--add-data={license_file};."]
    else:
        data_arg_license = []

    print("🧹 Limpiando compilaciones anteriores...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    spec_files = list(base_dir.glob("*.spec"))
    for f in spec_files:
        try:
            os.remove(f)
        except:
            pass

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean",
        "--name=BIGestPwd_2.4",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=sqlite3",
        "--hidden-import=requests",
        "--hidden-import=packaging",
        "--hidden-import=packaging.version",
    ]

    cmd.extend(icon_arg)
    cmd.extend(data_arg_icon)
    cmd.extend(data_arg_license)

    cmd.append(str(main_script))

    print("\n🔨 Ejecutando PyInstaller...")
    print("   (Incluyendo soporte para actualizaciones automáticas)")
    print("\n⏳ Compilando... (Esto puede tardar unos minutos)\n")

    try:
        start_time = time.time()
        process = subprocess.run(cmd, check=True)
        end_time = time.time()

        print(f"\n✅ Compilación finalizada en {end_time - start_time:.2f} segundos.")

        exe_path = dist_dir / "BIGestPwd_2.4.exe"

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 50)
            print(f"🎉 ÉXITO: Ejecutable creado correctamente")
            print(f"📂 Ubicación: {exe_path}")
            print(f"📏 Tamaño: {size_mb:.2f} MB")
            print("=" * 50)

            data_folder = dist_dir / "data"
            if not data_folder.exists():
                os.makedirs(data_folder)

            print("\n¿Quieres probar el ejecutable ahora?")
            resp = input(
                "Escribe 's' para sí, cualquier otra tecla para salir: "
            ).lower()
            if resp == "s":
                print("🚀 Lanzando aplicación...")
                os.startfile(exe_path)
        else:
            print("❌ Error: El comando terminó pero no se encuentra el .exe")

    except subprocess.CalledProcessError as e:
        print("\n❌ FATAL: Error durante la compilación.")
        print(f"Código de error: {e.returncode}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


if __name__ == "__main__":
    build_final()
