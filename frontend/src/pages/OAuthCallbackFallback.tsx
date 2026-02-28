/**
 * Fallback page when OAuth callback accidentally hits the frontend instead of backend.
 * Shows helpful message and link to fix nginx/API_BASE_URL configuration.
 */
import { useParams, useNavigate } from "react-router-dom";
import { PageContainer } from "@/ui/layout/PageContainer";
import { Button } from "@/ui/components/Button";
import { Alert } from "@/ui/components/Alert";
import { spacing } from "@/ui/theme";

export function OAuthCallbackFallback() {
  const { platform } = useParams<{ platform: string }>();
  const navigate = useNavigate();

  return (
    <PageContainer>
      <Alert type="error" style={{ marginBottom: spacing.lg }}>
        <>
          <strong>Ошибка OAuth</strong>
          <p style={{ margin: "0.5rem 0 0", lineHeight: 1.5 }}>
            Callback авторизации попал на frontend вместо backend. Авторизация не выполнена.
          </p>
          <p style={{ margin: "0.5rem 0 0", fontSize: 14, opacity: 0.9 }}>
            Проверьте nginx: <code>location /social/callback/</code> → backend. Либо{" "}
            <code>API_BASE_URL=https://ваш-домен/api</code> и в Google Console redirect URI:{" "}
            <code>https://ваш-домен/api/social/callback/{platform || "youtube"}</code>
          </p>
        </>
      </Alert>
      <Button variant="primary" onClick={() => navigate("/creators")}>
        Перейти к соцсетям
      </Button>
    </PageContainer>
  );
}
