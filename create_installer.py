import os
import subprocess
from pathlib import Path
from modules.config import APP_VERSION as CURRENT_VERSION


def create_installer_final():
    print(f"🎯 CREANDO INSTALADOR PROFESIONAL (BIGestPwd {CURRENT_VERSION})...")
    print("=" * 60)

    project_dir = Path(__file__).parent
    source_exe_name = f"BIGestPwd_{CURRENT_VERSION}.exe"
    installer_name = f"Instalador_BIGestPwd_{CURRENT_VERSION}"

    required_files = [
        (f"dist/{source_exe_name}", "Ejecutable compilado"),
        ("icon.ico", "Icono de la aplicación"),
        ("LICENSE", "Licencia de uso"),
    ]

    print("📋 Paso 1: Verificando archivos fuente...")
    all_ok = True
    for file_path, description in required_files:
        full_path = project_dir / file_path
        if full_path.exists():
            print(f"   ✅ {description} encontrado")
        else:
            print(f"   ❌ ERROR: {description} NO ENCONTRADO ({file_path})")
            all_ok = False

    if not all_ok:
        print("\n❌ Faltan archivos críticos. Por favor ejecuta 'build.py' primero.")
        return

    print("\n📝 Paso 2: Generando script de Inno Setup (.iss)...")

    iss_content = f"""#define MyAppName "BIGestPwd"
#define MyAppVersion "{CURRENT_VERSION}"
#define MyAppPublisher "BIGestPwd Security Team"
#define SourceExeName "{source_exe_name}"
#define DestExeName "BIGestPwd.exe"

[Setup]
AppId={{{{B1G3STPWD-SECURE-VAULT-2024}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppVerName={{#MyAppName}} {{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
DefaultDirName={{autopf}}\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={{app}}\icon.ico
Compression=lzma2/max
SolidCompression=yes
LicenseFile=LICENSE
OutputDir=Output
OutputBaseFilename={installer_name}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el &Escritorio"; GroupDescription: "Iconos adicionales:"

[Files]
Source: "dist\{{#SourceExeName}}"; DestDir: "{{app}}"; DestName: "{{#DestExeName}}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\{{#MyAppName}}"; Filename: "{{app}}\{{#DestExeName}}"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\icon.ico"
Name: "{{group}}\Desinstalar {{#MyAppName}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\{{#MyAppName}}"; Filename: "{{app}}\{{#DestExeName}}"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{{app}}\{{#DestExeName}}"; Description: "Ejecutar {{#MyAppName}} ahora"; Flags: nowait postinstall
"""

    iss_path = project_dir / "installer_final.iss"
    try:
        with open(iss_path, "w", encoding="utf-8") as f:
            f.write(iss_content)
        print(f"   ✅ Script .iss generado correctamente: {iss_path}")
    except Exception as e:
        print(f"   ❌ Error escribiendo el script: {e}")
        return

    print("\n📦 Paso 3: Compilando instalador con Inno Setup...")

    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
    ]

    inno_compiler = None
    for path in inno_paths:
        if os.path.exists(path):
            inno_compiler = path
            print(f"   ✅ Compilador encontrado en: {path}")
            break

    if not inno_compiler:
        print("❌ ERROR CRÍTICO: No se encontró Inno Setup (ISCC.exe).")
        print(
            "   Por favor instala Inno Setup 6 desde: https://jrsoftware.org/isdl.php"
        )
        return

    try:
        print("   ⏳ Compilando... (Espere unos segundos)")
        result = subprocess.run(
            [inno_compiler, str(iss_path)], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("   ✅ Compilación de Inno Setup finalizada.")
        else:
            print("   ❌ Error en Inno Setup:")
            print(result.stderr)
            return

    except Exception as e:
        print(f"   ❌ Error ejecutando ISCC: {e}")
        return

    output_dir = project_dir / "Output"
    setup_exe = output_dir / f"{installer_name}.exe"

    if setup_exe.exists():
        size_mb = setup_exe.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("🎉 ¡FELICIDADES! INSTALADOR PROFESIONAL LISTO")
        print(f"{'='*60}")
        print(f"📂 Ubicación: {setup_exe}")
        print(f"📏 Tamaño:    {size_mb:.2f} MB")
        print("\n🚀 CARACTERÍSTICAS:")
        print(f"   ✓ Versión {CURRENT_VERSION} Configurada")
        print("   ✓ Estandarización de nombre (BIGestPwd.exe)")
        print("   ✓ Acceso directo limpio")
        print("\n👉 Todo listo para subir el Release a GitHub.")

        try:
            os.startfile(output_dir)
        except:
            pass
    else:
        print("❌ Algo salió mal. No se encontró el archivo final.")


if __name__ == "__main__":
    create_installer_final()
