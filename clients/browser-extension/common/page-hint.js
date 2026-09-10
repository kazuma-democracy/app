(() => {
  const selectedText = String(
    globalThis.getSelection?.()?.toString() ?? "",
  ).slice(0, 256);
  const title = String(document.title ?? "").slice(0, 256);
  const hostname = String(
    globalThis.location?.hostname ?? "",
  ).slice(0, 256);
  return { selectedText, title, hostname };
})();
