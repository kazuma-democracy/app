export function normalizeQuery(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/\s+/gu, " ")
    .trim();
}

function companyKey(company) {
  return [
    normalizeQuery(company.canonical_name),
    String(company.corporate_number ?? ""),
  ];
}

export function searchCompanies(pack, query) {
  const normalized = normalizeQuery(query);
  if (!normalized) return [];
  const companies = Array.isArray(pack?.companies) ? pack.companies : [];

  const exactCode = companies.filter(
    (company) => normalizeQuery(company.security_code) === normalized,
  );
  const source = exactCode.length
    ? exactCode
    : companies.filter((company) => {
        const values = [
          company.canonical_name,
          ...(Array.isArray(company.aliases) ? company.aliases : []),
        ];
        return values.some((value) => normalizeQuery(value).includes(normalized));
      });

  return [...source].sort((left, right) => {
    const [ln, lc] = companyKey(left);
    const [rn, rc] = companyKey(right);
    return ln.localeCompare(rn, "ja") || lc.localeCompare(rc);
  });
}
