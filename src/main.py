from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query


load_dotenv()

app = FastAPI(
    title="OpenAQ measurements API",
    version="1.0.0",
    description="REST API stored OpenAQ air quality measurements.",
)


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", "../air_quality.sqlite"))


def get_connection() -> sqlite3.Connection:
    path = database_path()
    if not path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Database not found at {path}. Run the importer first.",
        )
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def day_bounds(selected_date: date) -> tuple[str, str]:
    start = datetime.combine(selected_date, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/locations/{location_id}/measurements")
def get_daily_measurements(
    location_id: int,
    selected_date: date = Query(alias="date"),
) -> dict[str, Any]:
    start, end = day_bounds(selected_date)
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                m.id,
                m.sensor_id,
                s.parameter_name,
                s.parameter_display_name,
                m.measured_at_utc,
                m.measured_at_local,
                m.value,
                m.unit,
                m.latitude,
                m.longitude,
                m.source_name
            FROM measurements m
            JOIN sensors s ON s.id = m.sensor_id
            WHERE s.location_id = ?
              AND m.measured_at_utc >= ?
              AND m.measured_at_utc < ?
            ORDER BY m.measured_at_utc
            """,
            (location_id, start, end),
        ).fetchall()

    return {
        "location_id": location_id,
        "date": selected_date.isoformat(),
        "count": len(rows),
        "measurements": [row_to_dict(row) for row in rows],
    }


@app.get("/locations/{location_id}/measurements/count")
def get_location_measurement_count(location_id: int) -> dict[str, int]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS measurement_count
            FROM measurements m
            JOIN sensors s ON s.id = m.sensor_id
            WHERE s.location_id = ?
            """,
            (location_id,),
        ).fetchone()

    return {
        "location_id": location_id,
        "measurement_count": int(row["measurement_count"]),
    }


@app.get("/locations/{location_id}/sensors/{sensor_id}/daily-average")
def get_sensor_daily_average(
    location_id: int,
    sensor_id: int,
    selected_date: date = Query(alias="date"),
) -> dict[str, Any]:
    start, end = day_bounds(selected_date)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                s.id AS sensor_id,
                s.location_id,
                s.parameter_name,
                s.parameter_display_name,
                s.unit,
                COUNT(m.id) AS measurement_count,
                AVG(m.value) AS average_value
            FROM sensors s
            LEFT JOIN measurements m
                ON m.sensor_id = s.id
               AND m.measured_at_utc >= ?
               AND m.measured_at_utc < ?
            WHERE s.id = ?
              AND s.location_id = ?
            GROUP BY s.id
            """,
            (start, end, sensor_id, location_id),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Sensor was not found for this location.")

    return {
        "location_id": location_id,
        "sensor_id": sensor_id,
        "date": selected_date.isoformat(),
        "parameter_name": row["parameter_name"],
        "parameter_display_name": row["parameter_display_name"],
        "unit": row["unit"],
        "measurement_count": int(row["measurement_count"]),
        "average_value": row["average_value"],
    }
