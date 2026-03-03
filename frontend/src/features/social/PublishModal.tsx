import { useState, useEffect } from "react";
import { socialApi, getErrorMessage } from "./api";
import { useSocialAccounts } from "./useSocialAccounts";
import { contentApi, type GeneratedContentItem } from "@/features/content";
import { apiBaseURL } from "@/services/api";

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isValidUuid(v: unknown): v is string {
  return typeof v === "string" && v.length > 0 && UUID_REGEX.test(v);
}

const platformLabels: Record<string, string> = {
  youtube: "YouTube",
  vk: "VK",
};

const contentTextTypeLabels: Record<string, string> = {
  short_post: "Короткий пост",
  video_description: "Описание видео",
  cta: "Призыв к действию",
  all: "Все",
};

export type PublishMode = "video" | "text";

interface VideoItem {
  id: string;
  file_path: string | null;
  content_variant?: number;
}

interface PublishModalProps {
  mode: PublishMode;
  contentId?: string;
  productId: string;
  productName: string;
  textContentItems: GeneratedContentItem[];
  videos?: VideoItem[];
  onClose: () => void;
  onPublished?: (publicationId: string) => void;
}

function getVideoUrl(filePath: string): string {
  return `${apiBaseURL}/content/media/${filePath}`;
}

export function PublishModal({
  mode,
  contentId,
  productId,
  productName,
  textContentItems,
  videos = [],
  onClose,
  onPublished,
}: PublishModalProps) {
  const { accounts } = useSocialAccounts();
  const [platform, setPlatform] = useState<string>(mode === "text" ? "vk" : "");
  const [accountId, setAccountId] = useState<string>("");
  const [title, setTitle] = useState<string>("");
  const [postText, setPostText] = useState<string>("");
  const [selectedVideoId, setSelectedVideoId] = useState<string>("");
  const [descriptionContentId, setDescriptionContentId] = useState<string>("");
  const [privacyStatus, setPrivacyStatus] = useState<"private" | "public" | "unlisted">("private");
  const [loading, setLoading] = useState(false);
  const [generateTitleLoading, setGenerateTitleLoading] = useState(false);
  const [generatePostLoading, setGeneratePostLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTitle(productName || "");
  }, [productName]);

  const videoAccounts = accounts.filter(
    (a) =>
      isValidUuid(a?.id) &&
      (a.platform === "youtube" || a.platform === "vk")
  );
  const platforms =
    mode === "text"
      ? ["vk"]
      : [...new Set(videoAccounts.map((a) => a.platform))];

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
          <p>Подключите YouTube или VK для публикации.</p>
          <button onClick={onClose} style={{ padding: "0.5rem 1rem", marginTop: "0.5rem" }}>
            Закрыть
          </button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!platform || !accountId) return;

    const aid = typeof accountId === "string" ? accountId.trim() : "";
    if (!aid || aid === "undefined" || aid === "null" || !isValidUuid(aid)) {
      setError("Выберите аккаунт для публикации.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let cid: string;

      if (mode === "text") {
        if (!title.trim() || !postText.trim()) {
          setError("Заполните заголовок и текст поста.");
          setLoading(false);
          return;
        }
        const videoUrl =
          selectedVideoId && videos.length > 0
            ? (() => {
                const v = videos.find((x) => x.id === selectedVideoId);
                return v?.file_path ? getVideoUrl(v.file_path) : undefined;
              })()
            : undefined;
        const created = await contentApi.createPostText(productId, {
          title: title.trim(),
          text: postText.trim(),
          video_url: videoUrl,
        });
        cid = created.id;
      } else {
        cid = typeof contentId === "string" ? contentId.trim() : "";
        if (!cid || cid === "undefined" || cid === "null" || !isValidUuid(cid)) {
          setError("Выберите видео. Если ошибка повторяется — обновите страницу.");
          setLoading(false);
          return;
        }
      }

      const descriptionItem =
        descriptionContentId && mode === "video"
          ? textContentItems.find((c) => c.id === descriptionContentId)
          : null;
      const description = descriptionItem?.content_text ?? "";

      const res = await socialApi.schedulePublication(cid, {
        platform,
        account_id: aid,
        title: mode === "video" ? title.trim() : undefined,
        description: mode === "video" ? (description || undefined) : undefined,
        privacy_status: platform === "youtube" ? privacyStatus : undefined,
      });
      onPublished?.(res.id);
      onClose();
    } catch (e) {
      const msg = getErrorMessage(e);
      setError(
        msg.includes("account_id") || msg.includes("аккаунт")
          ? "Выберите аккаунт для публикации."
          : msg.includes("content") || msg.includes("контент") || msg.includes("content_id")
            ? "Выберите видео. Если ошибка повторяется — обновите страницу."
            : msg.includes("platform") || msg.includes("платформ")
              ? "Выберите платформу."
              : msg
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePostText = async () => {
    setGeneratePostLoading(true);
    setError(null);
    try {
      const videoUrl =
        selectedVideoId && videos.length > 0
          ? (() => {
              const v = videos.find((x) => x.id === selectedVideoId);
              return v?.file_path ? getVideoUrl(v.file_path) : undefined;
            })()
          : undefined;
      const { title: t, text } = await contentApi.generatePostText(productId, videoUrl);
      setTitle(t);
      setPostText(text);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setGeneratePostLoading(false);
    }
  };

  const isVideoValid = mode === "video" && contentId && isValidUuid(contentId);
  const isTextValid = mode === "text" && title.trim() && postText.trim();
  const canSubmit =
    platform &&
    accountId &&
    (mode === "video" ? isVideoValid && title.trim() : isTextValid);

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
          maxWidth: 480,
          width: "90%",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>
          {mode === "text" ? "Опубликовать пост (VK)" : "Опубликовать видео"}
        </h3>
        <form onSubmit={handleSubmit}>
          {mode === "text" && videos.length > 0 && (
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
                Ссылка на видео в посте
              </label>
              <select
                value={selectedVideoId}
                onChange={(e) => setSelectedVideoId(e.target.value)}
                style={{ width: "100%", padding: "0.5rem" }}
              >
                <option value="">— Без ссылки —</option>
                {videos.map((v, idx) => (
                  <option key={v.id} value={v.id}>
                    Видео {v.content_variant ?? idx + 1}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
              {mode === "text" ? "Заголовок поста" : "Заголовок видео"}{" "}
              <span style={{ color: "#c00" }}>*</span>
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={
                  mode === "text"
                    ? "Заголовок поста"
                    : "Название товара или сгенерированный заголовок"
                }
                maxLength={mode === "text" ? 200 : 100}
                required
                style={{
                  flex: 1,
                  padding: "0.5rem",
                  boxSizing: "border-box",
                }}
              />
              {mode === "video" ? (
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
              ) : (
                <button
                  type="button"
                  onClick={handleGeneratePostText}
                  disabled={generatePostLoading}
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: generatePostLoading ? "#999" : "#0066cc",
                    color: "#fff",
                    border: "none",
                    borderRadius: 6,
                    cursor: generatePostLoading ? "default" : "pointer",
                    fontSize: 13,
                    whiteSpace: "nowrap",
                  }}
                >
                  {generatePostLoading ? "..." : "Сгенерировать"}
                </button>
              )}
            </div>
          </div>

          {mode === "text" && (
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
                Текст поста <span style={{ color: "#c00" }}>*</span>
              </label>
              <textarea
                value={postText}
                onChange={(e) => setPostText(e.target.value)}
                placeholder="Текст поста для VK"
                rows={4}
                maxLength={2000}
                required
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  boxSizing: "border-box",
                  resize: "vertical",
                }}
              />
            </div>
          )}

          {mode === "video" && textContentItems.length > 0 && (
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

          {platform === "youtube" && mode === "video" && (
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
                <option value="private">Ограничен (только вы)</option>
                <option value="unlisted">По ссылке (не в поиске)</option>
                <option value="public">Доступен всем</option>
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
              disabled={loading || !canSubmit}
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
