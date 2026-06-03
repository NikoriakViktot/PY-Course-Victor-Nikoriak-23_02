// Betweenness Centrality — find zones that act as bridges in the network
//
// High betweenness = many shortest paths pass through this zone
// Interpretation: removing a high-betweenness zone disrupts the most routes.
// Use for: critical infrastructure analysis, bottleneck detection.

CALL gds.betweenness.stream('taxi_graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS zone, score
RETURN
    zone.zone_id   AS zone_id,
    zone.zone_name AS zone_name,
    zone.borough   AS borough,
    round(score, 2) AS betweenness_score
ORDER BY betweenness_score DESC
LIMIT 30
