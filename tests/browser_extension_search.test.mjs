import test from "node:test";
import assert from "node:assert/strict";
import {
  normalizeQuery,
  searchCompanies,
} from "../clients/browser-extension/common/search.mjs";

const pack = {
  companies: [
    {
      corporate_number: "2222222222222",
      canonical_name: "合成電機株式会社",
      security_code: "2002",
      aliases: [],
    },
    {
      corporate_number: "1111111111111",
      canonical_name: "合成株式会社",
      security_code: "1001",
      aliases: ["合成"],
    },
  ],
};

test("security code and name searches are deterministic", () => {
  assert.deepEqual(
    searchCompanies(pack, "１００１").map((x) => x.security_code),
    ["1001"],
  );
  assert.deepEqual(
    searchCompanies(pack, "合成").map((x) => x.security_code),
    ["1001", "2002"],
  );
});

test("query normalization is limited and deterministic", () => {
  assert.equal(normalizeQuery("  ＡＢＣ　株式会社 "), "abc 株式会社");
  assert.equal(normalizeQuery(""), "");
});

test("empty query returns no candidates", () => {
  assert.deepEqual(searchCompanies(pack, "   "), []);
});
