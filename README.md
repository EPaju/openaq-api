# OpenAQ REST API

Tämä repositorio sisältää REST-rajapintasovelluksen, jolla haetaan `openaq-importer`-sovelluksen tallentamaa ilmanlaatudataa SQLite-tietokannasta.

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

Oletusosoite on:

`http://127.0.0.1:8000`

Swagger-dokumentaatio:

`http://127.0.0.1:8000/docs`

## Endpointit

### Mittauspaikan yhden päivän mittaukset

```http
GET /locations/{location_id}/measurements?date=2024-01-15
```

### Mittauspaikan kaikkien mittausten lukumäärä

```http
GET /locations/{location_id}/measurements/count
```

### Sensorin päivittäinen keskiarvo valitulla mittauspaikalla

```http
GET /locations/{location_id}/sensors/{sensor_id}/daily-average?date=2024-01-15
```

## Tietokanta

API lukee samaa SQLite-tietokantaa kuin importteri. Muuta polku `.env`-tiedostossa:

```env
DATABASE_PATH=../air_quality.sqlite
```
