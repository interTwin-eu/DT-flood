"""Utilities for ipyleaflet map."""
from pathlib import Path

import matplotlib.pyplot as plt
from ipyleaflet import WidgetControl
from ipywidgets import Image


def rm_layer_by_name(map, name):
    """Remove layer from map by its name."""
    names = [layer.name for layer in map.layers]
    if name not in names:
        pass
    for layer in map.layers:
        if layer.name == name:
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
