import React, { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Slider } from "./ui/slider";
import { Calendar } from "./ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { ChevronLeft, ChevronRight, Loader2, Search, X } from "lucide-react";
import { format } from "date-fns";
import { motion } from "framer-motion";

// --- Types ---------------------------------------------------------------
interface GameRow {
  app_id: string;
  name: string;
  current: number; // current players
  peak: number;    // 24h peak
  hours: number;   // playtime/hours if you collect it
  timestamp: string; // ISO string
}

interface ApiResponse {
  data: GameRow[];
  total: number;
  page: number;
  page_size: number;
}

// --- Helpers -------------------------------------------------------------
function classNames(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}

function useDebounce<T>(value: T, delay = 350) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return v;
}

// --- Component -----------------------------------------------------------
export default function GameSearchPrototype() {
  // query params
  const [q, setQ] = useState("");
  const debouncedQ = useDebounce(q);
  const [sort, setSort] = useState("-current"); // -desc, +asc
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [minPlayers, setMinPlayers] = useState([0]);
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<GameRow[]>([]);
  const [total, setTotal] = useState(0);

  // fetch
  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (debouncedQ) params.set("q", debouncedQ);
        if (sort) params.set("sort", sort);
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        if (minPlayers[0] > 0) params.set("min_current", String(minPlayers[0]));
        if (dateRange.from) params.set("from", dateRange.from.toISOString());
        if (dateRange.to) params.set("to", dateRange.to.toISOString());

        const res = await fetch(`/api/search?${params.toString()}`, { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json: ApiResponse = await res.json();
        setRows(json.data);
        setTotal(json.total);
      } catch (e: any) {
        if (e.name !== "AbortError") setError(e.message || "Failed to fetch");
      } finally {
        setLoading(false);
      }
    };
    run();
    return () => controller.abort();
  }, [debouncedQ, sort, page, pageSize, minPlayers, dateRange]);

  const maxPage = Math.max(1, Math.ceil(total / pageSize));

  // UI helpers
  const resetFilters = () => {
    setQ("");
    setSort("-current");
    setPage(1);
    setPageSize(25);
    setMinPlayers([0]);
    setDateRange({});
  };

  const sortOptions = [
    { value: "-current", label: "Current ↓" },
    { value: "+current", label: "Current ↑" },
    { value: "-peak", label: "Peak ↓" },
    { value: "+peak", label: "Peak ↑" },
    { value: "-timestamp", label: "Newest ↓" },
    { value: "+timestamp", label: "Oldest ↑" },
    { value: "+name", label: "Name A→Z" },
    { value: "-name", label: "Name Z→A" },
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="text-3xl font-bold tracking-tight mb-2">GameSearch</h1>
        <p className="text-neutral-400 mb-6">Query your collected SteamCharts dataset. Type to search by name or App ID, filter by players and date, and sort the results.</p>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.05 }}>
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-4 grid gap-4 md:grid-cols-12 items-center">
            <div className="md:col-span-5 flex items-center gap-2">
              <Search className="w-4 h-4 text-neutral-400" />
              <Input
                value={q}
                onChange={(e) => { setQ(e.target.value); setPage(1); }}
                placeholder="Search by game name or App ID…"
                className="bg-neutral-800 border-neutral-700"
              />
            </div>

            <div className="md:col-span-3">
              <Select value={sort} onValueChange={(v) => { setSort(v); setPage(1); }}>
                <SelectTrigger className="bg-neutral-800 border-neutral-700">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent className="bg-neutral-900 border-neutral-800">
                  {sortOptions.map(o => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="md:col-span-2">
              <Select value={String(pageSize)} onValueChange={(v) => { setPageSize(Number(v)); setPage(1); }}>
                <SelectTrigger className="bg-neutral-800 border-neutral-700">
                  <SelectValue placeholder="Page size" />
                </SelectTrigger>
                <SelectContent className="bg-neutral-900 border-neutral-800">
                  {[10, 25, 50, 100].map(n => (
                    <SelectItem key={n} value={String(n)}>{n} / page</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="md:col-span-2 flex justify-end gap-2">
              <Button variant="secondary" className="bg-neutral-800 border border-neutral-700" onClick={resetFilters}>
                <X className="w-4 h-4 mr-1" /> Reset
              </Button>
            </div>

            <div className="md:col-span-6">
              <label className="text-xs text-neutral-400">Min current players</label>
              <div className="flex items-center gap-3">
                <Slider value={minPlayers} onValueChange={(v) => { setMinPlayers(v); setPage(1); }} max={200000} step={1000} className="mt-2" />
                <div className="text-sm w-20 text-right tabular-nums">{minPlayers[0].toLocaleString()}</div>
              </div>
            </div>

            <div className="md:col-span-6">
              <label className="text-xs text-neutral-400">Date range</label>
              <div className="mt-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="bg-neutral-800 border-neutral-700 w-full justify-between">
                      <span>
                        {dateRange.from ? (
                          dateRange.to ? `${format(dateRange.from, "MMM d, yyyy")} – ${format(dateRange.to, "MMM d, yyyy")}` : `${format(dateRange.from, "MMM d, yyyy")} – …`
                        ) : (
                          "Pick a date range"
                        )}
                      </span>
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 bg-neutral-900 border-neutral-800" align="start">
                    <Calendar
                      mode="range"
                      selected={dateRange as any}
                      onSelect={(r: any) => { setDateRange(r || {}); setPage(1); }}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }}>
        <Card className="bg-neutral-900 border-neutral-800 mt-6">
          <CardContent className="p-0">
            <div className="flex items-center justify-between p-4 border-b border-neutral-800">
              <div className="text-sm text-neutral-400">{total.toLocaleString()} result{total === 1 ? "" : "s"}</div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <div className="px-3 py-1 rounded bg-neutral-800 text-xs tabular-nums">Page {page} / {maxPage}</div>
                <Button variant="ghost" size="icon" disabled={page >= maxPage} onClick={() => setPage(p => Math.min(maxPage, p + 1))}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="min-w-[120px]">Name</TableHead>
                    <TableHead className="w-[110px]">App ID</TableHead>
                    <TableHead className="w-[120px] text-right">Current</TableHead>
                    <TableHead className="w-[120px] text-right">24h Peak</TableHead>
                    <TableHead className="w-[120px] text-right">Hours</TableHead>
                    <TableHead className="w-[180px]">Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-10">
                        <div className="inline-flex items-center gap-2 text-neutral-400">
                          <Loader2 className="w-4 h-4 animate-spin" /> Loading…
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : rows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12 text-neutral-400">No results.</TableCell>
                    </TableRow>
                  ) : (
                    rows.map((r) => (
                      <TableRow key={`${r.app_id}-${r.timestamp}`} className="hover:bg-neutral-800/50">
                        <TableCell className="font-medium">{r.name}</TableCell>
                        <TableCell className="text-neutral-400">{r.app_id}</TableCell>
                        <TableCell className="text-right tabular-nums">{r.current.toLocaleString()}</TableCell>
                        <TableCell className="text-right tabular-nums">{r.peak.toLocaleString()}</TableCell>
                        <TableCell className="text-right tabular-nums">{r.hours?.toLocaleString?.() ?? "–"}</TableCell>
                        <TableCell className="text-neutral-300">{new Date(r.timestamp).toLocaleString()}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="text-xs text-neutral-500 mt-4">
        <p>Tip: Search accepts partial names ("baldu") and exact App IDs ("1086940"). Sorting and filters are executed on the server.</p>
      </div>
    </div>
  );
}
