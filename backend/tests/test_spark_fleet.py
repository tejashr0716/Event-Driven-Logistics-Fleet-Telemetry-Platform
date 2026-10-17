import pytest
from datetime import datetime
from spark.fleet_streaming_anomaly_job import create_spark_session, analyze_fleet_telemetry

def test_spark_fleet_analytics():
    spark = create_spark_session("FleetSync-Test-Spark")
    try:
        now = datetime.utcnow()
        sample = [
            (101, "ROVER_A", 12.97, 77.59, 95.0, 90.0, 85.0, now),
            (102, "ROVER_A", 12.98, 77.60, 105.0, 88.0, 87.0, now),
            (103, "ROVER_B", 12.95, 77.58, 45.0, 95.0, 80.0, now),
        ]
        results = analyze_fleet_telemetry(spark, sample)
        summary_rows = results["summary"].collect()
        assert len(summary_rows) == 2

        rover_a = [r for r in summary_rows if r["vehicle_id"] == "ROVER_A"][0]
        assert rover_a["overspeed_pings"] == 2
        assert rover_a["max_speed_kmh"] == 105.0

        rover_b = [r for r in summary_rows if r["vehicle_id"] == "ROVER_B"][0]
        assert rover_b["overspeed_pings"] == 0
    finally:
        spark.stop()
