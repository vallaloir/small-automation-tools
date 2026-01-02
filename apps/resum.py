import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo  # Recommended by Marimo to be imported as first and only
    return (mo,)


@app.cell
def _():
    import calendar
    import numpy as np
    import polars as pl
    return calendar, np, pl


@app.cell
def _(mo):
    # Define necessary constants
    PERMANENT_TYPE = 1
    TEMPORARY_TYPE = 2
    TITLE_TEMPORARY_PRICE = (
        "**Introduïu els preus en funció dels dies que s'ha quedat l'alumne:**"
    )
    TEMPORARY_PRICE_LABEL = "Preu (en €) per >{min_days} dies:"
    TITLE_PERMANENT_PRICE = "**Introduïu el descompte per faltar un dia:**"
    PERMANENT_PRICE_LABEL = "Descompte{type} (en €, serà considerat negatiu):"
    TITLE_MIN_DAYS_TO_DISCOUNT = (
        "**Introduïu el mínim nombre de dies per començar a descomptar absències:**"
    )
    SAVE_LABEL = "Utilitza els preus i descomptes modificats"
    MAIN_FILE_LABEL = "Selecciona el fitxer amb les files per agrupar:"
    DOWNLOAD_LABEL = "Descarrega l'Excel"
    N_ROWS_WITHOUT_RAW_DATA = 4
    FILE_NAME_COL = "Tarifa"
    COLS_TO_BE_REMOVED = [
        "Dates",
        "Menú",
        FILE_NAME_COL,
        "presents",
        "absències",
        "percentatge",
        "Total",
    ]
    STUDENT_NAME_COL = "Resum d'assistència"
    YEAR_COL = "Curs/classe"
    LEVEL_COL = "Nivell"
    CATEGORY_COL = "Inscripció"
    ENCODING = "ISO-8859-1"
    CATEGORIES = {
        "Inscripció permanent": {"code": PERMANENT_TYPE, "type_to_count": "A"},
        "Inscripció puntual": {"code": TEMPORARY_TYPE, "type_to_count": "P"},
    }
    PRICE_COL = "price"
    PRICE_LABEL = "Selecciona el fitxer amb els preus (alumnes puntuals):"
    DISCOUNT_COL = "discount"
    DISCOUNT_LABEL = (
        "Selecciona el fitxer amb els descomptes per faltes (alumnes permanents):"
    )
    MIN_DAYS_TO_DISCOUNT = 9
    MIN_DAYS_TO_DISCOUNT_LABEL = "Mínim de dies:"
    GROUP_TO_SINGLE_LINE_TOOL_LABEL = "Menjador"
    GROUP_TO_CATEGORY_LINE_TOOL_LABEL = "Acollida"
    TOOLS = [
        {"label": GROUP_TO_SINGLE_LINE_TOOL_LABEL, "code": "unique"},
        {"label": GROUP_TO_CATEGORY_LINE_TOOL_LABEL, "code": "category"},
    ]
    UNIQUE_TOOL_CODE = "unique"
    UNIQUE_TOOL_LABEL = next(
        filter(lambda tool: tool["code"] == UNIQUE_TOOL_CODE, TOOLS), {"label": None}
    )["label"]

    tool_selection = mo.ui.radio(
        options=[GROUP_TO_SINGLE_LINE_TOOL_LABEL, GROUP_TO_CATEGORY_LINE_TOOL_LABEL],
        inline=True,
    )

    def is_unique_tool_selected() -> bool:
        return tool_selection.value == UNIQUE_TOOL_LABEL

    tool_selection
    return (
        CATEGORIES,
        CATEGORY_COL,
        COLS_TO_BE_REMOVED,
        DISCOUNT_COL,
        DISCOUNT_LABEL,
        DOWNLOAD_LABEL,
        ENCODING,
        FILE_NAME_COL,
        LEVEL_COL,
        MAIN_FILE_LABEL,
        MIN_DAYS_TO_DISCOUNT,
        MIN_DAYS_TO_DISCOUNT_LABEL,
        N_ROWS_WITHOUT_RAW_DATA,
        PERMANENT_PRICE_LABEL,
        PERMANENT_TYPE,
        PRICE_COL,
        PRICE_LABEL,
        SAVE_LABEL,
        STUDENT_NAME_COL,
        TEMPORARY_PRICE_LABEL,
        TEMPORARY_TYPE,
        TITLE_MIN_DAYS_TO_DISCOUNT,
        TITLE_PERMANENT_PRICE,
        TITLE_TEMPORARY_PRICE,
        YEAR_COL,
        is_unique_tool_selected,
        tool_selection,
    )


