"use client";

import * as echarts from "echarts";
import type { ECBasicOption } from "echarts/types/dist/shared";
import { useEffect, useRef } from "react";

const ChartContainer = ({ option }: { option: ECBasicOption }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Initialize the chart
    chartInstance.current = echarts.init(chartRef.current, null, {
      renderer: "canvas",
      useDirtyRect: false,
    });

    const chartOption = option;

    chartInstance.current.setOption(chartOption);

    // Handle window resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener("resize", handleResize);

    // Cleanup function
    return () => {
      window.removeEventListener("resize", handleResize);
      chartInstance.current?.dispose();
    };
  }, [option]);

  return (
    <div
      ref={chartRef}
      className="w-full h-64"
      style={{ minHeight: "400px", minWidth: "450px" }}
    />
  );
};

export default ChartContainer;
