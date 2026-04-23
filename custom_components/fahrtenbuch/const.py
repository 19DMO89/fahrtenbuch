"""Constants for the Fahrtenbuch integration."""

DOMAIN = "fahrtenbuch"
STORAGE_KEY = "fahrtenbuch_trips"
STORAGE_VERSION = 1

CONF_ODOMETER_ENTITY = "odometer_entity"
CONF_PERSON_ENTITY = "person_entity"

TRIP_TYPE_BUSINESS = "dienstlich"
TRIP_TYPE_PRIVATE = "privat"

SERVICE_START_TRIP = "start_trip"
SERVICE_STOP_TRIP = "stop_trip"
SERVICE_EXPORT_CSV = "export_csv"
SERVICE_DELETE_TRIP = "delete_trip"
SERVICE_UPDATE_TRIP = "update_trip"
