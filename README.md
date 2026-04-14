# Structura

Structura es una aplicación de escritorio para organizar y escribir historias por niveles: historias, capítulos y escenas. Está pensada para autores que quieren una herramienta simple, local y rápida para estructurar proyectos narrativos, escribir contenido y llevar notas y personajes sin depender de servicios externos.

La aplicación está construida con Python y `tkinter`, empaquetada con PyInstaller y preparada para distribuirse en Windows mediante un instalador.

## Qué hace

- Gestiona múltiples proyectos de escritura en formato JSON
- Organiza contenido en una jerarquía de:
  - historias
  - capítulos
  - escenas
- Permite escribir contenido principal y notas por nodo
- Incluye panel de personajes con descripción y resaltado de nombres dentro del editor
- Tiene una pantalla inicial con lista de proyectos recientes/fijados
- Exporta historias a archivos de texto
- Puede compilarse como `.exe` y distribuirse con instalador para Windows

## Estado del proyecto

Versión actual: `1.0.0`

Structura está en una etapa funcional y orientada a escritorio Windows. Ya cuenta con:

- interfaz principal de edición
- pantalla de inicio para abrir proyectos
- empaquetado en ejecutable
- instalador con icono y acceso directo
- separación básica entre UI, dominio, repositorio y controlador

## Tecnologías usadas

- Python 3.13
- `tkinter` / `ttk`
- PyInstaller
- Inno Setup
- Pillow

## Estructura del proyecto

```text
app/
  controllers/    Estado y coordinación de la aplicación
  services/       Reglas de negocio y utilidades
  ui/             Componentes visuales de tkinter
  models.py       Modelos principales del dominio
  repository.py   Carga/guardado del proyecto
  project_library.py
  paths.py

icon/             Iconos de la aplicación
installer/        Script del instalador de Windows
tests/            Pruebas unitarias
main.py           Punto de entrada
main.spec         Configuración de PyInstaller
build_installer.ps1
version.txt
```

## Cómo ejecutar el proyecto en desarrollo

### 1. Crear entorno virtual

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias necesarias

```powershell
python -m pip install pillow pyinstaller
```

### 3. Ejecutar la app

```powershell
python main.py
```

## Datos locales del usuario

Structura guarda sus datos locales en la carpeta del usuario de Windows:

```text
%APPDATA%\Structura
```

Ahí se almacenan:

- biblioteca de proyectos recientes/fijados
- proyectos JSON creados por el usuario

Eso permite que la app instalada funcione correctamente sin escribir dentro de `Program Files`.

## Ejecutable e instalador

### Generar el ejecutable

```powershell
python -m PyInstaller main.spec
```

Salida esperada:

```text
dist\Structura.exe
```

### Generar el instalador

Requiere Inno Setup instalado en Windows.

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

Salida esperada:

```text
dist\installer\Structura-1.0.0-Setup.exe
```

La versión del instalador se toma desde:

```text
version.txt
```

Para crear una nueva versión:

1. cambia el número en `version.txt`
2. vuelve a ejecutar `build_installer.ps1`

## Pruebas

Ejecutar pruebas:

```powershell
python -m unittest discover -s tests -v
```

## Decisiones de diseño

- El almacenamiento actual usa JSON para mantener el proyecto simple y portable
- La app está desacoplada en capas para permitir migrar a SQLite en el futuro sin rehacer toda la UI
- La interfaz prioriza el editor central cuando la ventana se hace más pequeña
- La distribución actual está enfocada en Windows

## Qué se podría mejorar después

- versionado visible dentro de la propia app
- sistema de temas más completo
- exportación a más formatos
- búsqueda global dentro del proyecto
- autoguardado
- migración opcional a SQLite
- integración con GitHub Releases para publicar instaladores

## Licencia

Este proyecto está publicado bajo la licencia MIT.
