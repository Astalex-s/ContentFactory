/**
 * Button to trigger content generation.
 */
import React from "react";
import type { Platform, Tone } from "./api";

interface GenerateButtonProps {
  onClick: (platform: Platform, tone: Tone) => void;
  loading: boolean;
  disabled?: boolean;
}

const platformOptions: { value: Platform; label: string }[] = [
  { value: "youtube", label: "YouTube" },
  { value: "vk", label: "ВКонтакте" },
  { value: "tiktok", label: "TikTok" },
];

const toneOptions: { value: Tone; label: string }[] = [
  { value: "neutral", label: "Нейтральный" },
  { value: "emotional", label: "Эмоциональный" },
  { value: "expert", label: "Экспертный" },
];

export function GenerateButton({
  onClick,
  loading,
  disabled = false,
}: GenerateButtonProps) {
  const [platform, setPlatform] = React.useState<Platform>("youtube");
  const [tone, setTone] = React.useState<Tone>("emotional");

  const handleClick = () => {
    onClick(platform, tone);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.9rem", color: "#666" }}>Платформа:</span>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value as Platform)}
            disabled={loading || disabled}
            style={{
              padding: "0.35rem 0.5rem",
              borderRadius: 6,
              border: "1px solid #ccc",
            }}
          >
            {platformOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.9rem", color: "#666" }}>Тон:</span>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value as Tone)}
            disabled={loading || disabled}
            style={{
              padding: "0.35rem 0.5rem",
              borderRadius: 6,
              border: "1px solid #ccc",
            }}
          >
            {toneOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <button
        onClick={handleClick}
        disabled={loading || disabled}
        style={{
          padding: "0.75rem 1.5rem",
          background: loading ? "#999" : "#333",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          cursor: loading || disabled ? "not-allowed" : "pointer",
          alignSelf: "flex-start",
        }}
      >
        {loading ? "Генерация..." : "Сгенерировать контент"}
      </button>
    </div>
  );
}
