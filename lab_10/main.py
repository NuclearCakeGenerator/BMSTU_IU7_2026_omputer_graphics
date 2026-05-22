import tkinter as tk
from math import cos, inf, isclose, radians, sin
from tkinter import messagebox

from utils import (
    BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_AXIS_COLOR,
    DEFAULT_HORIZON_COLOR,
    DEFAULT_SURFACE_COLOR,
    EPS,
    LEFT_PANEL_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Point2D,
    Point3D,
    project,
    rotate_x,
    rotate_y,
    rotate_z,
)


SURFACE_NAMES = (
    "sin(x) * sin(z)",
    "sin(cos(x)) * sin(z)",
    "cos(x) * z / 3",
    "cos(x) * cos(sin(z))",
)


class Lab10App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lab 10 - Плавающий горизонт")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.surface_color = DEFAULT_SURFACE_COLOR
        self.axis_color = DEFAULT_AXIS_COLOR
        self.horizon_color = DEFAULT_HORIZON_COLOR

        self.surface_var = tk.StringVar(value=SURFACE_NAMES[0])
        self.x_min_var = tk.StringVar(value="-6")
        self.x_max_var = tk.StringVar(value="6")
        self.x_step_var = tk.StringVar(value="0.1")
        self.z_min_var = tk.StringVar(value="-6")
        self.z_max_var = tk.StringVar(value="6")
        self.z_step_var = tk.StringVar(value="0.2")

        self.angle_x_var = tk.StringVar(value="15")
        self.angle_y_var = tk.StringVar(value="25")
        self.angle_z_var = tk.StringVar(value="0")
        self.scale_var = tk.StringVar(value="55")

        self._build_layout()
        self._draw_scene()
        self._update_status(
            "Задайте поверхность, диапазоны x/z, углы и масштаб, "
            "затем нажмите 'Построить'."
        )

    def _build_layout(self):
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(
            self.container,
            width=LEFT_PANEL_WIDTH,
            padx=10,
            pady=10,
            relief="ridge",
            borderwidth=1,
        )
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self.container, padx=10, pady=10)
        self.right_frame.pack(side="left", fill="both", expand=True)

        self._build_surface_section()
        self._build_range_section()
        self._build_transform_section()
        self._build_action_section()

        tk.Label(self.right_frame, text="Статус:").pack(anchor="w")
        self.status_var = tk.StringVar(value="")
        self.status_entry = tk.Entry(
            self.right_frame,
            textvariable=self.status_var,
            state="readonly",
            readonlybackground="#FFFFFF",
        )
        self.status_entry.pack(fill="x", pady=(0, 8))

        self.canvas = tk.Canvas(
            self.right_frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="#555555",
        )
        self.canvas.pack(fill="both", expand=True)

    def _build_surface_section(self):
        frame = tk.LabelFrame(self.left_frame, text="Поверхность", padx=8, pady=8)
        frame.pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Функция").pack(anchor="w")
        self.surface_menu = tk.OptionMenu(
            frame,
            self.surface_var,
            *SURFACE_NAMES,
        )
        self.surface_menu.pack(fill="x", pady=(0, 4))

        tk.Label(
            frame,
            text="Выберите одну из 4 поверхностей из задания.",
            anchor="w",
            wraplength=340,
            justify="left",
        ).pack(fill="x")

    def _build_range_section(self):
        frame = tk.LabelFrame(self.left_frame, text="Диапазоны", padx=8, pady=8)
        frame.pack(fill="x", pady=(0, 10))

        self._build_range_row(frame, "x min", self.x_min_var)
        self._build_range_row(frame, "x max", self.x_max_var)
        self._build_range_row(frame, "x step", self.x_step_var)
        self._build_range_row(frame, "z min", self.z_min_var)
        self._build_range_row(frame, "z max", self.z_max_var)
        self._build_range_row(frame, "z step", self.z_step_var)

    def _build_range_row(self, parent, label, variable):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, width=9, anchor="w").pack(side="left")
        tk.Entry(row, textvariable=variable, width=12, justify="right").pack(
            side="left"
        )

    def _build_transform_section(self):
        frame = tk.LabelFrame(self.left_frame, text="Поворот и масштаб", padx=8, pady=8)
        frame.pack(fill="x", pady=(0, 10))

        self._build_transform_row(frame, "Ox", self.angle_x_var, "°")
        self._build_transform_row(frame, "Oy", self.angle_y_var, "°")
        self._build_transform_row(frame, "Oz", self.angle_z_var, "°")
        self._build_transform_row(frame, "Масштаб", self.scale_var, "")

        tk.Label(
            frame,
            text="Углы задаются в градусах.",
            anchor="w",
            wraplength=340,
            justify="left",
        ).pack(fill="x", pady=(4, 0))

    def _build_transform_row(self, parent, label, variable, suffix):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, width=9, anchor="w").pack(side="left")
        tk.Entry(row, textvariable=variable, width=12, justify="right").pack(
            side="left"
        )
        tk.Label(row, text=suffix, width=3, anchor="w").pack(side="left")

    def _build_action_section(self):
        frame = tk.LabelFrame(self.left_frame, text="Действия", padx=8, pady=8)
        frame.pack(fill="x", pady=(0, 10))

        tk.Button(
            frame,
            text="Построить",
            command=self._draw_scene,
            bg="#FFD8A8",
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            frame,
            text="Сбросить углы",
            command=self._reset_angles,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            frame,
            text="Очистить",
            command=self._clear_canvas,
            cursor="hand2",
        ).pack(fill="x")

    def _update_status(self, text: str):
        self.status_var.set(text)

    def _parse_float(self, value: str, field_name: str) -> float:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Поле {field_name} должно содержать число.") from exc

    def _parse_ranges(self):
        x_min = self._parse_float(self.x_min_var.get(), "x min")
        x_max = self._parse_float(self.x_max_var.get(), "x max")
        x_step = self._parse_float(self.x_step_var.get(), "x step")
        z_min = self._parse_float(self.z_min_var.get(), "z min")
        z_max = self._parse_float(self.z_max_var.get(), "z max")
        z_step = self._parse_float(self.z_step_var.get(), "z step")

        if isclose(x_step, 0.0, abs_tol=EPS) or isclose(z_step, 0.0, abs_tol=EPS):
            raise ValueError("Шаг по x и z должен быть ненулевым.")

        if x_step < 0:
            x_step = -x_step
        if z_step < 0:
            z_step = -z_step

        if x_max < x_min:
            x_min, x_max = x_max, x_min
        if z_max < z_min:
            z_min, z_max = z_max, z_min

        return x_min, x_max, x_step, z_min, z_max, z_step

    def _parse_angles_and_scale(self):
        angle_x = radians(self._parse_float(self.angle_x_var.get(), "Ox"))
        angle_y = radians(self._parse_float(self.angle_y_var.get(), "Oy"))
        angle_z = radians(self._parse_float(self.angle_z_var.get(), "Oz"))
        scale = self._parse_float(self.scale_var.get(), "Масштаб")
        if scale <= 0:
            raise ValueError("Масштаб должен быть положительным.")
        return angle_x, angle_y, angle_z, scale

    def _surface_function(self):
        name = self.surface_var.get()
        if name == SURFACE_NAMES[0]:
            return lambda x, z: sin(x) * sin(z)
        if name == SURFACE_NAMES[1]:
            return lambda x, z: sin(cos(x)) * sin(z)
        if name == SURFACE_NAMES[2]:
            return lambda x, z: cos(x) * z / 3.0
        return lambda x, z: cos(x) * cos(sin(z))

    def _iter_range(self, start: float, stop: float, step: float):
        current = start
        while current <= stop + EPS:
            yield current
            current += step

    def _transform_point(
        self,
        x: float,
        y: float,
        z: float,
        angle_x: float,
        angle_y: float,
        angle_z: float,
    ) -> Point3D:
        point = Point3D(x, y, z)
        point = rotate_x(point, angle_x)
        point = rotate_y(point, angle_y)
        point = rotate_z(point, angle_z)
        return point

    def _point_visible(self, x: float, y: float, top, bottom) -> bool:
        column = int(round(x))
        if column < 0 or column >= CANVAS_WIDTH:
            return False
        return y < top[column] - EPS or y > bottom[column] + EPS

    def _update_horizon(self, x: float, y: float, top, bottom):
        column = int(round(x))
        if column < 0 or column >= CANVAS_WIDTH:
            return
        if y < top[column]:
            top[column] = y
        if y > bottom[column]:
            bottom[column] = y

    def _draw_segment_sampled(self, p1: Point2D, p2: Point2D, top, bottom):
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        steps = max(int(max(abs(dx), abs(dy))), 1)
        prev = p1
        prev_visible = False

        for index in range(1, steps + 1):
            t = index / steps
            current = Point2D(
                p1.x + dx * t,
                p1.y + dy * t,
            )
            mid = Point2D(
                (prev.x + current.x) / 2.0,
                (prev.y + current.y) / 2.0,
            )
            visible = self._point_visible(mid.x, mid.y, top, bottom)
            if visible:
                self._update_horizon(prev.x, prev.y, top, bottom)
                self._update_horizon(current.x, current.y, top, bottom)
                self.canvas.create_line(
                    prev.x,
                    prev.y,
                    current.x,
                    current.y,
                    fill=self.surface_color,
                    width=2,
                )
            prev = current
            prev_visible = visible

        return prev_visible

    def _draw_axes(self, angle_x, angle_y, angle_z, scale):
        axes = [
            (Point3D(0, 0, 0), Point3D(5, 0, 0), self.axis_color),
            (Point3D(0, 0, 0), Point3D(0, 5, 0), self.axis_color),
            (Point3D(0, 0, 0), Point3D(0, 0, 5), self.axis_color),
        ]
        center_x = CANVAS_WIDTH / 2.0
        center_y = CANVAS_HEIGHT / 2.0
        for start, end, color in axes:
            start_t = self._transform_point(
                start.x,
                start.y,
                start.z,
                angle_x,
                angle_y,
                angle_z,
            )
            end_t = self._transform_point(
                end.x,
                end.y,
                end.z,
                angle_x,
                angle_y,
                angle_z,
            )
            start_p = project(start_t, scale, center_x, center_y)
            end_p = project(end_t, scale, center_x, center_y)
            self.canvas.create_line(
                start_p.x,
                start_p.y,
                end_p.x,
                end_p.y,
                fill=color,
                dash=(6, 3),
                width=1,
            )

    def _draw_scene(self):
        try:
            x_min, x_max, x_step, z_min, z_max, z_step = self._parse_ranges()
            angle_x, angle_y, angle_z, scale = self._parse_angles_and_scale()
        except ValueError as exc:
            messagebox.showwarning("Неверные параметры", str(exc))
            return

        surface_func = self._surface_function()
        self.canvas.delete("all")

        top_horizon = [inf] * CANVAS_WIDTH
        bottom_horizon = [-inf] * CANVAS_WIDTH

        center_x = CANVAS_WIDTH / 2.0
        center_y = CANVAS_HEIGHT / 2.0

        slices = []
        for z in self._iter_range(z_min, z_max, z_step):
            projected_points = []
            depth_sum = 0.0
            count = 0
            for x in self._iter_range(x_min, x_max, x_step):
                y = surface_func(x, z)
                transformed = self._transform_point(
                    x,
                    y,
                    z,
                    angle_x,
                    angle_y,
                    angle_z,
                )
                projected = project(transformed, scale, center_x, center_y)
                projected_points.append(projected)
                depth_sum += transformed.z
                count += 1
            if projected_points:
                slices.append((depth_sum / count, projected_points))

        slices.sort(key=lambda item: item[0], reverse=True)

        for _, projected_points in slices:
            for index in range(len(projected_points) - 1):
                self._draw_segment_sampled(
                    projected_points[index],
                    projected_points[index + 1],
                    top_horizon,
                    bottom_horizon,
                )

        self._draw_axes(angle_x, angle_y, angle_z, scale)
        self._update_status(
            f"Построено: {self.surface_var.get()}, "
            f"x=[{x_min}, {x_max}], z=[{z_min}, {z_max}]."
        )

    def _reset_angles(self):
        self.angle_x_var.set("0")
        self.angle_y_var.set("0")
        self.angle_z_var.set("0")
        self._draw_scene()

    def _clear_canvas(self):
        self.canvas.delete("all")
        self._update_status("Холст очищен.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab10App(root)
    root.mainloop()
