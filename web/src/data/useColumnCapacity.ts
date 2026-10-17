import { useCallback, useEffect, useRef, useState } from 'react';

export const MODEL_COLUMN_WIDTH = 320;
export const DATA_COLUMN_WIDTH = 180;
export const COMPACT_MODEL_WIDTH = 150;
export const BENCHMARK_LABEL_WIDTH = 260;
// A defensive DOM budget for extreme zoom-out / unusually large displays.
export const MAX_BENCHMARK_COLUMNS = 24;
export function columnCapacity(width: number, marketColumns = 0, transposed = false): number {
  // Small screens swipe through bounded groups instead of paging one model at a time.
  if (width <= 768) return Math.max(1, 3 - marketColumns);
  return Math.max(1, Math.min(MAX_BENCHMARK_COLUMNS,
    Math.floor((width - 2 - (transposed ? BENCHMARK_LABEL_WIDTH : MODEL_COLUMN_WIDTH)) / (transposed ? COMPACT_MODEL_WIDTH : DATA_COLUMN_WIDTH)) - marketColumns));
}

export function useColumnCapacity(marketColumns: number, transposed = false) {
  const [element, setElement] = useState<HTMLDivElement | null>(null);
  const [capacity, setCapacity] = useState(10);
  const frame = useRef<number | null>(null);
  const ref = useCallback((node: HTMLDivElement | null) => setElement(node), []);
  useEffect(() => {
    if (!element) return;
    const measure = () => {
      const width = element.clientWidth;
      if (width > 0) setCapacity(columnCapacity(width, marketColumns, transposed));
    };
    const schedule = () => {
      if (frame.current !== null) cancelAnimationFrame(frame.current);
      frame.current = requestAnimationFrame(() => { frame.current = null; measure(); });
    };
    measure();
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(schedule);
    observer?.observe(element);
    window.addEventListener('resize', schedule);
    return () => {
      observer?.disconnect();
      window.removeEventListener('resize', schedule);
      if (frame.current !== null) cancelAnimationFrame(frame.current);
    };
  }, [element, marketColumns, transposed]);
  return { tableRef: ref, columnsPerPage: capacity };
}
