from dataclasses import dataclass
from math import cos, sin


WINDOW_WIDTH = 1460
WINDOW_HEIGHT = 940
LEFT_PANEL_WIDTH = 430
CANVAS_WIDTH = 960
CANVAS_HEIGHT = 880

BACKGROUND_COLOR = "#101317"
DEFAULT_SURFACE_COLOR = "#93C5FD"
DEFAULT_AXIS_COLOR = "#F8FAFC"
DEFAULT_HORIZON_COLOR = "#F59E0B"

EPS = 1e-9


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


def rotate_x(point: Point3D, angle: float) -> Point3D:
    cosine = cos(angle)
    sine = sin(angle)
    y = point.y * cosine - point.z * sine
    z = point.y * sine + point.z * cosine
    return Point3D(point.x, y, z)


def rotate_y(point: Point3D, angle: float) -> Point3D:
    cosine = cos(angle)
    sine = sin(angle)
    x = point.x * cosine + point.z * sine
    z = -point.x * sine + point.z * cosine
    return Point3D(x, point.y, z)


def rotate_z(point: Point3D, angle: float) -> Point3D:
    cosine = cos(angle)
    sine = sin(angle)
    x = point.x * cosine - point.y * sine
    y = point.x * sine + point.y * cosine
    return Point3D(x, y, point.z)


def project(point: Point3D, scale: float, center_x: float, center_y: float) -> Point2D:
    return Point2D(
        center_x + point.x * scale,
        center_y - point.y * scale,
    )
