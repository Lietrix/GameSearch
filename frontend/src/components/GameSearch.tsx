// frontend/src/components/GameSearch.tsx
import React, { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

type Game = {
  app_id: number;
  name: string;
  current?: number | null;
  peak24?: number | null;
  peak?: number | null;
};

type Paged = {
  total: number;
  page: number;
  size: number;
  items: Game[];
};

const sortOptions = [
  { key: "current", label: "Current ↓" },
  { key: "-current", label: "Current ↑" },
  { key: "peak24", label: "24h Peak ↓" },
  { key: "peak", label: "All-time Peak ↓" },
  { key: "name", label: "Name A→Z" },
  { key: "-name", label: "Name Z→A" },
];

export default function GameSearch() {
  // inputQ = what user types, q = what we actually query with
  const [inputQ, setInputQ] = useState("");
  const [q, setQ] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const [sort, setSort] = useState("current");
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);

  const [data, setData] = useState<Paged | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const url = useMemo(() => {
    const params = new URLSearchParams({
      page: String(page),
      size: String(size),
      sort,
    });
    if (q.trim()) params.set("q", q.trim());
    return `${API_BASE}/games?${params.toString()}`;
  }, [q, sort, page, size]);

  const runSearch = () => {
    setPage(1);
    setQ(inputQ.trim());
    setHasSearched(true);
  };

  useEffect(() => {
    if (!hasSearched) return;

    let ignore = false;
    setLoading(true);
    setError(null);

    fetch(url)
      .then(async (r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((json: Paged) => {
        if (!ignore) setData(json);
      })
      .catch((e) => !ignore && setError(e.message))
      .finally(() => !ignore && setLoading(false));

    return () => {
      ignore = true;
    };
  }, [url, hasSearched]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / size)) : 1;

  const canSearch = !loading && inputQ.trim() !== q.trim();

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">GameSearch</h1>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center">
        <input
          value={inputQ}
          onChange={(e) => setInputQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") runSearch();
          }}
          placeholder="Search games…"
          className="md:col-span-2 h-11 rounded-2xl border px-4 outline-none focus:ring-2"
          disabled={loading}
        />

        <button
          onClick={runSearch}
          disabled={!canSearch}
          className="h-11 rounded-2xl border px-4 disabled:opacity-50"
          title="Run search"
        >
          {loading ? "Searching…" : "Search"}
        </button>

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="h-11 rounded-2xl border px-3"
          disabled={loading}
        >
          {sortOptions.map((o) => (
            <option key={o.key} value={o.key}>
              {o.label}
            </option>
          ))}
        </select>

        <select
          value={size}
          onChange={(e) => {
            setPage(1);
            setSize(parseInt(e.target.value));
          }}
          className="h-11 rounded-2xl border px-3"
          disabled={loading}
        >
          {[10, 25, 50, 100, 200].map((n) => (
            <option key={n} value={n}>
              {n}/page
            </option>
          ))}
        </select>
      </div>

      {/* Lightweight loading hint (in addition to skeleton rows) */}
      <div className="text-sm text-gray-600 min-h-[20px]">
        {!hasSearched && "Type a search and press Search"}
        {hasSearched && loading && "Loading results…"}
        {hasSearched && !loading && q && <>Showing results for <b>{q}</b></>}
        {hasSearched && !loading && !q && "Showing all games"}
      </div>


      <div className="rounded-2xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-2">App ID</th>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-right px-4 py-2">Current</th>
              <th className="text-right px-4 py-2">24h Peak</th>
              <th className="text-right px-4 py-2">All-time Peak</th>
            </tr>
          </thead>

          <tbody>
            {loading &&
              Array.from({ length: size }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-4 py-3">&nbsp;</td>
                  <td className="px-4 py-3">
                    <div className="h-4 rounded bg-gray-200" />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="h-4 rounded bg-gray-200" />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="h-4 rounded bg-gray-200" />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="h-4 rounded bg-gray-200" />
                  </td>
                </tr>
              ))}

            {!loading &&
              data?.items.map((g) => (
                <tr key={g.app_id} className="odd:bg-white even:bg-gray-50">
                  <td className="px-4 py-3 font-mono">{g.app_id}</td>
                  <td className="px-4 py-3">
                    <a
                      className="text-blue-600 hover:underline"
                      href={`https://store.steampowered.com/app/${g.app_id}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {g.name}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {g.current ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {g.peak24 ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {g.peak ?? "—"}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {error && <div className="text-red-600">Error: {error}</div>}

      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          {data && (
            <>
              Total <b>{data.total}</b> games • Page {data.page} / {totalPages}
            </>
          )}
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-2 rounded-xl border disabled:opacity-50"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </button>
          <button
            className="px-3 py-2 rounded-xl border disabled:opacity-50"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
