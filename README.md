# Tampere Data Dashboard

Interaktiivinen Dash-sovellus, joka näyttää Tampereen postinumeroalueiden
tilastoja kartalla ja kaavioissa.

## Näkymät

- **Kartta** (Folium), kaksi tasoa:
  - *General Information*: ympyrän pinta-ala kuvaa asukasmäärää, ponnahdusikkunassa
    pinta-ala, asukasmäärä, keski-ikä ja mediaanitulot.
  - *Population Density*: ympyrän väri kuvaa asukastiheyttä (as./km²).
- **Mediaanitulot** alueittain pylväskaaviona, suuruusjärjestyksessä.
- **Koulutusaste** ja **pääasiallinen toiminta** valitulla alueella verrattuna koko
  Tampereen (väestöllä painotettuun) keskiarvoon.

Alueen voi valita pudotusvalikosta tai klikkaamalla pylvästä. Valittu alue korostuu
kartalla ja pylväskaaviossa.

## Data

Tilastokeskus, Paavo – postinumeroalueittainen avoin tieto, vuosi 2022
(JSON-stat-muodossa):

| Tiedosto | Sisältö |
| --- | --- |
| `koordinaatit.json` | Alueiden keskipisteet (ETRS-TM35FIN, EPSG:3067) |
| `populaatio.json` | Asukkaat, miehet, naiset, keski-ikä (HE) |
| `asukastiheys.json` | Pinta-ala (m²) ja asukkaat (HE) |
| `tulot.json` | Asukkaiden mediaanitulot (HR) |
| `toiminta.json` | Pääasiallinen toiminta (PT) |
| `koulutus.json` | Koulutusasteiden osuudet (%) – valmiiksi laskettu, lähde tarkennettava |

## Asennus ja ajo

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Avaa selaimessa http://127.0.0.1:8050.
