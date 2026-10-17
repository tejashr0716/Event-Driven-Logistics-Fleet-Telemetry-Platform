import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, max as _max, min as _min, when, lit, round as _round
)
from pyspark.sql.types import (
    StructType, StructField, LongType, StringType, DoubleType, TimestampType
)

def create_spark_session(app_name="FleetSync-Anomaly-Analytics"):
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

def analyze_fleet_telemetry(spark: SparkSession, pings_data=None):
    schema = StructType([
        StructField("ping_id", LongType(), False),
        StructField("vehicle_id", StringType(), False),
        StructField("latitude", DoubleType(), False),
        StructField("longitude", DoubleType(), False),
        StructField("speed_kmh", DoubleType(), False),
        StructField("fuel_pct", DoubleType(), False),
        StructField("engine_temp_c", DoubleType(), False),
        StructField("recorded_at", TimestampType(), False),
    ])

    if pings_data:
        df = spark.createDataFrame(pings_data, schema=schema)
    else:
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        sample = [
            (1, "TRUCK_01", 12.9716, 77.5946, 65.0, 92.0, 84.0, now - timedelta(seconds=50)),
            (2, "TRUCK_01", 12.9740, 77.5980, 72.0, 91.5, 86.0, now - timedelta(seconds=40)),
            (3, "TRUCK_01", 12.9780, 77.6020, 85.0, 90.8, 89.0, now - timedelta(seconds=30)),
            (4, "TRUCK_02", 13.1980, 77.7060, 98.0, 78.0, 92.0, now - timedelta(seconds=20)),
            (5, "TRUCK_02", 13.2010, 77.7120, 102.0, 76.5, 94.0, now - timedelta(seconds=10)),
            (6, "VAN_01", 12.9300, 77.5500, 0.0, 85.0, 88.0, now),
        ]
        df = spark.createDataFrame(sample, schema=schema)

    # 1. Fleet Vehicle Performance Aggregation
    fleet_summary = df.groupBy("vehicle_id").agg(
        count("ping_id").alias("ping_count"),
        _round(avg("speed_kmh"), 1).alias("avg_speed_kmh"),
        _round(_max("speed_kmh"), 1).alias("max_speed_kmh"),
        _round(_min("fuel_pct"), 1).alias("current_fuel_pct"),
        _round(avg("engine_temp_c"), 1).alias("avg_engine_temp_c"),
        _sum(when(col("speed_kmh") > 80.0, lit(1)).otherwise(lit(0))).alias("overspeed_pings"),
        _sum(when(col("speed_kmh") == 0.0, lit(1)).otherwise(lit(0))).alias("idle_pings")
    ).orderBy(col("overspeed_pings").desc())

    # 2. Driver Safety Anomaly Score
    anomaly_df = fleet_summary.withColumn(
        "safety_risk_score",
        _round((col("overspeed_pings") * 25.0) + (col("max_speed_kmh") * 0.5), 1)
    )

    return {
        "summary": fleet_summary,
        "anomalies": anomaly_df
    }

if __name__ == "__main__":
    spark = create_spark_session()
    print("\n========== RUNNING FLEETSYNC APACHE SPARK TELEMETRY ANALYTICS ==========")
    results = analyze_fleet_telemetry(spark)

    print("\n--- Fleet Performance & Telemetry Summary ---")
    results["summary"].show(truncate=False)

    print("\n--- Driver Safety Risk & Anomaly Score ---")
    results["anomalies"].show(truncate=False)

    spark.stop()
