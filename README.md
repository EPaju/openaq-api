# Ilmanlaatudatan REST API

Tämä sovellus hakee aiemmin tallennettua OpenAQ-dataa SQLite-tietokannasta.

## Asennus

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Käynnistys

```powershell
uvicorn src.main:app --reload
```

Swagger-sivu:

```text
http://127.0.0.1:8000/docs
```

## Endpointit

### Yhden päivän mittaukset

```http
GET /locations/{location_id}/measurements?date=2024-01-15
```

### Mittausten lukumäärä

```http
GET /locations/{location_id}/measurements/count
```

### Päivän keskiarvo

```http
GET /locations/{location_id}/sensors/{sensor_id}/daily-average?date=2024-01-15
```

## Testaus

Testattu arvoilla:

```text
location_id = 2178
sensor_id = 3917
date = 2024-01-15
```

## Tietokanta

API käyttää samaa SQLite-tietokantaa kuin datan hakusovellus.

```env
DATABASE_PATH=../air_quality.sqlite
```
