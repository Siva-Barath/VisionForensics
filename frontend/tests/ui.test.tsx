import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import AuthShell from '@/components/AuthShell';
import ServiceHealthPanel from '@/components/ServiceHealthPanel';
import { DocumentViewer } from '@/features/explainability/components/DocumentViewer';
import { rawModelSummary } from '@/utils/analysisPresentation';
import ForensicModules from '@/features/explainability/components/ForensicModules';
import UserManagement from '@/components/UserManagement';
import api from '@/services/api';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost:5173' });
Object.assign(globalThis, { window: dom.window, document: dom.window.document, HTMLElement: dom.window.HTMLElement,
  MouseEvent: dom.window.MouseEvent, IS_REACT_ACT_ENVIRONMENT: true });

test('Authentication shell provides one clear sign-in heading', () => {
  const html = renderToStaticMarkup(<AuthShell><form aria-label="Controlled login"><input aria-label="Email" /></form></AuthShell>);
  assert.match(html, /Welcome back/);
  assert.equal((html.match(/<h1/g) ?? []).length, 1);
  assert.doesNotMatch(html, /FIPS|ISO\/IEC|guarantee authenticity/);
});

test('Health does not display success or a TLS version without evidence', () => {
  const html = renderToStaticMarkup(<ServiceHealthPanel health={null} />);
  assert.equal((html.match(/Not verified/g) ?? []).length, 5);
  assert.doesNotMatch(html, /System Operational|TLS 1\.3|Connected/);
});

test('Raw model result is independent of a heuristic document class', () => {
  const summary = rawModelSummary({ raw_ml: { available: true, status: 'SUCCESS', forgery_probability: .42,
    predicted_class: 'FORGED', risk_tier: 'SUSPICIOUS', operational_threshold: .40, feature_completeness: 1,
    imputed_features: {}, top_contributing_features: {}, source_page_index: 1,
    selection_method: 'maximum_page_probability', is_document_probability: false } });
  assert.match(summary, /Page 2: 42\.0%/);
  assert.match(summary, /Raw class: FORGED/);
  assert.match(summary, /not a document-wide probability/);
  assert.match(rawModelSummary({ raw_ml: null }), /unavailable/);
  assert.doesNotMatch(rawModelSummary({ raw_ml: null }), /0%|authentic/i);
});

test('Viewer zoom, page navigation and click-to-inspect work with real React events', async () => {
  const container = document.createElement('div');
  document.body.append(container);
  const root = createRoot(container);
  const selected: string[] = [];
  const pages: number[] = [];
  const regions = [
    { id: 'page0', type: 'IMAGE', detector: 'ela', severity: 70, confidence: .8, description: 'Controlled region',
      points: [[10, 10], [30, 10], [30, 30], [10, 30]], page_index: 0 },
    { id: 'page1', type: 'IMAGE', detector: 'ela', severity: 30, confidence: .7, description: 'Other page',
      points: [[40, 40], [60, 40], [60, 60], [40, 60]], page_index: 1 },
  ];
  const props = { imageUrl: '/controlled-image', regions, imageDimensions: { width: 200, height: 160 },
    selectedRegionId: null, hoveredRegionId: null, onRegionSelected: (region: any) => selected.push(region?.id),
    onRegionHovered: () => {}, currentPage: 0, pageCount: 2, onPageChange: (page: number) => pages.push(page) };
  await act(async () => root.render(<DocumentViewer {...props} />));
  const image = container.querySelector('img')!;
  Object.defineProperties(image, { naturalWidth: { value: 200 }, naturalHeight: { value: 160 } });
  await act(async () => image.dispatchEvent(new dom.window.Event('load', { bubbles: true })));
  assert.equal(container.querySelectorAll('polygon').length, 1);
  await act(async () => container.querySelector('polygon')!.dispatchEvent(new MouseEvent('click', { bubbles: true })));
  assert.deepEqual(selected, ['page0']);
  await act(async () => (container.querySelector('[aria-label="Next Page"]') as HTMLButtonElement).click());
  assert.deepEqual(pages, [1]);
  await act(async () => (container.querySelector('[aria-label="Zoom In"]') as HTMLButtonElement).click());
  assert.match(container.textContent ?? '', /125%/);
  await act(async () => root.unmount());
  container.remove();
});

