# Ilmanlaatudatan REST API

Tämä on tehtävän toinen sovellus. Se lukee aiemmin tallennettua ilmanlaatudataa SQLite-tietokannasta ja tarjoaa datan REST-rajapinnan kautta.

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

Sovellus käynnistyy yleensä osoitteeseen:

`http://127.0.0.1:8000`

Swagger-sivu, josta endpointteja voi testata:

`http://127.0.0.1:8000/docs`

## Endpointit

### 1. Yhden päivän mittaukset

```http
GET /locations/{location_id}/measurements?date=2024-01-15
```

Tällä haetaan valitun mittauspaikan mittaukset yhdeltä päivältä.

### 2. Mittausten lukumäärä

```http
GET /locations/{location_id}/measurements/count
```

Tällä haetaan, kuinka monta mittausta mittauspaikalla on yhteensä.

### 3. Päivän keskiarvo

```http
GET /locations/{location_id}/sensors/{sensor_id}/daily-average?date=2024-01-15
```

Tämä laskee valitun mittauspaikan ja sensorin mittausten keskiarvon yhdeltä päivältä.

## Tietokanta

API käyttää samaa tietokantaa kuin datan hakusovellus.

```env
DATABASE_PATH=../air_quality.sqlite
```
