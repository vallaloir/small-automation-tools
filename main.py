import subprocess

# Exports the notebook as WASM to use locally or upload to GitHub Pages
subprocess.run(
    [
        "uv",
        "run",
        "ruff",
        "check",
        "&",
        "uv",
        "run",
        "ruff",
        "format",
        "&",
        "uv",
        "run",
        "mypy",
        ".",
        "--",
        "--explicit-package-bases",
        "--ignore-missing-imports",
        "&",
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
