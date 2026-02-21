/**
 * Preview of generated content variants with radio selection.
 */
import type { GeneratedVariant } from "./api";

interface ContentPreviewProps {
  variants: GeneratedVariant[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRegenerate: () => void;
  loading: boolean;
}

export function ContentPreview({
  variants,
  selectedId,
  onSelect,
  onRegenerate,
  loading,
}: ContentPreviewProps) {
  if (variants.length === 0) return null;

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ fontSize: "1rem", margin: 0, color: "#666" }}>
          Варианты текста
        </h2>
        <button
          onClick={onRegenerate}
          disabled={loading}
          style={{
            padding: "0.4rem 0.8rem",
            background: "transparent",
            color: "#0066cc",
            border: "1px solid #0066cc",
            borderRadius: 6,
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "0.9rem",
          }}
        >
          {loading ? "Генерация..." : "Сгенерировать заново"}
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {variants.map((v) => (
          <label
            key={v.id}
            style={{
              display: "flex",
              gap: "0.75rem",
              padding: "1rem",
              border: selectedId === v.id ? "2px solid #333" : "1px solid #ddd",
              borderRadius: 8,
              cursor: "pointer",
              background: selectedId === v.id ? "#f8f8f8" : "#fff",
            }}
          >
            <input
              type="radio"
              name="content-variant"
              value={v.id}
              checked={selectedId === v.id}
              onChange={() => onSelect(v.id)}
              style={{ marginTop: "0.25rem" }}
            />
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: "0.85rem",
                  color: "#888",
                  marginBottom: "0.25rem",
                }}
              >
                Вариант {v.variant}
              </div>
              <pre
                style={{
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  fontFamily: "inherit",
                  fontSize: "0.95rem",
                  lineHeight: 1.5,
                }}
              >
                {v.text}
              </pre>
            </div>
          </label>
        ))}
      </div>
    </section>
  );
}
