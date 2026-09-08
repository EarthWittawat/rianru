"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { getGraph, getTopics, type GraphEdge, type GraphNode } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => <CanvasMessage>Loading graph…</CanvasMessage>,
});

/** react-force-graph types its accessors over its own loose node shape. */
type ForceNode = { [key: string]: unknown };
const asGraphNode = (node: ForceNode) => node as unknown as GraphNode;

// Rubric is reserved for the reader's own marks; the material itself is ink.
const NODE_COLORS: Record<GraphNode["type"], string> = {
  Document: "#57534c",
  Entity: "#1a1a1a",
  Highlight: "#c23a2a",
};

const NODE_RADII: Record<GraphNode["type"], number> = {
  Document: 7,
  Entity: 4,
  Highlight: 6,
};

/** Labels every node below this many nodes; above it, only the big ones. */
const LABEL_ALL_BELOW = 120;

export function KnowledgeGraph() {
  const [topics, setTopics] = useState<string[]>([]);
  const [topic, setTopic] = useState<string>("");
  const [data, setData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({
    nodes: [],
    edges: [],
  });
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 600 });

  useEffect(() => {
    getTopics().then(setTopics).catch(() => setTopics([]));
  }, []);

  useEffect(() => {
    getGraph(topic || undefined)
      .then((graph) => {
        setData(graph);
        setError("");
      })
      .catch(() => setError("Could not load the graph. Is the backend running?"));
  }, [topic]);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // react-force-graph mutates the objects it is given, so hand it copies.
  const graphData = useMemo(
    () => ({
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.edges.map((e) => ({ ...e })),
    }),
    [data],
  );

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-rule px-6 py-3">
          <label htmlFor="topic" className="apparatus">
            Topic
          </label>
          <select
            id="topic"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            className="border border-rule bg-paper px-2 py-1 text-fine"
          >
            <option value="">Whole course</option>
            {topics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <span className="apparatus tabular ml-auto">
            {data.nodes.length} nodes · {data.edges.length} connections
          </span>
        </div>

        <div ref={containerRef} className="relative flex-1 bg-paper">
          {error && <CanvasMessage>{error}</CanvasMessage>}
          {!error && data.nodes.length === 0 && (
            <CanvasMessage>
              Nothing in the graph yet. Run the ingest script first.
            </CanvasMessage>
          )}
          {!error && data.nodes.length > 0 && (
            <ForceGraph2D
              graphData={graphData}
              width={size.width}
              height={size.height}
              backgroundColor="#f3eee3"
              nodeLabel={(node: ForceNode) => asGraphNode(node).label}
              linkColor={() => "#cfc6b4"}
              linkWidth={0.6}
              linkDirectionalArrowLength={2.5}
              linkDirectionalArrowRelPos={1}
              onNodeClick={(node: ForceNode) => setSelected(asGraphNode(node))}
              cooldownTicks={120}
              nodeCanvasObject={(
                node: ForceNode,
                ctx: CanvasRenderingContext2D,
                scale: number,
              ) => drawNode(asGraphNode(node), node, ctx, scale, data.nodes.length)}
              nodePointerAreaPaint={(
                node: ForceNode,
                color: string,
                ctx: CanvasRenderingContext2D,
              ) => {
                const { x, y } = node as { x: number; y: number };
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, NODE_RADII[asGraphNode(node).type] + 2, 0, 2 * Math.PI);
                ctx.fill();
              }}
            />
          )}
        </div>
      </div>

      <GraphDetail node={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function drawNode(
  graphNode: GraphNode,
  node: ForceNode,
  ctx: CanvasRenderingContext2D,
  scale: number,
  nodeCount: number,
) {
  const { x, y } = node as { x: number; y: number };
  const radius = NODE_RADII[graphNode.type];

  ctx.beginPath();
  ctx.arc(x, y, radius, 0, 2 * Math.PI);
  ctx.fillStyle = NODE_COLORS[graphNode.type];
  ctx.fill();

  const showLabel =
    graphNode.type !== "Entity" || nodeCount <= LABEL_ALL_BELOW || scale > 1.6;
  if (!showLabel) return;

  const fontSize = Math.max(10 / scale, 2.5);
  ctx.font = `${fontSize}px "Source Serif 4", Georgia, serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillStyle = "#57534c";
  const label =
    graphNode.label.length > 28
      ? `${graphNode.label.slice(0, 28)}…`
      : graphNode.label;
  ctx.fillText(label, x, y + radius + 1);
}

function GraphDetail({
  node,
  onClose,
}: {
  node: GraphNode | null;
  onClose: () => void;
}) {
  return (
    <aside className="flex w-80 shrink-0 flex-col border-l border-rule bg-paper-lift">
      <div className="border-b border-rule px-6 py-4">
        <h2 className="apparatus">Details</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5">
        {!node && (
          <p className="text-fine text-slate">
            Click any node to see what it is.
          </p>
        )}

        {node && (
          <>
            <p className="apparatus" style={{ color: NODE_COLORS[node.type] }}>
              {node.type}
            </p>
            <p className="mt-2 text-lead break-words">{node.label}</p>
            {node.topic && <p className="apparatus mt-1.5">{node.topic}</p>}
            {node.entity_type && (
              <p className="apparatus mt-1.5">{node.entity_type}</p>
            )}
            {node.explanation && (
              <p className="bracketed mt-4 whitespace-pre-wrap text-fine text-slate">
                {node.explanation}
              </p>
            )}
            <button
              onClick={onClose}
              className="apparatus mt-5 underline decoration-rule hover:text-rubric"
            >
              Clear
            </button>
          </>
        )}

        <Legend />
      </div>
    </aside>
  );
}

function Legend() {
  return (
    <ul className="mt-10 border-t border-rule pt-4">
      {(Object.keys(NODE_COLORS) as GraphNode["type"][]).map((type) => (
        <li key={type} className="apparatus flex items-center gap-2 py-1">
          <span
            aria-hidden
            className="h-2 w-2 shrink-0"
            style={{ backgroundColor: NODE_COLORS[type] }}
          />
          {type}
        </li>
      ))}
    </ul>
  );
}

function CanvasMessage({ children }: { children: React.ReactNode }) {
  return (
    <p className="absolute inset-0 flex items-center justify-center text-fine text-slate">
      {children}
    </p>
  );
}
