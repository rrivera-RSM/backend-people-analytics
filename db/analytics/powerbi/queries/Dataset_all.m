let
    // Replace these two placeholders in Power Query before the first refresh.
    Server = "POWERBI_POSTGRES_SERVER:5432",
    Database = "POWERBI_POSTGRES_DATABASE",
    Source = PostgreSQL.Database(
        Server,
        Database,
        [CreateNavigationProperties = false]
    ),
    Data = Source{[Schema = "analytics", Item = "v_powerbi_dataset_all"]}[Data],
    TestEmployeeIds = List.Buffer(
        List.Distinct(
            Table.SelectRows(
                Data,
                each
                    Text.StartsWith(
                        Text.Upper(Text.Trim(if [society] = null then "" else [society])),
                        "ADN"
                    )
                    or Text.StartsWith(
                        Text.Upper(Text.Trim(if [department] = null then "" else [department])),
                        "ADN"
                    )
            )[employee_id]
        )
    ),
    WithoutTestEntities = Table.SelectRows(
        Data,
        each not List.Contains(TestEmployeeIds, [employee_id])
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
            {"office", "OFICINA"},
            {"society", "SOCIEDAD"},
            {"department", "AREA/DEPARTAMENTO"},
            {"dni", "DNI/NIE"},
            {"birth_date", "Fecha nacimiento"},
            {"gender", "Género"},
            {"fiscal_year", "Año Fiscal"},
            {"professional_category", "Categoria Profesional"},
            {"target", "Target"},
            {"age", "Edad"},
            {"tenure_years", "Antiguedad"},
            {"promotion", "Promocion"},
            {"salary", "SALARIO NUEVO"},
            {"salary_increase", "Incremento Salarial"},
            {"survey_q01", "Estoy orgulloso de trabajar en RSM Spain"},
            {"survey_q02", "Recomendaría RSM Spain como un muy buen lugar donde trabajar   "},
            {"survey_q03", "Creo que RSM Spain tiene un futuro excepcional"},
            {"survey_q04", "Me veo trabajando en RSM Spain dentro de 3 años"},
            {"survey_q05", "El ambiente en la oficina es muy bueno  "},
            {"survey_q06", "El ambiente en mi departamento es muy bueno  "},
            {"survey_q07", "RSM Spain valora y promueve suficientemente la diversidad"},
            {"survey_q08", "Tengo los recursos necesarios (equipo, programas informáticos, aplicaciones) para trabajar eficazmente  "},
            {"survey_q09", "La formación en conocimientos técnicos útiles para mi área es buena"},
            {"survey_q10", "La formación en habilidades soft (liderazgo, capacidad comercial, comunicación...) es buena"},
            {"survey_q11", "La formación en competencias y herramientas digitales es buena"},
            {"survey_q12", "RSM Spain me ofrece oportunidades y experiencias que facilitan mi crecimiento y desarrollo"},
            {"survey_q13", "Siento que mi carrera prospera como profesional en RSM Spain"},
            {"survey_q14", "Tengo la autonomía adecuada en el desempeño de mi trabajo"},
            {"survey_q15", "Percibo el apoyo de mi supervisor"},
            {"survey_q16", "Mis ideas y sugerencias se tienen en consideración por parte de mi supervisor directo"},
            {"survey_q17", "Tengo claro lo que mis responsables esperan de mí(*Solamente responde si participaste en la Evaluación del Desempeño en 2023) "},
            {"survey_q18", "RSM Spain se preocupa por proporcionarme un equilibrio entre mi vida laboral y personal"},
            {"survey_q19", "Los horarios actuales son adecuados"},
            {"survey_q20", "Estoy satisfecho con el porcentaje de días de trabajo a distancia"},
            {"survey_q21", "Estoy satisfecho con el número de días de vacaciones y con la posibilidad de elegir las fechas de las mismas"},
            {"survey_q22", "La carga de trabajo es adecuada y equitativa entre los miembros del equipo"},
            {"survey_q23", "En RSM Spain existe una comunicación bidireccional abierta y honesta"},
            {"survey_q24", "Los líderes de RSM Spain comunican adecuadamente las razones que hay detrás de los cambios relevantes que se realizan en la firma"},
            {"survey_q25", "Las iniciativas de comunicación existentes son suficientes y adecuadas"},
            {"survey_q26", "Mi salario es justo y el adecuado a mi nivel de responsabilidad"},
            {"survey_q27", "Considero que estoy bien retribuido en comparación con organizaciones similares"},
            {"survey_q28", "Estoy satisfecho con los beneficios sociales que recibo en RSM Spain"},
            {"survey_q29", "RSM Spain valora y promueve suficientemente la Responsabilidad Social Corporativa y las opciones de participar en distintas acciones de impacto en la sociedad"},
            {"bonus", "Bonus/Variable"},
            {"mileage", "KILOMETRAJE"},
            {"per_diem", "DIETA"},
            {"lodging", "DORMIR"},
            {"transport", "TRANSPORTE"},
            {"flexible_compensation", "Retribucion Flexible"},
            {"society_short_name", "SOCIEDAD-Nombre"},
            {"satisfaction_average", "Satisfacción"},
            {"exit_cause", "Causa de salida"},
            {"rotation_flag", "Cuenta Rotación"},
            {"exit_motive", "Motivo"},
            {"enc_brand", "ENC_Marca RSM y orgullo"},
            {"enc_environment", "ENC_ambienteTrabajo"},
            {"enc_training", "ENC_formacion"},
            {"exit_cause_group", "Causa de salida 2"},
            {"positive_impact", "Impacto positivo"},
            {"enc_development", "ENC_desarrollo"},
            {"enc_work_life", "ENC_conciliacion"},
            {"enc_internal_communication", "ENC_comunicacion_interna"},
            {"enc_salary", "ENC_salario"},
            {"total_expenses", "Total Gastos"},
            {"expense_category", "Total gastos categorica"},
            {"inorganic_growth", "crecimiento_inorganico"}
        },
        MissingField.Error
    ),
    Typed = Table.TransformColumnTypes(
        Renamed,
        {
            {"id", type text},
            {"first_name", type text},
            {"last_name", type text},
            {"email", type text},
            {"OFICINA", type text},
            {"SOCIEDAD", type text},
            {"AREA/DEPARTAMENTO", type text},
            {"DNI/NIE", type text},
            {"Fecha nacimiento", type date},
            {"Género", type text},
            {"joined_at", type date},
            {"left_at", type date},
            {"Año Fiscal", Int64.Type},
            {"Categoria Profesional", type text},
            {"Target", type text},
            {"Edad", Int64.Type},
            {"Antiguedad", type number},
            {"Promocion", type text},
            {"SALARIO NUEVO", type number},
            {"Incremento Salarial", type number},
            {"Estoy orgulloso de trabajar en RSM Spain", type number},
            {"Recomendaría RSM Spain como un muy buen lugar donde trabajar   ", type number},
            {"Creo que RSM Spain tiene un futuro excepcional", type number},
            {"Me veo trabajando en RSM Spain dentro de 3 años", type number},
            {"El ambiente en la oficina es muy bueno  ", type number},
            {"El ambiente en mi departamento es muy bueno  ", type number},
            {"RSM Spain valora y promueve suficientemente la diversidad", type number},
            {"Tengo los recursos necesarios (equipo, programas informáticos, aplicaciones) para trabajar eficazmente  ", type number},
            {"La formación en conocimientos técnicos útiles para mi área es buena", type number},
            {"La formación en habilidades soft (liderazgo, capacidad comercial, comunicación...) es buena", type number},
            {"La formación en competencias y herramientas digitales es buena", type number},
            {"RSM Spain me ofrece oportunidades y experiencias que facilitan mi crecimiento y desarrollo", type number},
            {"Siento que mi carrera prospera como profesional en RSM Spain", type number},
            {"Tengo la autonomía adecuada en el desempeño de mi trabajo", type number},
            {"Percibo el apoyo de mi supervisor", type number},
            {"Mis ideas y sugerencias se tienen en consideración por parte de mi supervisor directo", type number},
            {"Tengo claro lo que mis responsables esperan de mí(*Solamente responde si participaste en la Evaluación del Desempeño en 2023) ", type number},
            {"RSM Spain se preocupa por proporcionarme un equilibrio entre mi vida laboral y personal", type number},
            {"Los horarios actuales son adecuados", type number},
            {"Estoy satisfecho con el porcentaje de días de trabajo a distancia", type number},
            {"Estoy satisfecho con el número de días de vacaciones y con la posibilidad de elegir las fechas de las mismas", type number},
            {"La carga de trabajo es adecuada y equitativa entre los miembros del equipo", type number},
            {"En RSM Spain existe una comunicación bidireccional abierta y honesta", type number},
            {"Los líderes de RSM Spain comunican adecuadamente las razones que hay detrás de los cambios relevantes que se realizan en la firma", type number},
            {"Las iniciativas de comunicación existentes son suficientes y adecuadas", type number},
            {"Mi salario es justo y el adecuado a mi nivel de responsabilidad", type number},
            {"Considero que estoy bien retribuido en comparación con organizaciones similares", type number},
            {"Estoy satisfecho con los beneficios sociales que recibo en RSM Spain", type number},
            {"RSM Spain valora y promueve suficientemente la Responsabilidad Social Corporativa y las opciones de participar en distintas acciones de impacto en la sociedad", type number},
            {"Bonus/Variable", type number},
            {"KILOMETRAJE", type number},
            {"DIETA", type number},
            {"DORMIR", type number},
            {"TRANSPORTE", type number},
            {"final_score", type number},
            {"Retribucion Flexible", type text},
            {"SOCIEDAD-Nombre", type text},
            {"Satisfacción", type number},
            {"full_name", type text},
            {"Causa de salida", type text},
            {"Cuenta Rotación", type text},
            {"Motivo", type text},
            {"ENC_Marca RSM y orgullo", type number},
            {"ENC_ambienteTrabajo", type number},
            {"ENC_formacion", type number},
            {"Causa de salida 2", type text},
            {"Impacto positivo", Int64.Type},
            {"ENC_desarrollo", type number},
            {"ENC_conciliacion", type number},
            {"ENC_comunicacion_interna", type number},
            {"ENC_salario", type number},
            {"Total Gastos", type number},
            {"Total gastos categorica", type text},
            {"crecimiento_inorganico", type text},
            {"distance_km", type text}
        },
        "es-ES"
    )
in
    Typed
