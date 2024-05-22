import sys
import tkinter
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .map_widget import TkinterMapView

from .utility_functions import decimal_to_osm, osm_to_decimal


class CanvasRectMarker:
    def __init__(self,
                 map_widget: "TkinterMapView",
                 position: tuple,
                 text: str = None,
                 text_color: str = "#652A22",
                 text_bg_color: str = "#F0F0F0",
                 font: str = "Arial 10 bold",
                 radius: int = 10,
                 color: str = "#000000",
                 fill_color: str = "#C5542D",
                 width: int = 2,
                 command: Callable = None,
                 icon: tkinter.PhotoImage = None,
                 icon_anchor: str = "center",
                 image_zoom_visibility: tuple = (0, float("inf")),
                 data: any = None):

        self.map_widget = map_widget
        self.position = position
        self.radius = radius
        self.fill_color = fill_color
        self.color = color
        self.width = width
        self.text_color = text_color
        self.font = font
        self.text_bg_color = text_bg_color
        self.text = text
        self.icon = icon
        self.icon_anchor = icon_anchor  # can be center, n, nw, w, sw, s, ew, e, ne
        self.image_hidden = False
        self.image_zoom_visibility = image_zoom_visibility
        self.deleted = False
        self.command = command
        self.data = data

        self.circle = None
        self.canvas_text = None
        self.canvas_image = None
        self.canvas_icon = None
        self.text_background = None

    def delete(self):
        if self in self.map_widget.canvas_marker_list:
            self.map_widget.canvas_marker_list.remove(self)

        self.map_widget.canvas.delete(self.circle)
        self.map_widget.canvas.delete(self.canvas_text)
        self.map_widget.canvas.delete(self.canvas_icon)
        self.map_widget.canvas.delete(self.canvas_image)

        self.circle, self.canvas_text, self.canvas_image, self.canvas_icon = None, None, None, None
        self.deleted = True
        self.map_widget.canvas.update()

    def set_position(self, deg_x, deg_y):
        self.position = (deg_x, deg_y)
        self.draw()

    def set_text(self, text):
        self.text = text
        self.draw()

    def change_icon(self, new_icon: tkinter.PhotoImage):
        if self.icon is None:
            raise AttributeError("CanvasPositionMarker: marker needs icon image in constructor to change icon image later")
        else:
            self.icon = new_icon
            self.map_widget.canvas.itemconfigure(self.canvas_icon, image=self.icon)

    def mouse_enter(self, event=None):
        if sys.platform == "darwin":
            self.map_widget.canvas.config(cursor="pointinghand")
        elif sys.platform.startswith("win"):
            self.map_widget.canvas.config(cursor="hand2")
        else:
            self.map_widget.canvas.config(cursor="hand2")  # not tested what it looks like on Linux!
        if self.text is not None:
            canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)
            offset = self.radius + 10
            self.canvas_text = self.map_widget.canvas.create_text(canvas_pos_x + offset, canvas_pos_y + offset, font=self.font,
                                                                  text=self.text, fill=self.text_color, tag="marker")
            text_size = self.map_widget.canvas.bbox(self.canvas_text)
            #move by half the text size to center the text
            self.map_widget.canvas.coords(self.canvas_text, canvas_pos_x + offset + (text_size[2] - text_size[0]) / 2,
                                       canvas_pos_y + offset + (text_size[3] - text_size[1]) / 2)
            text_size = self.map_widget.canvas.bbox(self.canvas_text)
            self.text_background = self.map_widget.canvas.create_rectangle(text_size[0] - 5, text_size[1] - 5,
                                                                           text_size[2] + 5, text_size[3] + 5,
                                                                           fill=self.text_bg_color, outline="black", tag="marker")
            self.map_widget.canvas.lift(self.canvas_text)

    def mouse_leave(self, event=None):
        self.map_widget.canvas.config(cursor="arrow")
        if self.canvas_text is not None:
            self.map_widget.canvas.delete(self.canvas_text)
            self.map_widget.canvas.delete(self.text_background)

    def click(self, event=None):
        if self.command is not None:
            self.command(event)

    def get_canvas_pos(self, position):
        tile_position = decimal_to_osm(*position, round(self.map_widget.zoom))
        widget_tile_width = self.map_widget.lower_right_tile_pos[0] - self.map_widget.upper_left_tile_pos[0]
        widget_tile_height = self.map_widget.lower_right_tile_pos[1] - self.map_widget.upper_left_tile_pos[1]
        canvas_pos_x = ((tile_position[0] - self.map_widget.upper_left_tile_pos[0]) / widget_tile_width) * self.map_widget.width
        canvas_pos_y = ((tile_position[1] - self.map_widget.upper_left_tile_pos[1]) / widget_tile_height) * self.map_widget.height

        return canvas_pos_x, canvas_pos_y

    def draw(self, event=None):
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)

        if not self.deleted:
            if 0 - 50 < canvas_pos_x < self.map_widget.width + 50 and 0 < canvas_pos_y < self.map_widget.height + 70:

                # draw icon image for marker
                if self.icon is not None:
                    if self.canvas_icon is None:
                        self.canvas_icon = self.map_widget.canvas.create_image(canvas_pos_x, canvas_pos_y,
                                                                               anchor=self.icon_anchor,
                                                                               image=self.icon,
                                                                               tag="marker")
                        if self.text is not None:
                            self.map_widget.canvas.tag_bind(self.canvas_icon, "<Enter>", self.mouse_enter)
                            self.map_widget.canvas.tag_bind(self.canvas_icon, "<Leave>", self.mouse_leave)
                        if self.command is not None:
                            self.map_widget.canvas.tag_bind(self.canvas_icon, "<Button-1>", self.click)
                    else:
                        self.map_widget.canvas.coords(self.canvas_icon, canvas_pos_x, canvas_pos_y)

                # draw standard icon shape
                else:
                    x0, y0 = canvas_pos_x - self.radius, canvas_pos_y - self.radius
                    x1, y1 = canvas_pos_x + self.radius, canvas_pos_y + self.radius
                    if self.circle is None:
                        self.circle = self.map_widget.canvas.create_rectangle(x0, y0, x1, y1,
                                                                            fill=self.fill_color, width=self.width, outline=self.color, tag="marker")
                        if self.text is not None:
                            self.map_widget.canvas.tag_bind(self.circle, "<Enter>", self.mouse_enter)
                            self.map_widget.canvas.tag_bind(self.circle, "<Leave>", self.mouse_leave)
                        if self.command is not None:
                            self.map_widget.canvas.tag_bind(self.circle, "<Button-1>", self.click)
                    else:
                        self.map_widget.canvas.coords(self.circle, x0, y0, x1, y1)
            else:
                self.map_widget.canvas.delete(self.canvas_icon)
                self.map_widget.canvas.delete(self.circle)
                self.map_widget.canvas.delete(self.canvas_image)
                self.circle, self.canvas_image, self.canvas_icon = None, None, None

            self.map_widget.manage_z_order()
