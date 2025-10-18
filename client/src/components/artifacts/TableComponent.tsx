"use client";
import { TableDescriptor } from "@/schemas/ui";
import { motion } from "framer-motion";

type TableProps = TableDescriptor["props"];

export function TableComponent({ title, columns, rows, loading }: TableProps) {
  return (
    <motion.div
      layout
      className="rounded-2xl border border-gray-200 shadow-sm p-4 bg-white w-[400px]"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {title && <h2 className="text-lg font-semibold mb-3">{title}</h2>}

      {loading ? (
        <div className="animate-pulse w-full p-2 rounded-lg space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-2"></div>

          <div className="flex gap-2 mb-2">
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
          </div>

          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-2">
                <div className="h-4 bg-gray-100 rounded w-1/4"></div>
                <div className="h-4 bg-gray-100 rounded w-1/4"></div>
                <div className="h-4 bg-gray-100 rounded w-1/4"></div>
                <div className="h-4 bg-gray-100 rounded w-1/4"></div>
              </div>
            ))}
          </div>

          <div className="h-4 bg-gray-200 rounded w-1/3 mt-2"></div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                {columns &&
                  columns.map((col) => (
                    <th
                      key={col.key}
                      className="text-left px-3 py-2 font-medium text-gray-700"
                    >
                      {col.label}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody>
              {rows &&
                rows.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    {columns &&
                      columns.map((col) => (
                        <td key={col.key} className="px-3 py-2 text-gray-800">
                          {row[col.key]}
                        </td>
                      ))}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </motion.div>
  );
}
