from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pbix_mcp.server import (
    pbix_close,
    pbix_diff,
    pbix_doctor,
    pbix_list_data_sources,
    pbix_open,
    pbix_save,
    pbix_set_partition_m,
)


QUERY_FILES = {
    "Dataset_all": "Dataset_all.m",
    "Probabilidades_2024": "Probabilidades_2024.m",
    "Probabilidades_2025": "Probabilidades_2025.m",
    "Clustering_Salidas": "Clustering_Salidas.m",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_success(raw_response: str, operation: str) -> dict[str, object]:
    response = json.loads(raw_response)
    if not response.get("success"):
        raise RuntimeError(f"{operation} failed: {response}")
    return response


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a PostgreSQL-backed copy of HR Analytics EXCO.pbix "
            "without modifying the source file."
        )
    )
    parser.add_argument("source_pbix", type=Path)
    parser.add_argument("output_pbix", type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of an existing output copy. Never affects the source.",
    )
    args = parser.parse_args()

    source = args.source_pbix.expanduser().resolve()
    output = args.output_pbix.expanduser().resolve()

    if source == output:
        raise ValueError("The output path must be different from the source PBIX.")
    if not source.is_file():
        raise FileNotFoundError(source)
    if output.exists() and not args.overwrite:
        raise FileExistsError(
            f"{output} already exists. Choose another path or pass --overwrite."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    query_dir = Path(__file__).resolve().parent / "queries"
    source_hash_before = sha256(source)

    build_alias = "hr_analytics_postgresql_build"
    require_success(pbix_open(str(source), build_alias), "open source")
    try:
        for table_name, query_file in QUERY_FILES.items():
            m_expression = (query_dir / query_file).read_text(encoding="utf-8")
            require_success(
                pbix_set_partition_m(build_alias, table_name, m_expression),
                f"replace partition M for {table_name}",
            )

        require_success(
            pbix_save(
                build_alias,
                str(output),
                overwrite=args.overwrite,
                backup=False,
            ),
            "save copy",
        )
    finally:
        require_success(pbix_close(build_alias, force=True), "close build session")

    source_hash_after = sha256(source)
    if source_hash_after != source_hash_before:
        raise RuntimeError("The source PBIX hash changed; refusing to continue.")

    source_alias = "hr_analytics_source_validation"
    copy_alias = "hr_analytics_copy_validation"
    require_success(pbix_open(str(source), source_alias), "reopen source")
    require_success(pbix_open(str(output), copy_alias), "open output copy")
    try:
        source_list = require_success(
            pbix_list_data_sources(copy_alias),
            "list output data sources",
        )
        source_message = str(source_list.get("message", ""))
        for table_name in QUERY_FILES:
            expected = f"{table_name}: PostgreSQL (Import)"
            if expected not in source_message:
                raise RuntimeError(
                    f"Expected PostgreSQL source was not found: {expected}"
                )

        doctor = require_success(pbix_doctor(copy_alias), "diagnose output copy")
        doctor_message = str(doctor.get("message", ""))
        if "❌" in doctor_message:
            raise RuntimeError(
                "The generated copy failed one or more PBIX diagnostics."
            )

        diff = require_success(
            pbix_diff(source_alias, copy_alias),
            "compare source and output copy",
        )
    finally:
        require_success(pbix_close(copy_alias, force=True), "close output")
        require_success(pbix_close(source_alias, force=True), "close source")

    validation = {
        "source": str(source),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "output": str(output),
        "output_sha256": sha256(output),
        "output_size_bytes": output.stat().st_size,
        "updated_partitions": list(QUERY_FILES),
        "data_sources": source_message,
        "doctor": doctor_message,
        "diff": diff.get("message", ""),
    }
    validation_path = output.with_suffix(".validation.json")
    validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(validation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
