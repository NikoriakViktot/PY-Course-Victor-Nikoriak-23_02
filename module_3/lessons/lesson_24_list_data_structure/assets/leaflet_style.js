/*
 * leaflet_style.js  —  loaded automatically by Dash from the assets/ folder.
 *
 * Referenced in Python via:
 *   from dash_extensions.javascript import Namespace
 *   ns = Namespace("dashExtensions", "default")
 *   style_fn        = ns("styleFeature")
 *   on_each_feature = ns("onEachFeature")
 */
window.dashExtensions = Object.assign(window.dashExtensions || {}, {
    default: {

        /* Per-feature fill colour — read from GeoJSON properties */
        styleFeature: function (feature) {
            return {
                fillColor:   feature.properties.fillColor || "#cccccc",
                weight:      1,
                opacity:     0.85,
                color:       "#555555",
                fillOpacity: 0.72,
            };
        },

        /* Highlight on mouse-enter */
        highlightStyle: function (feature) {
            return {
                fillColor:   feature.properties.fillColor || "#aaaaaa",
                weight:      2.5,
                opacity:     1,
                color:       "#222222",
                fillOpacity: 0.92,
            };
        },

        /* Tooltip bound to each feature layer */
        onEachFeature: function (feature, layer) {
            if (!feature.properties) return;
            var p = feature.properties;
            var val = (p.display_value !== undefined && p.display_value !== null)
                      ? p.display_value : "—";
            var borough = p.borough || "—";
            var tip = [
                '<div style="font-family:system-ui,sans-serif;font-size:12px;line-height:1.8;min-width:160px">',
                '<strong style="font-size:13px">', (p.zone || "Unknown"), '</strong><br>',
                '<span style="color:#666">Borough: ', borough, '</span><br>',
                '<span style="color:#666">Zone ID: ', (p.location_id || "—"), '</span>',
                '<hr style="margin:4px 0;border-color:#eee">',
                '<span style="color:#333">', (p.metric_label || "Value"), ': </span>',
                '<strong>', val, '</strong>',
                '</div>'
            ].join('');
            layer.bindTooltip(tip, { sticky: true, opacity: 0.97, maxWidth: 240 });
        },
    },
});
