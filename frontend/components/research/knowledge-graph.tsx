"use client";

import { useMemo } from "react";
import { Background, Controls, MiniMap, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { KnowledgeGraph } from "@/lib/api";

const typeColor: Record<string, string> = {
  Paper: "#0f766e",
  Author: "#ca8a04",
  Method: "#dc2626",
  Dataset: "#2563eb",
  Metric: "#7c3aed",
  "Research Area": "#0891b2",
  Limitation: "#be123c",
  "Future Work": "#16a34a"
};

export function KnowledgeGraphView({ graph }: { graph: KnowledgeGraph }) {
  const { nodes, edges } = useMemo(() => {
    const radius = 260;
    const centerX = 360;
    const centerY = 260;
    const rfNodes: Node[] = graph.nodes.slice(0, 90).map((node, index) => {
      const angle = (index / Math.max(1, graph.nodes.length)) * Math.PI * 2;
      const isPaper = node.type === "Paper";
      return {
        id: node.id,
        data: { label: node.label },
        position: {
          x: isPaper ? centerX + Math.cos(angle) * 90 : centerX + Math.cos(angle) * radius,
          y: isPaper ? centerY + Math.sin(angle) * 80 : centerY + Math.sin(angle) * radius
        },
        style: {
          border: `1px solid ${typeColor[node.type] ?? "#64748b"}`,
          background: typeColor[node.type] ?? "#64748b",
          color: "white",
          fontSize: 11,
          width: isPaper ? 170 : 140,
          borderRadius: 8
        }
      };
    });
    const visible = new Set(rfNodes.map((node) => node.id));
    const rfEdges: Edge[] = graph.edges
      .filter((edge) => visible.has(edge.source) && visible.has(edge.target))
      .slice(0, 140)
      .map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: edge.label === "SUGGESTS" || edge.label === "LIMITED_BY",
        style: { strokeWidth: Math.max(1, edge.weight) }
      }));
    return { nodes: rfNodes, edges: rfEdges };
  }, [graph]);

  return (
    <div className="h-[560px] overflow-hidden rounded-lg border bg-card">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <MiniMap pannable zoomable />
        <Controls />
      </ReactFlow>
    </div>
  );
}
