import { useState } from 'react';

const icons: Record<string, string> = {
  anthropic: 'claude-color', openai: 'openai', meta: 'meta-color',
  xai: 'grok', google_deepmind: 'gemini-color', mistral: 'mistral-color',
  qwen: 'qwen-color', deepseek: 'deepseek-color',
};

export function ModelIcon({ labId, labName }: { labId: string; labName: string }) {
  const [failed, setFailed] = useState<string | null>(null);
  const icon = icons[labId];
  // Decorative: the adjacent model name and lab metadata identify the row.
  return icon && failed !== icon
    ? <img className="model-brand-icon" src={`${import.meta.env.BASE_URL}icons/${icon}.svg`} width={18} height={18} alt="" aria-hidden="true" decoding="async" onError={() => setFailed(icon)}/>
    : <span className="model-brand-icon model-brand-fallback" aria-hidden="true">{labName.charAt(0)}</span>;
}
