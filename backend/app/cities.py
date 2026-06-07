from unicodedata import combining, normalize


CITY_PRESETS = {
    "BR": {
        "Recife": {"lat": -8.0476, "lon": -34.8770, "radius": 25000},
        "São Paulo": {"lat": -23.5558, "lon": -46.6396, "radius": 25000},
        "Rio de Janeiro": {"lat": -22.9068, "lon": -43.1729, "radius": 25000},
        "Fortaleza": {"lat": -3.7319, "lon": -38.5267, "radius": 25000},
        "Manaus": {"lat": -3.1190, "lon": -60.0217, "radius": 25000},
        "Belo Horizonte": {"lat": -19.9167, "lon": -43.9345, "radius": 25000},
        "Curitiba": {"lat": -25.4284, "lon": -49.2733, "radius": 25000},
        "Porto Alegre": {"lat": -30.0346, "lon": -51.2177, "radius": 25000},
        "Brasília": {"lat": -15.7939, "lon": -47.8828, "radius": 25000},
    },
    "PT": {
        "Lisboa": {"lat": 38.7223, "lon": -9.1393, "radius": 25000},
        "Porto": {"lat": 41.1579, "lon": -8.6291, "radius": 25000},
        "Braga": {"lat": 41.5454, "lon": -8.4265, "radius": 25000},
        "Coimbra": {"lat": 40.2033, "lon": -8.4103, "radius": 25000},
    },
    "US": {
        "Los Angeles": {"lat": 34.0522, "lon": -118.2437, "radius": 25000},
        "New York": {"lat": 40.7128, "lon": -74.0060, "radius": 25000},
        "Chicago": {"lat": 41.8781, "lon": -87.6298, "radius": 25000},
        "Houston": {"lat": 29.7604, "lon": -95.3698, "radius": 25000},
        "Seattle": {"lat": 47.6062, "lon": -122.3321, "radius": 25000},
        "Denver": {"lat": 39.7392, "lon": -104.9903, "radius": 25000},
        "San Francisco": {"lat": 37.7749, "lon": -122.4194, "radius": 25000},
    },
    "AR": {
        "Buenos Aires": {"lat": -34.6037, "lon": -58.3816, "radius": 25000},
        "Córdoba": {"lat": -31.4201, "lon": -64.1888, "radius": 25000},
        "Mendoza": {"lat": -32.8895, "lon": -68.8458, "radius": 25000},
    },
    "GB": {
        "London": {"lat": 51.5072, "lon": -0.1276, "radius": 25000},
        "Manchester": {"lat": 53.4808, "lon": -2.2426, "radius": 25000},
        "Birmingham": {"lat": 52.4862, "lon": -1.8904, "radius": 25000},
    },
    "FR": {
        "Paris": {"lat": 48.8566, "lon": 2.3522, "radius": 25000},
        "Lyon": {"lat": 45.7640, "lon": 4.8357, "radius": 25000},
        "Marseille": {"lat": 43.2965, "lon": 5.3698, "radius": 25000},
    },
    "DE": {
        "Berlin": {"lat": 52.5200, "lon": 13.4050, "radius": 25000},
        "Munich": {"lat": 48.1351, "lon": 11.5820, "radius": 25000},
        "Hamburg": {"lat": 53.5511, "lon": 9.9937, "radius": 25000},
    },
    "ES": {
        "Madrid": {"lat": 40.4168, "lon": -3.7038, "radius": 25000},
        "Barcelona": {"lat": 41.3874, "lon": 2.1686, "radius": 25000},
        "Valencia": {"lat": 39.4699, "lon": -0.3763, "radius": 25000},
    },
    "IT": {
        "Rome": {"lat": 41.9028, "lon": 12.4964, "radius": 25000},
        "Milan": {"lat": 45.4642, "lon": 9.1900, "radius": 25000},
        "Naples": {"lat": 40.8518, "lon": 14.2681, "radius": 25000},
    },
    "CA": {
        "Toronto": {"lat": 43.6532, "lon": -79.3832, "radius": 25000},
        "Vancouver": {"lat": 49.2827, "lon": -123.1207, "radius": 25000},
        "Montreal": {"lat": 45.5019, "lon": -73.5674, "radius": 25000},
    },
    "MX": {
        "Mexico City": {"lat": 19.4326, "lon": -99.1332, "radius": 25000},
        "Guadalajara": {"lat": 20.6597, "lon": -103.3496, "radius": 25000},
        "Monterrey": {"lat": 25.6866, "lon": -100.3161, "radius": 25000},
    },
    "CL": {
        "Santiago": {"lat": -33.4489, "lon": -70.6693, "radius": 25000},
        "Valparaíso": {"lat": -33.0472, "lon": -71.6127, "radius": 25000},
    },
    "CO": {
        "Bogotá": {"lat": 4.7110, "lon": -74.0721, "radius": 25000},
        "Medellín": {"lat": 6.2442, "lon": -75.5812, "radius": 25000},
    },
    "JP": {
        "Tokyo": {"lat": 35.6762, "lon": 139.6503, "radius": 25000},
        "Osaka": {"lat": 34.6937, "lon": 135.5023, "radius": 25000},
    },
    "AU": {
        "Sydney": {"lat": -33.8688, "lon": 151.2093, "radius": 25000},
        "Melbourne": {"lat": -37.8136, "lon": 144.9631, "radius": 25000},
    },
    "IN": {
        "Delhi": {"lat": 28.6139, "lon": 77.2090, "radius": 25000},
        "Mumbai": {"lat": 19.0760, "lon": 72.8777, "radius": 25000},
        "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "radius": 25000},
    },
}

COUNTRY_LABELS = {
    "BR": "Brasil",
    "AR": "Argentina",
    "PT": "Portugal",
    "US": "Estados Unidos",
    "GB": "Reino Unido",
    "FR": "França",
    "DE": "Alemanha",
    "ES": "Espanha",
    "IT": "Itália",
    "CA": "Canadá",
    "MX": "México",
    "CL": "Chile",
    "CO": "Colômbia",
    "JP": "Japão",
    "AU": "Austrália",
    "IN": "Índia",
}


def normalize_city_name(value: str) -> str:
    value = normalize("NFKD", value)
    return "".join(char for char in value if not combining(char)).casefold()


def get_city_config(country: str, city: str) -> dict:
    country = country.upper()
    cities = CITY_PRESETS.get(country, {})
    if city not in cities:
        normalized = normalize_city_name(city)
        city = next((name for name in cities if normalize_city_name(name) == normalized), city)
    if country not in CITY_PRESETS or city not in CITY_PRESETS[country]:
        available = ", ".join(CITY_PRESETS.get(country, {}).keys()) or "nenhuma cidade cadastrada"
        raise ValueError(f"Cidade não cadastrada para {country}: {city}. Disponíveis: {available}.")
    return CITY_PRESETS[country][city]
