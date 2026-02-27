import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Select } from "../ui/components/Select";
import { Table, Column } from "../ui/components/Table";
import { Alert } from "../ui/components/Alert";
import { apiBaseURL } from "../services/api";
import { productsService, type MarketplaceImportReport } from "../services/products";
import type { Product, ProductFilters } from "../types/product";
import { spacing, colors } from "../ui/theme";

function getProductImageUrl(p: Product): string {
  return p.image_filename
    ? `${apiBaseURL}/images/${p.image_filename}`
    : `${apiBaseURL}/products/${p.id}/image`;
}

const SORT_OPTIONS = [
  { value: "", label: "Без сортировки" },
  { value: "price", label: "По цене" },
  { value: "popularity", label: "По популярности" },
];

export function ProductsListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ProductFilters>({
    category: "",
    min_price: undefined,
    max_price: undefined,
    sort_by: undefined,
    page: 1,
    page_size: 20,
  });
  const [appliedFilters, setAppliedFilters] = useState<ProductFilters>(filters);
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<MarketplaceImportReport | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deletingAll, setDeletingAll] = useState(false);
  const [categories, setCategories] = useState<string[]>([]);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await productsService.getProducts(appliedFilters);
      setProducts(result.items);
      setTotal(result.total);
    } catch {
      setError("Не удалось загрузить товары");
      setProducts([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [appliedFilters]);

  const handleApply = () => {
    setAppliedFilters({
      ...filters,
      category: filters.category || undefined,
      sort_by: (filters.sort_by as "price" | "popularity") || undefined,
    });
  };

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const cats = await productsService.getCategories();
        setCategories(cats);
      } catch (err) {
        console.error("Failed to load categories", err);
      }
    };
    loadCategories();
  }, []);

  const handleFilterChange = <K extends keyof ProductFilters>(
    key: K,
    value: ProductFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleOpen = (id: string) => {
    navigate(`/products/${id}`);
  };

  const handleImportFromMarketplace = async () => {
    setImportLoading(true);
    setImportResult(null);
    setError(null);
    try {
      const result = await productsService.importFromMarketplace();
      setImportResult(result);
      await fetchProducts();
    } catch {
      setImportResult(null);
      setError("Не удалось загрузить товары с маркетплейса.");
    } finally {
      setImportLoading(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Удалить товар «${name}»?`)) return;
    setDeletingId(id);
    try {
      await productsService.deleteProduct(id);
      await fetchProducts();
    } catch {
      setError("Не удалось удалить товар");
    } finally {
      setDeletingId(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm("Удалить все товары? Это действие нельзя отменить.")) return;
    setDeletingAll(true);
    setError(null);
    try {
      await productsService.deleteAllProducts();
      await fetchProducts();
    } catch {
      setError("Не удалось удалить товары");
    } finally {
      setDeletingAll(false);
    }
  };

  const columns: Column<Product>[] = [
    {
      key: "image",
      header: "Фото",
      width: "60px",
      render: (p) => (
        <img
          src={getProductImageUrl(p)}
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
      key: "popularity_score",
      header: "Популярность",
      render: (p) => p.popularity_score?.toFixed(2) || "—",
    },
  ];

  return (
    <PageContainer>
      <h1 style={{ margin: 0, marginBottom: spacing.lg }}>Товары</h1>

      <div style={{ display: "flex", gap: spacing.sm, flexWrap: "wrap", marginBottom: spacing.lg }}>
        <Button variant="secondary" onClick={handleImportFromMarketplace} loading={importLoading}>
          Загрузить из маркетплейса
        </Button>
        {total > 0 && (
          <Button variant="danger" onClick={handleDeleteAll} loading={deletingAll}>
            Удалить все
          </Button>
        )}
      </div>

      {importResult && (
        <Alert type={importResult.errors.length > 0 ? "warning" : "success"} title="Результат импорта">
          Импортировано: {importResult.imported}
          {importResult.errors.length > 0 && (
            <ul style={{ margin: "0.5rem 0 0 1rem", padding: 0 }}>
              {importResult.errors.slice(0, 5).map((err: string, i: number) => (
                <li key={i}>{err}</li>
              ))}
              {importResult.errors.length > 5 && (
                <li>… и ещё {importResult.errors.length - 5}</li>
              )}
            </ul>
          )}
        </Alert>
      )}

      {error && <Alert type="error">{error}</Alert>}

      <Card title="Фильтры" style={{ marginBottom: spacing.lg }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: spacing.md, alignItems: "end" }}>
          <div>
            <Select
              label="Категория"
              value={filters.category ?? ""}
              onChange={(e) => handleFilterChange("category", e.target.value)}
            >
              <option value="">Все</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14, fontWeight: 500, color: colors.gray[700] }}>
              Мин. цена
            </label>
            <input
              type="number"
              min={0}
              step={1}
              value={filters.min_price ?? ""}
              onChange={(e) =>
                handleFilterChange(
                  "min_price",
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
              placeholder="—"
              style={{ padding: "10px 12px", width: "100%", border: "1px solid #ddd", borderRadius: 6, fontSize: 14 }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14, fontWeight: 500, color: colors.gray[700] }}>
              Макс. цена
            </label>
            <input
              type="number"
              min={0}
              step={1}
              value={filters.max_price ?? ""}
              onChange={(e) =>
                handleFilterChange(
                  "max_price",
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
              placeholder="—"
              style={{ padding: "10px 12px", width: "100%", border: "1px solid #ddd", borderRadius: 6, fontSize: 14 }}
            />
          </div>
          <div>
            <Select
              label="Сортировка"
              value={filters.sort_by ?? ""}
              onChange={(e) =>
                handleFilterChange(
                  "sort_by",
                  e.target.value ? (e.target.value as "price" | "popularity") : undefined
                )
              }
            >
              {SORT_OPTIONS.map((s) => (
                <option key={s.value || "none"} value={s.value}>
                  {s.label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14, fontWeight: 500, color: "transparent" }}>
              .
            </label>
            <Button variant="primary" onClick={handleApply} style={{ height: "42px", width: "100%" }}>
              Применить
            </Button>
          </div>
        </div>
      </Card>

      <Card title={`Товары (${total})`} padding="none">
        <Table
          data={products}
          columns={columns}
          isLoading={loading}
          onRowClick={(p) => handleOpen(p.id)}
          emptyMessage="Нет товаров. Загрузите товары с маркетплейса."
          actions={(p) => (
            <div style={{ display: "flex", gap: spacing.xs, justifyContent: "flex-end" }}>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e?.stopPropagation();
                  handleOpen(p.id);
                }}
              >
                Открыть
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={(e) => {
                  e?.stopPropagation();
                  handleDelete(p.id, p.name);
                }}
                loading={deletingId === p.id}
                disabled={deletingId === p.id}
              >
                Удалить
              </Button>
            </div>
          )}
        />
      </Card>
    </PageContainer>
  );
}
