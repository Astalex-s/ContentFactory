import React from "react";
import { radius, spacing } from "../../theme";

export interface AlertProps {
  type?: "success" | "warning" | "error" | "info";
  variant?: "success" | "warning" | "error" | "info";
  title?: string;
  children: React.ReactNode;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const Alert: React.FC<AlertProps> = ({
  type,
  variant,
  title,
  children,
  onClick,
  style,
}) => {
  const alertType = variant || type || "info";
  const styles = {
    success: { bg: "#F0FDF4", border: "#BBF7D0", text: "#166534" },
    warning: { bg: "#FFFBEB", border: "#FDE68A", text: "#92400E" },
    error: { bg: "#FEF2F2", border: "#FECACA", text: "#991B1B" },
    info: { bg: "#EFF6FF", border: "#BFDBFE", text: "#1E40AF" },
  };

  const currentStyle = styles[alertType];

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: currentStyle.bg,
        border: `1px solid ${currentStyle.border}`,
        color: currentStyle.text,
        padding: spacing.md,
        borderRadius: radius.md,
        marginBottom: spacing.md,
        cursor: onClick ? "pointer" : "default",
        ...style,
      }}
    >
      {title && <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>}
      <div style={{ fontSize: "14px" }}>{children}</div>
    </div>
  );
};
