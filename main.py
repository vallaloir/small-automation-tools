import subprocess

# Exports the notebook as WASM to use locally or upload to GitHub Pages
subprocess.run(
    [
        "uv",
        "run",
        "build.py",
        "--output_dir",
        "_site",
        "--template",
        "templates/tailwind.html.j2",
    ]
)
