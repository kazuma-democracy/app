# WA Commons Browser Extension Privacy Policy

Effective date: 2026-09-11

WA Commons Browser Extension v0.1 is designed to work locally in the browser without a WA Commons account or always-on WA Commons application server.

## Data sent to WA Commons

The extension does not send browsing history, page contents, search queries, selected text, company selections, or policy choices to a WA Commons server.

WA Commons does not operate telemetry or analytics in v0.1.

## Data stored locally

The extension stores only the user's selected policy profile in browser local extension storage.

The bundled public Evidence Pack is part of the extension package and is read locally.

## Current-page access

When the user explicitly presses the page-hint button, the extension temporarily uses the browser's `activeTab` and `scripting` permissions.

It reads only:
- selected text, limited to 256 characters;
- the current page title, limited to 256 characters;
- the current hostname as context.

This information is used locally to produce search candidates. It is not used as authoritative company identity evidence, is not automatically persisted, and is not transmitted to WA Commons.

The extension does not request persistent access to all websites and does not request browsing-history or cookie permissions.

## External links

Evidence cards may contain links to original source pages or the WA Commons GitHub issue tracker. Those websites receive normal browser requests only when the user chooses to open a link.

Their own privacy policies apply after the user leaves the extension.

## Evidence and company data

The extension contains a rights-reviewed public projection of company identity and Evidence data.

Restricted raw source rows are not bundled. Missing, unresolved, disputed, expired, or not-integrated information is not converted into a positive safety or ethical judgment.

## Sale or advertising use

WA Commons v0.1 does not sell personal data, use personal data for advertising, or include advertising trackers.

## Changes and contact

Material privacy changes should be documented in the public WA Commons repository before a new extension release.

Questions, corrections, and challenges can be raised through the public repository issue tracker:
https://github.com/kazuma-democracy/wa-commons/issues
