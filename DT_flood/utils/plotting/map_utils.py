"""Utilities for ipyleaflet map."""
from pathlib import Path

import matplotlib.pyplot as plt
from ipycanvas import Canvas
from ipyleaflet import CircleMarker, WidgetControl
from ipywidgets import Image

legendmarker_base = {"stroke": "black", "line_width": 3, "alpha": 0.7}


def get_layer_by_name(map, name):
    """Get map layer by name."""
    for layer in map.layers:
        if layer.name == name:
            return layer
    return ValueError(f"Layer {name} not found in map")


def rm_layer_by_name(map, name):
    """Remove layer from map by its name."""
    names = [layer.name for layer in map.layers]
    if name not in names:
        pass
    layer = get_layer_by_name(map, name)
    map.remove(layer)


def add_plot_box(map):
    """Add box for plots to map."""
    controls = [
        control for control in map.controls if isinstance(control, WidgetControl)
    ]
    for control in controls:
        if isinstance(control.widget, Image):
            return control.widget

    im_wdg = Image(name="plot_image")
    im_wdg.layout.margin = "0px 20px 20px 20px"
    im_wdg.layout.height = "400px"
    control = WidgetControl(widget=im_wdg, position="bottomright", name="plot_box")
    map.add(control)

    return im_wdg


def add_fig_to_widg(im_widg, fig):
    """Add figure to image widget."""
    fig.savefig("figure.png")
    plt.close(fig)
    fn = open("figure.png", "rb")
    image = fn.read()
    fn.close()
    im_widg.value = image
    Path.unlink("figure.png")


def add_plot_marker(map, location, color="black"):
    """Add marker to map for timeseries plots."""
    circle = CircleMarker(name="plot_marker")
    circle.location = location
    circle.radius = 8
    circle.color = color
    circle.fill_color = color
    circle.weight = 3
    circle.dashArray = 1
    circle.fillOpacity = 1
    map.add(circle)


def legend_marker(color):
    """Add marker to legend."""
    canvas = Canvas(width=50, height=50)
    canvas.fill_style = color
    canvas.global_alpha = legendmarker_base["alpha"]
    canvas.stroke_style = legendmarker_base["stroke"]
    canvas.line_width = legendmarker_base["line_width"]
    canvas.fill_circle(20, 15, 10)
    canvas.stroke_circle(20, 15, 10)

    return canvas


def legend_line(color):
    """Add line to legend."""
    canvas = Canvas(width=50, height=50)
    canvas.stroke_style = color
    canvas.line_width = 2
    canvas.stroke_line(5, 15, 25, 15)

    return canvas
