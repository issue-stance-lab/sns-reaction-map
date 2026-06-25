#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function parseArgs(argv) {
  const args = { query: [], output: "", markdown: "", waitMs: 6000, dedupe: false };
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === "--query") args.query.push(argv[++i]);
    else if (key === "--output") args.output = argv[++i];
    else if (key === "--markdown") args.markdown = argv[++i];
    else if (key === "--wait-ms") args.waitMs = Number(argv[++i]);
    else if (key === "--dedupe") args.dedupe = true;
    else if (key === "--help" || key === "-h") {
      console.log("usage: fetch_yahoo_realtime_node.mjs --query QUERY [--query QUERY] --output FILE [--markdown FILE] [--dedupe] [--wait-ms 6000]");
      process.exit(0);
    }
  }
  if (!args.query.length || !args.output) {
    throw new Error("--query and --output are required");
  }
  return args;
}

function resolveProject(filePath) {
  return path.isAbsolute(filePath) ? filePath : path.join(projectRoot, filePath);
}

function cleanUrl(url) {
  return url && url.includes("?") ? url.split("?")[0] : url;
}

function extractEntries(html) {
  const match = html.match(/<script id="__NEXT_DATA__" type="application\/json">(.*?)<\/script>/s);
  if (!match) return { total: 0, entries: [] };
  const data = JSON.parse(match[1]);
  const timeline = data?.props?.pageProps?.pageData?.timeline || {};
  return {
    total: Number(timeline?.head?.totalResultsAvailable || 0),
    entries: Array.isArray(timeline.entry) ? timeline.entry : [],
  };
}

async function fetchQuery(page, query, waitMs) {
  const url = `https://search.yahoo.co.jp/realtime/search?p=${encodeURIComponent(query)}`;
  console.log(`fetch: ${query} -> ${url}`);
  await page.goto(url, { timeout: 90000, waitUntil: "domcontentloaded" });
  await page.waitForTimeout(waitMs);
  const { total, entries } = extractEntries(await page.content());
  const fetchedAt = new Date().toISOString();
  const rows = [];
  for (const entry of entries) {
    const text = entry.displayTextBody || "";
    if (!text) continue;
    const tweetId = entry.tweetId || entry.id || "";
    const url = cleanUrl(entry.url || "");
    rows.push({
      query,
      fetched_at: fetchedAt,
      text,
      tweet_id: tweetId,
      url: url || (tweetId ? `https://x.com/i/status/${tweetId}` : ""),
      user_id: entry.thid || entry.userId || "",
      source: "yahoo_realtime",
    });
  }
  console.log(`  total_available=${total} returned=${rows.length}`);
  return { total, rows };
}

function writeMarkdown(filePath, rows, totals) {
  const lines = ["# Yahooリアルタイム検索 取得サンプル", "", `取得件数: ${rows.length}`, "", "## 検索語別表示件数", ""];
  for (const [query, total] of Object.entries(totals)) {
    lines.push(`- \`${query}\`: Yahoo表示 ${total}件`);
  }
  lines.push("", "## サンプル", "");
  rows.forEach((row, index) => {
    lines.push(`### ${index + 1}. \`${row.query}\``, "", row.text.replaceAll("\n", " / "), "", row.url || "", "");
  });
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, lines.join("\n"), "utf8");
}

async function main() {
  const args = parseArgs(process.argv);
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport: { width: 1920, height: 1080 },
    locale: "ja-JP",
    timezoneId: "Asia/Tokyo",
  });
  const page = await context.newPage();
  const allRows = [];
  const totals = {};
  for (const query of args.query) {
    const { total, rows } = await fetchQuery(page, query, args.waitMs);
    totals[query] = total;
    allRows.push(...rows);
  }
  await browser.close();

  let rows = allRows;
  if (args.dedupe) {
    const seen = new Set();
    rows = [];
    for (const row of allRows) {
      const key = row.tweet_id || row.url || row.text;
      if (seen.has(key)) continue;
      seen.add(key);
      rows.push(row);
    }
  }

  const output = resolveProject(args.output);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(rows, null, 2), "utf8");
  if (args.markdown) {
    writeMarkdown(resolveProject(args.markdown), rows, totals);
  }
  console.log(`saved=${output} rows=${rows.length}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
