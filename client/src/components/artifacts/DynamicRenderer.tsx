import { UIDescriptor } from "@/schemas/ui";
import { CardComponent } from "./CardComponent";
import { SectionComponent } from "./SectionComponent";
import { TableComponent } from "./TableComponent";

export interface DynamicRendererProps {
  descriptor: UIDescriptor;
}

interface BaseComponentProps {
  [key: string]: any;
  children?: React.ReactNode;
}
export const componentRegistry = {
  section: SectionComponent,
  card: CardComponent,
  table: TableComponent,
} as BaseComponentProps;

const DynamicRenderer = ({ descriptor }: DynamicRendererProps) => {
  const Component = componentRegistry[descriptor.type];
  if (!Component) {
    return (
      <div className="border border-gray-400 rounded-xl py-6 px-2 bg-red-500/10">
        ❌ Unable to load component (component type: {descriptor.type})
      </div>
    );
  }

  // Render children recursively if they exist
  const children =
    "children" in descriptor.props && Array.isArray(descriptor.props.children)
      ? descriptor.props.children.map((child) => (
          <DynamicRenderer key={child.id} descriptor={child} />
        ))
      : null;

  return (
    <Component key={descriptor.id} {...descriptor.props}>
      {children}
    </Component>
  );
};

export default DynamicRenderer;
