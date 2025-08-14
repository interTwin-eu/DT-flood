"""SFINCS plot style variables."""
bzs_color = "#3366cc"
dis_color = "#e9980c"

_geodata_base_style = {
    "color": "black",
    "radius": 8,
    "opacity": 0.5,
    "weigth": 2,
    "dashArray": 2,
    "fillOpacity": 0.6,
}
_geodata_base_style_point = {
    "radius": 5,
    "color": "red",
    "fillOpacity": 0.8,
    "weight": 3,
}
geodata_dis_style = {"fillColor": dis_color, **_geodata_base_style}
geodata_dis_style_point = {"fillColor": dis_color, **_geodata_base_style_point}
geodata_bzs_style = {"fillColor": bzs_color, **_geodata_base_style}
geodata_bzs_style_point = {"fillColor": bzs_color, **_geodata_base_style_point}

hover_style = {"fillColor": "black", "fillOpacity": 0.4}
