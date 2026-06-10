// PageRank — identify the most "central" zones in the taxi network
//
// High PageRank = many trips arrive from other high-traffic zones
// Interpretation: hubs like JFK, Penn Station, Midtown score highest.
// Use for: zone importance ranking, demand forecasting weights.

CALL gds.pageRank.stream('taxi_graph', {
    maxIterations:    20,
    dampingFactor:    0.85,
    relationshipWeightProperty: 'trips_count'
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS zone, score
RETURN
    zone.zone_id   AS zone_id,
    zone.zone_name AS zone_name,
    zone.borough   AS borough,
    round(score, 6) AS pagerank_score
ORDER BY pagerank_score DESC
LIMIT 30
