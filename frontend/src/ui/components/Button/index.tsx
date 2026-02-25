import React from "react";
import { colors, radius, spacing } from "../../theme";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  fullWidth?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  fullWidth = false,
  iconLeft,
  iconRight,
  style,
  disabled,
  ...props
}) => {
  const baseStyles: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    borderRadius: radius.sm,
    fontWeight: 500,
    cursor: disabled || loading ? "not-allowed" : "pointer",
    opacity: disabled || loading ? 0.6 : 1,
    border: "1px solid transparent",
    transition: "all 0.2s ease-in-out",
    width: fullWidth ? "100%" : "auto",
    fontFamily: "inherit",
    ...style,
  };

  const sizeStyles = {
    sm: { padding: "6px 12px", fontSize: "12px" },
    md: { padding: "8px 16px", fontSize: "14px" },
    lg: { padding: "12px 24px", fontSize: "16px" },
  };

  const variantStyles = {
    primary: {
      backgroundColor: colors.primary[500],
      color: colors.white,
      borderColor: colors.primary[500],
    },
    secondary: {
      backgroundColor: colors.gray[100],
      color: colors.gray[900],
      borderColor: colors.gray[200],
    },
    outline: {
      backgroundColor: "transparent",
      color: colors.gray[700],
      borderColor: colors.gray[300],
    },
    danger: {
      backgroundColor: colors.danger,
      color: colors.white,
      borderColor: colors.danger,
    },
    ghost: {
      backgroundColor: "transparent",
      color: colors.gray[700],
      borderColor: "transparent",
    },
  };

  return (
    <button
      style={{ ...baseStyles, ...sizeStyles[size], ...variantStyles[variant] }}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span style={{ marginRight: 8 }}>...</span>}
      {!loading && iconLeft}
      {children}
      {!loading && iconRight}
    </button>
  );
};
