import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type AnchorHTMLAttributes,
  type ReactNode,
} from "react";

/**
 * Zero-dependency client router (history API). Avoids react-router-dom, which
 * is blocked on this network. Supports the handful of routes we need, with a
 * Link component and programmatic navigate().
 */
type RouterCtx = { path: string; navigate: (to: string) => void };
const Ctx = createContext<RouterCtx>({ path: "/", navigate: () => {} });

export function RouterProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [path, setPath] = useState(() => globalThis.location.pathname || "/");

  useEffect(() => {
    const onPop = () => setPath(globalThis.location.pathname || "/");
    globalThis.addEventListener("popstate", onPop);
    return () => globalThis.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((to: string) => {
    if (to === globalThis.location.pathname) return;
    globalThis.history.pushState({}, "", to);
    setPath(to);
    globalThis.scrollTo({ top: 0, behavior: "auto" });
  }, []);

  const value = useMemo(() => ({ path, navigate }), [path, navigate]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useRouter() {
  return useContext(Ctx);
}

/** Anchor that navigates client-side (falls back to normal nav on modified click). */
export function Link({
  to,
  className,
  children,
  ...rest
}: Readonly<
  {
    to: string;
    className?: string;
    children: ReactNode;
  } & AnchorHTMLAttributes<HTMLAnchorElement>
>) {
  const { navigate } = useRouter();
  return (
    <a
      href={to}
      className={className}
      onClick={(e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        navigate(to);
      }}
      {...rest}
    >
      {children}
    </a>
  );
}


