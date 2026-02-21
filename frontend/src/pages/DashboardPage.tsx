import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { productsService } from "@/services/products";
import type { Product, ProductFilters } from "@/types/product";

const CATEGORIES = [
  { value: "", label: "Все" },
  { value: "Сувениры", label: "Сувениры" },
  { value: "Аксессуары", label: "Аксессуары" },
  { value: "Декор", label: "Декор" },
  { value: "Косметика", label: "Косметика" },
  { value: "Игрушки", label: "Игрушки" },
  { value: "Кухня", label: "Кухня" },
  { value: "Канцтовары", label: "Канцтовары" },
];

const SORT_OPTIONS = [
  { value: "", label: "Без сортировки" },
  { value: "price", label: "По цене" },
  { value: "popularity", label: "По популярности" },
];

export function DashboardPage() {
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

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await productsService.getProducts(appliedFilters);
      setProducts(result.items);
      setTotal(result.total);
    } catch (e) {
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

  const handleFilterChange = <K extends keyof ProductFilters>(
    key: K,
    value: ProductFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleOpen = (id: string) => {
    navigate(`/products/${id}`);
  };

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1200, margin: "0 auto" }}>
      <h1 style={{ marginBottom: "1.5rem" }}>Dashboard</h1>

      <section
        style={{
          marginBottom: "1.5rem",
          padding: "1rem",
          border: "1px solid #ddd",
          borderRadius: 8,
        }}
      >
        <h2 style={{ marginBottom: "1rem", fontSize: "1rem" }}>Фильтры</h2>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "1rem",
            alignItems: "flex-end",
          }}
        >
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
              Категория
            </label>
            <select
              value={filters.category ?? ""}
              onChange={(e) => handleFilterChange("category", e.target.value)}
              style={{ padding: "0.5rem", minWidth: 140 }}
            >
              {CATEGORIES.map((c) => (
                <option key={c.value || "all"} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
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
              style={{ padding: "0.5rem", width: 100 }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
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
              style={{ padding: "0.5rem", width: 100 }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
              Сортировка
            </label>
            <select
              value={filters.sort_by ?? ""}
              onChange={(e) =>
                handleFilterChange(
                  "sort_by",
                  e.target.value ? (e.target.value as "price" | "popularity") : undefined
                )
              }
              style={{ padding: "0.5rem", minWidth: 160 }}
            >
              {SORT_OPTIONS.map((s) => (
                <option key={s.value || "none"} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleApply}
            style={{
              padding: "0.5rem 1rem",
              background: "#333",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            Применить
          </button>
        </div>
      </section>

      <section>
        <h2 style={{ marginBottom: "1rem", fontSize: "1rem" }}>Товары</h2>
        {error && (
          <p style={{ color: "#c00", marginBottom: "1rem" }}>{error}</p>
        )}
        {loading ? (
          <p>Загрузка...</p>
        ) : (
          <>
            <p style={{ marginBottom: "1rem", color: "#666" }}>
              Найдено: {total}
            </p>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                border: "1px solid #ddd",
              }}
            >
              <thead>
                <tr style={{ background: "#f5f5f5" }}>
                  <th style={thStyle}>Название</th>
                  <th style={thStyle}>Категория</th>
                  <th style={thStyle}>Цена</th>
                  <th style={thStyle}>Популярность</th>
                  <th style={thStyle}></th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={tdStyle}>{p.name}</td>
                    <td style={tdStyle}>{p.category ?? "—"}</td>
                    <td style={tdStyle}>{p.price ?? "—"}</td>
                    <td style={tdStyle}>{p.popularity_score ?? "—"}</td>
                    <td style={tdStyle}>
                      <button
                        onClick={() => handleOpen(p.id)}
                        style={{
                          padding: "0.25rem 0.75rem",
                          background: "#333",
                          color: "#fff",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                        }}
                      >
                        Открыть
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {products.length === 0 && !loading && !error && (
              <p style={{ marginTop: "1rem", color: "#666" }}>
                Нет товаров. Нажмите «Применить» для загрузки.
              </p>
            )}
          </>
        )}
      </section>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: "0.75rem",
  textAlign: "left",
  fontWeight: 600,
};
const tdStyle: React.CSSProperties = {
  padding: "0.75rem",
};
