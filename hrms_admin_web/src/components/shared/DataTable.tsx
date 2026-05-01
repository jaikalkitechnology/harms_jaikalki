import { useState } from "react";
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/shared/LoadingScreen";
import { cn } from "@/lib/utils";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  loading?: boolean;
  pageSize?: number;
  searchPlaceholder?: string;
  onRowClick?: (row: TData) => void;
  emptyMessage?: string;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  loading,
  pageSize = 10,
  searchPlaceholder = "Search…",
  onRowClick,
  emptyMessage = "Nothing to show.",
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize } },
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-brown-light" />
          <Input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder={searchPlaceholder}
            className="pl-9"
          />
        </div>
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
          {table.getFilteredRowModel().rows.length} rows
        </div>
      </div>

      <div className="rounded-2xl border border-brand-brown-100 overflow-hidden bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/60">
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((h) => {
                    const sorted = h.column.getIsSorted();
                    return (
                      <th
                        key={h.id}
                        className="text-left px-4 py-3 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light select-none"
                      >
                        {h.isPlaceholder ? null : (
                          <button
                            className={cn(
                              "flex items-center gap-1.5",
                              h.column.getCanSort() &&
                                "hover:text-brand-brown-darker",
                            )}
                            onClick={h.column.getToggleSortingHandler()}
                            disabled={!h.column.getCanSort()}
                          >
                            {flexRender(
                              h.column.columnDef.header,
                              h.getContext(),
                            )}
                            {sorted === "asc" && <span>↑</span>}
                            {sorted === "desc" && <span>↓</span>}
                          </button>
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="p-6">
                    <CardSkeleton rows={5} />
                  </td>
                </tr>
              ) : table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="p-10 text-center text-brand-brown-light"
                  >
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => onRowClick?.(row.original)}
                    className={cn(
                      "border-t border-brand-brown-100/70",
                      onRowClick && "cursor-pointer hover:bg-brand-brown-50/40",
                    )}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="px-4 py-3 text-brand-brown-darker"
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between px-4 py-3 border-t border-brand-brown-100 text-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount() || 1}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
