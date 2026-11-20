let
    Server = "POWERBI_POSTGRES_SERVER:5432",
    Database = "POWERBI_POSTGRES_DATABASE",
    Source = PostgreSQL.Database(
        Server,
        Database,
        [CreateNavigationProperties = false]
    ),
    Data = Source{[Schema = "analytics", Item = "v_powerbi_clustering_salidas"]}[Data],
    Renamed = Table.RenameColumns(
        Data,
        {
            {"tsne1", "TSNE1"},
            {"tsne2", "TSNE2"},
            {"workload", "Carga trabajo"},
            {"salary", "SALARIO NUEVO"},
            {"environment", "Ambiente"},
            {"salary_increase", "Incremento Salarial"},
            {"bonus", "Bonus/Variable"},
            {"technical_training", "Formación técnica"},
            {"professional_category", "Categoria Profesional"},
            {"age", "Edad"},
            {"tenure", "Antiguedad"},
            {"total_expenses_category", "TOTAL_GASTOS"},
            {"autonomy", "Autonomía"},
            {"exit_cause", "Causa de salida"},
            {"motive_cluster", "motivo_cluster"},
            {"society", "SOCIEDAD"},
            {"office", "OFICINA"},
            {"employee_id", "id"}
        },
        MissingField.Error
    ),
    Typed = Table.TransformColumnTypes(
        Renamed,
        {
            {"TSNE1", type number},
            {"TSNE2", type number},
            {"Carga trabajo", type number},
            {"SALARIO NUEVO", type number},
            {"Ambiente", type number},
            {"Incremento Salarial", type number},
            {"Bonus/Variable", type number},
            {"Formación técnica", type number},
            {"Categoria Profesional", type text},
            {"Edad", Int64.Type},
            {"Antiguedad", type number},
            {"TOTAL_GASTOS", type text},
            {"Autonomía", type number},
            {"cluster", type text},
            {"Causa de salida", type text},
            {"motivo_cluster", type text},
            {"SOCIEDAD", type text},
            {"OFICINA", type text},
            {"id", type text},
            {"last_name", type text},
            {"first_name", type text}
        },
        "es-ES"
    )
in
    Typed
