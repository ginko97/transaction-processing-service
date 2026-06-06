from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, max as spark_max, min as spark_min
import glob
import os


def run_spark_analytics():
    spark = (
        SparkSession.builder.appName("Transaction Analytics")
        .master("local[1]")
        .config("spark.driver.memory", "1g")
        .getOrCreate()
    )

    print("✅ SparkSession created successfully!")

    # Find the latest parquet file
    parquet_files = glob.glob("data/clean_transactions_*.parquet")

    if not parquet_files:
        print("No Parquet files found in data/ folder. Run ETL first.")
        spark.stop()
        return

    latest_file = max(parquet_files, key=os.path.getctime)
    print(f"Reading file: {latest_file}")

    df = spark.read.parquet(latest_file)

    print(f"Total transactions: {df.count()}")

    # Basic analytics
    df.groupBy("currency").agg(
        count("*").alias("tx_count"),
        avg("amount").alias("avg_amount"),
        spark_max("amount").alias("max_amount"),
        spark_min("risk_score").alias("min_risk"),
    ).show()

    # High risk transactions
    high_risk = df.filter(col("risk_score") >= 70)
    print(f"High risk transactions: {high_risk.count()}")

    spark.stop()


if __name__ == "__main__":
    run_spark_analytics()
