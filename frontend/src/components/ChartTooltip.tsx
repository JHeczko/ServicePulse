interface Props {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
  unit?: string;
}

export default function ChartTooltip({ active, payload, label, unit = "" }: Props) {
  if (!active || !payload?.length) return null;

  return (
    <div className="custom-tooltip">
      <div className="custom-tooltip__label">{label}</div>
      <div className="custom-tooltip__value">
        {payload[0].value}
        {unit}
      </div>
    </div>
  );
}
