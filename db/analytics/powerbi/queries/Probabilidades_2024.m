let
    Server = "POWERBI_POSTGRES_SERVER:5432",
    Database = "POWERBI_POSTGRES_DATABASE",
    Source = PostgreSQL.Database(
        Server,
        Database,
        [CreateNavigationProperties = false]
    ),
    Data = Source{[Schema = "analytics", Item = "v_powerbi_probabilities_2024"]}[Data],
    WithoutTestEntities = Table.SelectRows(
        Data,
        each
            not Text.StartsWith(
                Text.Upper(Text.Trim(if [society] = null then "" else [society])),
                "ADN"
            )
            and not Text.StartsWith(
                Text.Upper(Text.Trim(if [department] = null then "" else [department])),
                "ADN"
            )
    ),
    Renamed = Table.RenameColumns(
        WithoutTestEntities,
        {
            {"employee_id", "ID"},
            {"first_name", "Nombre"},
            {"last_name", "Apellidos"},
            {"professional_category", "Categoria Profesional"},
            {"office", "OFICINA"},
            {"society", "SOCIEDAD"},
            {"department", "AREA/DEPARTAMENTO"},
            {"job_title", "PUESTO DE TRABAJO"},
            {"joined_at", "Fecha alta"},
            {"left_at", "Fecha Baja"},
            {"salary", "SALARIO ACTUAL"},
            {"probability", "Probabilidad "},
            {"permanence_label", "Permance o Abandona"}
        },
        MissingField.Error
    ),
    Typed = Table.TransformColumnTypes(
        Renamed,
        {
            {"ID", type text},
            {"Nombre", type text},
            {"Apellidos", type text},
            {"Categoria Profesional", type text},
            {"OFICINA", type text},
            {"SOCIEDAD", type text},
            {"AREA/DEPARTAMENTO", type text},
            {"PUESTO DE TRABAJO", type text},
            {"Fecha alta", type date},
            {"Fecha Baja", type date},
            {"SALARIO ACTUAL", type number},
            {"Probabilidad ", type number},
            {"Permance o Abandona", type text}
        },
        "es-ES"
    )
in
    Typed
