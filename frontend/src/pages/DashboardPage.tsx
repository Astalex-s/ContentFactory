import { useRef, useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiBaseURL } from "@/services/api";
import { productsService, type ImportReport } from "@/services/products";
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
  const [importResult, setImportResult] = useState<ImportReport | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deletingAll, setDeletingAll] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportLoading(true);
    setImportResult(null);
    setError(null);
    try {
      const result = await productsService.importFromCsv(file);
      setImportResult(result);
      await fetchProducts();
    } catch (err) {
      setImportResult(null);
      setError("Не удалось загрузить CSV. Проверьте формат файла.");
    } finally {
      setImportLoading(false);
      e.target.value = "";
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
        <h2 style={{ marginBottom: "1rem", fontSize: "1rem" }}>Загрузка CSV</h2>
        <p style={{ marginBottom: "0.5rem", fontSize: 14, color: "#666" }}>
          Загрузите данные, выгруженные из маркетплейса (колонки: name, description, category, price, marketplace_url)
        </p>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleCsvUpload}
            disabled={importLoading}
            style={{ display: "none" }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importLoading}
            style={btnStyle}
          >
            {importLoading ? "Загрузка..." : "Выбрать и загрузить CSV"}
          </button>
        </div>
        {importResult && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.75rem",
              background: importResult.errors.length > 0 ? "#fff3cd" : "#d4edda",
              borderRadius: 6,
              fontSize: 14,
            }}
          >
            Импортировано: {importResult.imported}, пропущено: {importResult.skipped}
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
          </div>
        )}
      </section>

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
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
          <h2 style={{ fontSize: "1rem", margin: 0 }}>Товары</h2>
          {total > 0 && (
            <button
              onClick={handleDeleteAll}
              disabled={deletingAll}
              style={{
                ...btnStyle,
                background: "#c00",
              }}
            >
              {deletingAll ? "Удаление..." : "Удалить все товары"}
            </button>
          )}
        </div>
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
                  <th style={thStyle}>Фото</th>
                  <th style={thStyle}>Название</th>
                  <th style={thStyle}>Категория</th>
                  <th style={thStyle}>Цена</th>
                  <th style={thStyle}>Популярность</th>
                  <th style={thStyle}></th>
                  <th style={thStyle}></th>
                  <th style={thStyle}></th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={tdStyle}>
                      {p.image_filename ? (
                        <img
                          src={`${apiBaseURL}/images/${p.image_filename}`}
                          alt={p.name}
                          style={{
                            width: 48,
                            height: 48,
                            objectFit: "cover",
                            borderRadius: 4,
                          }}
                        />
                      ) : (
                        <span style={{ color: "#999", fontSize: 12 }}>—</span>
                      )}
                    </td>
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
                    <td style={tdStyle}>
                      <button
                        onClick={() => navigate(`/products/${p.id}/generate`)}
                        style={{
                          padding: "0.25rem 0.75rem",
                          background: "#0066cc",
                          color: "#fff",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                        }}
                      >
                        Сгенерировать
                      </button>
                    </td>
                    <td style={tdStyle}>
                      <button
                        onClick={() => handleDelete(p.id, p.name)}
                        disabled={deletingId === p.id}
                        style={{
                          padding: "0.25rem 0.75rem",
                          background: "#c00",
                          color: "#fff",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                        }}
                      >
                        {deletingId === p.id ? "…" : "Удалить"}
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

const btnStyle: React.CSSProperties = {
  padding: "0.5rem 1rem",
  background: "#333",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
};
