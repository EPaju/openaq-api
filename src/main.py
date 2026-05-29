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


def find_location(
    connection: sqlite3.Connection,
    country: str,
    city: str,
    location: str,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            l.id AS location_id,
            l.name AS location_name,
            c.name AS city_name,
            co.name AS country_name,
            co.code AS country_code
        FROM locations l
        JOIN cities c ON c.id = l.city_id
        JOIN countries co ON co.id = c.country_id
        WHERE LOWER(co.name) = LOWER(?)
          AND LOWER(c.name) = LOWER(?)
          AND LOWER(l.name) = LOWER(?)
        """,
        (country, city, location),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Location was not found.")
    return row


def find_sensor(
    connection: sqlite3.Connection,
    location_id: int,
    sensor: str,
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT id, parameter_name, parameter_display_name, unit
        FROM sensors
        WHERE location_id = ?
          AND (
            LOWER(parameter_name) = LOWER(?)
            OR LOWER(parameter_display_name) = LOWER(?)
          )
        """,
        (location_id, sensor, sensor),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Sensor was not found for this location.")
    return row


def find_city(connection: sqlite3.Connection, city: str) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT
            c.id AS city_id,
            c.name AS city_name,
            co.name AS country_name,
            co.code AS country_code
        FROM cities c
        JOIN countries co ON co.id = c.country_id
        WHERE LOWER(c.name) = LOWER(?)
        """,
        (city,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="City was not found.")
    return row


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/places")
def get_places() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                co.name AS country,
                c.name AS city,
                l.id AS location_id,
                l.name AS location,
                s.id AS sensor_id,
                s.parameter_name,
                s.parameter_display_name,
                s.unit
            FROM locations l
            JOIN cities c ON c.id = l.city_id
            JOIN countries co ON co.id = c.country_id
            JOIN sensors s ON s.location_id = l.id
            ORDER BY co.name, c.name, l.name, s.parameter_name
            """
        ).fetchall()

    return [row_to_dict(row) for row in rows]


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


@app.get("/measurements/by-name")
def get_daily_measurements_by_name(
    country: str,
    city: str,
    location: str,
    selected_date: date = Query(alias="date"),
) -> dict[str, Any]:
    start, end = day_bounds(selected_date)
    with get_connection() as connection:
        place = find_location(connection, country, city, location)
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
            (place["location_id"], start, end),
        ).fetchall()

    return {
        "country": place["country_name"],
        "city": place["city_name"],
        "location": place["location_name"],
        "location_id": place["location_id"],
        "date": selected_date.isoformat(),
        "count": len(rows),
        "measurements": [row_to_dict(row) for row in rows],
    }


@app.get("/measurements/by-city")
def get_daily_measurements_by_city(
    city: str,
    selected_date: date = Query(alias="date"),
) -> dict[str, Any]:
    start, end = day_bounds(selected_date)
    with get_connection() as connection:
        city_row = find_city(connection, city)
        rows = connection.execute(
            """
            SELECT
                co.name AS country,
                c.name AS city,
                l.id AS location_id,
                l.name AS location,
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
            JOIN locations l ON l.id = s.location_id
            JOIN cities c ON c.id = l.city_id
            JOIN countries co ON co.id = c.country_id
            WHERE c.id = ?
              AND m.measured_at_utc >= ?
              AND m.measured_at_utc < ?
            ORDER BY l.name, s.parameter_name, m.measured_at_utc
            """,
            (city_row["city_id"], start, end),
        ).fetchall()

    return {
        "country": city_row["country_name"],
        "city": city_row["city_name"],
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


@app.get("/measurements/count/by-name")
def get_location_measurement_count_by_name(
    country: str,
    city: str,
    location: str,
) -> dict[str, Any]:
    with get_connection() as connection:
        place = find_location(connection, country, city, location)
        row = connection.execute(
            """
            SELECT COUNT(*) AS measurement_count
            FROM measurements m
            JOIN sensors s ON s.id = m.sensor_id
            WHERE s.location_id = ?
            """,
            (place["location_id"],),
        ).fetchone()

    return {
        "country": place["country_name"],
        "city": place["city_name"],
        "location": place["location_name"],
        "location_id": place["location_id"],
        "measurement_count": int(row["measurement_count"]),
    }


@app.get("/measurements/count/by-city")
def get_measurement_count_by_city(city: str) -> dict[str, Any]:
    with get_connection() as connection:
        city_row = find_city(connection, city)
        row = connection.execute(
            """
            SELECT COUNT(*) AS measurement_count
            FROM measurements m
            JOIN sensors s ON s.id = m.sensor_id
            JOIN locations l ON l.id = s.location_id
            WHERE l.city_id = ?
            """,
            (city_row["city_id"],),
        ).fetchone()

    return {
        "country": city_row["country_name"],
        "city": city_row["city_name"],
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


@app.get("/daily-average/by-name")
def get_sensor_daily_average_by_name(
    country: str,
    city: str,
    location: str,
    sensor: str,
    selected_date: date = Query(alias="date"),
) -> dict[str, Any]:
    start, end = day_bounds(selected_date)
    with get_connection() as connection:
        place = find_location(connection, country, city, location)
        sensor_row = find_sensor(connection, place["location_id"], sensor)
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
            (start, end, sensor_row["id"], place["location_id"]),
        ).fetchone()

    return {
        "country": place["country_name"],
        "city": place["city_name"],
        "location": place["location_name"],
        "location_id": place["location_id"],
        "sensor_id": row["sensor_id"],
        "date": selected_date.isoformat(),
        "parameter_name": row["parameter_name"],
        "parameter_display_name": row["parameter_display_name"],
        "unit": row["unit"],
        "measurement_count": int(row["measurement_count"]),
        "average_value": row["average_value"],
    }


@app.get("/daily-average/by-city")
def get_daily_average_by_city(
    city: str,
    sensor: str,
    selected_date: date = Query(alias="date"),
) -> dict[str, Any]:
    start, end = day_bounds(selected_date)
    with get_connection() as connection:
        city_row = find_city(connection, city)
        row = connection.execute(
            """
            SELECT
                c.name AS city,
                s.parameter_name,
                s.parameter_display_name,
                s.unit,
                COUNT(m.id) AS measurement_count,
                AVG(m.value) AS average_value
            FROM measurements m
            JOIN sensors s ON s.id = m.sensor_id
            JOIN locations l ON l.id = s.location_id
            JOIN cities c ON c.id = l.city_id
            WHERE c.id = ?
              AND (
                LOWER(s.parameter_name) = LOWER(?)
                OR LOWER(s.parameter_display_name) = LOWER(?)
              )
              AND m.measured_at_utc >= ?
              AND m.measured_at_utc < ?
            GROUP BY c.id, s.parameter_name, s.parameter_display_name, s.unit
            """,
            (city_row["city_id"], sensor, sensor, start, end),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="No measurements were found for this city and sensor.")

    return {
        "country": city_row["country_name"],
        "city": city_row["city_name"],
        "date": selected_date.isoformat(),
        "parameter_name": row["parameter_name"],
        "parameter_display_name": row["parameter_display_name"],
        "unit": row["unit"],
        "measurement_count": int(row["measurement_count"]),
        "average_value": row["average_value"],
    }