@app.cell
def _(PRICE_LABEL, mo):
    prices = mo.ui.file(
        filetypes=[".csv"],
        label=PRICE_LABEL,
        kind="area",
    )
    prices
    return (prices,)


@app.cell
def _(DISCOUNT_LABEL, mo):
    discounts = mo.ui.file(
        filetypes=[".csv"],
        label=DISCOUNT_LABEL,
        kind="area",
    )
    discounts
    return (discounts,)


@app.cell
def _(
    DISCOUNT_COL,
    MIN_DAYS_TO_DISCOUNT,
    MIN_DAYS_TO_DISCOUNT_LABEL,
    PERMANENT_PRICE_LABEL,
    PRICE_COL,
    SAVE_LABEL,
    TEMPORARY_PRICE_LABEL,
    TITLE_MIN_DAYS_TO_DISCOUNT,
    TITLE_PERMANENT_PRICE,
    TITLE_TEMPORARY_PRICE,
    discounts,
    is_unique_tool_selected,
    mo,
    pl,
    prices,
    tool_selection,
):
    # Prevent displaying any value depending on the selection of the tool
    mo.stop(tool_selection.value is None)

    # Display the prices and allowing updating them according to the tool and concrete formatting of the input file
    if is_unique_tool_selected():
        SORTING_COL = "min_days"
        IS_DESCENDING_SORT = True
    else:
        SORTING_COL = "type"
        IS_DESCENDING_SORT = False

    # Generate all the elements
    temporary_day_prices = pl.read_csv(prices.contents(), separator=";").sort(
        by=SORTING_COL, descending=IS_DESCENDING_SORT
    )
    permanent_discount = pl.read_csv(discounts.contents(), separator=";")
    if not is_unique_tool_selected():
        permanent_discount = permanent_discount.sort(
            by=SORTING_COL, descending=IS_DESCENDING_SORT
        )
    fields = []
    for limit in temporary_day_prices.iter_rows(named=True):
        input = mo.ui.number(
            start=0,
            value=limit[PRICE_COL],
            label=TEMPORARY_PRICE_LABEL.format(min_days=limit[SORTING_COL])
            if is_unique_tool_selected()
            else f"{limit[SORTING_COL]}:",
        )
        fields.append(input)
    discount_fields = []
    for limit in permanent_discount.iter_rows(named=True):
        discount_input = mo.ui.number(
            start=0,
            value=limit[DISCOUNT_COL],
            label=PERMANENT_PRICE_LABEL.format(type="")
            if is_unique_tool_selected()
            else PERMANENT_PRICE_LABEL.format(
                type=f" per {limit[SORTING_COL].lower()}"
            ),
        )
        discount_fields.append(discount_input)
    min_days_to_discount = (
        mo.ui.number(
            start=0,
            value=MIN_DAYS_TO_DISCOUNT,
            label=MIN_DAYS_TO_DISCOUNT_LABEL,
        )
        if not is_unique_tool_selected()
        else ""
    )
    edit_button = mo.ui.run_button(kind="success", label=SAVE_LABEL)

    # Display the elements in the correct order
    mo.vstack(
        [
            mo.md(text=TITLE_TEMPORARY_PRICE),
            *fields,
            mo.md(text=TITLE_PERMANENT_PRICE),
            *discount_fields,
            mo.md(text="" if is_unique_tool_selected() else TITLE_MIN_DAYS_TO_DISCOUNT),
            min_days_to_discount,
            edit_button,
        ]
    )
    return (
        discount_fields,
        edit_button,
        fields,
        min_days_to_discount,
        permanent_discount,
        temporary_day_prices,
    )


@app.cell
def _(
    DISCOUNT_COL,
    PRICE_COL,
    discount_fields,
    edit_button,
    fields,
    mo,
    permanent_discount,
    pl,
    temporary_day_prices,
):
    # Callback for Edit button. Block the execution until button is clicked
    mo.stop(not edit_button.value)

    temporary_day_prices.replace_column(
        temporary_day_prices.columns.index(PRICE_COL),
        pl.Series(PRICE_COL, list(map(lambda input: input.value, fields))),
    )
    permanent_discount.replace_column(
        permanent_discount.columns.index(DISCOUNT_COL),
        pl.Series(DISCOUNT_COL, list(map(lambda input: input.value, discount_fields))),
    )
    return


