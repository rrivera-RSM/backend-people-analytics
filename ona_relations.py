import json
import math
import pandas as pd
from pathlib import Path

EXCEL_MAX_ROWS = 1_048_576


def read_json_flexible(path: str, chunksize: int = 200_000):
    """
    Lee JSON en 2 formatos:
      - Array JSON: [ {...}, {...} ]
      - JSON Lines (JSONL/NDJSON): 1 objeto por línea
    Devuelve:
      - DataFrame si es array JSON
      - iterador de chunks si es JSONL
    """
    p = Path(path)
    # Heurística: si extensión es .jsonl -> lines
    if p.suffix.lower() in [".jsonl", ".ndjson"]:
        return pd.read_json(path, lines=True, chunksize=chunksize)

    # Si es .json, intentamos cargar como array
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(2048).lstrip()
    if first.startswith("["):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.json_normalize(data, sep=".")
    else:
        # Puede ser objeto con key: {"data":[...]} etc.
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # intenta encontrar una lista dentro
        for k, v in data.items():
            if isinstance(v, list):
                return pd.json_normalize(v, sep=".")
        raise ValueError(
            "No se encontró lista de registros en el JSON. ¿Viene anidado con otra key?"
        )


def split_to_sheets(writer, df, base_sheet_name: str):
    """
    Escribe un DataFrame en una o varias hojas, respetando el máximo de filas de Excel.
    """
    if len(df) <= EXCEL_MAX_ROWS:
        df.to_excel(writer, index=False, sheet_name=base_sheet_name)
        return

    n_parts = math.ceil(len(df) / EXCEL_MAX_ROWS)
    for i in range(n_parts):
        part = df.iloc[i * EXCEL_MAX_ROWS : (i + 1) * EXCEL_MAX_ROWS]
        sheet = f"{base_sheet_name}_{i+1}"
        part.to_excel(writer, index=False, sheet_name=sheet)


def enrich_edges(df_edges, lookup_df, id_col="id", email_col="email"):
    """
    Añade from_email y to_email a partir de lookup id->email.
    """
    lookup = lookup_df[[id_col, email_col]].drop_duplicates()

    out = (
        df_edges.merge(lookup, left_on="from_id", right_on=id_col, how="left")
        .rename(columns={email_col: "from_email"})
        .drop(columns=[id_col])
    )

    out = (
        out.merge(lookup, left_on="to_id", right_on=id_col, how="left")
        .rename(columns={email_col: "to_email"})
        .drop(columns=[id_col])
    )

    return out


