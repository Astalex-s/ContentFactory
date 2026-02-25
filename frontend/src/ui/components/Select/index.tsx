import React from "react";
import { colors, radius, spacing, shadows } from "../../theme";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  fullWidth,
  style,
  children,
  ...props
}) => {
  return (
    <div style={{ width: fullWidth ? "100%" : "auto" }}>
      {label && (
        <label
          style={{
            display: "block",
            marginBottom: 4,
            fontSize: "14px",
            fontWeight: 500,
            color: colors.gray[700],
          }}
        >
          {label}
        </label>
      )}
      <select
        style={{
          padding: "10px 12px",
          borderRadius: radius.sm,
          border: `1px solid ${error ? colors.danger : colors.gray[300]}`,
          backgroundColor: colors.white,
          fontSize: "14px",
          width: "100%",
          boxShadow: shadows.input,
          outline: "none",
          cursor: props.disabled ? "not-allowed" : "pointer",
          opacity: props.disabled ? 0.7 : 1,
          height: "42px",
          ...style,
        }}
        {...props}
      >
        {children}
      </select>
      {error && (
        <div style={{ marginTop: spacing.xs, fontSize: "12px", color: colors.danger }}>
          {error}
        </div>
      )}
    </div>
  );
};
