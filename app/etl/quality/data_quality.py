import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
)

import great_expectations as gx
import pandas as pd
from datetime import datetime


def run_data_quality_check(df: pd.DataFrame) -> dict:
    """Run data quality checks using Great Expectations."""
    try:
        context = gx.get_context()

        batch = context.data_sources.pandas_default.read_dataframe(
            dataframe=df, asset_name="transactions"
        )
        validator = context.get_validator(batch=batch)

        results = {}

        results["row_count"] = validator.expect_table_row_count_to_be_between(
            min_value=1
        )
        results["no_null_amount"] = validator.expect_column_values_to_not_be_null(
            column="amount"
        )
        results["positive_amount"] = validator.expect_column_values_to_be_between(
            column="amount", min_value=0.01
        )
        results["valid_risk_score"] = validator.expect_column_values_to_be_between(
            column="risk_score", min_value=0, max_value=100
        )
        results["valid_currency"] = validator.expect_column_values_to_be_in_set(
            column="currency", value_set=["USD", "SGD", "EUR", "IDR"]
        )

        success_count = sum(1 for v in results.values() if v["success"])
        total_checks = len(results)

        print(
            f"Data Quality Check Completed: {success_count}/{total_checks} checks passed"
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "total_checks": total_checks,
            "successful_checks": success_count,
            "success_rate": round(success_count / total_checks * 100, 2),
            "results": {k: v["success"] for k, v in results.items()},
        }

    except Exception as e:
        print(f"Data Quality Check Failed: {e}")
        return {"error": str(e)}


# Test function
if __name__ == "__main__":
    from src.app.core.database import SessionLocal
    from src.app.etl.etl_pipeline import extract_transactions, transform_data

    db = SessionLocal()
    df = extract_transactions(db)
    df = transform_data(df)
    dq_result = run_data_quality_check(df)
    print(dq_result)
    db.close()
