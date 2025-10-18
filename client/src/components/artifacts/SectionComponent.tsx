"use client";
import { motion } from "framer-motion";
import React from "react";

export interface SectionComponentProps {
  title?: string;
  subtitle?: string;
  className?: string;
  loading?: boolean;
  children?: React.ReactNode;
}

export const SectionComponent: React.FC<SectionComponentProps> = ({
  title,
  subtitle,
  className = "",
  loading,
  children,
}) => {
  return (
    <motion.section
      layout
      className={`space-y-3 ${className}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {loading ? (
        <div className="animate-pulse space-y-6 w-[400px] p-4 rounded-lg border border-gray-200 bg-white">
          {/* Section header */}
          <div className="space-y-2 mb-4">
            <div className="h-8 w-1/3 bg-gray-200 rounded"></div>
            <div className="h-4 w-2/3 bg-gray-100 rounded"></div>
          </div>

          {/* Cards row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-3">
                {/* Card placeholder */}
                <div className="h-36 bg-gray-100 rounded-lg shadow-sm"></div>

                {/* Card content placeholders */}
                <div className="space-y-2">
                  <div className="h-5 w-3/4 bg-gray-200 rounded"></div>
                  <div className="h-4 w-1/2 bg-gray-100 rounded"></div>
                  <div className="h-3 w-1/4 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>

          {/* Table row */}
          <div className="mt-6 space-y-2 border-t border-gray-200 pt-4">
            {/* Table header */}
            <div className="h-6 w-1/2 bg-gray-200 rounded mb-2"></div>

            {/* Table column headers */}
            <div className="flex gap-2 mb-2">
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            </div>

            {/* Table rows */}
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

            {/* Optional table footer */}
            <div className="h-4 w-1/3 bg-gray-200 rounded mt-2"></div>
          </div>
        </div>
      ) : (
        <>
          {(title || subtitle) && (
            <div className="space-y-1">
              {title && (
                <h2 className="text-xl font-bold text-gray-900">{title}</h2>
              )}
              {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
            </div>
          )}
          <div className="grid gap-4">{children}</div>
        </>
      )}
    </motion.section>
  );
};
