import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { TextInput } from "../../components/ui/TextInput";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../state/auth";

export function LoginScreen() {
  const { login } = useAuth();
  const loginCall = useAsync(login);
  const [username, setUsername] = useState("nguyenvana");
  const [password, setPassword] = useState("123456");

  async function submit() {
    await loginCall.run(username, password).catch(() => undefined);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-sm space-y-4">
        <Card title="BNPL Assistant — Đăng nhập">
          <div className="space-y-3">
            {loginCall.error && <ErrorBanner message={loginCall.error} />}
            <Field label="Tên đăng nhập">
              <TextInput
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </Field>
            <Field label="Mật khẩu">
              <TextInput
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <Button onClick={submit} disabled={loginCall.loading} className="w-full">
              {loginCall.loading ? "Đang đăng nhập…" : "Đăng nhập"}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
