import ctypes
import os
import threading
from typing import Dict, Any, Optional
from ..config import settings

class GeofenceResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("is_inside_geofence", ctypes.c_int32),
        ("is_overspeeding", ctypes.c_int32),
        ("distance_to_center_km", ctypes.c_double),
        ("speed_delta_kmh", ctypes.c_double),
        ("latency_ns", ctypes.c_uint64),
    ]

class SpatialMetricsC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("total_pings_evaluated", ctypes.c_uint64),
        ("total_breaches_detected", ctypes.c_uint64),
        ("total_overspeeding_alerts", ctypes.c_uint64),
        ("avg_latency_ns", ctypes.c_double),
        ("min_latency_ns", ctypes.c_uint64),
        ("max_latency_ns", ctypes.c_uint64),
    ]

class CppSpatialEngine:
    def __init__(self, lib_path: Optional[str] = None):
        self.lib_path = lib_path or settings.CPP_LIB_PATH
        if not os.path.isabs(self.lib_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.lib_path = os.path.join(base_dir, "cpp", "libgeofence_engine.dylib")

        if not os.path.exists(self.lib_path):
            fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../cpp/libgeofence_engine.dylib"))
            if os.path.exists(fallback):
                self.lib_path = fallback
            else:
                raise FileNotFoundError(f"FleetSync C++ library not found at: {self.lib_path}")

        self._lib = ctypes.CDLL(self.lib_path)
        self._lock = threading.Lock()
        self._setup_bindings()
        self._handle = self._lib.create_geofence_engine()

    def _setup_bindings(self):
        self._lib.create_geofence_engine.restype = ctypes.c_void_p
        self._lib.destroy_geofence_engine.argtypes = [ctypes.c_void_p]
        self._lib.destroy_geofence_engine.restype = None

        self._lib.reset_geofence_engine.argtypes = [ctypes.c_void_p]
        self._lib.reset_geofence_engine.restype = None

        self._lib.haversine_distance_km.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double
        ]
        self._lib.haversine_distance_km.restype = ctypes.c_double

        self._lib.evaluate_vehicle_telemetry.argtypes = [
            ctypes.c_void_p,
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int32
        ]
        self._lib.evaluate_vehicle_telemetry.restype = GeofenceResultC

        self._lib.get_spatial_metrics.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(SpatialMetricsC)
        ]
        self._lib.get_spatial_metrics.restype = None

    def calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return self._lib.haversine_distance_km(
            ctypes.c_double(lat1), ctypes.c_double(lon1),
            ctypes.c_double(lat2), ctypes.c_double(lon2)
        )

    def evaluate_telemetry(
        self,
        v_lat: float,
        v_lon: float,
        speed_kmh: float,
        speed_limit_kmh: float,
        center_lat: float,
        center_lon: float,
        radius_km: float
    ) -> Dict[str, Any]:
        with self._lock:
            res = self._lib.evaluate_vehicle_telemetry(
                self._handle,
                ctypes.c_double(v_lat),
                ctypes.c_double(v_lon),
                ctypes.c_double(speed_kmh),
                ctypes.c_double(speed_limit_kmh),
                ctypes.c_double(center_lat),
                ctypes.c_double(center_lon),
                ctypes.c_double(radius_km),
                None, None, 0
            )

        return {
            "is_inside_geofence": bool(res.is_inside_geofence == 1),
            "is_overspeeding": bool(res.is_overspeeding == 1),
            "distance_to_hub_km": round(res.distance_to_center_km, 2),
            "speed_delta_kmh": round(res.speed_delta_kmh, 1),
            "latency_ns": res.latency_ns
        }

    def get_metrics(self) -> Dict[str, Any]:
        m = SpatialMetricsC()
        with self._lock:
            self._lib.get_spatial_metrics(self._handle, ctypes.byref(m))

        return {
            "total_pings_evaluated": m.total_pings_evaluated,
            "total_breaches_detected": m.total_breaches_detected,
            "total_overspeeding_alerts": m.total_overspeeding_alerts,
            "avg_latency_ns": round(m.avg_latency_ns, 2),
            "min_latency_ns": m.min_latency_ns,
            "max_latency_ns": m.max_latency_ns,
        }

    def reset(self):
        with self._lock:
            self._lib.reset_geofence_engine(self._handle)

cpp_spatial = CppSpatialEngine()
