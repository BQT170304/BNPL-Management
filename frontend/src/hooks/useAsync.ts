// frontend/src/hooks/useAsync.ts
import { useCallback, useState } from "react";
import { ApiError } from "../api/client";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useAsync<TArgs extends unknown[], TData>(
  fn: (...args: TArgs) => Promise<TData>,
) {
  const [state, setState] = useState<AsyncState<TData>>({
    data: null,
    loading: false,
    error: null,
  });

  const run = useCallback(
    async (...args: TArgs): Promise<TData> => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const data = await fn(...args);
        setState({ data, loading: false, error: null });
        return data;
      } catch (err) {
        const message =
          err instanceof ApiError ? err.detail : "Đã xảy ra lỗi không xác định";
        setState((s) => ({ ...s, loading: false, error: message }));
        throw err;
      }
    },
    [fn],
  );

  return { ...state, run };
}
