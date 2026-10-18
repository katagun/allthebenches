import { ModelIcon } from './ModelIcon';

/** Shared model identity. Logos are decorative; the visible name is the accessible label. */
export function ModelIdentity({ name, labId = '', labName = '' }: { name: string; labId?: string; labName?: string }) {
  return <span className="model-identity"><ModelIcon labId={labId} labName={labName}/><span className="model-name">{name}</span></span>;
}
