import { Chip } from './Chip';

export interface ChipRowItem {
  label: string;
  active?: boolean;
}

export interface ChipRowProps {
  chips: ChipRowItem[];
  onSelect?: (label: string) => void;
}

export function ChipRow({ chips, onSelect }: ChipRowProps) {
  return (
    <div className="ds-chip-row">
      {chips.map((chip, i) => (
        <Chip
          key={i}
          label={chip.label}
          active={chip.active}
          onClick={onSelect ? () => onSelect(chip.label) : undefined}
        />
      ))}
    </div>
  );
}
