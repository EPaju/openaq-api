# Ilmanlaatudatan REST API

Sovellus lukee aiemmin tallennettua OpenAQ-dataa SQLite-tietokannasta.

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

## Endpointit id-arvoilla

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

## Endpointit nimillä

Tallennetut paikat ja sensorit:

```http
GET /places
```

Yhden päivän mittaukset nimillä:

```http
GET /measurements/by-name?country=United States&city=New York&location=Queens College&date=2024-01-15
```

Mittausten lukumäärä nimillä:

```http
GET /measurements/count/by-name?country=United States&city=New York&location=Queens College
```

Päivän keskiarvo nimillä:

```http
GET /daily-average/by-name?country=United States&city=New York&location=Queens College&sensor=pm25&date=2024-01-15
```

Nämä nimihakua varten, jotta tulevaa sovellusta voi käyttää helpommin!

## Endpointit kaupungilla

Yhden päivän mittaukset kaupungin perusteella:

```http
GET /measurements/by-city?city=New York&date=2024-01-15
```

Kaupungin kaikkien mittausten lukumäärä:

```http
GET /measurements/count/by-city?city=New York
```

Kaupungin ja sensorin päivän keskiarvo:

```http
GET /daily-average/by-city?city=New York&sensor=pm25&date=2024-01-15
```

## Tietokanta

```env
DATABASE_PATH=../air_quality.sqlite
```

## Testaus

testattu uusilla muokkauksilla
