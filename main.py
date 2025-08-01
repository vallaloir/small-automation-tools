import subprocess

# Formats and exports the notebook as WASM to use locally or upload to GitHub Pages
print("Running ruff check...")
lint = subprocess.run(
    [
        "uv",
        "run",
        "ruff",
        "check",
    ]
)
if lint.returncode != 0:
    exit()

print("Running ruff format...")
format_python_files = subprocess.run(
    [
        "uv",
        "run",
        "ruff",
        "format",
    ]
)
if format_python_files.returncode != 0:
    exit()

print("Running mypy...")
type_check = subprocess.run(
    [
        "uv",
        "run",
        "mypy",
        ".",
        "--explicit-package-bases",
        "--ignore-missing-imports",
    ]
)
if type_check.returncode != 0:
    exit()

print("Building...")
build = subprocess.run(
    [
        "uv",
        "run",
        "build.py",
        "--",
        "--output_dir",
        "_site",
        "--template",
        "templates/tailwind.html.j2",
    ]
)
