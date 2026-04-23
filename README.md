# Fahrtenbuch für Home Assistant

Digitales Fahrtenbuch als Home Assistant Custom Integration.  
Zeichnet Fahrten automatisch auf – mit KM-Stand vom Auto und GPS-Standort von deiner Person.

---

## Features

- **Fahrt starten** – erfasst automatisch den aktuellen KM-Stand und deinen Standort
- **Fahrt beenden** – als **dienstlich** oder **privat** markieren, optionaler Zweck/Ziel
- **Gefahrene KM** werden automatisch berechnet
- **Alle Fahrten** werden dauerhaft in Home Assistant gespeichert
- **CSV-Export** direkt aus HA heraus
- **5 Sensor-Entitäten**: Status, Fahrtenzähler, Dienstliche KM, Private KM, Aktuelle Start-KM
- Fertige **Lovelace-Dashboard-Vorlage** enthalten

---

## Installation via HACS

### Schritt 1 – Repository hinzufügen

1. HACS in Home Assistant öffnen
2. **Integrationen** auswählen
3. Oben rechts auf die **drei Punkte (⋮)** klicken → **Benutzerdefinierte Repositories**
4. URL eingeben: `https://github.com/19DMO89/fahrtenbuch`
5. Kategorie: **Integration**
6. **Hinzufügen** klicken

### Schritt 2 – Integration installieren

1. In HACS → Integrationen nach **Fahrtenbuch** suchen
2. **Herunterladen** klicken
3. Home Assistant **neu starten**

### Schritt 3 – Integration einrichten

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **Fahrtenbuch** suchen
3. Im Dialog auswählen:
   - **KM-Stand Sensor** – der Sensor deines Autos (z. B. `sensor.auto_odometer`)
   - **Personen-Tracker** – deine Person oder Device Tracker (z. B. `person.ich`)
4. **Fertig**

---

## Dashboard einrichten

Die Datei [`lovelace_dashboard.yaml`](lovelace_dashboard.yaml) enthält eine fertige Lovelace-Vorlage mit:

- Statusanzeige (aktive Fahrt / Bereit)
- Drei Buttons: **Fahrt starten**, **Dienstlich beenden**, **Privat beenden**
- Tabelle der letzten 5 Fahrten
- CSV-Export-Button

**Einbinden:**
1. Einstellungen → Dashboards → **Dashboard hinzufügen**
2. Titel vergeben, Typ: **YAML**
3. Den Inhalt von `lovelace_dashboard.yaml` einfügen

---

## Services

| Service | Beschreibung |
|---|---|
| `fahrtenbuch.start_trip` | Startet eine Fahrt – liest KM-Stand + Standort automatisch |
| `fahrtenbuch.stop_trip` | Beendet die Fahrt – Parameter: `trip_type` (`dienstlich`/`privat`), optionaler `purpose` |
| `fahrtenbuch.export_csv` | Exportiert alle Fahrten als CSV ins HA-Konfigurationsverzeichnis |
| `fahrtenbuch.delete_trip` | Löscht einen Eintrag per `trip_id` |

### Beispiel: Fahrt per Automation beenden

```yaml
service: fahrtenbuch.stop_trip
data:
  trip_type: dienstlich
  purpose: Kundentermin München
```

---

## Sensoren

Nach der Einrichtung stehen folgende Entitäten zur Verfügung (alle unter einem Gerät gruppiert):

| Entität | Beschreibung |
|---|---|
| `sensor.fahrtenbuch_status` | "Fahrt aktiv" oder "Bereit" |
| `sensor.fahrtenbuch_fahrten_gesamt` | Gesamtanzahl der Fahrten + letzte 5 als Attribut |
| `sensor.fahrtenbuch_dienstliche_km` | Summe aller dienstlichen Kilometer |
| `sensor.fahrtenbuch_private_km` | Summe aller privaten Kilometer |
| `sensor.fahrtenbuch_aktuelle_fahrt_start_km` | KM-Stand beim Start der aktiven Fahrt |

---

## Manuelle Installation (ohne HACS)

1. Den Ordner `custom_components/fahrtenbuch/` in dein HA-Konfigurationsverzeichnis kopieren  
   (normalerweise `/config/custom_components/fahrtenbuch/`)
2. Home Assistant neu starten
3. Integration wie oben beschrieben einrichten

---

## Voraussetzungen

- Home Assistant 2024.1 oder neuer
- Ein Auto-Integration mit KM-Stand-Sensor (z. B. Volkswagen, BMW, Tesla, generic OBDII)
- Eine Person- oder Device-Tracker-Entität mit GPS-Standort (z. B. HA Companion App)

---

## Lizenz

MIT License – siehe [LICENSE](LICENSE)
