import { useMemo } from "react";

/**
 * Lightweight, dependency-free syntax highlighter.
 *
 * Tokenizes a few common languages (python, js/ts, html, yaml, json, markdown)
 * with regex and wraps matches in colored spans. It is intentionally small —
 * good enough for a beautiful demo without pulling in a heavy highlighter lib.
 */

type Token = { text: string; cls: string };

const COLORS: Record<string, string> = {
  comment: "text-slate-500 italic",
  string: "text-emerald-300",
  number: "text-amber-300",
  keyword: "text-violet-300 font-medium",
  function: "text-sky-300",
  tag: "text-rose-300",
  attr: "text-amber-200",
  heading: "text-brand-300 font-semibold",
};

// IMPORTANT: highlighting tokenizes first, then wraps each token EXACTLY ONCE.
// Never run another regex over already-injected <span> markup, or the number /
// attribute regexes match digits inside Tailwind class names (e.g. the "300" in
// text-violet-300) and corrupt the HTML — which leaked stray `300">` text.
const KEYWORD_SET = new Set(
  (
    // Python
    "def class return import from as if elif else for while try except finally raise " +
    "with async await lambda yield pass break continue in is not and or None True False self " +
    // JS / TS
    "const let var function export default new typeof interface type extends implements " +
    "public private protected void null undefined this super readonly enum namespace " +
    "static get set keyof as satisfies declare module " +
    // Go
    "func struct map range chan go defer select package var const fallthrough goto " +
    // Rust
    "fn impl trait mut pub use mod crate where dyn move ref match loop unsafe " +
    "Some None Ok Err Option Result Box Vec String " +
    // Java / C# / C / C++
    "abstract final synchronized volatile transient native throws switch case instanceof " +
    "using override virtual sealed partial namespace struct template typename include " +
    "int long short double float boolean char byte unsigned signed bool string " +
    // Ruby
    "end module require do nil unless until elsif when then begin rescue ensure attr_accessor " +
    // PHP
    "echo foreach elseif endif endforeach use trait " +
    // Kotlin / Swift
    "fun val when object companion data suspend init deinit guard protocol extension " +
    // common
    "throw catch finally"
  ).split(" ")
);

// Normalize incoming language labels/aliases to a small canonical set the
// highlighter understands. Unknown languages still render (as plain code) fine.
const LANG_ALIASES: Record<string, string> = {
  js: "javascript", jsx: "javascript", mjs: "javascript", cjs: "javascript",
  ts: "typescript", tsx: "typescript",
  py: "python", rb: "ruby", rs: "rust", kt: "kotlin", "c#": "csharp", cs: "csharp",
  "c++": "cpp", cxx: "cpp", cc: "cpp", hpp: "cpp", golang: "go", yml: "yaml",
  sh: "bash", shell: "bash", zsh: "bash", ps1: "powershell",
  htm: "html", xml: "markup", vue: "markup", svelte: "markup",
  md: "markdown", txt: "text",
};
function normLang(language: string): string {
  const l = (language || "").toLowerCase();
  return LANG_ALIASES[l] ?? l;
}

// Languages whose line comments start with `#` vs `//`.
const HASH_COMMENT = new Set([
  "python", "yaml", "bash", "ruby", "perl", "r", "toml", "ini", "makefile", "dockerfile",
]);
const SLASH_COMMENT = new Set([
  "javascript", "typescript", "java", "go", "rust", "csharp", "cpp", "c", "php",
  "kotlin", "swift", "scala", "dart", "graphql", "css", "scss", "less",
]);

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const wrap = (cls: string, t: string) => `<span class="${cls}">${escapeHtml(t)}</span>`;

function nextIsParen(parts: string[], i: number): boolean {
  for (let j = i + 1; j < parts.length; j++) {
    if (/^\s+$/.test(parts[j])) continue;
    return parts[j][0] === "(";
  }
  return false;
}

/** Highlight a fragment of code that contains NO markup (wrap once per token). */
function hlCode(frag: string): string {
  const parts = frag.match(/[A-Za-z_$][\w$]*|\d[\w.]*|\s+|[^\sA-Za-z0-9_$]+/g) || [];
  let out = "";
  for (let i = 0; i < parts.length; i++) {
    const t = parts[i];
    if (/^[A-Za-z_$]/.test(t)) {
      if (KEYWORD_SET.has(t)) out += wrap(COLORS.keyword, t);
      else if (nextIsParen(parts, i)) out += wrap(COLORS.function, t);
      else out += escapeHtml(t);
    } else if (/^\d/.test(t)) {
      out += wrap(COLORS.number, t);
    } else {
      out += escapeHtml(t);
    }
  }
  return out;
}

