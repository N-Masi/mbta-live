import requests

# to filter by direction, use 'direction_id'
_BUS_DIRECTIONS = {

    83: {
        0: {
            "destination": "Rindge Avenue",
            "destination_short": "Porter",
            "name": "Outbound",
            "name_short": "OUT",
            "stop_id": 2453,
            "stop_name": "45 Beacon St",
        },
        1: {
            "destination": "Central Square, Cambridge",
            "destination_short": "Central",
            "name": "Inbound",
            "name_short": "IN",
            "stop_id": 2437,
            "stop_name": "Beacon St @ Cooney St",
        }
    },

    109: {
        0: {
            "destination": "Harvard Square",
            "destination_short": "Harvard",
            "name": "Outbound",
            "name_short": "OUT", 
        },
    },

}

_BASE_URL = "https://api-v3.mbta.com/"
