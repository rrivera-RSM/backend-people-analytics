let
    Server = "POWERBI_POSTGRES_SERVER:5432",
    Database = "POWERBI_POSTGRES_DATABASE",
    Source = PostgreSQL.Database(
        Server,
        Database,
        [CreateNavigationProperties = false]
    ),
    Data = Source{[Schema = "analytics", Item = "v_powerbi_probabilities_2025"]}[Data],
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
    CanonicalArea = Table.AddColumn(
        Table.RemoveColumns(WithoutTestEntities, {"society_short_name"}, MissingField.Ignore),
        "society_short_name",
        each
            let
                Society = if [society] = null then null else Text.Trim([society]),
                Normalized = if Society = null then null else Text.Upper(Society)
            in
                if Normalized = null then null
                else if Text.Contains(Normalized, "SERVICIOS ADMINISTRATIVOS") then "Servicios"
                else if Text.Contains(Normalized, "AUDITORES") then "Auditoría"
                else if Text.Contains(Normalized, "CONSULTORES") then "Consulting"
                else if Text.Contains(Normalized, "ASESORES LEGALES Y TRIBUTARIOS") then "Tax & Legal"
                else if Text.Contains(Normalized, "CORPORATE FINANCE") then "Corporate"
                else Society,
        type text
    ),
    Renamed = Table.RenameColumns(
        CanonicalArea,
        {
            {"employee_id", "id"},
            {"target", "Target"},
            {"fiscal_year", "Año Fiscal"},
            {"prediction_target", "Predicción_Target"},
            {"probability_actual", "Probabilidad Actual"},
            {"office", "OFICINA"},
            {"society", "SOCIEDAD"},
            {"department", "AREA/DEPARTAMENTO"},
            {"birth_date", "Fecha nacimiento"},
            {"gender", "Género"},
            {"professional_category", "Categoria Profesional"},
            {"society_short_name", "SOCIEDAD-Nombre"}
        },
        MissingField.Error
    ),
    Typed = Table.TransformColumnTypes(
        Renamed,
        {
            {"id", type text},
            {"Target", type text},
            {"Año Fiscal", type text},
            {"Predicción_Target", type text},
            {"Probabilidad Actual", type text},
            {"first_name", type text},
            {"last_name", type text},
            {"OFICINA", type text},
            {"SOCIEDAD", type text},
            {"AREA/DEPARTAMENTO", type text},
            {"Fecha nacimiento", type text},
            {"Género", type text},
            {"joined_at", type text},
            {"left_at", type text},
            {"final_score", type number},
            {"Categoria Profesional", type text},
            {"SOCIEDAD-Nombre", type text}
        },
        "es-ES"
    )
in
    Typed
