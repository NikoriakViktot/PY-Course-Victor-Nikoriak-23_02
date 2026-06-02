// Dijkstra — minimize total fare cost between two zones
// Parameters: sourceZoneId (INT), targetZoneId (INT)
//
// weight_cost = avg_fare on each edge
// Use when answering: "What is the cheapest route from A to B?"

MATCH (source:Zone {zone_id: $sourceZoneId})
MATCH (target:Zone {zone_id: $targetZoneId})
CALL gds.shortestPath.dijkstra.stream('taxi_graph', {
    sourceNode:        id(source),
    targetNode:        id(target),
    relationshipWeightProperty: 'weight_cost'
})
YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
RETURN
    index,
    totalCost                                           AS total_cost,
    [n IN gds.util.asNodes(nodeIds) | n.zone_name]     AS zone_names,
    [n IN gds.util.asNodes(nodeIds) | n.zone_id]       AS zone_ids,
    costs
ORDER BY totalCost
