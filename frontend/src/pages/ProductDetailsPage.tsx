import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiBaseURL } from "@/services/api";
import { productsService } from "@/services/products";
import { contentApi } from "@/features/content";
import type { Product } from "@/types/product";
import { PageContainer } from "@/ui/layout/PageContainer";
import { Button } from "@/ui/components/Button";
import { Card } from "@/ui/components/Card";
import { Loader } from "@/ui/components/Loader";
import { Alert } from "@/ui/components/Alert";
import { spacing } from "@/ui/theme";
import { ImageModal } from "@/ui/components/ImageModal";

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
  const [modalOpen, setModalOpen] = useState(false);
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
      <PageContainer>
        <Loader />
      </PageContainer>
    );
  }

  if (error || !product) {
    return (
      <PageContainer>
        <Button variant="ghost" onClick={() => navigate(-1)} style={{ marginBottom: spacing.md }}>
          ← Назад
        </Button>
        <Alert type="error">{error ?? "Товар не найден"}</Alert>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <Button variant="ghost" onClick={() => navigate(-1)} style={{ marginBottom: spacing.md }}>
        ← Назад
      </Button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: spacing.md, marginBottom: spacing.lg }}>
        <h1 style={{ margin: 0 }}>{product.name}</h1>
        <div style={{ display: "flex", gap: spacing.sm, flexWrap: "wrap" }}>
          <Button variant="secondary" onClick={handleEdit}>
            Редактировать
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Удалить
          </Button>
          <Button variant="primary" onClick={() => navigate(`/products/${id}/generate`)}>
            Создать контент
          </Button>
          {hasContent && (
            <Button variant="outline" onClick={() => navigate(`/products/${id}/content`)}>
              Просмотреть контент
            </Button>
          )}
        </div>
      </div>

      {editing && (
        <Card title="Редактирование" style={{ marginBottom: spacing.lg }}>
          <div style={{ display: "flex", flexDirection: "column", gap: spacing.md, maxWidth: 400 }}>
            <div>
              <label style={{ display: "block", marginBottom: 4 }}>Название</label>
              <input
                value={editForm.name}
                onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                style={{ padding: "8px", width: "100%", border: "1px solid #ddd", borderRadius: 6 }}
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 4 }}>Описание</label>
              <textarea
                value={editForm.description}
                onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                rows={3}
                style={{ padding: "8px", width: "100%", border: "1px solid #ddd", borderRadius: 6 }}
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 4 }}>Категория</label>
              <input
                value={editForm.category}
                onChange={(e) => setEditForm((f) => ({ ...f, category: e.target.value }))}
                style={{ padding: "8px", width: "100%", border: "1px solid #ddd", borderRadius: 6 }}
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 4 }}>Цена</label>
              <input
                type="number"
                value={editForm.price}
                onChange={(e) => setEditForm((f) => ({ ...f, price: e.target.value }))}
                style={{ padding: "8px", width: "100%", border: "1px solid #ddd", borderRadius: 6 }}
              />
            </div>
            <div style={{ display: "flex", gap: spacing.sm }}>
              <Button variant="primary" onClick={handleSaveEdit}>
                Сохранить
              </Button>
              <Button variant="secondary" onClick={handleCancelEdit}>
                Отмена
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: spacing.lg }}>
        <div>
          <img
            src={getProductImageUrl(product)}
            alt={product.name}
            onClick={() => setModalOpen(true)}
            style={{
              width: "100%",
              maxHeight: 400,
              objectFit: "contain",
              borderRadius: 8,
              border: "1px solid #ddd",
              backgroundColor: "#fff",
              cursor: "zoom-in",
            }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          {modalOpen && (
            <ImageModal
              src={getProductImageUrl(product)}
              alt={product.name}
              onClose={() => setModalOpen(false)}
            />
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: spacing.lg }}>
          <Card title="Описание">
            <p style={{ lineHeight: 1.6 }}>{product.description ?? "—"}</p>
          </Card>

          <Card title="Детали">
            <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
              <div>
                <strong>Категория:</strong> {product.category ?? "—"}
              </div>
              <div>
                <strong>Цена:</strong> {product.price ? `${product.price} ₽` : "—"}
              </div>
              <div>
                <strong>Популярность:</strong> {product.popularity_score ?? "—"}
              </div>
              <div>
                <strong>Ссылка:</strong>{" "}
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
                  "—"
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}