def main():
    json_path = "./centralizado.json"  # cambia si aplica
    lookup_path = "./cts_id_into_mail.xlsx"  # cambia si aplica
    output_path = "./centralizado.xlsx"

    # 1) lookup
    lookup = pd.read_excel(lookup_path, engine="openpyxl")

    # Ajusta aquí si tus columnas se llaman distinto
    ID_COL = "id"
    EMAIL_COL = "email"

    # 2) JSON flexible
    data = read_json_flexible(json_path)

    # 3) Preparar writer
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Si data es DataFrame (JSON array)
        if isinstance(data, pd.DataFrame):
            edges_raw = data.copy()

            # Asegura columnas mínimas esperadas
            expected = {
                "survey_id",
                "question_id",
                "from_id",
                "to_id",
                "run_id",
            }
            missing = expected - set(edges_raw.columns)
            if missing:
                print("Aviso: faltan columnas:", missing)

            edges_enriched = enrich_edges(
                edges_raw, lookup, ID_COL, EMAIL_COL
            )

            # nodes = ids únicos de from/to, con email
            node_ids = pd.unique(
                pd.concat(
                    [edges_raw["from_id"], edges_raw["to_id"]],
                    ignore_index=True,
                )
            )
            nodes = (
                pd.DataFrame({"id": node_ids})
                .merge(
                    lookup[[ID_COL, EMAIL_COL]].drop_duplicates(),
                    left_on="id",
                    right_on=ID_COL,
                    how="left",
                )
                .drop(columns=[ID_COL])
                .rename(columns={EMAIL_COL: "email"})
            )

            # summary
            summary_by_question = (
                edges_enriched.groupby("question_id")
                .size()
                .reset_index(name="count")
            )

            pairs_by_question = (
                edges_enriched.groupby(
                    ["question_id", "from_email", "to_email"]
                )
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )

            # Export
            split_to_sheets(writer, edges_raw, "edges_raw")
            split_to_sheets(writer, edges_enriched, "edges_enriched")
            split_to_sheets(writer, nodes, "nodes")
            summary_by_question.to_excel(
                writer, index=False, sheet_name="summary_by_question"
            )
            split_to_sheets(writer, pairs_by_question, "pairs_by_question")

        else:
            # JSONL por chunks
            chunks = data

            # Preparar hojas incrementales (ojo límite filas)
            # Para JSONL enorme, lo más seguro es escribir SOLO enriched y un summary incremental.
            # Si necesitas raw también, se añade igual.

            # Acumuladores para summary (ligero)
            summary_counter = {}
            pair_counter = {}

            # Buffer de nodes (si lookup cubre todos, no hace falta construir nodes de edges)
            # Aun así, guardaremos nodes que aparezcan en edges
            node_set = set()

            # Escritura incremental en hojas (partiendo por Excel max rows)
            # Usamos un contador de filas por hoja para enriched y raw.
            raw_part = 1
            enr_part = 1
            raw_row = 0
            enr_row = 0

            for chunk in chunks:
                # Normaliza
                edges_raw = pd.json_normalize(chunk, sep=".")
                edges_enriched = enrich_edges(
                    edges_raw, lookup, ID_COL, EMAIL_COL
                )

                # Actualiza nodes vistos
                if (
                    "from_id" in edges_raw.columns
                    and "to_id" in edges_raw.columns
                ):
                    node_set.update(
                        edges_raw["from_id"].dropna().astype(str).tolist()
                    )
                    node_set.update(
                        edges_raw["to_id"].dropna().astype(str).tolist()
                    )

                # summary incremental
                if "question_id" in edges_enriched.columns:
                    vc = edges_enriched["question_id"].value_counts(
                        dropna=False
                    )
                    for k, v in vc.items():
                        summary_counter[k] = summary_counter.get(k, 0) + int(
                            v
                        )

                # pair summary incremental (puede crecer mucho; úsalo si no es enorme)
                if set(["question_id", "from_email", "to_email"]).issubset(
                    edges_enriched.columns
                ):
                    grp = edges_enriched.groupby(
                        ["question_id", "from_email", "to_email"]
                    ).size()
                    for idx, v in grp.items():
                        pair_counter[idx] = pair_counter.get(idx, 0) + int(v)

                # Escribir raw incremental
                sheet_raw = f"edges_raw_{raw_part}"
                if raw_row == 0:
                    edges_raw.to_excel(
                        writer,
                        index=False,
                        sheet_name=sheet_raw,
                        startrow=0,
                        header=True,
                    )
                else:
                    edges_raw.to_excel(
                        writer,
                        index=False,
                        sheet_name=sheet_raw,
                        startrow=raw_row,
                        header=False,
                    )
                raw_row += len(edges_raw)

                if raw_row >= EXCEL_MAX_ROWS:
                    raw_part += 1
                    raw_row = 0

                # Escribir enriched incremental
                sheet_enr = f"edges_enriched_{enr_part}"
                if enr_row == 0:
                    edges_enriched.to_excel(
                        writer,
                        index=False,
                        sheet_name=sheet_enr,
                        startrow=0,
                        header=True,
                    )
                else:
                    edges_enriched.to_excel(
                        writer,
                        index=False,
                        sheet_name=sheet_enr,
                        startrow=enr_row,
                        header=False,
                    )
                enr_row += len(edges_enriched)

                if enr_row >= EXCEL_MAX_ROWS:
                    enr_part += 1
                    enr_row = 0

            # Construir nodes al final
            nodes = (
                pd.DataFrame({"id": list(node_set)})
                .merge(
                    lookup[[ID_COL, EMAIL_COL]].drop_duplicates(),
                    left_on="id",
                    right_on=ID_COL,
                    how="left",
                )
                .drop(columns=[ID_COL])
                .rename(columns={EMAIL_COL: "email"})
            )

            # summary_by_question
            summary_by_question = pd.DataFrame(
                [
                    {"question_id": k, "count": v}
                    for k, v in summary_counter.items()
                ]
            ).sort_values("question_id")

            # pairs_by_question
            pairs_by_question = pd.DataFrame(
                [
                    {
                        "question_id": k[0],
                        "from_email": k[1],
                        "to_email": k[2],
                        "count": v,
                    }
                    for k, v in pair_counter.items()
                ]
            ).sort_values("count", ascending=False)

            # Export nodes & summaries
            split_to_sheets(writer, nodes, "nodes")
            summary_by_question.to_excel(
                writer, index=False, sheet_name="summary_by_question"
            )
            split_to_sheets(writer, pairs_by_question, "pairs_by_question")

    print("OK ->", output_path)


if __name__ == "__main__":
    main()
