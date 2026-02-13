"""
GPS Handler Module
Manejo de GPS, cálculo de pendientes y estadísticas de ruta
"""

from plyer import gps
from datetime import datetime
import math
import json
from typing import List, Dict, Tuple, Optional
import os


class GPSPoint:
    """Representa un punto de GPS con coordenadas y altitud"""
    
    def __init__(self, lat: float, lon: float, altitude: float, timestamp: float):
        self.lat = lat
        self.lon = lon
        self.altitude = altitude
        self.timestamp = timestamp
    
    def to_dict(self) -> dict:
        return {
            'lat': self.lat,
            'lon': self.lon,
            'altitude': self.altitude,
            'timestamp': self.timestamp
        }


class GPSHandler:
    """Manejador de GPS y cálculo de pendientes"""
    
    EARTH_RADIUS = 6371000  # metros
    
    def __init__(self):
        self.route_points: List[GPSPoint] = []
        self.tracking = False
        self.current_position = None
        self.last_update_time = None
    
    def start_tracking(self):
        """Inicia el rastreo GPS"""
        self.tracking = True
        self.route_points = []
        try:
            gps.configure(on_location=self._on_gps_location)
            gps.start()
        except Exception as e:
            print(f"Error al iniciar GPS: {e}")
    
    def stop_tracking(self):
        """Detiene el rastreo GPS"""
        self.tracking = False
        try:
            gps.stop()
        except Exception as e:
            print(f"Error al detener GPS: {e}")
    
    def _on_gps_location(self, **kwargs):
        """Callback cuando se recibe actualización de GPS"""
        if not self.tracking:
            return
        
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        altitude = kwargs.get('altitude', 0)
        
        if lat is not None and lon is not None:
            point = GPSPoint(lat, lon, altitude, datetime.now().timestamp())
            self.route_points.append(point)
            self.current_position = point
    
    def calculate_slope(self, point1: GPSPoint, point2: GPSPoint) -> float:
        """
        Calcula la pendiente entre dos puntos GPS
        Retorna el porcentaje de pendiente
        """
        # Distancia horizontal (haversine)
        horizontal_distance = self._haversine_distance(
            point1.lat, point1.lon, point2.lat, point2.lon
        )
        
        if horizontal_distance == 0:
            return 0
        
        # Diferencia de altitud
        vertical_distance = point2.altitude - point1.altitude
        
        # Pendiente en porcentaje
        slope_percent = (vertical_distance / horizontal_distance) * 100
        
        return slope_percent
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calcula distancia entre dos puntos usando fórmula haversine
        Retorna distancia en metros
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS * c
    
    def get_current_data(self) -> Optional[Dict]:
        """Retorna datos actuales de la ruta"""
        if not self.route_points or len(self.route_points) < 2:
            return None
        
        last_point = self.route_points[-1]
        prev_point = self.route_points[-2]
        
        # Pendiente actual
        slope = self.calculate_slope(prev_point, last_point)
        
        # Distancia total
        total_distance = self._calculate_total_distance()
        
        # Velocidad (si hay cambio de tiempo)
        speed = 0
        if last_point.timestamp != prev_point.timestamp:
            horizontal_dist = self._haversine_distance(
                prev_point.lat, prev_point.lon,
                last_point.lat, last_point.lon
            )
            time_diff = last_point.timestamp - prev_point.timestamp
            speed = (horizontal_dist / time_diff) * 3.6  # a km/h
        
        return {
            'slope': slope,
            'speed': speed,
            'altitude': last_point.altitude,
            'distance': total_distance / 1000,  # a km
            'lat': last_point.lat,
            'lon': last_point.lon
        }
    
    def _calculate_total_distance(self) -> float:
        """Calcula la distancia total recorrida"""
        if len(self.route_points) < 2:
            return 0
        
        total = 0
        for i in range(1, len(self.route_points)):
            dist = self._haversine_distance(
                self.route_points[i-1].lat,
                self.route_points[i-1].lon,
                self.route_points[i].lat,
                self.route_points[i].lon
            )
            total += dist
        
        return total
    
    def get_route_statistics(self) -> Dict:
        """Calcula estadísticas de la ruta completa"""
        if not self.route_points:
            return {}
        
        distances = []
        slopes = []
        elevations = [p.altitude for p in self.route_points]
        
        for i in range(1, len(self.route_points)):
            dist = self._haversine_distance(
                self.route_points[i-1].lat,
                self.route_points[i-1].lon,
                self.route_points[i].lat,
                self.route_points[i].lon
            )
            distances.append(dist)
            slope = self.calculate_slope(
                self.route_points[i-1],
                self.route_points[i]
            )
            slopes.append(slope)
        
        total_distance = sum(distances) / 1000  # km
        total_elevation_gain = sum(max(0, e2-e1) 
                                   for e1, e2 in zip(elevations[:-1], elevations[1:]))
        avg_slope = sum(slopes) / len(slopes) if slopes else 0
        max_slope = max(slopes) if slopes else 0
        min_slope = min(slopes) if slopes else 0
        
        return {
            'total_distance_km': round(total_distance, 2),
            'total_elevation_gain_m': round(total_elevation_gain, 0),
            'average_slope_percent': round(avg_slope, 2),
            'max_slope_percent': round(max_slope, 2),
            'min_slope_percent': round(min_slope, 2),
            'total_points': len(self.route_points)
        }
    
    def export_to_gpx(self) -> str:
        """
        Exporta la ruta a formato GPX
        Retorna el nombre del archivo creado
        """
        if not self.route_points:
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ruta_mtb_{timestamp}.gpx'
        
        gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="MTB Slope Tracker">\n  <trk>\n    <name>Ruta MTB {}<\/name>\n    <trkseg>\n'''.format(timestamp)
        
        for point in self.route_points:
            gpx_content += f'''      <trkpt lat="{point.lat}" lon="{point.lon}">\n        <ele>{point.altitude}</ele>\n        <time>{{datetime.fromtimestamp(point.timestamp).isoformat()}}</time>\n      <\/trkpt>\n'''
        
        gpx_content += '''    </trkseg>\n  <\/trk>\n</gpx>'''\n        
        # Guardar en almacenamiento externo\n        try:\n            if os.path.exists('/storage/emulated/0/Documents'):\n                filepath = f'/storage/emulated/0/Documents/{filename}'\n            else:\n                filepath = os.path.expanduser(f'~/{filename}')\n            \n            with open(filepath, 'w') as f:\n                f.write(gpx_content)\n            \n            return filename\n        except Exception as e:\n            print(f"Error al exportar GPX: {e}")\n            return ""\n    
    def export_to_json(self) -> str:\n        """Exporta la ruta a JSON"""\n        if not self.route_points:\n            return ""\n        \n        data = {\n            'timestamp': datetime.now().isoformat(),\n            'statistics': self.get_route_statistics(),\n            'points': [p.to_dict() for p in self.route_points]\n        }\n        \n        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n        filename = f'ruta_mtb_{timestamp}.json'\n        \n        try:\n            if os.path.exists('/storage/emulated/0/Documents'):\n                filepath = f'/storage/emulated/0/Documents/{filename}'\n            else:\n                filepath = os.path.expanduser(f'~/{filename}')\n            \n            with open(filepath, 'w') as f:\n                json.dump(data, f, indent=2)\n            \n            return filename\n        except Exception as e:\n            print(f"Error al exportar JSON: {e}")\n            return ""