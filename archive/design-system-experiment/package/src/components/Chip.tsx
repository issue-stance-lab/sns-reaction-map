export interface ChipProps {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

export function Chip({ label, active = false, onClick }: ChipProps) {
  return (
    <button
      type="button"
      className={`ds-chip${active ? ' ds-chip--active' : ''}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
