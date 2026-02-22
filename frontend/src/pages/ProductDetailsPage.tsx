import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiBaseURL } from "@/services/api";
import { productsService } from "@/services/products";
import { contentApi } from "@/features/content";
import type { Product } from "@/types/product";

function getProductImageUrl(p: Product): string {
  return p.image_filename
    ? `${apiBaseURL}/images/${p.image_filename}`
    : `${apiBaseURL}/products/${p.id}/image`;
}

export function ProductDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasContent, setHasContent] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: "", description: "", category: "", price: "" });

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    productsService
      .getProduct(id)
      .then((p) => {
        if (!cancelled) {
          setProduct(p);
          if (p === null) setError("Товар не найден");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Не удалось загрузить товар");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!id) return;
    contentApi.hasContent(id).then(setHasContent).catch(() => setHasContent(false));
  }, [id]);

  const handleDelete = async () => {
    if (!id || !product || !window.confirm(`Удалить товар «${product.name}»?`)) return;
    try {
      await productsService.deleteProduct(id);
      navigate("/");
    } catch {
      setError("Не удалось удалить товар");
    }
  };

  const handleEdit = () => {
    if (product) {
      setEditForm({
        name: product.name,
        description: product.description ?? "",
        category: product.category ?? "",
        price: String(product.price ?? ""),
      });
      setEditing(true);
    }
  };

  const handleSaveEdit = async () => {
    if (!id) return;
    try {
      const updated = await productsService.updateProduct(id, {
        name: editForm.name || undefined,
        description: editForm.description || undefined,
        category: editForm.category || undefined,
        price: editForm.price ? Number(editForm.price) : undefined,
      });
      setProduct(updated);
      setEditing(false);
    } catch {
      setError("Не удалось сохранить изменения");
    }
  };

  const handleCancelEdit = () => setEditing(false);

  if (loading) {
    return (
      <div style={{ padding: "1.5rem", maxWidth: 800, margin: "0 auto" }}>
        <p>Загрузка...</p>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div style={{ padding: "1.5rem", maxWidth: 800, margin: "0 auto" }}>
        <button onClick={() => navigate(-1)} style={btnStyle}>
          ← Назад
        </button>
        <p style={{ color: "#c00", marginTop: "1rem" }}>{error ?? "Товар не найден"}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: 800, margin: "0 auto" }}>
      <button onClick={() => navigate(-1)} style={btnStyle}>
        ← Назад
      </button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
        <h1 style={{ marginTop: "1.5rem", margin: 0 }}>{product.name}</h1>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button onClick={handleEdit} style={{ ...btnStyle, background: "#333" }}>
            Редактировать
          </button>
          <button onClick={handleDelete} style={{ ...btnStyle, background: "#c00" }}>
            Удалить
          </button>
          <button
            onClick={() => navigate(`/products/${id}/generate`)}
            style={{ ...btnStyle, background: "#0066cc" }}
          >
            Создать контент
          </button>
          {hasContent && (
            <button
              onClick={() => navigate(`/products/${id}/content`)}
              style={{ ...btnStyle, background: "#28a745" }}
            >
              Просмотреть контент
            </button>
          )}
        </div>
      </div>

      {editing && (
        <section style={{ marginBottom: "1.5rem", padding: "1rem", border: "1px solid #ddd", borderRadius: 8 }}>
          <h3 style={{ marginTop: 0, marginBottom: "0.75rem" }}>Редактирование</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: 400 }}>
            <label>Название</label>
            <input
              value={editForm.name}
              onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
              style={{ padding: "0.5rem" }}
            />
            <label>Описание</label>
            <textarea
              value={editForm.description}
              onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              style={{ padding: "0.5rem" }}
            />
            <label>Категория</label>
            <input
              value={editForm.category}
              onChange={(e) => setEditForm((f) => ({ ...f, category: e.target.value }))}
              style={{ padding: "0.5rem" }}
            />
            <label>Цена</label>
            <input
              type="number"
              value={editForm.price}
              onChange={(e) => setEditForm((f) => ({ ...f, price: e.target.value }))}
              style={{ padding: "0.5rem" }}
            />
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
              <button onClick={handleSaveEdit} style={{ ...btnStyle, background: "#28a745" }}>
                Сохранить
              </button>
              <button onClick={handleCancelEdit} style={{ ...btnStyle, background: "#666" }}>
                Отмена
              </button>
            </div>
          </div>
        </section>
      )}

      <section style={{ marginBottom: "1.5rem" }}>
        <img
          src={getProductImageUrl(product)}
          alt={product.name}
          style={{
            maxWidth: "100%",
            maxHeight: 400,
            objectFit: "contain",
            borderRadius: 8,
            border: "1px solid #ddd",
          }}
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem", color: "#666" }}>
          Описание
        </h2>
        <p style={{ lineHeight: 1.6 }}>{product.description ?? "—"}</p>
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem", color: "#666" }}>
          Ссылка на маркетплейс
        </h2>
        {product.marketplace_url ? (
          <a
            href={product.marketplace_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#0066cc", textDecoration: "underline" }}
          >
            {product.marketplace_url}
          </a>
        ) : (
          <p>—</p>
        )}
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem", color: "#666" }}>
          Популярность (popularity_score)
        </h2>
        <p>{product.popularity_score ?? "—"}</p>
      </section>

    </div>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "0.5rem 1rem",
  background: "#666",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
};
