import { useState, useEffect } from "react";
import { socialApi, getErrorMessage, type PublicationStatusResponse } from "./api";

const statusLabels: Record<string, string> = {
  pending: "Ожидание",
  processing: "Публикация...",
  published: "Опубликовано",
  failed: "Ошибка",
};

interface PublicationStatusProps {
  publicationId: string;
  onClose?: () => void;
}

export function PublicationStatus({ publicationId, onClose }: PublicationStatusProps) {
  const [status, setStatus] = useState<PublicationStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let retryCount = 0;
    const maxRetries = 3;

    const poll = async () => {
      try {
        const data = await socialApi.getPublicationStatus(publicationId);
        if (cancelled) return;
        setStatus(data);
        setLoading(false);
        if (data.status === "published" || data.status === "failed") return;
        await new Promise((r) => setTimeout(r, 2000));
        if (!cancelled) poll();
      } catch (e) {
        if (cancelled) return;
        const msg = getErrorMessage(e);
        if (msg.includes("не найдена") && retryCount < maxRetries) {
          retryCount++;
          await new Promise((r) => setTimeout(r, 800));
          if (!cancelled) poll();
        } else {
          setError(msg);
          setLoading(false);
        }
      }
    };

    const timer = setTimeout(poll, 500);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [publicationId]);

  if (loading && !status) return <p style={{ color: "#666" }}>Загрузка статуса...</p>;
  if (error) return <p style={{ color: "#c00" }}>Ошибка: {error}</p>;
  if (!status) return null;

  const label = statusLabels[status.status] ?? status.status;

  return (
    <div
      style={{
        padding: "0.75rem",
        border: "1px solid #ddd",
        borderRadius: 8,
        marginTop: "0.5rem",
        background: status.status === "published" ? "#e8f5e9" : status.status === "failed" ? "#ffebee" : "#f5f5f5",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>
          <strong>{label}</strong>
          {status.platform_video_id && status.status === "published" && (
            <span style={{ marginLeft: 8, fontSize: 12, color: "#666" }}>
              ID: {status.platform_video_id}
            </span>
          )}
        </span>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              padding: "0.25rem 0.5rem",
              background: "transparent",
              border: "1px solid #999",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            Закрыть
          </button>
        )}
      </div>
      {status.error_message && (
        <p style={{ marginTop: "0.5rem", fontSize: 12, color: "#c00" }}>
          {status.error_message}
        </p>
      )}
    </div>
  );
}
