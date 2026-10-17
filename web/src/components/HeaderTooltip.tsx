import { useId, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

/** Mounted only while hovered/focused; portal escapes the table's scroll clipping. */
export function HeaderTooltip({ text, children }: { text: string; children: ReactNode }) {
  const id = useId();
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null);
  const show = (element: HTMLElement) => {
    const rect = element.getBoundingClientRect();
    setPosition({ left: Math.max(8, Math.min(rect.left, window.innerWidth - 296)), top: rect.bottom + 6 });
  };
  return <div className="model-header-tooltip" aria-describedby={position ? id : undefined}
    onMouseEnter={event => show(event.currentTarget)} onMouseLeave={() => setPosition(null)}
    onFocus={event => show(event.currentTarget)} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setPosition(null); }}
    onKeyDown={event => { if (event.key === 'Escape') setPosition(null); }}>
    {children}
    {position && createPortal(<div id={id} role="tooltip" className="model-header-details" style={position}>{text}</div>, document.body)}
  </div>;
}
