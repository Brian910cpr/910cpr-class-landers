import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../docs/assets/analytics-attribution.js", import.meta.url), "utf8");

function run({ referrer = "", search = "", cookie = "", href = "https://coastalcprtraining.enrollware.com/enroll?id=12345" } = {}) {
  const listeners = {};
  const attributes = new Map([["href", href]]);
  const link = {
    dataset: {},
    get href() { return attributes.get("href"); },
    getAttribute(name) { return attributes.get(name) || null; },
    setAttribute(name, value) { attributes.set(name, value); }
  };
  const document = {
    cookie,
    referrer,
    documentElement: {},
    querySelectorAll() { return [link]; },
    addEventListener(name, handler) { listeners[name] = handler; }
  };
  const session = new Map();
  const context = {
    URL,
    URLSearchParams,
    document,
    location: { href: "https://www.910cpr.com/bls.html" + search, hostname: "www.910cpr.com", pathname: "/bls.html", search },
    sessionStorage: { getItem: key => session.get(key) || null, setItem: (key, value) => session.set(key, value) },
    MutationObserver: class { observe() {} },
    window: { dataLayer: [] }
  };
  vm.runInNewContext(source, context);
  return { attributes, context, link, listeners };
}

test("decorates Enrollware handoff with the real organic source", () => {
  const result = run({ referrer: "https://www.google.com/search?q=bls+wilmington" });
  const destination = new URL(result.attributes.get("href"));
  assert.equal(destination.searchParams.get("utm_source"), "google");
  assert.equal(destination.searchParams.get("utm_medium"), "organic");
  assert.equal(destination.searchParams.get("utm_campaign"), "910cpr_registration");
  assert.equal(destination.searchParams.get("utm_content"), "bls-html_id-12345");
});

test("preserves genuine ChatGPT referral attribution and emits registration", () => {
  const result = run({ referrer: "https://chatgpt.com/" });
  result.listeners.click({ target: { closest: () => result.link } });
  const event = result.context.window.dataLayer.at(-1);
  assert.equal(event.event, "begin_registration");
  assert.equal(event.acquisition_source, "chatgpt.com");
  assert.equal(event.acquisition_medium, "ai-assistant");
  assert.equal(event.session_id, "12345");
  assert.equal(result.link.dataset.attributionBeginRegistration, "1");
});

test("does not turn an apex-to-www visit into a 910cpr self-referral", () => {
  const result = run({ referrer: "https://910cpr.com/bls.html" });
  const destination = new URL(result.attributes.get("href"));
  assert.equal(destination.searchParams.get("utm_source"), "direct");
  assert.equal(destination.searchParams.get("utm_medium"), "none");
});

test("does nothing on an excluded work device", () => {
  const result = run({ cookie: "lw_analytics_excluded=1" });
  assert.equal(result.attributes.get("href"), "https://coastalcprtraining.enrollware.com/enroll?id=12345");
  assert.equal(result.listeners.click, undefined);
});
