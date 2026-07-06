from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AssistantShapRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_employee_attrition_shap_context(
        self,
        employee_id: int,
        model_type: str = "employee_attrition",
    ) -> dict[str, Any] | None:
        latest_shap_query = text(
            """
            SELECT
                id,
                employee_id,
                model_type,
                model_version,
                prediction_date,
                shap_values,
                shap_top_drivers,
                source_file_name,
                source_run_id
            FROM people.employee_shap_values
            WHERE employee_id = :employee_id
              AND model_type = :model_type
            ORDER BY prediction_date DESC, created_at DESC, id DESC
            LIMIT 1
            """
        )
        latest_shap = (
            await self.db.execute(
                latest_shap_query,
                {"employee_id": employee_id, "model_type": model_type},
            )
        ).mappings().first()

        if latest_shap is None:
            return None

        attrition_query = text(
            """
            SELECT attrition_rate, calculated_at
            FROM people.employee_attrition
            WHERE employee_id = :employee_id
            ORDER BY calculated_at DESC, id DESC
            LIMIT 1
            """
        )
        attrition = (
            await self.db.execute(
                attrition_query,
                {"employee_id": employee_id},
            )
        ).mappings().first()

        drivers_query = text(
            """
            WITH latest_shap AS (
                SELECT model_type, model_version, shap_values
                FROM people.employee_shap_values
                WHERE employee_id = :employee_id
                  AND model_type = :model_type
                ORDER BY prediction_date DESC, created_at DESC, id DESC
                LIMIT 1
            ), drivers AS (
                SELECT
                    item.key AS feature_key,
                    CAST(item.value AS numeric) AS shap_value,
                    ABS(CAST(item.value AS numeric)) AS abs_shap_value,
                    catalog.model_feature_name,
                    COALESCE(catalog.human_label_es, item.key) AS human_label_es,
                    catalog.business_domain,
                    catalog.description_es,
                    catalog.positive_impact_meaning_es,
                    catalog.negative_impact_meaning_es,
                    catalog.sensitivity_level,
                    CASE
                        WHEN CAST(item.value AS numeric) > 0 THEN 'increases_risk'
                        WHEN CAST(item.value AS numeric) < 0 THEN 'decreases_risk'
                        ELSE 'neutral'
                    END AS impact_direction
                FROM latest_shap
                CROSS JOIN LATERAL jsonb_each_text(latest_shap.shap_values) item
                LEFT JOIN people.attrition_feature_catalog catalog
                  ON catalog.model_type = latest_shap.model_type
                 AND catalog.model_version = latest_shap.model_version
                 AND catalog.feature_key = item.key
                 AND catalog.is_active = TRUE
            )
            SELECT *
            FROM drivers
            WHERE shap_value <> 0
            ORDER BY abs_shap_value DESC, feature_key ASC
            """
        )
        driver_rows = (
            await self.db.execute(
                drivers_query,
                {"employee_id": employee_id, "model_type": model_type},
            )
        ).mappings().all()

        drivers = [self._serialize_driver(row) for row in driver_rows]
        increases_risk = [
            driver for driver in drivers if driver["impact_direction"] == "increases_risk"
        ][:3]
        decreases_risk = [
            driver for driver in drivers if driver["impact_direction"] == "decreases_risk"
        ][:3]

        return {
            "employee_id": latest_shap["employee_id"],
            "model_type": latest_shap["model_type"],
            "model_version": latest_shap["model_version"],
            "prediction_date": latest_shap["prediction_date"].isoformat()
            if latest_shap["prediction_date"]
            else None,
            "source_file_name": latest_shap["source_file_name"],
            "source_run_id": latest_shap["source_run_id"],
            "attrition_rate": float(attrition["attrition_rate"])
            if attrition and attrition["attrition_rate"] is not None
            else None,
            "attrition_calculated_at": attrition["calculated_at"].isoformat()
            if attrition and attrition["calculated_at"]
            else None,
            "drivers_increasing_risk": increases_risk,
            "drivers_decreasing_risk": decreases_risk,
        }

    def _serialize_driver(self, row: Any) -> dict[str, Any]:
        shap_value = float(row["shap_value"])
        abs_shap_value = float(row["abs_shap_value"])
        return {
            "feature_key": row["feature_key"],
            "model_feature_name": row["model_feature_name"],
            "label": row["human_label_es"],
            "business_domain": row["business_domain"],
            "description": row["description_es"],
            "positive_impact_meaning": row["positive_impact_meaning_es"],
            "negative_impact_meaning": row["negative_impact_meaning_es"],
            "sensitivity_level": row["sensitivity_level"],
            "shap_value": round(shap_value, 6),
            "abs_shap_value": round(abs_shap_value, 6),
            "impact_direction": row["impact_direction"],
        }
