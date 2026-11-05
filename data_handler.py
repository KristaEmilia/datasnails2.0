"""Reads the Paavo JSON-stat files and combines them into one record per postal code area."""

import json
import os
import re

import pyproj

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ETRS-TM35FIN (EPSG:3067) -> WGS84 (EPSG:4326)
_transformer = pyproj.Transformer.from_crs('EPSG:3067', 'EPSG:4326', always_xy=True)


def read_json_file(file_name):
    with open(os.path.join(DATA_DIR, file_name), 'r', encoding='utf-8') as file:
        return json.load(file)


def convert_to_lat_lon(x_coord, y_coord):
    lon, lat = _transformer.transform(x_coord, y_coord)
    return lat, lon


def _values_by_area(dataset):
    """Split a JSON-stat dataset into {postal_code: [values...]}.

    Values are stored area by area, so each area gets an equal-sized slice.
    """
    index = dataset['dimension']['Postinumeroalue']['category']['index']
    values = dataset['value']
    per_area = len(values) // len(index)
    return {code: values[i * per_area:(i + 1) * per_area] for code, i in index.items()}


def _area_names(dataset):
    """'33100  Tampere Keskus (Tampere)' -> 'Tampere Keskus'."""
    labels = dataset['dimension']['Postinumeroalue']['category']['label']
    names = {}
    for code, label in labels.items():
        match = re.match(r'^\d{5}\s+(.*?)\s*\([^)]*\)$', label)
        names[code] = match.group(1) if match else label
    return names


def _percentages(counts, total):
    return {key: (count / total * 100 if total else 0) for key, count in counts.items()}


def load_areas():
    """Return a list of area dicts, ordered by postal code."""
    coordinates = read_json_file('koordinaatit.json')['dataset']
    population = _values_by_area(read_json_file('populaatio.json')['dataset'])
    density = _values_by_area(read_json_file('asukastiheys.json')['dataset'])
    income = _values_by_area(read_json_file('tulot.json')['dataset'])
    activity = _values_by_area(read_json_file('toiminta.json')['dataset'])
    education = read_json_file('koulutus.json')

    names = _area_names(coordinates)
    xy = _values_by_area(coordinates)

    areas = []
    for code in sorted(xy):
        latitude, longitude = convert_to_lat_lon(*xy[code])
        inhabitants, _males, _females, average_age = population[code]
        surface_area_km2 = density[code][0] / 1_000_000

        total, employed, unemployed, children, students, retired, other = activity[code]

        areas.append({
            'code': code,
            'name': names[code],
            'lat': latitude,
            'lon': longitude,
            'population': int(inhabitants),
            'average_age': average_age,
            'surface_area_km2': surface_area_km2,
            'density': inhabitants / surface_area_km2 if surface_area_km2 else 0,
            'median_income': income[code][0],
            'education': education.get(code, {}),
            'activity': _percentages({
                'Employed': employed,
                'Unemployed': unemployed,
                'Children (0–14)': children,
                'Students': students,
                'Retired': retired,
                'Other': other,
            }, total),
        })
    return areas
