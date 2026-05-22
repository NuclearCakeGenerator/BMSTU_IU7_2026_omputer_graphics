import tkinter as tk
from enum import Enum, auto
from math import isclose
from tkinter import colorchooser, messagebox

from utils import (
    BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_CLIPPER_COLOR,
    DEFAULT_RESULT_COLOR,
    DEFAULT_SUBJECT_COLOR,
    EPS,
    LEFT_PANEL_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Point,
    vec_sub,
    dot,
    cross,
)


class MouseMode(Enum):
    NONE = auto()
    SUBJECT = auto()
    CLIPPER = auto()


class Lab09App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lab 09 - Отсечение многоугольника методом Сазерленда-Ходжмена")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.clipper_color = DEFAULT_CLIPPER_COLOR
        self.subject_color = DEFAULT_SUBJECT_COLOR
        self.result_color = DEFAULT_RESULT_COLOR

        self.clipper_vertices: list[Point] = []
        self.clipper_closed = False
        self.subject_vertices: list[Point] = []
        self.subject_closed = False
        self.result_vertices: list[Point] = []

        self.mouse_mode = MouseMode.NONE
        self.preview_point: Point | None = None

        self.vertex_vars = [
            tk.StringVar(value="200"),
            tk.StringVar(value="180"),
        ]
        self.subject_vars = [
            tk.StringVar(value="120"),
            tk.StringVar(value="120"),
        ]

        self._build_layout()
        self._bind_events()
        self._redraw_all()
        self._update_status(
            "Задайте отсекатель и субъектный многоугольник "
            "(мышью или координатами), затем нажмите 'Отсечь'."
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

        self._build_color_section()
        self._build_clipper_section()
        self._build_subject_section()
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
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True)

    def _build_color_section(self):
        color_frame = tk.LabelFrame(self.left_frame, text="Цвета", padx=8, pady=8)
        color_frame.pack(fill="x", pady=(0, 10))

        self._build_color_picker(
            color_frame,
            "Отсекатель",
            self.clipper_color,
            self._choose_clipper_color,
        )
        self._build_color_picker(
            color_frame,
            "Субъект",
            self.subject_color,
            self._choose_subject_color,
        )
        self._build_color_picker(
            color_frame,
            "Результат",
            self.result_color,
            self._choose_result_color,
        )

    def _build_color_picker(self, parent, label, color, command):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, width=12, anchor="w").pack(side="left")
        preview = tk.Label(row, text="      ", bg=color, relief="sunken", borderwidth=1)
        preview.pack(side="left")
        tk.Button(
            row,
            text="Выбрать",
            command=command,
            cursor="hand2",
        ).pack(side="left", padx=8)
        if label == "Отсекатель":
            self.clipper_color_preview = preview
        elif label == "Субъект":
            self.subject_color_preview = preview
        else:
            self.result_color_preview = preview

    def _build_clipper_section(self):
        clipper_frame = tk.LabelFrame(
            self.left_frame,
            text="Отсекатель",
            padx=8,
            pady=8,
        )
        clipper_frame.pack(fill="x", pady=(0, 10))

        grid = tk.Frame(clipper_frame)
        grid.pack(fill="x")
        tk.Label(grid, text="x").grid(row=0, column=0, padx=4, sticky="w")
        tk.Label(grid, text="y").grid(row=0, column=1, padx=4, sticky="w")
        tk.Entry(
            grid,
            textvariable=self.vertex_vars[0],
            width=10,
            justify="right",
        ).grid(row=1, column=0, padx=4, pady=(2, 0))
        tk.Entry(
            grid,
            textvariable=self.vertex_vars[1],
            width=10,
            justify="right",
        ).grid(row=1, column=1, padx=4, pady=(2, 0))

        tk.Button(
            clipper_frame,
            text="Добавить вершину",
            command=self._add_clipper_vertex_from_entries,
            cursor="hand2",
        ).pack(fill="x", pady=(8, 4))
        tk.Button(
            clipper_frame,
            text="Замкнуть отсекатель",
            command=self._close_clipper,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            clipper_frame,
            text="Ввод мышью",
            command=self._start_clipper_mouse_mode,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            clipper_frame,
            text="Очистить отсекатель",
            command=self._clear_clipper,
            cursor="hand2",
        ).pack(fill="x")

        tk.Label(
            clipper_frame,
            text=(
                "Мышь: левый клик добавляет вершину, правый клик "
                "замыкает."
            ),
            anchor="w",
            wraplength=340,
            justify="left",
        ).pack(fill="x", pady=(6, 0))
        self.clipper_info_var = tk.StringVar(value="Вершин: 0")
        tk.Label(
            clipper_frame,
            textvariable=self.clipper_info_var,
            anchor="w",
            fg="#0B5",
        ).pack(fill="x", pady=(6, 0))

    def _build_subject_section(self):
        subject_frame = tk.LabelFrame(
            self.left_frame,
            text="Субъектный многоугольник",
            padx=8,
            pady=8,
        )
        subject_frame.pack(fill="x", pady=(0, 10))

        grid = tk.Frame(subject_frame)
        grid.pack(fill="x")
        tk.Label(grid, text="x").grid(row=0, column=0, padx=4, sticky="w")
        tk.Label(grid, text="y").grid(row=0, column=1, padx=4, sticky="w")
        tk.Entry(
            grid,
            textvariable=self.subject_vars[0],
            width=10,
            justify="right",
        ).grid(row=1, column=0, padx=4, pady=(2, 0))
        tk.Entry(
            grid,
            textvariable=self.subject_vars[1],
            width=10,
            justify="right",
        ).grid(row=1, column=1, padx=4, pady=(2, 0))

        tk.Button(
            subject_frame,
            text="Добавить вершину",
            command=self._add_subject_vertex_from_entries,
            cursor="hand2",
        ).pack(fill="x", pady=(8, 4))
        tk.Button(
            subject_frame,
            text="Ввод мышью",
            command=self._start_subject_mouse_mode,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            subject_frame,
            text="Замкнуть субъект",
            command=self._close_subject,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            subject_frame,
            text="Очистить субъект",
            command=self._clear_subject,
            cursor="hand2",
        ).pack(fill="x")

        tk.Label(
            subject_frame,
            text=(
                "Мышь: левый клик добавляет вершину, правый клик "
                "замыкает."
            ),
            anchor="w",
            wraplength=340,
            justify="left",
        ).pack(fill="x", pady=(6, 0))
        self.subject_info_var = tk.StringVar(value="Вершин: 0")
        tk.Label(
            subject_frame,
            textvariable=self.subject_info_var,
            anchor="w",
            fg="#0B5",
        ).pack(fill="x", pady=(6, 0))

    def _build_action_section(self):
        action_frame = tk.LabelFrame(self.left_frame, text="Действия", padx=8, pady=8)
        action_frame.pack(fill="x", pady=(0, 10))

        tk.Button(
            action_frame,
            text="Отсечь",
            command=self._clip_subject,
            bg="#FFD8A8",
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            action_frame,
            text="Очистить результат",
            command=self._clear_result,
            cursor="hand2",
        ).pack(fill="x", pady=(0, 4))
        tk.Button(
            action_frame,
            text="Очистить всё",
            command=self._clear_all,
            bg="#FFCCCC",
            cursor="hand2",
        ).pack(fill="x")

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Motion>", self._on_canvas_mouse_move)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

    def _update_status(self, text: str):
        self.status_var.set(text)

    def _update_clipper_info(self):
        closed_text = "замкнут" if self.clipper_closed else "не замкнут"
        self.clipper_info_var.set(
            f"Вершин: {len(self.clipper_vertices)}, {closed_text}."
        )

    def _update_subject_info(self):
        closed_text = "замкнут" if self.subject_closed else "не замкнут"
        self.subject_info_var.set(
            f"Вершин: {len(self.subject_vertices)}, {closed_text}."
        )

    def _choose_clipper_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет отсекателя",
            color=self.clipper_color,
        )[1]
        if color is None:
            return
        self.clipper_color = color.upper()
        self.clipper_color_preview.config(bg=self.clipper_color)
        self._redraw_all()

    def _choose_subject_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет субъекта",
            color=self.subject_color,
        )[1]
        if color is None:
            return
        self.subject_color = color.upper()
        self.subject_color_preview.config(bg=self.subject_color)
        self._redraw_all()

    def _choose_result_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет результата",
            color=self.result_color,
        )[1]
        if color is None:
            return
        self.result_color = color.upper()
        self.result_color_preview.config(bg=self.result_color)
        self._redraw_all()

    def _parse_float(self, value: str, field_name: str) -> float:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Поле {field_name} должно содержать число.") from exc

    def _point_from_event(self, event: tk.Event) -> Point | None:
        if not (0 <= event.x < CANVAS_WIDTH and 0 <= event.y < CANVAS_HEIGHT):
            return None
        return Point(float(event.x), float(event.y))

    def _add_clipper_vertex_from_entries(self):
        try:
            x = self._parse_float(self.vertex_vars[0].get(), "x")
            y = self._parse_float(self.vertex_vars[1].get(), "y")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return
        self._add_clipper_vertex(Point(x, y))

    def _add_clipper_vertex(self, p: Point):
        if self.clipper_closed:
            self.clipper_vertices.clear()
            self.clipper_closed = False
        if self.clipper_vertices:
            prev = self.clipper_vertices[-1]
            if isclose(prev.x, p.x, abs_tol=EPS) and isclose(prev.y, p.y, abs_tol=EPS):
                self._update_status("Вершина совпадает с предыдущей и была пропущена.")
                return
        self.clipper_vertices.append(p)
        self._clear_result()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status(f"Добавлена вершина отсекателя: ({p.x:.0f}, {p.y:.0f}).")

    def _add_subject_vertex_from_entries(self):
        try:
            x = self._parse_float(self.subject_vars[0].get(), "x")
            y = self._parse_float(self.subject_vars[1].get(), "y")
        except ValueError as exc:
            messagebox.showwarning("Неверные координаты", str(exc))
            return
        self._add_subject_vertex(Point(x, y))

    def _add_subject_vertex(self, p: Point):
        if self.subject_closed:
            self.subject_vertices.clear()
            self.subject_closed = False
        if self.subject_vertices:
            prev = self.subject_vertices[-1]
            if isclose(prev.x, p.x, abs_tol=EPS) and isclose(prev.y, p.y, abs_tol=EPS):
                self._update_status("Вершина совпадает с предыдущей и была пропущена.")
                return
        self.subject_vertices.append(p)
        self._clear_result()
        self._update_subject_info()
        self._redraw_all()
        self._update_status(f"Добавлена вершина субъекта: ({p.x:.0f}, {p.y:.0f}).")

    def _polygon_orientation(self, vertices: list[Point]) -> float:
        area2 = 0.0
        for i in range(len(vertices)):
            a = vertices[i]
            b = vertices[(i + 1) % len(vertices)]
            area2 += a.x * b.y - b.x * a.y
        return area2

    def _is_convex_polygon(self, vertices: list[Point]) -> bool:
        n = len(vertices)
        if n < 3:
            return False
        sign = 0
        for i in range(n):
            a = vertices[i]
            b = vertices[(i + 1) % n]
            c = vertices[(i + 2) % n]
            ab = vec_sub(b, a)
            bc = vec_sub(c, b)
            z = cross(ab, bc)
            if abs(z) < EPS:
                continue
            current_sign = 1 if z > 0 else -1
            if sign == 0:
                sign = current_sign
            elif sign != current_sign:
                return False
        return sign != 0

    def _close_clipper(self):
        if len(self.clipper_vertices) < 3:
            messagebox.showwarning(
                "Некорректный отсекатель",
                "Для замыкания нужно минимум 3 вершины.",
            )
            return
        if not self._is_convex_polygon(self.clipper_vertices):
            messagebox.showwarning(
                "Некорректный отсекатель",
                "Отсекатель должен быть выпуклым и без вырожденных сторон.",
            )
            return
        self.clipper_closed = True
        self._clear_result()
        self._clear_mouse_state()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status(
            f"Отсекатель замкнут. Вершин: {len(self.clipper_vertices)}."
        )

    def _close_subject(self):
        if len(self.subject_vertices) < 3:
            messagebox.showwarning(
                "Некорректный субъект",
                "Для замыкания нужно минимум 3 вершины.",
            )
            return
        self.subject_closed = True
        self._clear_result()
        self._clear_mouse_state()
        self._update_subject_info()
        self._redraw_all()
        self._update_status(f"Субъект замкнут. Вершин: {len(self.subject_vertices)}.")

    def _start_clipper_mouse_mode(self):
        self.mouse_mode = MouseMode.CLIPPER
        self.preview_point = None
        self._redraw_all()
        self._update_status(
            "Режим отсекателя: левый клик добавляет вершину, "
            "правый - замыкает."
        )

    def _start_subject_mouse_mode(self):
        self.mouse_mode = MouseMode.SUBJECT
        self.preview_point = None
        self._redraw_all()
        self._update_status(
            "Режим субъекта: левый клик добавляет вершину, "
            "правый - замыкает."
        )

    def _clear_mouse_state(self):
        self.mouse_mode = MouseMode.NONE
        self.preview_point = None

    def _on_canvas_left_click(self, event: tk.Event):
        point = self._point_from_event(event)
        if point is None:
            return
        if self.mouse_mode is MouseMode.CLIPPER:
            self._add_clipper_vertex(point)
            return
        if self.mouse_mode is MouseMode.SUBJECT:
            self._add_subject_vertex(point)
            return

    def _on_canvas_mouse_move(self, event: tk.Event):
        point = self._point_from_event(event)
        if point is None:
            return
        if self.mouse_mode in (MouseMode.CLIPPER, MouseMode.SUBJECT):
            self.preview_point = point
            self._redraw_all()

    def _on_canvas_right_click(self, event: tk.Event):
        if self.mouse_mode is MouseMode.CLIPPER:
            self._close_clipper()
            return
        if self.mouse_mode is MouseMode.SUBJECT:
            self._close_subject()
            return
        self._clear_mouse_state()
        self._redraw_all()
        self._update_status("Режим мыши отменен.")

    def _clip_polygon_sutherland_hodgman(
        self,
        subject: list[Point],
        clipper: list[Point],
    ) -> list[Point]:
        if not subject or not clipper:
            return []
        output = subject[:]
        orientation = self._polygon_orientation(clipper)
        ccw = orientation > 0

        for i in range(len(clipper)):
            input_list = output[:]
            output = []
            if not input_list:
                break
            p_i = clipper[i]
            p_j = clipper[(i + 1) % len(clipper)]
            edge = vec_sub(p_j, p_i)
            if ccw:
                normal = Point(edge.y, -edge.x)
            else:
                normal = Point(-edge.y, edge.x)

            def inside(pt: Point) -> bool:
                return dot(vec_sub(pt, p_i), normal) <= EPS

            def compute_intersection(s: Point, e: Point) -> Point:
                d = vec_sub(e, s)
                w = vec_sub(s, p_i)
                denom = dot(d, normal)
                if abs(denom) < EPS:
                    return s
                t = -dot(w, normal) / denom
                return Point(s.x + d.x * t, s.y + d.y * t)

            s = input_list[-1]
            for e in input_list:
                s_in = inside(s)
                e_in = inside(e)
                if s_in and e_in:
                    output.append(e)
                elif s_in and not e_in:
                    inter = compute_intersection(s, e)
                    output.append(inter)
                elif not s_in and e_in:
                    inter = compute_intersection(s, e)
                    output.append(inter)
                    output.append(e)
                s = e
        return output

    def _clip_subject(self):
        if not self.clipper_closed:
            messagebox.showwarning(
                "Невозможно отсечь",
                "Сначала задайте и замкните выпуклый отсекатель.",
            )
            return
        if not self.subject_closed:
            messagebox.showwarning(
                "Невозможно отсечь",
                "Сначала задайте и замкните субъектный многоугольник.",
            )
            return
        self.result_vertices = (
            self._clip_polygon_sutherland_hodgman(
                self.subject_vertices,
                self.clipper_vertices,
            )
        )
        self._redraw_all()
        self._update_status(
            f"Отсечение выполнено. Результат вершин: {len(self.result_vertices)}."
        )

    def _draw_polygon(
        self,
        vertices: list[Point],
        outline_color: str,
        fill: str = "",
        width: int = 2,
    ):
        if not vertices:
            return
        points = []
        for v in vertices:
            points.extend((v.x, v.y))
        if len(vertices) == 1:
            v = vertices[0]
            self.canvas.create_oval(
                v.x - 2,
                v.y - 2,
                v.x + 2,
                v.y + 2,
                fill=outline_color,
            )
            return
        if fill:
            self.canvas.create_polygon(
                points,
                outline=outline_color,
                fill=fill,
                width=width,
            )
        else:
            self.canvas.create_polygon(
                points,
                outline=outline_color,
                fill="",
                width=width,
            )

    def _redraw_all(self):
        self.canvas.delete("all")
        self._draw_polygon(self.subject_vertices, self.subject_color)
        self._draw_polygon(self.clipper_vertices, self.clipper_color)
        if self.result_vertices:
            self._draw_polygon(self.result_vertices, self.result_color, fill="")
        for idx, v in enumerate(self.clipper_vertices, start=1):
            self.canvas.create_oval(
                v.x - 3,
                v.y - 3,
                v.x + 3,
                v.y + 3,
                fill=self.clipper_color,
            )
            self.canvas.create_text(
                v.x + 10,
                v.y - 10,
                text=str(idx),
                fill=self.clipper_color,
            )
        for idx, v in enumerate(self.subject_vertices, start=1):
            self.canvas.create_oval(
                v.x - 3,
                v.y - 3,
                v.x + 3,
                v.y + 3,
                fill=self.subject_color,
            )
            self.canvas.create_text(
                v.x + 10,
                v.y - 10,
                text=str(idx),
                fill=self.subject_color,
            )
        if self.preview_point is not None:
            last = None
            if self.mouse_mode is MouseMode.CLIPPER and self.clipper_vertices:
                last = self.clipper_vertices[-1]
            if self.mouse_mode is MouseMode.SUBJECT and self.subject_vertices:
                last = self.subject_vertices[-1]
            if last is not None:
                self.canvas.create_line(
                    last.x,
                    last.y,
                    self.preview_point.x,
                    self.preview_point.y,
                    fill="#7DD3FC",
                    width=2,
                    dash=(6, 3),
                )

    def _clear_result(self):
        self.result_vertices.clear()
        self._redraw_all()

    def _clear_clipper(self):
        self.clipper_vertices.clear()
        self.clipper_closed = False
        self._clear_result()
        self._clear_mouse_state()
        self._update_clipper_info()
        self._redraw_all()
        self._update_status("Отсекатель очищен.")

    def _clear_subject(self):
        self.subject_vertices.clear()
        self.subject_closed = False
        self._clear_result()
        self._clear_mouse_state()
        self._update_subject_info()
        self._redraw_all()
        self._update_status("Субъект очищен.")

    def _clear_all(self):
        self.clipper_vertices.clear()
        self.clipper_closed = False
        self.subject_vertices.clear()
        self.subject_closed = False
        self.result_vertices.clear()
        self._clear_mouse_state()
        self._update_clipper_info()
        self._update_subject_info()
        self._redraw_all()
        self._update_status("Холст очищен.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab09App(root)
    root.mainloop()
