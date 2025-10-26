"use client";

import { CardDescriptor } from "@/schemas/ui";
import { motion } from "framer-motion";
import { Minus, TrendingDown, TrendingUp } from "lucide-react";

type CardProps = CardDescriptor["props"];

export const CardComponent: React.FC<CardProps> = ({
  title,
  description,
  value,
  unit,
  previousValue,
  delta,
  trend = "neutral",
  trendColor,
  icon,
  loading,
  size = "md",
  bordered = true,
  shadow = true,
  rounded = true,
  className,
  progress,
  progressColor = "bg-blue-500",
}) => {
  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  const sizeClasses =
    size === "sm"
      ? "p-3 text-sm"
      : size === "lg"
      ? "p-6 text-lg"
      : "p-5 text-base";

  const borderClass = bordered ? "border" : "";
  const shadowClass = shadow ? "shadow-sm" : "";
  const roundedClass = rounded ? "rounded-2xl" : "rounded";

  const cardContent = loading ? (
    <div className="animate-pulse p-2 rounded-2xl flex flex-col gap-4 w-[400px]">
      <div className="flex items-center gap-3 justify-start">
        <div className="h-10 w-10 rounded-full bg-gray-200"></div>
        <div className="h-4 w-3/5 bg-gray-200 rounded"></div>
      </div>

      <div className="h-8 w-2/3 bg-gray-300 rounded"></div>

      <div className="h-4 w-1/2 bg-gray-200 rounded"></div>

      <div className="flex gap-2 items-center justify-start">
        <div className="h-4 w-4 bg-gray-200 rounded-full"></div>
        <div className="h-4 w-1/3 bg-gray-200 rounded"></div>
      </div>

      <div className="h-2 w-[350px] bg-gray-200 rounded">
        <div className="h-2 w-1/2 bg-gray-300 rounded"></div>
      </div>

      <div className="h-8 w-24 bg-gray-200 rounded"></div>
    </div>
  ) : (
    <>
      <div className={`flex items-center justify-start mb-2`}>
        <h3 className="text-gray-700 font-semibold">{title}</h3>
      </div>

      <div className="text-3xl font-bold text-gray-900 my-2 flex items-baseline gap-1">
        {value}
        {unit && (
          <span className="text-lg font-medium text-gray-500">{unit}</span>
        )}
      </div>

      {previousValue !== undefined && delta !== undefined && (
        <div className="text-sm text-gray-500">
          Change from previous: {delta > 0 ? "+" : ""}
          {delta} ({previousValue})
        </div>
      )}

      {description && <p className="text-sm text-gray-500">{description}</p>}

      {progress !== undefined && (
        <div className="w-full h-2 bg-gray-200 rounded mt-2">
          <div
            className={`${progressColor} h-2 rounded`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="flex items-center gap-2 mt-2 text-sm">
        <TrendIcon
          size={16}
          className={
            trendColor ??
            (trend === "up"
              ? "text-green-500"
              : trend === "down"
              ? "text-red-500"
              : "text-gray-400")
          }
        />
        <span
          className={
            trendColor ??
            (trend === "up"
              ? "text-green-500"
              : trend === "down"
              ? "text-red-500"
              : "text-gray-400")
          }
        >
          {trend === "up"
            ? "Positive trend"
            : trend === "down"
            ? "Negative trend"
            : "No change"}
        </span>
      </div>
    </>
  );

  return (
    <motion.div
      layout
      className={`${roundedClass} ${borderClass} ${shadowClass} ${sizeClasses} bg-white p-5 flex flex-col justify-between w-[400px] ${
        className ?? ""
      }`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {cardContent}
    </motion.div>
  );
};
