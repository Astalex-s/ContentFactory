import React from "react";
import { Button } from "../../../ui/components/Button";
import { Card } from "../../../ui/components/Card";
import { Table, Column } from "../../../ui/components/Table";
import { apiBaseURL } from "../../../services/api";
import { Product } from "../../../types/product";
import { StatusBadge } from "./StatusBadge";

interface ProductsTableProps {
  products: Product[];
  loading: boolean;
  onView: (id: string) => void;
  onGenerate: (id: string) => void;
}

export const ProductsTable: React.FC<ProductsTableProps> = ({
  products,
  loading,
  onView,
  onGenerate,
}) => {
  const columns: Column<Product>[] = [
    {
      key: "image",
      header: "Product",
      width: "60px",
      render: (p) => (
        <img
          src={
            p.image_filename
              ? `${apiBaseURL}/images/${p.image_filename}`
              : `${apiBaseURL}/products/${p.id}/image`
          }
          alt={p.name}
          style={{
            width: 40,
            height: 40,
            objectFit: "cover",
            borderRadius: 6,
          }}
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Crect fill='%23eee' width='40' height='40'/%3E%3C/svg%3E";
          }}
        />
      ),
    },
    {
      key: "name",
      header: "Name",
      render: (p) => <span style={{ fontWeight: 500 }}>{p.name}</span>,
    },
    {
      key: "category",
      header: "Category",
      render: (p) => p.category || "—",
    },
    {
      key: "price",
      header: "Price",
      render: (p) => (p.price ? `${p.price} ₽` : "—"),
    },
    {
      key: "content_status",
      header: "Content",
      render: () => <StatusBadge status="no_content" type="content" />, // Placeholder, need real status from backend
    },
    {
      key: "publication_status",
      header: "Publication",
      render: () => <StatusBadge status="not_scheduled" type="publication" />, // Placeholder
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (p) => (
        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onView(p.id); }}>
            View
          </Button>
          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); onGenerate(p.id); }}>
            Generate
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Card title="Products Overview" padding="none">
      <Table
        data={products}
        columns={columns}
        isLoading={loading}
        onRowClick={(p) => onView(p.id)}
        emptyMessage="No products found."
      />
    </Card>
  );
};
