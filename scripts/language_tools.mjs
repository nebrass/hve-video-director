#!/usr/bin/env node
import { readFileSync } from "node:fs";

const unspacedScripts = new Set(["Hans", "Hant", "Jpan", "Thai", "Laoo", "Khmr", "Mymr"]);

function localeInfo(tag) {
  if (typeof tag !== "string" || !tag.trim()) {
    throw new Error("language must be a nonempty BCP 47 tag");
  }
  const locale = new Intl.Locale(tag.trim());
  if (["und", "mul", "zxx"].includes(locale.language)) {
    throw new Error("choose a specific language, not und, mul, or zxx");
  }
  const script = locale.maximize().script;
  const direction = (locale.getTextInfo?.() ?? locale.textInfo)?.direction;
  if (!script || !["ltr", "rtl"].includes(direction)) {
    throw new Error(`cannot resolve script/direction for ${tag}; use a supported locale and full-ICU Node`);
  }
  return {
    tag: locale.toString(),
    language: locale.language,
    script,
    direction,
    name: new Intl.DisplayNames(["en"], { type: "language" }).of(locale.toString()),
    word_separator: unspacedScripts.has(script) ? "" : " ",
  };
}

function run(operation, input) {
  if (typeof Intl.Locale !== "function" || typeof Intl.Segmenter !== "function"
      || typeof Intl.DisplayNames !== "function") {
    throw new Error("language handling requires Node with Intl.Locale, Intl.Segmenter, and Intl.DisplayNames");
  }
  if (operation === "locales") {
    if (!Array.isArray(input)) throw new Error("locales input must be an array of language tags");
    return input.map(localeInfo);
  }
  if (operation === "segment") {
    if (!input || !Array.isArray(input.texts)
        || input.texts.some((text) => typeof text !== "string")) {
      throw new Error("segment input requires language and a texts array of strings");
    }
    const locale = localeInfo(input.language);
    if (!Intl.Segmenter.supportedLocalesOf([locale.tag]).length) {
      throw new Error(`Node ICU does not support segmentation for ${locale.tag}`);
    }
    const graphemes = new Intl.Segmenter(locale.tag, { granularity: "grapheme" });
    const words = new Intl.Segmenter(locale.tag, { granularity: "word" });
    return {
      locale,
      texts: input.texts.map((text) => ({
        graphemes: Array.from(graphemes.segment(text), (part) => part.segment),
        words: Array.from(words.segment(text), (part) => ({
          text: part.segment,
          word: part.isWordLike,
        })),
      })),
    };
  }
  throw new Error(`unknown language operation: ${operation}`);
}

try {
  const result = run(process.argv[2], JSON.parse(readFileSync(0, "utf8")));
  process.stdout.write(`${JSON.stringify(result)}\n`);
} catch (error) {
  process.stderr.write(`Language error: ${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 2;
}
