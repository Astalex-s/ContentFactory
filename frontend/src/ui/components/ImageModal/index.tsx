import React, { useEffect } from "react";
import { createPortal } from "react-dom";

interface ImageModalProps {
  src: string;
  alt?: string;
  onClose: () => void;
}

export const ImageModal: React.FC<ImageModalProps> = ({ src, alt = "", onClose }) => {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0,0,0,0.82)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        cursor: "zoom-out",
      }}
    >
      <img
        src={src}
        alt={alt}
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: "90vw",
          maxHeight: "90vh",
          objectFit: "contain",
          borderRadius: 8,
          boxShadow: "0 8px 40px rgba(0,0,0,0.6)",
          cursor: "default",
        }}
      />
      <button
        onClick={onClose}
        style={{
          position: "fixed",
          top: 20,
          right: 24,
          background: "rgba(255,255,255,0.15)",
          border: "none",
          color: "#fff",
          fontSize: 28,
          lineHeight: 1,
          width: 44,
          height: 44,
          borderRadius: "50%",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
        aria-label="Закрыть"
      >
        ×
      </button>
    </div>,
    document.body
  );
};
