from django import template
register = template.Library()

@register.filter
def color_badge(value):
    if not value:
        return ""

    map = {
        "gray_wrinkle":       {"abbr": "GW", "color": "#808080"},
        "beige_wrinkle":      {"abbr": "BW", "color": "#f5f5dc"},
        "black_wrinkle":      {"abbr": "BK", "color": "#000000"},
        "blue_wrinkle":       {"abbr": "BL", "color": "#007bff"},
        "green_wrinkle":      {"abbr": "GN", "color": "#28a745"},
        "light_gray_wrinkle": {"abbr": "LG", "color": "#d3d3d3"},
        "orange_wrinkle":     {"abbr": "OR", "color": "#fd7e14"},
        "red_wrinkle":        {"abbr": "RD", "color": "#dc3545"},
        "white_wrinkle":      {"abbr": "WH", "color": "#ffffff"},
        "yellow_wrinkle":     {"abbr": "YL", "color": "#ffc107"},
        "stainless_steel":    {"abbr": "SS", "color": "#c0c0c0"},
        "item_only":          {"abbr": "IO", "color": "#27a19b"},
        "others":             {"abbr": "OTH", "color": "#6c757d"}
    }

    light_colors = ['#ffffff', '#f5f5dc', '#d3d3d3', '#ffc107', '#c0c0c0']

    key = value.lower()
    entry = map.get(key, {"abbr": value[:3].upper(), "color": "#000"})
    text_color = "#000" if entry["color"].lower() in light_colors else "#fff"

    html = f"""
    <span style="
        display:inline-block;
        background-color:{entry['color']};
        color:{text_color};
        padding:2px 6px;
        border-radius:6px;
        font-size:12px;
        font-weight:bold;
        text-transform:uppercase;
        min-width:30px;
        text-align:center;
        border:1px solid #999;">
        {entry['abbr']}
    </span>
    """
    return html

color_badge.is_safe = True
