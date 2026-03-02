import React, { useState } from "react";
import { Button } from "../../../ui/components/Button";
import { Card } from "../../../ui/components/Card";
import { Table, Column } from "../../../ui/components/Table";
import { apiBaseURL } from "../../../services/api";
import { Product } from "../../../types/product";
import { StatusBadge } from "./StatusBadge";
import { ImageModal } from "../../../ui/components/ImageModal";

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
  const [modalImage, setModalImage] = useState<{ src: string; alt: string } | null>(null);

  const getImgUrl = (p: Product) =>
    p.image_filename
      ? `${apiBaseURL}/images/${p.image_filename}`
      : `${apiBaseURL}/products/${p.id}/image`;

  const columns: Column<Product>[] = [
    {
      key: "image",
      header: "Фото",
      width: "60px",
      render: (p) => (
        <img
          src={getImgUrl(p)}
          alt={p.name}
          onClick={(e) => { e.stopPropagation(); setModalImage({ src: getImgUrl(p), alt: p.name }); }}
          style={{
            width: 40,
            height: 40,
            objectFit: "cover",
            borderRadius: 6,
            cursor: "zoom-in",
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
      header: "Название",
      render: (p) => <span style={{ fontWeight: 500 }}>{p.name}</span>,
    },
    {
      key: "category",
      header: "Категория",
      render: (p) => p.category || "—",
    },
    {
      key: "price",
      header: "Цена",
      render: (p) => (p.price ? `${p.price} ₽` : "—"),
    },
    {
      key: "content_status",
      header: "Контент",
      render: (p) => (
        <StatusBadge status={p.content_status ?? "no_content"} type="content" />
      ),
    },
    {
      key: "publication_status",
      header: "Публикация",
      render: (p) => (
        <StatusBadge
          status={p.publication_status ?? "not_scheduled"}
          type="publication"
        />
      ),
    },
    {
      key: "actions",
      header: "Действия",
      align: "right",
      render: (p) => (
        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onView(p.id); }}>
            Открыть
          </Button>
          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); onGenerate(p.id); }}>
            Генерировать
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <Card title="Последние товары" padding="none">
        <Table
          data={products}
          columns={columns}
          isLoading={loading}
          onRowClick={(p) => onView(p.id)}
          emptyMessage="Нет товаров."
        />
      </Card>
      {modalImage && (
        <ImageModal
          src={modalImage.src}
          alt={modalImage.alt}
          onClose={() => setModalImage(null)}
        />
      )}
    </>
  );
};
