import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { productsService } from "@/services/products";
import type { Product } from "@/types/product";

export function ProductDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const handleGenerateContent = () => {
    // Заглушка — без AI логики
    alert("Сгенерировать контент (функция будет реализована позже)");
  };

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
        <button
          onClick={() => navigate(-1)}
          style={btnStyle}
        >
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

      <h1 style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>{product.name}</h1>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem", color: "#666" }}>
          Описание
        </h2>
        <p style={{ lineHeight: 1.6 }}>
          {product.description ?? "—"}
        </p>
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

      <button
        onClick={handleGenerateContent}
        style={{
          ...btnStyle,
          background: "#333",
          color: "#fff",
          padding: "0.75rem 1.5rem",
        }}
      >
        Сгенерировать контент
      </button>
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