/** Highlight a single raw HTML tag ("<...>"), escaping each piece once. */
function hlTag(tag: string): string {
  const parts = tag.match(/<\/?|\/?>|"[^"]*"|'[^']*'|[A-Za-z_:][\w:.-]*|\s+|[^\s]/g) || [];
  let out = "";
  let sawAngle = false;
  let named = false;
  for (const t of parts) {
    if (t === "<" || t === "</") {
      out += wrap("text-slate-500", t);
      sawAngle = true;
      named = false;
    } else if (t === ">" || t === "/>") {
      out += wrap("text-slate-500", t);
      sawAngle = false;
    } else if (/^["']/.test(t)) {
      out += wrap(COLORS.string, t);
    } else if (/^[A-Za-z_:]/.test(t)) {
      if (sawAngle && !named) {
        out += wrap(COLORS.tag, t);
        named = true;
      } else {
        out += wrap(COLORS.attr, t);
      }
    } else {
      out += escapeHtml(t);
    }
  }
  return out;
}

function hlMarkup(line: string): string {
  let out = "";
  let last = 0;
  let m: RegExpExecArray | null;
  const re = /<[^>]*>/g;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) out += escapeHtml(line.slice(last, m.index));
    out += hlTag(m[0]);
    last = m.index + m[0].length;
  }
  if (last < line.length) out += escapeHtml(line.slice(last));
  return out;
}

/** Full-line comment for the language, or null if the line isn't one. */
function lineComment(line: string, lang: string): string | null {
  if (HASH_COMMENT.has(lang)) {
    const m = /^(\s*)(#.*)$/.exec(line);
    if (m) return escapeHtml(m[1]) + wrap(COLORS.comment, m[2]);
  }
  if (SLASH_COMMENT.has(lang)) {
    const m = /^(\s*)(\/\/.*)$/.exec(line);
    if (m) return escapeHtml(m[1]) + wrap(COLORS.comment, m[2]);
  }
  return null;
}

/** Highlight one line; returns an HTML string with colored spans. */
function highlightLine(line: string, language: string): string {
  const lang = normLang(language);
  if (lang === "markdown") {
    if (/^#{1,6}\s/.test(line)) return wrap(COLORS.heading, line);
    const bullet = /^(\s*[-*]\s)(.*)$/.exec(line);
    if (bullet) return wrap(COLORS.keyword, bullet[1]) + escapeHtml(bullet[2]);
    return escapeHtml(line);
  }

  const comment = lineComment(line, lang);
  if (comment !== null) return comment;

  // HTML / markup
  if (lang === "html" || lang === "markup") return hlMarkup(line);

  // Generic: split out string literals, highlight the rest as code.
  const tokens: Token[] = [];
  const stringRe = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g;
  let lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = stringRe.exec(line)) !== null) {
    if (m.index > lastIndex) tokens.push({ text: line.slice(lastIndex, m.index), cls: "" });
    tokens.push({ text: m[0], cls: COLORS.string });
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < line.length) tokens.push({ text: line.slice(lastIndex), cls: "" });

  return tokens
    .map((t) => (t.cls ? wrap(t.cls, t.text) : hlCode(t.text)))
    .join("");
}

export default function CodeBlock({
  content,
  language,
}: {
  content: string;
  language: string;
}) {
  const lines = useMemo(() => content.replace(/\n$/, "").split("\n"), [content]);
  const isProse = normLang(language) === "markdown" || normLang(language) === "text";

  return (
    <div className="code-scroll h-full overflow-auto p-4 font-mono text-[12.5px] leading-[1.6]">
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((line, i) => (
            <tr key={i} className="align-top">
              {!isProse && (
                <td className="w-8 select-none pr-4 text-right text-slate-600">{i + 1}</td>
              )}
              <td
                className="whitespace-pre-wrap break-words text-slate-200"
                dangerouslySetInnerHTML={{ __html: highlightLine(line, language) || "&nbsp;" }}
              />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


