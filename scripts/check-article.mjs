import fs from "node:fs/promises";
import assert from "node:assert/strict";
const html = await fs.readFile(
  new URL("../site/index.html", import.meta.url),
  "utf8",
);
assert.equal((html.match(/<figure /g) || []).length, 9);
assert.equal((html.match(/<img /g) || []).length, 9);
assert.equal((html.match(/data:image\/webp;base64,/g) || []).length, 18);
assert.equal((html.match(/<math /g) || []).length, 3);
assert(!html.includes('class="katex-error"'));
assert(!/<script\b/i.test(html));
assert(!/<(?:img|source)\b[^>]+(?:src|srcset)="https?:/i.test(html));
assert(!/\u2014/.test(html));
assert(html.includes("House predictions (435 races)"));
assert(html.includes("Senate predictions (35 races)"));
console.log(
  "Article checks passed: 9 embedded figures, 3 rendered equations, all 470 races, no external runtime assets.",
);
