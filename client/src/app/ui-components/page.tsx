import { CardComponent } from "@/components/artifacts/CardComponent";
import { TableComponent } from "@/components/artifacts/TableComponent";

const page = () => {
  return (
    <div className="">
      <CardComponent loading={true} />
      <CardComponent
        title="Total Revenue"
        description="Revenue generated this month"
        value={125000}
        unit="$"
        previousValue={110000}
        delta={15000}
        trend="up"
        trendColor="text-green-600"
        loading={false}
        size="sm"
        bordered={true}
        shadow={true}
        rounded={true}
        className="max-w-sm"
        progress={75}
        progressColor="bg-yellow-500"
      />
      <TableComponent loading={true} />
      <TableComponent
        title="Product Inventory"
        loading={false}
        columns={[
          { key: "product", label: "Product" },
          { key: "stock", label: "Stock" },
          { key: "price", label: "Price" },
        ]}
        rows={[
          { product: "Laptop", stock: 12, price: "$1200" },
          { product: "Phone", stock: 30, price: "$800" },
          { product: "Tablet", stock: 20, price: "$600" },
        ]}
      />
      {/* <SectionComponent loading={true}/> */}
    </div>
  );
};

export default page;
