import { useMemo, useState } from 'react';
import type { AppData } from '../data/snapshots';
import { ModelIdentity } from './ModelIdentity';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { Input } from './ui/input';
import { SheetDescription, SheetHeader, SheetTitle } from './ui/sheet';

export function ModelPicker({ data, selected, onApply }: { data: AppData; selected: string[]; onApply: (ids: string[]) => void }) {
  const [draft, setDraft] = useState(selected);
  const [search, setSearch] = useState('');
  const groups = useMemo(() => data.catalog.models.map(model => ({
    model,
    lab: data.catalog.labs.find(lab => model.lab_ids.includes(lab.id)),
    configurations: data.catalog.configurations.filter(config => config.model_id === model.id),
  })).filter(group => `${group.model.name} ${group.lab?.name}`.toLowerCase().includes(search.toLowerCase())), [data, search]);
  return <>
    <SheetHeader><SheetTitle>Choose models to compare</SheetTitle><SheetDescription>Select the exact configurations you want to compare. Columns are paginated to fit your screen. Starting a comparison clears model filters and keeps your chosen benchmarks.</SheetDescription></SheetHeader>
    <div className="picker-search"><Input aria-label="Find a model" type="search" placeholder="Find a model or lab…" value={search} onChange={event => setSearch(event.target.value)}/><span>{draft.length} selected</span><Button variant="ghost" size="sm" onClick={() => setDraft([])}>Clear selection</Button></div>
    <div className="drawer-scroll model-picker">{groups.length === 0 && <p>No models match your search.</p>}{groups.map(({ model, lab, configurations }) => <section key={model.id} className="picker-model"><h3><ModelIdentity name={model.name} labId={lab?.id} labName={lab?.name}/></h3><small>{lab?.name} · {model.release_date?.slice(0, 4) ?? 'Release date unknown'}</small>{configurations.map(config => <label className="check-option" key={config.id}><Checkbox checked={draft.includes(config.id)} onCheckedChange={checked => setDraft(ids => checked ? [...new Set([...ids, config.id])] : ids.filter(id => id !== config.id))}/><span>{config.reasoning_label ?? config.mode ?? 'Unknown reasoning'}</span></label>)}</section>)}</div>
    <div className="drawer-footer"><Button disabled={draft.length === 0} onClick={() => onApply(draft)}>Compare selected models</Button></div>
  </>;
}
