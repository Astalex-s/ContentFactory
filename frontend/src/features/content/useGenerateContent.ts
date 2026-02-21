/**
 * Hook for content generation with loading, error handling, regenerate.
 */
import { useState, useCallback } from "react";
import { contentApi } from "./api";
import type {
  ContentTextType,
  GenerateContentResponse,
  Platform,
  Tone,
} from "./api";

interface UseGenerateContentState {
  data: GenerateContentResponse | null;
  loading: boolean;
  error: string | null;
}

export function useGenerateContent(productId: string | undefined) {
  const [state, setState] = useState<UseGenerateContentState>({
    data: null,
    loading: false,
    error: null,
  });

  const generate = useCallback(
    async (
      platform: Platform,
      tone: Tone,
      contentTextType: ContentTextType = "short_post"
    ) => {
      if (!productId) return;

      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const data = await contentApi.generate(productId, {
          platform,
          tone,
          content_text_type: contentTextType,
        });
        setState({ data, loading: false, error: null });
        return data;
      } catch (err: unknown) {
        const message =
          err && typeof err === "object" && "response" in err
            ? (err as { response?: { data?: { detail?: string } } }).response
                ?.data?.detail ?? "Ошибка генерации контента"
            : "Ошибка генерации контента";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: message,
        }));
        throw err;
      }
    },
    [productId]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    generate,
    reset,
  };
}
