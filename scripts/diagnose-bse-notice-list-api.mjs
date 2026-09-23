const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
const BASE = "https://www.bseindices.com/AsiaIndexAPI";
const URLS = [
  BASE + "/api/GetLatestNotices/w",
  BASE + "/api/GetNoticesadvancesearch_newcomb/w",
  BASE + "/api/NoticesAsiaDownload/w?NoticeId=20260113-26",
  BASE + "/api/DisplayNoticecircular/w?NoticeId=20260113-26"
];

function summarizeJson(value) {
  if (Array.isArray(value)) {
    return {
      type: "array",
      length: value.length,
      sample: value.slice(0, 2)
    };
  }
  if (value && typeof value === "object") {
    const result = {
      type: "object",
      keys: Object.keys(value).slice(0, 20)
    };
    for (const [key, child] of Object.entries(value).slice(0, 12)) {
      if (Array.isArray(child)) {
        result[key] = {
          type: "array",
          length: child.length,
          sample: child.slice(0, 2)
        };
      } else if (child && typeof child === "object") {
        result[key] = { type: "object", keys: Object.keys(child).slice(0, 20) };
      } else {
        result[key] = child;
      }
    }
    return result;
  }
  return { type: typeof value, value };
}

for (const url of URLS) {
  try {
    const response = await fetch(url, {
      headers: {
        "user-agent": USER_AGENT,
        "accept": "application/json,*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.bseindices.com/notices"
      },
      signal: AbortSignal.timeout(20000)
    });
    const body = await response.text();
    let parsed = null;
    let json_error = null;
    try {
      parsed = JSON.parse(body);
    } catch (error) {
      json_error = String(error?.message || error);
    }
    console.log(JSON.stringify({
      url,
      status: response.status,
      ok: response.ok,
      content_type: response.headers.get("content-type"),
      bytes: body.length,
      json_error,
      json_summary: parsed === null ? null : summarizeJson(parsed),
      body_prefix: parsed === null ? body.slice(0, 400) : null
    }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      url,
      fetch_error: String(error?.message || error)
    }, null, 2));
  }
}