@app.cell
def _(MAIN_FILE_LABEL, mo, tool_selection):
    # Prevent displaying any value depending on the selection of the tool
    mo.stop(tool_selection.value is None)

    file = mo.ui.file(
        filetypes=[".csv"],
        label=MAIN_FILE_LABEL,
        kind="area",
    )
    file
    return (file,)


@app.cell
def _(
    CATEGORIES,
    CATEGORY_COL,
    COLS_TO_BE_REMOVED,
    DISCOUNT_COL,
    ENCODING,
    FILE_NAME_COL,
    LEVEL_COL,
    N_ROWS_WITHOUT_RAW_DATA,
    PERMANENT_TYPE,
    PRICE_COL,
    STUDENT_NAME_COL,
    TEMPORARY_TYPE,
    YEAR_COL,
    file,
    is_unique_tool_selected,
    min_days_to_discount,
    mo,
    np,
    permanent_discount,
    pl,
    temporary_day_prices,
):
    # Prevent running the cell if all the necessary files are not present
    mo.stop(file.name() is None)

    # Define necessary auxiliary functions
    def count_row_values(values: dict) -> dict[str, int]:
        counts = np.unique_counts(list(values.values()))
        return dict(zip(counts.values, counts.counts))

    def _get_struct_cols(selected_type: int) -> list[str]:
        cols = [
            CATEGORY_COL,
            next(
                filter(
                    lambda category: category["code"] == selected_type,
                    CATEGORIES.values(),
                ),
                {"type_to_count": ""},
            )["type_to_count"],
        ]
        if not is_unique_tool_selected():
            cols.append(FILE_NAME_COL)
        return cols

    def _price_for_unique(price_info: dict[str, int | float], n_days: int) -> float:
        return n_days > price_info["min_days"]

    def _price_for_category(price_info: dict[str, int | float], category: str) -> float:
        return price_info["type"] == category

    def calculate_presence_price_in_temporary(category_and_days: dict) -> str:
        if (
            category_and_days[CATEGORY_COL] not in CATEGORIES
            or CATEGORIES[category_and_days[CATEGORY_COL]]["code"] != TEMPORARY_TYPE
        ):
            return ""
        n_days = (
            category_and_days.get(
                CATEGORIES[category_and_days[CATEGORY_COL]]["type_to_count"]
            )
            or 0
        )
        return str(
            round(
                n_days
                * next(
                    filter(
                        lambda price_info: _price_for_unique(price_info, n_days)
                        if is_unique_tool_selected()
                        else _price_for_category(
                            price_info,
                            category_and_days[
                                CATEGORY_COL
                                if is_unique_tool_selected()
                                else FILE_NAME_COL
                            ],
                        ),
                        temporary_day_prices.iter_rows(named=True),
                    ),
                    {
                        PRICE_COL: 0
                    },  # In case the student has not attended during the whole month
                )[PRICE_COL],
                2,
            )
        ).replace(
            ".", ","
        )  # Use comma as decimal separator, since current Polars version cannot handle it

    def calculate_absence_discount_in_permanent(category_and_days: dict) -> str:
        if (
            category_and_days[CATEGORY_COL] not in CATEGORIES
            or CATEGORIES[category_and_days[CATEGORY_COL]]["code"] != PERMANENT_TYPE
        ):
            return ""
        n_days = (
            category_and_days.get(
                CATEGORIES[category_and_days[CATEGORY_COL]]["type_to_count"]
            )
            or 0
        )
        if not is_unique_tool_selected():
            n_days = (
                n_days - min_days_to_discount.value
                if min_days_to_discount.value < n_days
                else 0
            )
        return str(
            round(
                n_days
                * -1
                * next(
                    filter(
                        # Return the single line of the unique tool or find the one for the corresponding category
                        lambda price_info: price_info
                        if is_unique_tool_selected()
                        else _price_for_category(
                            price_info,
                            category_and_days[
                                CATEGORY_COL
                                if is_unique_tool_selected()
                                else FILE_NAME_COL
                            ],
                        ),
                        permanent_discount.iter_rows(named=True),
                    ),
                    {
                        DISCOUNT_COL: 0
                    },  # In case the student has not attended during the whole month
                )[DISCOUNT_COL],
                2,
            )
        ).replace(
            ".", ","
        )  # Use comma as decimal separator, since current Polars version cannot handle it

    # Read as DF and format as expected
    if not is_unique_tool_selected() and FILE_NAME_COL in COLS_TO_BE_REMOVED:
        COLS_TO_BE_REMOVED.remove(
            FILE_NAME_COL
        )  # Do not remove the column with information about the subcategory
    data = (
        pl.read_csv(file.contents(), encoding=ENCODING, separator=";")
        .limit(-N_ROWS_WITHOUT_RAW_DATA)
        .drop(COLS_TO_BE_REMOVED, strict=False)
    )
    value_columns = list(data.columns)
    if STUDENT_NAME_COL in value_columns:
        value_columns.remove(STUDENT_NAME_COL)
    if YEAR_COL in value_columns:
        value_columns.remove(YEAR_COL)

    SORTING_COLS = (
        [LEVEL_COL, CATEGORY_COL, STUDENT_NAME_COL]
        if is_unique_tool_selected()
        else [LEVEL_COL, STUDENT_NAME_COL, CATEGORY_COL, FILE_NAME_COL]
    )
    other_than_date_cols = [CATEGORY_COL, FILE_NAME_COL]
    cols_to_group_by = [STUDENT_NAME_COL]
    if not is_unique_tool_selected():
        cols_to_group_by.append(FILE_NAME_COL)
        value_columns.remove(FILE_NAME_COL)

    # Use the sorting functionality of np.unique to get the 'P', which is the last
    # possible value if present and has highest priority. It also works for the
    # categories, since if both are present ('puntual' and 'permanent'), 'puntual'
    # (the last in alphabetic order) is wanted. For the year column, all the rows
    # per student should have the same, so it is enough selecting the first.
    # Then add up the corresponding type (A/P) based on the category
    # (puntual/permanent) and get the correct price or discount
    grouped_data = (
        data.group_by(cols_to_group_by, maintain_order=True)
        .agg(
            # Generate the level column
            [
                pl.map_groups(
                    exprs=YEAR_COL,
                    function=lambda years: np.unique(years)[0].split(" / ", 1)[0],
                    return_dtype=pl.datatypes.String,
                    returns_scalar=True,
                ).alias(LEVEL_COL)
            ]
            # If more than one row within the category,
            # select the type with highest priority (last)
            + [
                pl.map_groups(
                    exprs=col,
                    function=lambda values: np.unique(values)[-1],
                    return_dtype=pl.datatypes.String,
                    returns_scalar=True,
                )
                for col in value_columns
            ]
        )
        # Convert the level column to categorical to be able to keep the logical order
        .with_columns(pl.col(LEVEL_COL).cast(pl.datatypes.Categorical))
        .sort(by=pl.col(SORTING_COLS))
        # Calculate the subtotals of each type and get each in a separate column
        .with_columns(
            Recompte=pl.struct(
                # i.e. include only the date columns
                pl.col(
                    filter(lambda col: col not in other_than_date_cols, value_columns)
                )
            ).map_elements(
                count_row_values,
                return_dtype=pl.Struct(
                    [pl.Field("-", pl.Int64)]
                    + [
                        pl.Field(category, pl.Int64)
                        for category in map(
                            lambda category: category["type_to_count"],
                            CATEGORIES.values(),
                        )
                    ]
                ),
            )
        )
        .unnest("Recompte")
        # Calculate the prices and discounts according to school rules
        .with_columns(
            Cobrar=pl.struct(_get_struct_cols(TEMPORARY_TYPE)).map_elements(
                calculate_presence_price_in_temporary, return_dtype=str
            ),
            Devolucions=pl.struct(_get_struct_cols(PERMANENT_TYPE)).map_elements(
                calculate_absence_discount_in_permanent, return_dtype=str
            ),
        )
    )

    grouped_data
    return (grouped_data,)


@app.cell
def _(
    CATEGORY_COL,
    DOWNLOAD_LABEL,
    ENCODING,
    FILE_NAME_COL,
    LEVEL_COL,
    STUDENT_NAME_COL,
    calendar,
    file,
    grouped_data,
    is_unique_tool_selected,
    mo,
    pl,
):
    base_file_name = pl.read_csv(
        file.contents(), encoding=ENCODING, separator=";", n_rows=1
    )[FILE_NAME_COL][0]
    non_month_cols = [STUDENT_NAME_COL, CATEGORY_COL, LEVEL_COL]
    if not is_unique_tool_selected():
        non_month_cols.append(FILE_NAME_COL)
    month_number = int(
        grouped_data.drop(non_month_cols).columns[0].split("/")[1].split(" ")[0]
    )
    filename = f"{base_file_name}_{calendar.month_name[month_number]}.csv"
    excel_download = mo.download(
        data=grouped_data.write_csv(separator=";").encode(ENCODING),
        filename=filename,
        mimetype="text/csv",
        label=DOWNLOAD_LABEL,
    )
    excel_download
    return


if __name__ == "__main__":
    app.run()