test('Route primitives remain compatible after the security dependency update', () => {
  const html = renderToStaticMarkup(<MemoryRouter><p>Investigation workspace</p></MemoryRouter>);
  assert.match(html, /Investigation workspace/);
});

test('Legacy analysis never invents completed module results', () => {
  const html = renderToStaticMarkup(<ForensicModules analysis={{ raw_ml: null } as any} onDetails={() => {}} />);
  assert.equal((html.match(/>UNAVAILABLE</g) ?? []).length, 9);
  assert.match(html, /NOT IMPLEMENTED/);
  assert.doesNotMatch(html, />COMPLETED</);
});

test('ELA toggle displays only the actual artifact and fails visibly on load error', async () => {
  const container = document.createElement('div');
  document.body.append(container);
  const root = createRoot(container);
  const props = { imageUrl: '/preview', regions: [], selectedRegionId: null, hoveredRegionId: null,
    onRegionSelected: () => {}, onRegionHovered: () => {} };
  await act(async () => root.render(<DocumentViewer {...props} />));
  assert.equal((container.querySelector('[aria-pressed]') as HTMLButtonElement).disabled, true);
  await act(async () => root.render(<DocumentViewer {...props} heatmapUrl="/actual-stored-ela" />));
  await act(async () => container.querySelector('img')!.dispatchEvent(new dom.window.Event('load')));
  await act(async () => (container.querySelector('[aria-pressed]') as HTMLButtonElement).click());
  const map = container.querySelector('img[alt="Derived normalized ELA error map"]')!;
  assert.equal(map.getAttribute('src'), '/actual-stored-ela');
  assert.equal(container.querySelectorAll('[style*="radial-gradient"]').length, 0);
  await act(async () => map.dispatchEvent(new dom.window.Event('error')));
  assert.match(container.textContent ?? '', /Stored ELA map could not be loaded/);
  assert.equal((container.querySelector('[aria-pressed]') as HTMLButtonElement).disabled, true);
  await act(async () => root.unmount());
  container.remove();
});

test('Account management prevents self-deactivation and calls the protected status API', async () => {
  const originalAdapter = api.defaults.adapter;
  const calls: string[] = [];
  let active = true;
  api.defaults.adapter = async config => {
    calls.push(`${config.method} ${config.url}`);
    if (config.method === 'put') active = false;
    const users = [{ id: 'self', full_name: 'Current administrator', email: 'self@example.test', role: 'SYSTEM_ADMINISTRATOR', is_active: true },
      { id: 'other', full_name: 'Controlled analyst', email: 'other@example.test', role: 'FORENSIC_ANALYST', is_active: active }];
    return { data: config.method === 'get' ? users : users[1], status: 200, statusText: 'OK', headers: {}, config };
  };
  const container = document.createElement('div');
  document.body.append(container);
  const root = createRoot(container);
  try {
    await act(async () => root.render(<UserManagement currentUserId="self" />));
    const self = [...container.querySelectorAll('button')].find(button => button.textContent === 'Your account')!;
    assert.equal(self.disabled, true);
    const deactivate = [...container.querySelectorAll('button')].find(button => button.textContent === 'Deactivate')!;
    await act(async () => deactivate.click());
    assert.ok(calls.includes('put /admin/users/other/status'));
    assert.ok([...container.querySelectorAll('button')].some(button => button.textContent === 'Activate'));
  } finally {
    await act(async () => root.unmount());
    container.remove();
    api.defaults.adapter = originalAdapter;
  }
});
