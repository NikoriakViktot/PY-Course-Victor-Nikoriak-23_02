// Dijkstra — maximize traffic flow (find underutilized route)
// Parameters: sourceZoneId (INT), targetZoneId (INT)
//
// weight_flow = 1 / trips_count
// High weight_flow → low traffic → route is underused
// Use when answering: "Which route has the least congestion?"

MATCH (source:Zone {zone_id: $sourceZoneId})
MATCH (target:Zone {zone_id: $targetZoneId})
CALL gds.shortestPath.dijkstra.stream('taxi_graph', {
    sourceNode:        id(source),
    targetNode:        id(target),
    relationshipWeightProperty: 'weight_flow'
})
YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
RETURN
    index,
    totalCost                                           AS total_flow_weight,
    [n IN gds.util.asNodes(nodeIds) | n.zone_name]     AS zone_names,
    [n IN gds.util.asNodes(nodeIds) | n.zone_id]       AS zone_ids,
    costs
ORDER BY totalCost
