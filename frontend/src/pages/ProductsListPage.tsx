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
import { ImageModal } from "../ui/components/ImageModal";

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
    page_size: 10,
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
  const [modalImage, setModalImage] = useState<{ src: string; alt: string } | null>(null);

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
      page: 1,
      category: filters.category || undefined,
      sort_by: (filters.sort_by as "price" | "popularity") || undefined,
    });
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
    setAppliedFilters((prev) => ({ ...prev, page: newPage }));
  };

  const totalPages = Math.ceil(total / (appliedFilters.page_size ?? 10));
  const currentPage = appliedFilters.page ?? 1;

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
          onClick={(e) => { e.stopPropagation(); setModalImage({ src: getProductImageUrl(p), alt: p.name }); }}
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
        {totalPages > 1 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: spacing.sm,
              padding: spacing.md,
              borderTop: `1px solid ${colors.border}`,
              flexWrap: "wrap",
            }}
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1 || loading}
            >
              ← Назад
            </Button>

            <div style={{ display: "flex", gap: 4 }}>
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter((p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                .reduce<(number | "...")[]>((acc, p, idx, arr) => {
                  if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("...");
                  acc.push(p);
                  return acc;
                }, [])
                .map((p, idx) =>
                  p === "..." ? (
                    <span key={`ellipsis-${idx}`} style={{ padding: "4px 8px", color: colors.gray[400] }}>…</span>
                  ) : (
                    <button
                      key={p}
                      onClick={() => handlePageChange(p as number)}
                      disabled={loading}
                      style={{
                        padding: "4px 10px",
                        borderRadius: 6,
                        border: `1px solid ${p === currentPage ? colors.primary[500] : colors.border}`,
                        background: p === currentPage ? colors.primary[500] : "transparent",
                        color: p === currentPage ? "#fff" : colors.text,
                        fontWeight: p === currentPage ? 600 : 400,
                        cursor: p === currentPage ? "default" : "pointer",
                        fontSize: 14,
                      }}
                    >
                      {p}
                    </button>
                  )
                )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages || loading}
            >
              Вперёд →
            </Button>

            <span style={{ fontSize: 13, color: colors.gray[500] }}>
              стр. {currentPage} из {totalPages} ({total} товаров)
            </span>
          </div>
        )}
      </Card>
      {modalImage && (
        <ImageModal
          src={modalImage.src}
          alt={modalImage.alt}
          onClose={() => setModalImage(null)}
        />
      )}
    </PageContainer>
  );
}
