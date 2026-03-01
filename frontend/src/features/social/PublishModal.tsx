import { useState, useEffect } from "react";
import { socialApi, getErrorMessage } from "./api";
import { useSocialAccounts } from "./useSocialAccounts";
import { contentApi, type GeneratedContentItem } from "@/features/content";

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isValidUuid(v: unknown): v is string {
  return typeof v === "string" && v.length > 0 && UUID_REGEX.test(v);
}

const platformLabels: Record<string, string> = {
  youtube: "YouTube",
  vk: "VK",
  tiktok: "TikTok",
};

const contentTextTypeLabels: Record<string, string> = {
  short_post: "Короткий пост",
  video_description: "Описание видео",
  cta: "Призыв к действию",
  all: "Все",
};

interface PublishModalProps {
  contentId: string;
  productId: string;
  productName: string;
  textContentItems: GeneratedContentItem[];
  onClose: () => void;
  onPublished?: (publicationId: string) => void;
}

export function PublishModal({
  contentId,
  productId,
  productName,
  textContentItems,
  onClose,
  onPublished,
}: PublishModalProps) {
  const { accounts } = useSocialAccounts();
  const [platform, setPlatform] = useState<string>("");
  const [accountId, setAccountId] = useState<string>("");
  const [title, setTitle] = useState<string>("");
  const [descriptionContentId, setDescriptionContentId] = useState<string>("");
  const [privacyStatus, setPrivacyStatus] = useState<"private" | "public" | "unlisted">("private");
  const [loading, setLoading] = useState(false);
  const [generateTitleLoading, setGenerateTitleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTitle(productName || "");
  }, [productName]);

  const videoAccounts = accounts.filter(
    (a) =>
      isValidUuid(a?.id) &&
      (a.platform === "youtube" || a.platform === "vk")
  );
  const platforms = [...new Set(videoAccounts.map((a) => a.platform))];

  if (videoAccounts.length === 0) {
    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
        }}
        onClick={onClose}
      >
        <div
          style={{
            background: "#fff",
            padding: "1.5rem",
            borderRadius: 8,
            maxWidth: 400,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <p>Подключите YouTube или VK для публикации видео.</p>
          <button onClick={onClose} style={{ padding: "0.5rem 1rem", marginTop: "0.5rem" }}>
            Закрыть
          </button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!platform || !accountId || !title.trim()) return;
    const cid = typeof contentId === "string" ? contentId.trim() : "";
    if (!cid || cid === "undefined" || cid === "null" || !isValidUuid(cid)) {
      setError("Выберите видео. Если ошибка повторяется — обновите страницу.");
      return;
    }
    const aid = typeof accountId === "string" ? accountId.trim() : "";
    if (!aid || aid === "undefined" || aid === "null" || !isValidUuid(aid)) {
      setError("Выберите аккаунт (YouTube или VK) для публикации.");
      return;
    }
    const descriptionItem = descriptionContentId
      ? textContentItems.find((c) => c.id === descriptionContentId)
      : null;
    const description = descriptionItem?.content_text ?? "";
    setLoading(true);
    setError(null);
    try {
      const res = await socialApi.schedulePublication(cid, {
        platform,
        account_id: aid,
        title: title.trim(),
        description: description || undefined,
        privacy_status: platform === "youtube" ? privacyStatus : undefined,
      });
      onPublished?.(res.id);
      onClose();
    } catch (e) {
      const msg = getErrorMessage(e);
      setError(
        msg.includes("account_id") || msg.includes("аккаунт")
          ? "Выберите аккаунт (YouTube или VK) для публикации."
          : msg.includes("content") || msg.includes("контент") || msg.includes("content_id")
            ? "Выберите видео. Если ошибка повторяется — обновите страницу."
            : msg.includes("platform") || msg.includes("платформ")
              ? "Выберите платформу (YouTube или VK)."
              : msg
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#fff",
          padding: "1.5rem",
          borderRadius: 8,
          maxWidth: 400,
          width: "90%",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>Опубликовать видео</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
              Заголовок видео <span style={{ color: "#c00" }}>*</span>
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Название товара или сгенерированный заголовок"
                maxLength={100}
                required
                style={{
                  flex: 1,
                  padding: "0.5rem",
                  boxSizing: "border-box",
                }}
              />
              <button
                type="button"
                onClick={async () => {
                  setGenerateTitleLoading(true);
                  setError(null);
                  try {
                    const generated = await contentApi.generateVideoTitle(productId);
                    setTitle(generated);
                  } catch (e) {
                    setError(getErrorMessage(e));
                  } finally {
                    setGenerateTitleLoading(false);
                  }
                }}
                disabled={generateTitleLoading}
                style={{
                  padding: "0.5rem 0.75rem",
                  background: generateTitleLoading ? "#999" : "#0066cc",
                  color: "#fff",
                  border: "none",
                  borderRadius: 6,
                  cursor: generateTitleLoading ? "default" : "pointer",
                  fontSize: 13,
                  whiteSpace: "nowrap",
                }}
              >
                {generateTitleLoading ? "..." : "Сгенерировать"}
              </button>
            </div>
          </div>
          {textContentItems.length > 0 && (
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
                Текст для описания
              </label>
              <select
                value={descriptionContentId}
                onChange={(e) => setDescriptionContentId(e.target.value)}
                style={{ width: "100%", padding: "0.5rem" }}
              >
                <option value="">— Не использовать —</option>
                {textContentItems.map((item) => (
                  <option key={item.id} value={item.id}>
                    {contentTextTypeLabels[item.content_text_type] ?? item.content_text_type} •{" "}
                    {item.platform} • вариант {item.content_variant}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
              Платформа
            </label>
            <select
              value={platform}
              onChange={(e) => {
                setPlatform(e.target.value);
                setAccountId("");
              }}
              required
              style={{ width: "100%", padding: "0.5rem" }}
            >
              <option value="">Выберите</option>
              {platforms.map((p) => (
                <option key={p} value={p}>
                  {platformLabels[p] ?? p}
                </option>
              ))}
            </select>
          </div>
          {platform === "youtube" && (
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
                Доступ к видео
              </label>
              <select
                value={privacyStatus}
                onChange={(e) =>
                  setPrivacyStatus(e.target.value as "private" | "public" | "unlisted")
                }
                style={{ width: "100%", padding: "0.5rem" }}
              >
                <option value="private">Приватный (только вы)</option>
                <option value="unlisted">По ссылке (не в поиске)</option>
                <option value="public">Публичный (без ограничений)</option>
              </select>
            </div>
          )}
          {platform && (
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
                Аккаунт
              </label>
              <select
                value={accountId}
                onChange={(e) => {
                  const v = (e.target.value ?? "").trim();
                  setAccountId(v === "undefined" || v === "null" ? "" : v);
                }}
                required
                style={{ width: "100%", padding: "0.5rem" }}
              >
                <option value="">Выберите</option>
                {videoAccounts
                  .filter((a) => a.platform === platform && a.id && isValidUuid(a.id))
                  .map((a) => {
                    const label = platformLabels[a.platform] ?? a.platform;
                    const channelLabel = a.channel_title
                      ? `${label}: ${a.channel_title}`
                      : label;
                    return (
                      <option key={a.id} value={String(a.id)}>
                        {channelLabel}
                      </option>
                    );
                  })}
              </select>
            </div>
          )}
          {error && (
            <p style={{ color: "#c00", fontSize: 14, marginBottom: "0.5rem" }}>
              {error}
            </p>
          )}
          <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: "0.5rem 1rem",
                background: "#666",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
              }}
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading || !platform || !accountId || !title.trim()}
              style={{
                padding: "0.5rem 1rem",
                background: loading ? "#999" : "#28a745",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                cursor: loading ? "default" : "pointer",
              }}
            >
              {loading ? "Публикация..." : "Опубликовать"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
