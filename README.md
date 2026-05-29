# Ilmanlaatudatan REST API

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

## Endpointit

### Yhden päivän mittaukset

```http
GET /locations/{location_id}/measurements?date=2024-01-15
```

## Haetaan valitun mittauspaikan mittaukset yhdeltä päivältä

### 2. Mittausten lukumäärä

```http
GET /locations/{location_id}/measurements/count
```

## Haetaan, kuinka monta mittausta mittauspaikalla on yhteensä

### 3. Päivän keskiarvo

```http
GET /locations/{location_id}/sensors/{sensor_id}/daily-average?date=2024-01-15
```

## Lasketaan valitun mittauspaikan ja sensorin mittausten keskiarvot yhdeltä päivältä

## Tietokanta

```env
DATABASE_PATH=../air_quality.sqlite
```
