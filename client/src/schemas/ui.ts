export interface UIEvent {
  type: "ui_event";
  action: "create_component" | "update_component";
  target: string;
  component: UIDescriptor;
}

export type ComponentType = "table" | "card" | "section";

export interface BaseDescriptor {
  id: string;
  type: ComponentType;
  props: Record<string, unknown> & {
    children?: UIDescriptor[];
  };
}

/* Table */
export interface TableColumn {
  key: string;
  label: string;
}

export interface TableRow {
  [key: string]: string | number | boolean | null;
}

export interface TableDescriptor extends BaseDescriptor {
  type: "table";
  props: {
    title?: string;
    loading?: boolean;
    columns?: TableColumn[];
    rows?: TableRow[];
    children?: UIDescriptor[];
  };
}

/* Card */
export interface CardDescriptor extends BaseDescriptor {
  type: "card";
  props: {
    title?: string;
    description?: string;
    value?: string | number;
    icon?: string;
    trend?: "up" | "down" | "neutral";
    loading?: boolean;
    children?: UIDescriptor[];
    unit?: string;
    previousValue?: number;
    delta?: number;
    trendColor?: string;
    size?: "sm" | "md" | "lg";
    bordered?: boolean;
    shadow?: boolean;
    rounded?: boolean;
    className?: string;
    progress?: number;
    progressColor?: string;
  };
}

/* Section */
export interface SectionDescriptor extends BaseDescriptor {
  type: "section";
  props: {
    title?: string;
    subtitle?: string;
    className?: string;
    loading?: boolean;
    children?: UIDescriptor[];
  };
}

export type UIDescriptor = TableDescriptor | CardDescriptor | SectionDescriptor;
