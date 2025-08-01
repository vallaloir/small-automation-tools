import marimo

__generated_with = "0.14.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo  # Recommended by Marimo to be imported as first and only

    return (mo,)


@app.cell
def _(mo):
    CURRENT_SCRIPT = "importació"
    script_path = mo.notebook_location() / "public" / f"{CURRENT_SCRIPT}.bat"
    DOWNLOAD_INSTRUCTIONS = f"""Descarregueu-vos [aquest fitxer]({script_path}) i arrossegueu-hi el CSV que voleu importar a Clickedu per fer-lo córrer. Cal que navegueu fins a la pàgina correcta en menys d'un minut des que s'hagi obert el navegador. Un cop el programa hagi fet els canvis i els hagueu comprovat, guardeu en menys de 15 minuts. El programa tancarà el navegador en aquest temps o abans si guardeu els canvis."""

    mo.md(DOWNLOAD_INSTRUCTIONS)
    return


if __name__ == "__main__":
    app.run()
